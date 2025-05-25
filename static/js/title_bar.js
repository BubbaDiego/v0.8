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
  const THEMES = ["light", "dark", "funky"];
  const THEME_ICONS = ["☀️", "🌙", "🎨"];
  let themeIndex = 0;

  function setTheme(idx) {
    const theme = THEMES[idx];
    if (theme === "light") {
      // Apply theme on <html> so CSS :root selectors work
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", theme);
    }
    localStorage.setItem("dashboardTheme", theme);
    const icon = document.getElementById("currentThemeIcon");
    if (icon) icon.innerText = THEME_ICONS[idx];
  }

  const savedTheme = localStorage.getItem("dashboardTheme") || "light";
  themeIndex = THEMES.indexOf(savedTheme);
  if (themeIndex === -1) themeIndex = 0;
  setTheme(themeIndex);

  const themeToggle = document.getElementById("themeModeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", function(e) {
      e.preventDefault();
      themeIndex = (themeIndex + 1) % THEMES.length;
      setTheme(themeIndex);
    });
  }

  // Apply shimmer animation to the title pill on load
  const titlePill = document.querySelector('.sonic-title-pill');
  if (titlePill) {
    titlePill.classList.add('shimmer');
  }
});
