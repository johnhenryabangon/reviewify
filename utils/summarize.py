"""Summarization layer.

Two paths:
  - Extractive (default): frequency-based sentence ranking + keyword boost.
  - AI (optional): Hugging Face transformers `sshleifer/distilbart-cnn-12-6`.
"""
from __future__ import annotations
from typing import List, Dict
import re

_AI_PIPELINE = None


def summarize_sections(sections: List[Dict], mode: str = "concise",
                       use_ai: bool = False) -> List[Dict]:
    summarizer = _get_ai() if use_ai else None
    target = 2 if mode == "concise" else 5

    for s in sections:
        text = (s.get("body") or "").strip()
        # If the slide is mostly bullets, synthesize a short overview from them.
        if not text and s.get("bullets"):
            text = " ".join(s["bullets"])

        if not text:
            s["summary"] = ""
            continue
        if summarizer and len(text.split()) > 60:
            s["summary"] = _ai_summarize(summarizer, text, mode)
        else:
            s["summary"] = _extractive(text, target, s.get("keywords") or [])
    return sections


# ---------- Extractive ----------
_STOP = set("""a an the and or but if while of in on at to for with by from is are was were be been being
this that these those it its as not no do does did has have had will would can could should may might
i you he she we they them his her our their your my me us""".split())


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _extractive(text: str, n: int, keywords: List[str]) -> str:
    sentences = _split_sentences(text)
    if len(sentences) <= n:
        return " ".join(sentences)

    freq: Dict[str, int] = {}
    for w in re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower()):
        if w in _STOP or len(w) < 3:
            continue
        freq[w] = freq.get(w, 0) + 1

    kw_set = {k.lower() for k in keywords}
    scored = []
    for idx, sent in enumerate(sentences):
        words = re.findall(r"[A-Za-z][A-Za-z\-']+", sent.lower())
        if not words:
            continue
        base = sum(freq.get(w, 0) for w in words) / len(words)
        boost = 1.5 if any(k in sent.lower() for k in kw_set) else 1.0
        # prefer earlier sentences slightly (lecture flow)
        position = 1.0 + (0.2 if idx == 0 else 0.0)
        scored.append((base * boost * position, idx, sent))
    if not scored:
        return " ".join(sentences[:n])
    top = sorted(scored, reverse=True)[:n]
    top.sort(key=lambda x: x[1])
    return " ".join(s for _, _, s in top)


# ---------- AI ----------
def _get_ai():
    global _AI_PIPELINE
    if _AI_PIPELINE is not None:
        return _AI_PIPELINE
    try:
        from transformers import pipeline
        _AI_PIPELINE = pipeline("summarization",
                                model="sshleifer/distilbart-cnn-12-6")
        return _AI_PIPELINE
    except Exception as e:
        print(f"[summarize] AI summarizer unavailable, falling back: {e}")
        return None


def _ai_summarize(pipe, text: str, mode: str) -> str:
    max_len = 80 if mode == "concise" else 180
    min_len = 25 if mode == "concise" else 60
    words = text.split()
    if len(words) > 900:
        text = " ".join(words[:900])
    try:
        out = pipe(text, max_length=max_len, min_length=min_len,
                   do_sample=False)
        return out[0]["summary_text"].strip()
    except Exception as e:
        print(f"[summarize] AI failed: {e}")
        return _extractive(text, 2 if mode == "concise" else 5, [])
