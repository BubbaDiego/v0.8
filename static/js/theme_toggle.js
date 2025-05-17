// === theme_toggle.js ===
// Handles user theme switching and persists selection

// Key names
const THEME_KEY = "themeMode"; // Cookie/localStorage key
const ICONSET_KEY = "iconSet"; // For icon set selection

// Set theme on <html data-theme="..."> and set default icon set on <body>
function setTheme(mode) {
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem(THEME_KEY, mode); // Save for reloads

  // Optional: set a cookie for server-side detection (if you want)
  document.cookie = THEME_KEY + "=" + mode + ";path=/;max-age=31536000"; // 1 year

  // Set default icon set based on theme
  let iconSet = "";
  if (mode === "dark") {
    iconSet = "fa"; // Font Awesome for dark
  } else if (mode === "funky") {
    iconSet = "material"; // Material for funky
  } else {
    iconSet = ""; // Emoji for light/other
  }
  document.body.setAttribute("data-icon-set", iconSet);
  localStorage.setItem(ICONSET_KEY, iconSet);
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

// Read persisted icon set from localStorage
function getPersistedIconSet() {
  let iconSet = localStorage.getItem(ICONSET_KEY);
  return iconSet || "";
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

// On page load, initialize theme and icon set from saved preference or default
document.addEventListener("DOMContentLoaded", () => {
  const mode = getPersistedTheme();
  setTheme(mode); // this sets theme AND icon set

  // In case the user previously overrode the icon set, restore it
  const iconSet = getPersistedIconSet();
  if (iconSet !== "" && iconSet !== "fa" && iconSet !== "material") {
    document.body.setAttribute("data-icon-set", iconSet);
  }

  bindThemeButtons();
});
