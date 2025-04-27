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

      // 🔥 Now update CSS variables dynamically
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
        requestAnimationFrame(() => {
          container.style.display = '';
        });
      });
    });
  }

  // --- Theme Icon Sync on Load ---
  (function syncThemeIconOnLoad() {
    const currentTheme = localStorage.getItem('themeMode') || 'light';
    const icon = document.getElementById('themeIcon');
    if (icon) {
      icon.className = currentTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
    }
  })();

});
