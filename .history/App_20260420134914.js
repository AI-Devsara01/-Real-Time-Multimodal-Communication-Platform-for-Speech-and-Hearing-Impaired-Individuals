/* ═══════════════════════════════════════════
   CommuniSense — Shared JS Utilities
   ═══════════════════════════════════════════ */

// ── Toast notifications ──────────────────────
const toastContainer = document.createElement('div');
toastContainer.className = 'toast-container';
document.body.appendChild(toastContainer);

function showToast(msg, type = 'info', duration = 3500) {
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = `<span>${icons[type]||'·'}</span><span>${msg}</span>`;
  toastContainer.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'slide-out 0.3s ease forwards';
    setTimeout(() => t.remove(), 300);
  }, duration);
}

// ── Loading overlay ──────────────────────────
const loadOverlay = document.createElement('div');
loadOverlay.className = 'loading-overlay';
loadOverlay.innerHTML = `<div class="spinner" style="width:40px;height:40px;border-width:3px"></div><p style="color:var(--text2);font-size:.9rem">Processing…</p>`;
document.body.appendChild(loadOverlay);

function setLoading(on) {
  loadOverlay.classList.toggle('active', on);
}

// ── Fetch wrapper ────────────────────────────
async function apiFetch(url, options = {}) {
  try {
    setLoading(true);
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  } catch (e) {
    showToast(e.message, 'error');
    throw e;
  } finally {
    setLoading(false);
  }
}

async function apiFetchForm(url, formData) {
  try {
    setLoading(true);
    const res = await fetch(url, { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  } catch (e) {
    showToast(e.message, 'error');
    throw e;
  } finally {
    setLoading(false);
  }
}

// ── Play base64 audio ────────────────────────
function playAudio(b64, fmt = 'mp3') {
  const audio = new Audio(`data:audio/${fmt};base64,${b64}`);
  audio.play();
  return audio;
}

// ── Copy to clipboard ────────────────────────
function copyText(text) {
  navigator.clipboard.writeText(text)
    .then(() => showToast('Copied to clipboard!', 'success'))
    .catch(() => showToast('Copy failed', 'error'));
}

// ── Animate elements on scroll ──────────────
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.style.opacity = '';
      e.target.style.transform = '';
      e.target.classList.add('animate-fade-up');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('[data-animate]').forEach(el => {
  el.style.opacity = '0';
  io.observe(el);
});

// ── Active nav link ──────────────────────────
document.querySelectorAll('.nav-link').forEach(link => {
  if (link.href === location.href || location.pathname.startsWith(link.getAttribute('href'))) {
    link.classList.add('active');
  }
});

// ── Cursor glow effect ───────────────────────
const cursorGlow = document.createElement('div');
cursorGlow.style.cssText = `
  position:fixed;width:400px;height:400px;
  background:radial-gradient(circle,rgba(79,139,255,0.04) 0%,transparent 70%);
  border-radius:50%;pointer-events:none;z-index:0;
  transform:translate(-50%,-50%);transition:opacity 0.3s;
`;
document.body.appendChild(cursorGlow);
document.addEventListener('mousemove', e => {
  cursorGlow.style.left = e.clientX + 'px';
  cursorGlow.style.top  = e.clientY + 'px';
});

// ── Logout ───────────────────────────────────
window.doLogout = async function() {
  await fetch('/api/logout', { method: 'POST' });
  location.href = '/login';
};