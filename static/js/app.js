// ============================================================
// COMMBRIDGE — Shared Utilities
// ============================================================

// CUSTOM CURSOR
(function() {
  const cursor = document.querySelector('.cursor');
  const ring = document.querySelector('.cursor-ring');
  if (!cursor || !ring) return;
  
  let mouseX = 0, mouseY = 0, ringX = 0, ringY = 0;
  
  document.addEventListener('mousemove', e => {
    mouseX = e.clientX; mouseY = e.clientY;
    cursor.style.transform = `translate(${mouseX - 5}px, ${mouseY - 5}px)`;
  });
  
  // Ring follows with lag
  function animateRing() {
    ringX += (mouseX - ringX) * 0.12;
    ringY += (mouseY - ringY) * 0.12;
    ring.style.transform = `translate(${ringX - 20}px, ${ringY - 20}px)`;
    requestAnimationFrame(animateRing);
  }
  animateRing();
  
  document.querySelectorAll('a, button, .btn, .key, .feature-card').forEach(el => {
    el.addEventListener('mouseenter', () => { cursor.style.transform += ' scale(2)'; ring.style.transform += ' scale(1.5)'; ring.style.borderColor = 'rgba(99,102,241,0.8)'; });
    el.addEventListener('mouseleave', () => { ring.style.borderColor = 'rgba(99,102,241,0.5)'; });
  });
})();

// PARTICLE CANVAS BACKGROUND
function initParticles(canvasId = 'bg-canvas') {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];
  
  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);
  
  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = (Math.random() - 0.5) * 0.3;
      this.alpha = Math.random() * 0.5;
      this.size = Math.random() * 1.5 + 0.5;
      this.color = Math.random() > 0.6 ? '#6366f1' : '#a855f7';
    }
    update() {
      this.x += this.vx; this.y += this.vy;
      if (this.x < 0 || this.x > W || this.y < 0 || this.y > H) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.globalAlpha = this.alpha;
      ctx.fill();
    }
  }
  
  for (let i = 0; i < 120; i++) particles.push(new Particle());
  
  // Connection lines
  function drawConnections() {
    ctx.globalAlpha = 1;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 100) {
          ctx.beginPath();
          ctx.strokeStyle = '#6366f1';
          ctx.globalAlpha = (1 - dist/100) * 0.08;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }
  }
  
  function animate() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });
    drawConnections();
    requestAnimationFrame(animate);
  }
  animate();
}

// TOAST NOTIFICATIONS
const Toast = {
  show(msg, type = 'info', duration = 3500) {
    let el = document.querySelector('.toast');
    if (!el) {
      el = document.createElement('div');
      el.className = 'toast';
      document.body.appendChild(el);
    }
    const icons = { success: '✓', error: '✕', info: '◆' };
    el.innerHTML = `<span>${icons[type] || '◆'}</span><span>${msg}</span>`;
    el.className = `toast toast-${type}`;
    requestAnimationFrame(() => { el.classList.add('show'); });
    clearTimeout(el._timer);
    el._timer = setTimeout(() => { el.classList.remove('show'); }, duration);
  },
  success(m) { this.show(m, 'success'); },
  error(m) { this.show(m, 'error'); },
  info(m) { this.show(m, 'info'); }
};

