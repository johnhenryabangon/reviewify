// Theme toggle
const tt = document.getElementById('themeToggle');
if (tt) {
  tt.addEventListener('click', () => {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });
}

// ---- Upload queue: drag-drop, multi-add, reorder ----
const dz = document.getElementById('dropzone');
const input = document.getElementById('files');
const queueWrap = document.getElementById('queueWrap');
const queueEl = document.getElementById('queue');
const orderInput = document.getElementById('orderInput');
const clearBtn = document.getElementById('clearBtn');
const form = document.getElementById('uploadForm');
const submitBtn = document.getElementById('submitBtn');
const progress = document.getElementById('progress');

// Authoritative ordered list of File objects.
let queue = [];

function fileIcon(name) {
  const ext = (name.split('.').pop() || '').toLowerCase();
  if (ext === 'pdf') return '📕';
  if (ext === 'ppt' || ext === 'pptx') return '📊';
  return '📄';
}

function render() {
  if (!queueEl) return;
  queueEl.innerHTML = '';
  queue.forEach((f, idx) => {
    const li = document.createElement('li');
    li.className = 'flex items-center gap-3 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/60 cursor-grab';
    li.dataset.idx = idx;
    li.innerHTML = `
      <span class="text-slate-400 select-none">⋮⋮</span>
      <span class="text-lg">${fileIcon(f.name)}</span>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-medium truncate">${f.name}</div>
        <div class="text-xs text-slate-500">${(f.size / 1024).toFixed(0)} KB · Lesson ${idx + 1}</div>
      </div>
      <button type="button" class="text-xs text-slate-400 hover:text-red-500" data-remove="${idx}">Remove</button>
    `;
    queueEl.appendChild(li);
  });
  queueWrap.classList.toggle('hidden', queue.length === 0);
  syncFileInput();
}

function syncFileInput() {
  // Rebuild the FileList in queue order so the server receives them sorted.
  if (!input) return;
  const dt = new DataTransfer();
  queue.forEach(f => dt.items.add(f));
  input.files = dt.files;
  if (orderInput) {
    orderInput.value = queue.map((_, i) => i).join(',');
  }
}

function addFiles(fileList) {
  const allowed = ['pdf', 'ppt', 'pptx'];
  [...fileList].forEach(f => {
    const ext = (f.name.split('.').pop() || '').toLowerCase();
    if (!allowed.includes(ext)) return;
    // de-dup by name+size
    if (queue.some(q => q.name === f.name && q.size === f.size)) return;
    queue.push(f);
  });
  render();
}

if (dz && input) {
  ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, e => {
    e.preventDefault(); dz.classList.add('border-indigo-500');
  }));
  ['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => {
    e.preventDefault(); dz.classList.remove('border-indigo-500');
  }));
  dz.addEventListener('drop', e => {
    if (e.dataTransfer?.files?.length) addFiles(e.dataTransfer.files);
  });
  input.addEventListener('change', () => {
    if (input.files?.length) {
      // user picked through dialog — append rather than replace
      const picked = [...input.files];
      // syncFileInput re-assigns input.files, so capture first
      addFiles(picked);
    }
  });
}

if (queueEl && window.Sortable) {
  Sortable.create(queueEl, {
    animation: 150,
    handle: 'li',
    onEnd: () => {
      const newOrder = [...queueEl.children].map(li => parseInt(li.dataset.idx, 10));
      queue = newOrder.map(i => queue[i]);
      render();
    },
  });
}

if (queueEl) {
  queueEl.addEventListener('click', e => {
    const t = e.target;
    if (t && t.dataset && t.dataset.remove !== undefined) {
      queue.splice(parseInt(t.dataset.remove, 10), 1);
      render();
    }
  });
}

if (clearBtn) {
  clearBtn.addEventListener('click', () => { queue = []; render(); });
}

if (form) {
  form.addEventListener('submit', () => {
    if (!queue.length) return;
    submitBtn?.setAttribute('disabled', 'disabled');
    submitBtn?.querySelector('.btn-label')?.classList.add('hidden');
    submitBtn?.querySelector('.btn-loading')?.classList.remove('hidden');
    progress?.classList.remove('hidden');
  });
}
