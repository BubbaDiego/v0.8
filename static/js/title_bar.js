// static/js/title_bar.js

console.log("✅ title_bar.js loaded");

// ======================
// Toast Utility
// ======================
function showToast(message, isError = false) {
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-bg-${isError ? 'danger' : 'success'} border-0`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;
  const container = document.getElementById('toastContainer');
  if (container) container.appendChild(toast);
  const bootstrapToast = new bootstrap.Toast(toast, { delay: 4000 });
  bootstrapToast.show();
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// ======================
// Action Endpoints
// ======================
function callEndpoint(url, icon = "✅", label = "Action", postAction = null) {
  showToast(`${icon} ${label} started...`);
  return fetch(url, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      if (data.message) {
        showToast(`${icon} ${label} complete: ${data.message}`);
      } else if (data.error) {
        showToast(`❌ ${label} failed: ${data.error}`, true);
      } else {
        showToast(`⚠️ ${label} returned unknown response`, true);
      }
    })
    .catch(err => {
      console.error(`${label} error:`, err);
      showToast(`❌ ${label} failed to connect`, true);
    });
}

// ======================
// Title Bar Button Logic
// ======================
document.addEventListener('DOMContentLoaded', () => {
  // Right action buttons
  const actions = {
    sync:   () => callEndpoint('/cyclone/run_position_updates', "🪐", "Jupiter Sync"),
    market: () => callEndpoint('/cyclone/run_market_updates',   "💲", "Market Update"),
    full:   () => callEndpoint('/cyclone/run_full_cycle',       "🌪️", "Full Cycle"),
    wipe:   () => callEndpoint('/cyclone/clear_all_data',       "🗑️", "Cyclone Delete")
  };

  document.querySelectorAll('[data-action]').forEach(btn => {
    const clone = btn.cloneNode(true);
    btn.parentNode.replaceChild(clone, btn);
    const key = clone.getAttribute('data-action');
    clone.addEventListener('click', function() {
      if (actions[key]) {
        actions[key]();
      } else {
        showToast(`⚠️ Unknown [data-action="${key}"]`, true);
      }
    });
  });

  // ========== Theme Toggle (cyclic) ==========
  const THEMES = ['light', 'dark', 'funky'];
  const THEME_ICONS = ['☀️', '🌙', '🎨'];
  let themeIndex = 0;
  function applyTheme(idx) {
    const theme = THEMES[idx];
    if (theme === 'light') {
      document.body.removeAttribute('data-theme');
    } else {
      document.body.setAttribute('data-theme', theme);
    }
    const icon = document.getElementById('currentThemeIcon');
    if (icon) icon.innerText = THEME_ICONS[idx];
    localStorage.setItem('dashboardTheme', idx);
  }
  const themeBtn = document.getElementById('themeModeToggle');
  themeIndex = Number(localStorage.getItem('dashboardTheme')) || 0;
  if (themeIndex >= THEMES.length) themeIndex = 0;
  applyTheme(themeIndex);
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      themeIndex = (themeIndex + 1) % THEMES.length;
      applyTheme(themeIndex);
    });
  }
});
