// === base.js (Production) ===
console.log('✅ base.js loaded');

(function () {
  const body = document.body;
  const themeToggleButton = document.getElementById('themeToggleButton');
  const themeIcon = document.getElementById('themeIcon');

  function applyTheme(mode) {
    document.documentElement.setAttribute('data-theme', mode);

    if (mode === 'dark') {
      body.classList.remove('light-bg');
      body.classList.add('dark-bg');
      themeIcon?.classList.replace('fa-sun', 'fa-moon');
    } else if (mode === 'light') {
      body.classList.remove('dark-bg');
      body.classList.add('light-bg');
      themeIcon?.classList.replace('fa-moon', 'fa-sun');
    } else {
      body.classList.remove('dark-bg', 'light-bg');
      themeIcon?.classList.remove('fa-moon', 'fa-sun');
    }

    // Add slight visual cue
    body.style.transition = 'transform 0.3s ease';
    body.style.transform = 'scale(1.01)';
    setTimeout(() => body.style.transform = 'scale(1)', 300);
  }

  if (themeToggleButton) {
    themeToggleButton.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : current === 'light' ? 'funky' : 'dark';
      console.log(`🎛️ Toggling theme: ${current} ➡️ ${next}`);
      applyTheme(next);
      localStorage.setItem('preferredThemeMode', next);
    });

    const savedTheme = localStorage.getItem('preferredThemeMode') || 'light';
    applyTheme(savedTheme);
  } else {
    console.warn('⚠️ Theme toggle button not found.');
  }
})();