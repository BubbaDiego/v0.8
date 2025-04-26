// title_bar.js

console.log('✅ title_bar.js loaded');

document.addEventListener('DOMContentLoaded', function () {

  // === THEME TOGGLE ===
  const toggleContainer = document.getElementById('toggleContainer');
  if (toggleContainer) {
    const sunIcon = `
      <svg viewBox="0 0 24 24" width="20" height="20" fill="white" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1" x2="12" y2="3" stroke="white" stroke-width="2"/>
        <line x1="12" y1="21" x2="12" y2="23" stroke="white" stroke-width="2"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="white" stroke-width="2"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="white" stroke-width="2"/>
        <line x1="1" y1="12" x2="3" y2="12" stroke="white" stroke-width="2"/>
        <line x1="21" y1="12" x2="23" y2="12" stroke="white" stroke-width="2"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="white" stroke-width="2"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="white" stroke-width="2"/>
      </svg>`;
    const moonIcon = `
      <svg viewBox="0 0 24 24" width="20" height="20" fill="white" xmlns="http://www.w3.org/2000/svg">
        <path d="M21 12.79A9 9 0 0 1 11.21 3 A7 7 0 0 0 12 17 a7 7 0 0 0 9-4.21z"/>
      </svg>`;

    toggleContainer.innerHTML = '{{ theme_mode }}' === 'dark' ? sunIcon : moonIcon;

    toggleContainer.addEventListener('click', () => {
      const nextMode = '{{ theme_mode }}' === 'dark' ? 'light' : 'dark';
      fetch('/save_theme_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme_mode: nextMode })
      })
      .then(r => r.json())
      .then(d => {
        if (d.success) window.location.reload();
        else console.error('Theme save error:', d.error);
      })
      .catch(console.error);
    });
  }

  // === TIMER LOGIC ===
  function getRemaining(start, period) {
    if (!start) return period;
    const elapsed = Math.floor(Date.now() / 1000) - start;
    return Math.max(period - elapsed, 0);
  }

  function updateTimers() {
    fetch(ALERT_LIMITS_URL)
      .then(r => r.json())
      .then(data => {
        const callPeriod = data.call_refractory_period;
        const snoozeCount = data.snooze_countdown;
        const callStart = data.call_refractory_start;
        const snoozeStart = data.snooze_start;

        function refreshDisplay() {
          const callRemaining = getRemaining(callStart, callPeriod);
          const snoozeRemaining = getRemaining(snoozeStart, snoozeCount);

          document.getElementById('callTimer').textContent = (callRemaining > 5 ? '☎' : '⏰') + ' ' + callRemaining;
          document.getElementById('snoozeTimer').textContent = (snoozeRemaining > 5 ? '💤' : '😴') + ' ' + snoozeRemaining;
        }

        refreshDisplay();
        setInterval(refreshDisplay, 1000);
      })
      .catch(err => console.error('Timer error:', err));
  }
  updateTimers();

  // === BUTTON ACTIONS ===
  function setupButton(id, url) {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener('click', () => {
      btn.classList.add('spin');
      fetch(url, { method: 'POST' })
        .then(r => r.json())
        .then(() => window.location.reload())
        .catch(err => {
          console.error(id + ' update error:', err);
          btn.classList.remove('spin');
        });
    });
  }

  setupButton('updateJupiterBtn', '/positions/update_jupiter?source=User');
  setupButton('updatePricesBtn', '/prices/update?source=User');
  setupButton('updateFullCycleBtn', FULL_CYCLE_API_URL);
  setupButton('clearAllBtn', '/api/clear_all_data');

  // === LAYOUT TOGGLE (fluid/fixed container) ===
  const layoutToggle = document.getElementById('layoutToggle');
  if (layoutToggle) {
    layoutToggle.addEventListener('click', (e) => {
      e.preventDefault();
      const mode = localStorage.getItem("layoutMode") || "fluid";
      const newMode = (mode === "fluid") ? "fixed" : "fluid";
      localStorage.setItem("layoutMode", newMode);
      window.location.reload();
    });
  }

});
