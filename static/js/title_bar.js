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
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  document.getElementById('toastContainer').appendChild(toast);
  new bootstrap.Toast(toast, { delay: 4000 }).show();
}

function callEndpoint(url) {
  fetch(url, { method: 'POST' })
    .then(res => res.json())
    .then(data => showToast(data.message || data.error, !!data.error))
    .catch(err => showToast('Something went wrong.', true));
}

function triggerAlertEvaluation() {
  callEndpoint('/cyclone/run_alert_evaluations');
}

function triggerMarketUpdate() {
  callEndpoint('/cyclone/run_market_updates');
}

function triggerPositionUpdate() {
  callEndpoint('/cyclone/run_position_updates');
}

function triggerFullCycle() {
  callEndpoint('/cyclone/run_full_cycle');
}
