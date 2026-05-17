"""
Reviewify — AI-powered reviewer generator (v2).

What's new in v2:
  - Multiple lesson upload (PDF + PPT/PPTX mixed) compiled into ONE reviewer.
  - Reorder lessons before generation (drag-and-drop in the UI).
  - Smarter extraction: keywords, formulas, dedupe, image extraction.
  - Embedded diagrams/figures in the generated reviewer (HTML, PDF, DOCX).

Run locally:
    python -m venv .venv
    .\\.venv\\Scripts\\Activate.ps1     (Windows PowerShell)
    pip install -r requirements.txt
    python app.py
"""
import os
import re
import json
import uuid
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_from_directory, abort, flash,
)
from werkzeug.utils import secure_filename

from utils.extract import extract_document
from utils.summarize import summarize_sections
from utils.export import export_pdf, export_docx

BASE = Path(__file__).parent
STATIC_DIR = BASE / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
EXPORT_DIR = BASE / "exports"
DB_PATH = BASE / "database" / "reviewify.db"
ALLOWED = {".pdf", ".ppt", ".pptx"}
MAX_MB = 60   # bumped: multi-file uploads

for d in (UPLOAD_DIR, EXPORT_DIR, DB_PATH.parent):
    d.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024
app.secret_key = "reviewify-dev-secret-change-me"


# ---------- DB ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reviewers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'concise',
                content_json TEXT NOT NULL
            );
        """)


init_db()


# ---------- helpers ----------
def _lesson_title_from(filename: str) -> str:
    stem = Path(filename).stem
    # strip leading "01_", "Lesson 1 - ", etc but keep them as ordering hints
    cleaned = re.sub(r"^[\s_\-]+", "", stem)
    cleaned = cleaned.replace("_", " ").replace("-", " ").strip()
    return cleaned or stem


def _natural_key(name: str):
    parts = re.split(r"(\d+)", name.lower())
    return [int(p) if p.isdigit() else p for p in parts]


# ---------- Routes ----------
@app.route("/")
def index():
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, source_filename, created_at, mode "
            "FROM reviewers ORDER BY created_at DESC LIMIT 24"
        ).fetchall()
    return render_template("index.html", recent=rows)


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    mode = request.form.get("mode", "concise")
    use_ai = request.form.get("use_ai") == "on"
    compiled_title = (request.form.get("title") or "").strip()
    # client-supplied ordering: comma-separated original indices
    order_raw = (request.form.get("order") or "").strip()

    files = [f for f in files if f and f.filename]
    if not files:
        flash("Please select at least one file.", "error")
        return redirect(url_for("index"))

    # honour client reorder, then natural-sort the rest
    if order_raw:
        try:
            order = [int(x) for x in order_raw.split(",") if x.strip().isdigit()]
            files = [files[i] for i in order if 0 <= i < len(files)]
        except Exception:
            pass
    else:
        files.sort(key=lambda f: _natural_key(f.filename or ""))

    batch_id = uuid.uuid4().hex
    image_dir = UPLOAD_DIR / batch_id / "images"
    image_url_prefix = f"/static/uploads/{batch_id}/images"

    lessons = []
    sources = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            flash(f"Skipped {f.filename}: unsupported type.", "error")
            continue

        safe_name = secure_filename(f.filename)
        stored = UPLOAD_DIR / batch_id / safe_name
        stored.parent.mkdir(parents=True, exist_ok=True)
        f.save(stored)

        try:
            sections = extract_document(
                stored,
                image_dir=image_dir,
                image_url_prefix=image_url_prefix,
            )
            sections = summarize_sections(sections, mode=mode, use_ai=use_ai)
        except Exception as e:
            flash(f"Failed to process {safe_name}: {e}", "error")
            continue

        lessons.append({
            "title": _lesson_title_from(safe_name),
            "source": safe_name,
            "sections": sections,
        })
        sources.append(safe_name)

    if not lessons:
        flash("No files could be processed.", "error")
        return redirect(url_for("index"))

    title = compiled_title or (
        lessons[0]["title"] if len(lessons) == 1
        else f"Compiled Reviewer ({len(lessons)} lessons)"
    )
    rid = batch_id
    with db() as conn:
        conn.execute(
            "INSERT INTO reviewers(id,title,source_filename,created_at,mode,content_json) "
            "VALUES (?,?,?,?,?,?)",
            (
                rid, title, ", ".join(sources),
                datetime.utcnow().isoformat(timespec="seconds"),
                mode,
                json.dumps({"lessons": lessons}, ensure_ascii=False),
            ),
        )
    return redirect(url_for("reviewer", rid=rid))


@app.route("/reviewer/<rid>")
def reviewer(rid):
    with db() as conn:
        row = conn.execute("SELECT * FROM reviewers WHERE id=?", (rid,)).fetchone()
    if not row:
        abort(404)
    payload = json.loads(row["content_json"])
    # backwards compat: old rows stored a list of sections
    if isinstance(payload, list):
        lessons = [{"title": row["title"], "source": row["source_filename"],
                    "sections": payload}]
    else:
        lessons = payload.get("lessons", [])
    return render_template("reviewer.html", r=row, lessons=lessons)


@app.route("/reviewer/<rid>/export/<fmt>")
def export(rid, fmt):
    with db() as conn:
        row = conn.execute("SELECT * FROM reviewers WHERE id=?", (rid,)).fetchone()
    if not row:
        abort(404)
    payload = json.loads(row["content_json"])
    if isinstance(payload, list):
        lessons = [{"title": row["title"], "source": row["source_filename"],
                    "sections": payload}]
    else:
        lessons = payload.get("lessons", [])

    safe_title = re.sub(r"[^\w\-]+", "_", row["title"])[:60] or "reviewer"
    out_name = f"{safe_title}_{rid[:6]}.{fmt}"
    out_path = EXPORT_DIR / out_name
    if fmt == "pdf":
        export_pdf(row["title"], lessons, out_path, static_root=STATIC_DIR)
    elif fmt == "docx":
        export_docx(row["title"], lessons, out_path, static_root=STATIC_DIR)
    else:
        abort(400)
    return send_from_directory(EXPORT_DIR, out_name, as_attachment=True)


@app.route("/reviewer/<rid>/delete", methods=["POST"])
def delete(rid):
    with db() as conn:
        conn.execute("DELETE FROM reviewers WHERE id=?", (rid,))
    return redirect(url_for("index"))


@app.errorhandler(413)
def too_large(_):
    flash(f"File too large. Max {MAX_MB} MB total.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
