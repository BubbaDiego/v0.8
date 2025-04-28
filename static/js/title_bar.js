// === title_bar.js ===

document.addEventListener('DOMContentLoaded', function () {
  console.log('✅ Title Bar JS Loaded');

  // --- Universal POST with Spinner Helper ---
  function postWithSpin(btn, url, msg, reloadOnSuccess = false) {
    if (!url) {
      console.warn('No URL provided for', btn);
      return;
    }
    btn.classList.add('spin');
    fetch(url, { method: 'POST' })
      .then(response => response.json())
      .then(data => {
        console.log(msg, data);
        showToast('✅ ' + msg);
        if (reloadOnSuccess) {
          setTimeout(() => {
            location.reload();
          }, 1000); // Slight delay to allow toast to show
        }
      })
      .catch(err => {
        console.error('Error:', err);
        showToast('❌ API Error', true);
      })
      .finally(() => btn.classList.remove('spin'));
  }

  // --- Local Action Helper (theme toggle, layout toggle) ---
  function localAction(fn, successMessage) {
    try {
      fn();
      showToast('✅ ' + successMessage);
    } catch (e) {
      console.error('Local action failed:', e);
      showToast('❌ Local action failed', true);
    }
  }

  // --- Toast Notification Helper ---
  function showToast(message, isError = false) {
    const toast = document.createElement('div');
    toast.className = 'toast-notify';
    if (isError) toast.classList.add('error');
    toast.innerText = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 500);
    }, 2500);
  }

  // --- Utility Buttons ---

  // Update Jupiter Positions
  const updateJupiterBtn = document.getElementById('updateJupiterBtn');
  if (updateJupiterBtn) {
    updateJupiterBtn.addEventListener('click', () =>
      postWithSpin(updateJupiterBtn, API_ROUTES.positionUpdates, 'Positions Updated', true) // ✅ Reload needed
    );
  }

  // Update Market Prices
  const updatePricesBtn = document.getElementById('updatePricesBtn');
  if (updatePricesBtn) {
    updatePricesBtn.addEventListener('click', () =>
      postWithSpin(updatePricesBtn, API_ROUTES.marketUpdates, 'Prices Updated', false) // ❌ No reload
    );
  }

  // Run Full Cycle
  const updateFullCycleBtn = document.getElementById('updateFullCycleBtn');
  if (updateFullCycleBtn) {
    updateFullCycleBtn.addEventListener('click', () =>
      postWithSpin(updateFullCycleBtn, API_ROUTES.fullCycle, 'Full Cycle Completed', true) // ✅ Reload needed
    );
  }

  // Clear All Data
  const clearAllBtn = document.getElementById('clearAllBtn');
  if (clearAllBtn) {
    clearAllBtn.addEventListener('click', () =>
      postWithSpin(clearAllBtn, API_ROUTES.clearAllData, 'All Data Cleared', true) // ✅ Reload needed
    );
  }

  // --- Layout Toggle Button ---
  const layoutToggleButton = document.getElementById('layoutToggleButton');
  if (layoutToggleButton) {
    layoutToggleButton.addEventListener('click', () =>
      localAction(() => {
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
      }, 'Layout Toggled')
    );
  }

  // --- Theme Toggle Button ---
  const themeToggleButton = document.getElementById('themeToggleButton');
  if (themeToggleButton) {
    themeToggleButton.addEventListener('click', () =>
      localAction(() => {
        let currentTheme = localStorage.getItem('preferredThemeMode') || 'light';
        let newTheme = (currentTheme === 'light') ? 'dark' : 'light';
        localStorage.setItem('preferredThemeMode', newTheme);

        document.body.classList.remove('light-bg', 'dark-bg');
        document.body.classList.add(newTheme + '-bg');

        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
          themeIcon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        }
      }, 'Theme Changed')
    );
  }

});
