// === theme_toggle.js ===
// Handles user theme switching and persists selection

// Key names
const THEME_KEY = "themeMode"; // Cookie/localStorage key

// Set theme on <html data-theme="...">
function setTheme(mode) {
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem(THEME_KEY, mode); // Save for reloads

  // Optional: set a cookie for server-side detection (if you want)
  document.cookie = THEME_KEY + "=" + mode + ";path=/;max-age=31536000"; // 1 year
}

// Read persisted theme from localStorage or cookie
function getPersistedTheme() {
  let mode = localStorage.getItem(THEME_KEY);
  if (!mode) {
    // fallback to cookie if needed
    const cookie = document.cookie.split('; ').find(r => r.startsWith(THEME_KEY + '='));
    if (cookie) mode = cookie.split('=')[1];
  }
  return mode || "light";
}

// Bind events to the theme toggle buttons in title bar
function bindThemeButtons() {
  const buttons = document.querySelectorAll('.theme-btn[data-theme]');
  buttons.forEach(btn => {
    btn.addEventListener('click', e => {
      const mode = btn.getAttribute('data-theme');
      setTheme(mode);

      // Optional: give feedback
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

// On page load, initialize theme from saved preference or default
document.addEventListener("DOMContentLoaded", () => {
  setTheme(getPersistedTheme());
  bindThemeButtons();
});
