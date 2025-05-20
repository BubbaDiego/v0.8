// == SONIC THEME TOGGLE LOGIC ==

const THEME_KEY = "themeMode";

// Sets the theme on <html> and persists to localStorage & cookie
function setTheme(mode) {
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem(THEME_KEY, mode);
  document.cookie = THEME_KEY + "=" + mode + ";path=/;max-age=31536000";
}

// Reads persisted theme
function getPersistedTheme() {
  let mode = localStorage.getItem(THEME_KEY);
  if (!mode) {
    const cookie = document.cookie.split('; ').find(r => r.startsWith(THEME_KEY + '='));
    if (cookie) mode = cookie.split('=')[1];
  }
  return mode || "light";
}

// Activates the clicked button
function bindThemeButtons() {
  const buttons = document.querySelectorAll('.theme-btn[data-theme]');
  buttons.forEach(btn => {
    btn.addEventListener('click', e => {
      const mode = btn.getAttribute('data-theme');
      setTheme(mode);

      // Update visual active state
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

// On load, set theme from storage/cookie and highlight correct button
document.addEventListener("DOMContentLoaded", () => {
  const mode = getPersistedTheme();
  setTheme(mode);

  // Set button state
  const buttons = document.querySelectorAll('.theme-btn[data-theme]');
  buttons.forEach(btn => {
    if (btn.getAttribute('data-theme') === mode) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  bindThemeButtons();
});
