function showToast(message, isError = false) {
  const toastId = 'toast-' + Date.now();
  const toast = document.createElement('div');

  toast.className = `toast align-items-center text-bg-${isError ? 'danger' : 'success'} border-0`;
  toast.id = toastId;
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

  const bootstrapToast = new bootstrap.Toast(toast, { delay: 5000 });
  bootstrapToast.show();

  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function callEndpoint(url, icon = "✅", label = "Action") {
  showToast(`${icon} ${label} started...`, false);

  fetch(url, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      if (data.message) {
        showToast(`${icon} ${label} complete: ${data.message}`, false);
      } else if (data.error) {
        showToast(`❌ ${label} failed: ${data.error}`, true);
      } else {
        showToast(`⚠️ ${label} returned unexpected response.`, true);
      }
    })
    .catch(err => {
      console.error(`${label} error:`, err);
      showToast(`❌ ${label} failed to connect.`, true);
    });
}

// Individual triggers
function triggerPositionUpdate() {
  callEndpoint('/cyclone/run_position_updates', "🪐", "Jupiter Sync");
}

function triggerMarketUpdate() {
  callEndpoint('/cyclone/run_market_updates', "💲", "Market Update");
}

function triggerAlertEvaluation() {
  callEndpoint('/cyclone/run_alert_evaluations', "🔔", "Alert Evaluation");
}

function triggerFullCycle() {
  callEndpoint('/cyclone/run_full_cycle', "🌪️", "Cyclone Run");
}