// LOADING STATES
function setLoading(btn, loading, text) {
  if (loading) {
    btn._text = btn.textContent;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> ${text || 'Loading...'}`;
  } else {
    btn.disabled = false;
    btn.textContent = btn._text || text;
  }
}

// API WRAPPER
async function apiCall(endpoint, method = 'GET', data = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include'
  };
  if (data) opts.body = JSON.stringify(data);
  try {
    const res = await fetch(endpoint, opts);
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

// AUDIO PLAYER
function playAudio(base64, mimeType = 'audio/mpeg') {
  const audio = new Audio(`data:${mimeType};base64,${base64}`);
  audio.play();
  return audio;
}

// STAGGER ANIMATION
function staggerAnimate(selector, delay = 80) {
  document.querySelectorAll(selector).forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    setTimeout(() => {
      el.style.transition = 'all 0.4s ease';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, i * delay);
  });
}

// WEBCAM
async function startWebcam(videoEl) {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    videoEl.srcObject = stream;
    await videoEl.play();
    return stream;
  } catch (e) {
    Toast.error('Camera access denied');
    return null;
  }
}

// MICROPHONE
async function startMicrophone() {
  try {
    return await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    Toast.error('Microphone access denied');
    return null;
  }
}

// SESSION HELPERS
const Session = {
  get(key) { try { return JSON.parse(localStorage.getItem('cb_' + key)); } catch { return null; } },
  set(key, val) { localStorage.setItem('cb_' + key, JSON.stringify(val)); },
  clear(key) { localStorage.removeItem('cb_' + key); },
  user() { return this.get('user'); },
  isLoggedIn() { return !!this.get('user'); },
  redirect() { if (!this.isLoggedIn()) { window.location.href = '/login.html'; } }
};

// KEYBOARD NAV
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal.open, .overlay.open').forEach(m => m.classList.remove('open'));
  }
});

// NAV ACTIVE STATE
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname.split('/').pop();
  document.querySelectorAll('.nav-link').forEach(l => {
    if (l.getAttribute('href') === path) l.classList.add('active');
  });
  initParticles();
  staggerAnimate('.feature-card', 60);
  
  // Status indicator updates
  const dots = document.querySelectorAll('[data-status]');
  dots.forEach(dot => {
    const key = dot.dataset.status;
    const el = document.getElementById(key + '-status');
    if (el) { el.classList.add('status-active'); }
  });
});

// CONFIDENCE COLOR
function confColor(val) {
  if (val >= 0.85) return '#10b981';
  if (val >= 0.65) return '#f59e0b';
  return '#ef4444';
}

// FORMAT HELPERS
function fmt(n, d = 1) { return Number(n).toFixed(d); }
function pct(n) { return `${fmt(n * 100)}%`; }

// IMAGE PREVIEW
function previewImage(input, imgEl) {
  input.addEventListener('change', e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => { imgEl.src = ev.target.result; imgEl.style.display = 'block'; };
    reader.readAsDataURL(file);
  });
}

// COPY TO CLIPBOARD
async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    Toast.success('Copied to clipboard');
  } catch { Toast.error('Copy failed'); }
}

// LANGUAGE UTILS
const LANGS = {
  "English":"en","Hindi":"hi","Kannada":"kn","Tamil":"ta","Telugu":"te",
  "Malayalam":"ml","Marathi":"mr","Gujarati":"gu","Punjabi":"pa","Urdu":"ur",
  "Bengali":"bn","Spanish":"es","French":"fr","German":"de","Italian":"it",
  "Japanese":"ja","Korean":"ko","Chinese (Simplified)":"zh-cn","Arabic":"ar",
  "Russian":"ru","Portuguese":"pt","Dutch":"nl","Swedish":"sv","Polish":"pl",
  "Turkish":"tr","Vietnamese":"vi","Thai":"th","Indonesian":"id","Malay":"ms",
  "Filipino":"fil","Ukrainian":"uk","Romanian":"ro","Czech":"cs","Slovak":"sk",
  "Hungarian":"hu","Finnish":"fi","Danish":"da","Norwegian":"no","Greek":"el",
  "Bulgarian":"bg","Croatian":"hr","Serbian":"sr","Slovenian":"sl",
  "Estonian":"et","Latvian":"lv","Lithuanian":"lt","Hebrew":"he","Swahili":"sw",
  "Afrikaans":"af","Catalan":"ca","Icelandic":"is","Macedonian":"mk",
  "Albanian":"sq","Armenian":"hy","Azerbaijani":"az","Belarusian":"be"
};

function buildLangSelect(id) {
  const sel = document.getElementById(id);
  if (!sel) return;
  Object.entries(LANGS).forEach(([name, code]) => {
    const opt = document.createElement('option');
    opt.value = code; opt.textContent = name;
    if (code === 'en') opt.selected = true;
    sel.appendChild(opt);
  });
}