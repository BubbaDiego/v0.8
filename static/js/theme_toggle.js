console.log("✅ theme_toggle.js loaded");

(function () {
  const root = document.documentElement;
  const current = localStorage.getItem("themeMode") || "light";
  root.setAttribute("data-theme", current);

  const toggle = document.getElementById("themeToggleButton");
  if (!toggle) return;

  toggle.addEventListener("click", () => {
    const mode = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", mode);
    localStorage.setItem("themeMode", mode);
    document.cookie = `themeMode=${mode}; path=/; max-age=31536000`;

    // Optional: Call backend
    fetch("/system/theme_mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme_mode: mode }),
    });
  });
})();
