// == SONIC THEME TOGGLE LOGIC ==

const THEME_KEY = "themeMode";
const THEMES = ["light", "dark", "funky"];
const THEME_ICONS = ["☀️", "🌙", "🎨"];
let themeIndex = 0;

function applyTheme(idx) {
  const mode = THEMES[idx];
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem(THEME_KEY, mode);
  document.cookie = THEME_KEY + "=" + mode + ";path=/;max-age=31536000";
  const icon = document.getElementById('currentThemeIcon');
  if (icon) icon.innerText = THEME_ICONS[idx];
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById('themeModeToggle');
  const persisted = localStorage.getItem(THEME_KEY) || "light";
  themeIndex = THEMES.indexOf(persisted);
  if (themeIndex === -1) themeIndex = 0;
  applyTheme(themeIndex);
  if (btn) {
    btn.addEventListener('click', () => {
      themeIndex = (themeIndex + 1) % THEMES.length;
      applyTheme(themeIndex);
    });
  }
});
