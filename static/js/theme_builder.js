console.log("🎨 theme_builder.js loaded");

function applyThemePreview(config) {
  document.documentElement.style.setProperty("--bg", config.background || "#ffffff");
  document.documentElement.style.setProperty("--text", config.text || "#111111");
  document.documentElement.style.setProperty("--card-bg", config.card || "#f0f0f0");
  document.documentElement.style.setProperty("--navbar-bg", config.navbar || "#fafafa");
}

function getThemeConfigFromUI() {
  return {
    background: document.getElementById("backgroundColor").value,
    text: document.getElementById("textColor").value,
    card: document.getElementById("cardBackground").value,
    navbar: document.getElementById("navbarBackground").value
  };
}

function loadPresets() {
  fetch("/system/theme_config")
    .then(res => res.json())
    .then(data => {
      const presetList = document.getElementById("presetList");
      presetList.innerHTML = "";

      if (!data || typeof data !== "object") return;

      Object.entries(data).forEach(([name, values]) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        option.dataset.config = JSON.stringify(values);
        presetList.appendChild(option);
      });
    });
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("🎛️ Theme Builder loaded");

  loadPresets();

  // Live preview when selecting preset
  document.getElementById("presetList").addEventListener("change", e => {
    const selected = e.target.selectedOptions[0];
    if (!selected) return;
    const config = JSON.parse(selected.dataset.config);
    applyThemePreview(config);
    Object.entries(config).forEach(([key, val]) => {
      if (key === "background") document.getElementById("backgroundColor").value = val;
      if (key === "text") document.getElementById("textColor").value = val;
      if (key === "card") document.getElementById("cardBackground").value = val;
      if (key === "navbar") document.getElementById("navbarBackground").value = val;
    });
  });

  // Save preset
  document.getElementById("savePresetBtn").addEventListener("click", () => {
    const name = document.getElementById("presetName").value.trim();
    if (!name) return alert("Preset name required.");
    const config = getThemeConfigFromUI();

    fetch("/system/theme_config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [name]: config })
    }).then(() => {
      alert("Preset saved!");
      loadPresets();
    });
  });

  // Set selected as active theme
  document.getElementById("setActiveBtn").addEventListener("click", () => {
    const selected = document.getElementById("presetList").selectedOptions[0];
    if (!selected) return;
    const config = JSON.parse(selected.dataset.config);
    applyThemePreview(config);
    // Optional: Store active theme on backend if needed
  });

  // Delete selected
  document.getElementById("deletePresetBtn").addEventListener("click", () => {
    const selected = document.getElementById("presetList").selectedOptions[0];
    if (!selected) return;
    const name = selected.value;

    fetch("/system/theme_config")
      .then(res => res.json())
      .then(config => {
        delete config[name];
        return fetch("/system/theme_config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(config)
        });
      })
      .then(() => {
        alert("Preset deleted.");
        loadPresets();
      });
  });
});
