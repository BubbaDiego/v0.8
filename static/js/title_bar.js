// title_bar.js

document.addEventListener('DOMContentLoaded', function () {

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
      if (icon) {
        icon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
      }

      // 🔥 Force basic CSS refresh if needed
      if (newTheme === 'dark') {
        document.documentElement.style.setProperty('--page-bg-color', '#3a3838');
        document.documentElement.style.setProperty('--page-text-color', '#ddd');
      } else {
        document.documentElement.style.setProperty('--page-bg-color', '#f5f5f5');
        document.documentElement.style.setProperty('--page-text-color', '#000');
      }
    });
  }

  // --- Layout Mode Toggle Handler ---
  const layoutToggleButton = document.getElementById('layoutToggleButton');
  const layoutContainer = document.getElementById('layoutContainer');
  if (layoutToggleButton && layoutContainer) {
    layoutToggleButton.addEventListener('click', function () {
      let currentMode = localStorage.getItem('layoutMode') || 'fluid';
      let newMode = currentMode === 'fixed' ? 'fluid' : 'fixed';
      localStorage.setItem('layoutMode', newMode);

      layoutContainer.classList.remove('container', 'container-fluid');
      layoutContainer.classList.add(newMode === 'fixed' ? 'container' : 'container-fluid');

      // 🔥 Force reflow trick
      layoutContainer.style.display = 'none';
      setTimeout(() => {
        layoutContainer.style.display = '';
      }, 10);
    });
  }

  // --- Sync Theme Icon on Load ---
  (function syncThemeIconOnLoad() {
    const currentTheme = localStorage.getItem('themeMode') || 'light';
    const icon = document.getElementById('themeIcon');
    if (icon) {
      icon.className = currentTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
    }
  })();

});

