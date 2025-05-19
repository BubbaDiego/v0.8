document.addEventListener("DOMContentLoaded", function () {
  const layoutModes = ["wide-mode", "fitted-mode", "mobile-mode"];
  const layoutToggle = document.getElementById("layoutToggle");

  layoutToggle?.addEventListener("click", () => {
    const body = document.body;
    const current = layoutModes.find(mode => body.classList.contains(mode));
    const currentIndex = layoutModes.indexOf(current);
    const nextIndex = (currentIndex + 1) % layoutModes.length;

    layoutModes.forEach(mode => body.classList.remove(mode));
    body.classList.add(layoutModes[nextIndex]);
    localStorage.setItem("layoutMode", layoutModes[nextIndex]);
  });

  const themeButtons = document.querySelectorAll(".theme-btn");
  themeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const theme = btn.dataset.theme;
      document.body.setAttribute("data-theme", theme);
      localStorage.setItem("theme", theme);
    });
  });

  const savedTheme = localStorage.getItem("theme");
  const savedLayout = localStorage.getItem("layoutMode");

  if (savedTheme) document.body.setAttribute("data-theme", savedTheme);
  if (savedLayout) {
    document.body.classList.add(savedLayout);
  } else {
    document.body.classList.add("wide-mode");
  }
});