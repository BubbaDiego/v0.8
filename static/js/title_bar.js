// title_bar.js

// Wait for the DOM to load
document.addEventListener('DOMContentLoaded', function () {

  // Helper: generic POST with spinner
  function postWithSpin(btn, url, msg) {
    if (!url) {
      console.warn('No URL provided for', btn);
      return;
    }
    btn.classList.add('spin');
    fetch(url, { method: 'POST' })
      .then(response => response.json())
      .then(data => console.log(msg, data))
      .catch(err => console.error('Error:', err))
      .finally(() => btn.classList.remove('spin'));
  }

  // --- Utility Buttons ---
  const updateJupiterBtn = document.getElementById('updateJupiterBtn');
  if (updateJupiterBtn) {
    updateJupiterBtn.addEventListener('click', () =>
      postWithSpin(updateJupiterBtn, window.POSITION_UPDATES_URL, 'Jupiter positions updated')
    );
  }

  const updatePricesBtn = document.getElementById('updatePricesBtn');
  if (updatePricesBtn) {
    updatePricesBtn.addEventListener('click', () =>
      postWithSpin(updatePricesBtn, window.MARKET_UPDATES_URL, 'Prices updated')
    );
  }

  const updateFullCycleBtn = document.getElementById('updateFullCycleBtn');
  if (updateFullCycleBtn) {
    updateFullCycleBtn.addEventListener('click', () =>
      postWithSpin(updateFullCycleBtn, window.FULL_CYCLE_API_URL, 'Full cycle completed')
    );
  }

  const clearAllBtn = document.getElementById('clearAllBtn');
  if (clearAllBtn) {
    clearAllBtn.addEventListener('click', () =>
      postWithSpin(clearAllBtn, window.CLEAR_ALL_URL, 'All data cleared')
    );
  }

  // --- Timer Updates ---
  function updateTimers() {
    if (!window.ALERT_LIMITS_URL) return;
    fetch(window.ALERT_LIMITS_URL)
      .then(res => res.json())
      .then(limits => {
        const now = Date.now();
        // Call timer
        let callText = '--';
        if (limits.call_refractory_start) {
          const start = new Date(limits.call_refractory_start).getTime();
          const end = start + (limits.call_refractory_period || 0) * 1000;
          const diff = Math.round((end - now) / 1000);
          callText = diff > 0 ? `${diff}s` : '--';
        }
        document.getElementById('callTimer').textContent = `☎ ${callText}`;
        // Snooze timer
        let snoozeText = '--';
        if (limits.snooze_start) {
          const sStart = new Date(limits.snooze_start).getTime();
          const sEnd = sStart + (limits.snooze_countdown || 0) * 1000;
          const sDiff = Math.round((sEnd - now) / 1000);
          snoozeText = sDiff > 0 ? `${sDiff}s` : '--';
        }
        document.getElementById('snoozeTimer').textContent = `💤 ${snoozeText}`;
      })
      .catch(err => console.error('Timer fetch error', err));
  }
  updateTimers();
  setInterval(updateTimers, 10000);

  // --- Theme Toggle Handler ---
  const themeToggleButton = document.getElementById('themeToggleButton');
  if (themeToggleButton) {
    themeToggleButton.addEventListener('click', function () {
      let currentTheme = localStorage.getItem('themeMode') || 'light';
      let newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('themeMode', newTheme);

      document.body.classList.remove('light-bg', 'dark-bg');
      document.body.classList.add(newTheme + '-bg');

      const icon = document.getElementById('themeIcon');
      if (icon) icon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';

      // Update CSS variables dynamically
      if (newTheme === 'dark') {
        document.documentElement.style.setProperty('--page-bg-color', '#3a3838');
        document.documentElement.style.setProperty('--page-text-color', '#ddd');
        document.documentElement.style.setProperty('--card-title-color', '#212529');
        document.documentElement.style.setProperty('--card-background-color', '#2a2a2a');
        document.documentElement.style.setProperty('--border-color', '#444');
        document.documentElement.style.setProperty('--text-color', '#ddd');
      } else {
        document.documentElement.style.setProperty('--page-bg-color', '#f5f5f5');
        document.documentElement.style.setProperty('--page-text-color', '#000');
        document.documentElement.style.setProperty('--card-title-color', '#343a40');
        document.documentElement.style.setProperty('--card-background-color', '#e9ecef');
        document.documentElement.style.setProperty('--border-color', '#ccc');
        document.documentElement.style.setProperty('--text-color', '#000');
      }
    });
  }

  // --- Layout Mode Toggle Handler ---
  const layoutToggleButton = document.getElementById('layoutToggleButton');
  if (layoutToggleButton) {
    layoutToggleButton.addEventListener('click', function () {
      let currentMode = localStorage.getItem('layoutMode') || 'fluid';
      let newMode = currentMode === 'fixed' ? 'fluid' : 'fixed';
      localStorage.setItem('layoutMode', newMode);

      const allLayouts = document.querySelectorAll('.container, .container-fluid');
      allLayouts.forEach(container => {
        container.classList.remove('container', 'container-fluid');
        container.classList.add(newMode === 'fixed' ? 'container' : 'container-fluid');
        container.style.display = 'none';
        requestAnimationFrame(() => { container.style.display = ''; });
      });
    });
  }

  // --- Theme Icon Sync on Load ---
  (function syncThemeIconOnLoad() {
    const currentTheme = localStorage.getItem('themeMode') || 'light';
    const icon = document.getElementById('themeIcon');
    if (icon) icon.className = currentTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
  })();

});
