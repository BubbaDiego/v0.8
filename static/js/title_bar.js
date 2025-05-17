// Show toast messages (uses your existing #toastContainer)
function showToast(message, type = "info") {
  const toastContainer = document.getElementById("toastContainer");
  if (!toastContainer) return;
  const color =
    type === "success"
      ? "#198754"
      : type === "error"
      ? "#d72d36"
      : type === "warning"
      ? "#ffc107"
      : "#4678d8";
  const toast = document.createElement("div");
  toast.className = `toast align-items-center text-bg-${type} show mb-2`;
  toast.style.background = color;
  toast.style.color = "#fff";
  toast.role = "alert";
  toast.ariaLive = "assertive";
  toast.ariaAtomic = "true";
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 800);
  }, 3200);
}

// Fetch new cards and swap in live (AJAX)
function refreshDashboardCards() {
  fetch('/api/dashboard_cards')
    .then(resp => resp.json())
    .then(data => {
      if (data.success && data.html) {
        document.getElementById('dashboardCardsContainer').innerHTML = data.html;
        if (typeof bindFlipCards === "function") bindFlipCards(); // Rebind flip cards if you use this!
        showToast('Dashboard updated!', 'success');
      } else {
        showToast('Dashboard update failed.', 'error');
      }
    })
    .catch(() => showToast('Dashboard update error.', 'error'));
}

// After a successful backend action, call refreshDashboardCards()
function handleAction(apiUrl, method = "POST", friendlyName = "Action") {
  fetch(apiUrl, { method })
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        showToast(`${friendlyName} complete!`, "success");
        setTimeout(refreshDashboardCards, 600); // Let the toast be visible
      } else {
        let msg =
          resp.message ||
          resp.error ||
          `${friendlyName} failed. Please try again.`;
        showToast(msg, "error");
      }
    })
    .catch((err) => {
      showToast(
        `${friendlyName} failed: ${err.message || "Unknown error"}`,
        "error"
      );
    });
}

document.addEventListener("DOMContentLoaded", function () {
  // Jupiter Sync Button
  document
    .querySelector('[data-action="sync"]')
    ?.addEventListener("click", function () {
      handleAction("/cyclone_sync", "POST", "Jupiter Sync");
    });

  // Market Update Button
  document
    .querySelector('[data-action="market"]')
    ?.addEventListener("click", function () {
      handleAction("/cyclone_market_update", "POST", "Market Update");
    });

  // Full Cycle Button
  document
    .querySelector('[data-action="full"]')
    ?.addEventListener("click", function () {
      handleAction("/cyclone_full_cycle", "POST", "Full Cycle");
    });

  // Wipe All Button
  document
    .querySelector('[data-action="wipe"]')
    ?.addEventListener("click", function () {
      if (
        confirm(
          "Are you sure you want to wipe all data? This cannot be undone."
        )
      ) {
        handleAction("/cyclone_wipe_all", "POST", "Wipe All");
      }
    });
});
