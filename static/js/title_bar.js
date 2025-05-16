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
        if (typeof postAction === "function") postAction();
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
// Dashboard Section Refresh (Optional)
// ======================
function reloadDashboardSection() {
  const section = document.getElementById("dashboardSection");
  if (!section) return;
  section.classList.add("loading");
  fetch("/api/dashboard_html")
    .then(res => {
      if (!res.ok) throw new Error("Failed to load dashboard HTML");
      return res.text();
    })
    .then(html => {
      section.innerHTML = html;
      section.classList.remove("loading");
      console.log("✅ Dashboard reloaded via AJAX");
    })
    .catch(err => {
      console.error("❌ Error refreshing dashboard section:", err);
      section.classList.remove("loading");
    });
}

// ======================
// Title Bar Button Logic (Ultimate Fix)
// ======================
document.addEventListener('DOMContentLoaded', () => {
  // Right action buttons
  const actions = {
    sync:   () => callEndpoint('/cyclone/run_position_updates', "🪐", "Jupiter Sync", reloadDashboardSection),
    market: () => callEndpoint('/cyclone/run_market_updates',   "💲", "Market Update", reloadDashboardSection),
    full:   () => callEndpoint('/cyclone/run_full_cycle',       "🌪️", "Full Cycle", reloadDashboardSection),
    wipe:   () => callEndpoint('/cyclone/clear_all_data',       "🗑️", "Cyclone Delete", reloadDashboardSection)
  };

  // Remove old listeners (cloneNode) and rebind—**guaranteed no double firing**
  document.querySelectorAll('[data-action]').forEach(btn => {
    const clone = btn.cloneNode(true);
    btn.parentNode.replaceChild(clone, btn);
    const key = clone.getAttribute('data-action');
    clone.addEventListener('click', function() {
      if (actions[key]) {
        actions[key]();
      } else {
        showToast(`⚠️ Unknown [data-action="${key}"]`, true);
        console.warn(`⚠️ Unknown [data-action="${key}"]`);
      }
    });
  });

  // ========== Theme Toggle (3-way) ==========
  const THEMES = ["light", "dark", "funky"];
  function setTheme(theme) {
    if (theme === "light") {
      document.body.removeAttribute("data-theme");
    } else {
      document.body.setAttribute("data-theme", theme);
    }
    localStorage.setItem("dashboardTheme", theme);
    // Highlight the active theme button
    document.querySelectorAll('.theme-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-theme') === theme);
    });
  }
  // Set initial theme from localStorage
  const savedTheme = localStorage.getItem("dashboardTheme") || "light";
  setTheme(savedTheme);
  document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      setTheme(this.getAttribute('data-theme'));
    });
  });
});
