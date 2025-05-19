// --------- LAYOUT MODE TOGGLE SUPPORT ----------
function setLayoutMode(mode) {
  document.body.classList.remove("wide-mode", "fitted-mode", "mobile-mode");
  document.body.classList.add(mode);
  localStorage.setItem("layoutMode", mode);
}

function cycleLayoutMode() {
  const modes = ["wide-mode", "fitted-mode", "mobile-mode"];
  const current = modes.find(m => document.body.classList.contains(m)) || "wide-mode";
  const next = modes[(modes.indexOf(current) + 1) % modes.length];
  setLayoutMode(next);
  console.log("🌀 Layout mode switched to:", next);
}

// =============================
// Designer-Proud Title Bar JS - SONIC ONLY, CENTERED WITH FLAIR
// =============================

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

// ---- Dashboard AJAX actions (unchanged) ----
function refreshDashboardCards() {
  fetch('/api/dashboard_cards')
    .then(resp => resp.json())
    .then(data => {
      if (data.success && data.html) {
        document.getElementById('dashboardCardsContainer').innerHTML = data.html;
        if (typeof bindFlipCards === "function") bindFlipCards();
        showToast('Dashboard updated!', 'success');
      } else {
        showToast('Dashboard update failed.', 'error');
      }
    })
    .catch(() => showToast('Dashboard update error.', 'error'));
}

function handleAction(apiUrl, method = "POST", friendlyName = "Action") {
  fetch(apiUrl, { method })
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        showToast(`${friendlyName} complete!`, "success");
        setTimeout(refreshDashboardCards, 600);
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

// --------- COUNTDOWN BAR LOGIC (SONIC ONLY) ----------
function pad(n) { return n < 10 ? "0" + n : n; }

function renderCountdowns(monitors) {
  const container = document.getElementById("countdown-bar");
  if (!container) return;
  const sonic = monitors.find(m => m.name === "sonic_monitor");
  if (!sonic) { container.innerHTML = ""; return; }
  container.innerHTML = `
    <span class="countdown-label">
      <span class="countdown-icon" title="Sonic Monitor Backend">🌀</span>
      Sonic Monitor
      <span class="countdown-timer"
        data-last="${sonic.last_run}"
        data-interval="${sonic.interval_seconds}"
        id="countdown-timer-sonic"
      >--:--</span>
    </span>`;
}

function updateCountdownTimers() {
  const now = Date.now();
  const el = document.getElementById('countdown-timer-sonic');
  if (!el) return;
  const last = Date.parse(el.getAttribute("data-last"));
  const interval = parseInt(el.getAttribute("data-interval"));
  if (!last || !interval) { el.textContent = "--:--"; return; }
  let next = last + interval * 1000;
  let diff = Math.max(0, Math.floor((next - now) / 1000));
  let mm = Math.floor(diff / 60), ss = diff % 60;
  el.textContent = `${pad(mm)}:${pad(ss)}`;
  if (diff < 10) {
    el.setAttribute('data-blink', 'true');
    el.title = "Next update in " + diff + " seconds";
  } else {
    el.removeAttribute('data-blink');
    el.title = "";
  }
}

function startCountdowns() {
  function poll() {
    fetch('/api/heartbeat').then(r => r.json()).then(data => {
      if (data && data.monitors) renderCountdowns(data.monitors);
    });
  }
  poll();
  setInterval(poll, 15_000); // re-fetch heartbeat every 15 seconds
  setInterval(updateCountdownTimers, 1000);
}

// --------- MAIN BINDINGS ----------
document.addEventListener("DOMContentLoaded", function () {
  document
    .querySelector('[data-action="sync"]')
    ?.addEventListener("click", function () {
      handleAction("/cyclone_sync", "POST", "Jupiter Sync");
    });
  document
    .querySelector('[data-action="market"]')
    ?.addEventListener("click", function () {
      handleAction("/cyclone_market_update", "POST", "Market Update");
    });
  document
    .querySelector('[data-action="full"]')
    ?.addEventListener("click", function () {
      handleAction("/cyclone_full_cycle", "POST", "Full Cycle");
    });
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

  // 📐 Layout Toggle Button Support
  const toggleBtn = document.getElementById("layoutModeToggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", cycleLayoutMode);
  }

  const saved = localStorage.getItem("layoutMode");
  if (saved) setLayoutMode(saved);

  // Start live, centered Sonic countdown
  startCountdowns();
});
