// === title_bar.js ===
console.log("✅ title_bar.js loaded");

// Toast utility
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

// Core action endpoint handler
function callEndpoint(url, icon = "✅", label = "Action") {
  showToast(`${icon} ${label} started...`);
  fetch(url, { method: 'POST' })
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

// === Bind all [data-action] buttons ===
document.addEventListener('DOMContentLoaded', () => {
  const actions = {
    sync: () => callEndpoint('/cyclone/run_position_updates', "🪐", "Jupiter Sync"),
    market: () => callEndpoint('/cyclone/run_market_updates', "💲", "Market Update"),
    full: () => callEndpoint('/cyclone/run_full_cycle', "🌪️", "Full Cycle"),
    wipe: () => callEndpoint('/cyclone/clear_all_data', "🗑️", "Cyclone Delete")
  };

  document.querySelectorAll('[data-action]').forEach(btn => {
    const key = btn.getAttribute('data-action');
    if (actions[key]) {
      btn.addEventListener('click', actions[key]);
    }
  });
});
