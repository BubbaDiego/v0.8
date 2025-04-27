// === base.js ===

console.log('✅ base.js loaded');

(function() {
  const body = document.body;
  const themeToggleButton = document.getElementById('themeToggleButton');
  const themeIcon = document.getElementById('themeIcon');

  function applyTheme(mode) {
    if (mode === 'dark') {
      body.classList.remove('light-bg');
      body.classList.add('dark-bg');
      if (themeIcon) {
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
      }
      // Optional: darken navbar too
      const navbar = document.querySelector('.main-header.navbar');
      if (navbar) navbar.classList.remove('gradient-navbar');
    } else {
      body.classList.remove('dark-bg');
      body.classList.add('light-bg');
      if (themeIcon) {
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
      }
      // Optional: restore blue navbar gradient in light mode
      const navbar = document.querySelector('.main-header.navbar');
      if (navbar && !navbar.classList.contains('gradient-navbar')) {
        navbar.classList.add('gradient-navbar');
      }
    }
  }

  // === INITIAL LOAD: Apply saved theme ===
  const savedTheme = localStorage.getItem('preferredThemeMode');
  if (savedTheme) {
    applyTheme(savedTheme);
  } else {
    applyTheme('light'); // Default fallback
  }

  // === On button click: Toggle theme ===
  if (themeToggleButton) {
    themeToggleButton.addEventListener('click', function() {
      const currentTheme = body.classList.contains('dark-bg') ? 'dark' : 'light';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('preferredThemeMode', newTheme);
    });
  }
})();
