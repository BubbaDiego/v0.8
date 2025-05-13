console.log("🎨 theme_builder.js loaded");

// 🚨 DEFAULTS — You can change these colors
const DEFAULT_THEME = {
  background: "#ffffff",
  text: "#111111",
  card: "#f0f0f0",
  navbar: "#fafafa"
};

function applyThemePreview(config) {
  const preview = document.querySelector(".theme-preview-box");
  const card = document.querySelector(".theme-preview-card");
  const table = document.querySelector(".theme-preview-table");
  const chart = document.querySelector(".theme-preview-chart");

  if (!config) return;

  preview.style.backgroundColor = config.background || DEFAULT_THEME.background;
  preview.style.color = config.text || DEFAULT_THEME.text;
  card.style.backgroundColor = config.card || DEFAULT_THEME.card;
  card.style.color = config.text || DEFAULT_THEME.text;

  table.style.backgroundColor = config.background || DEFAULT_THEME.background;
  table.style.color = config.text || DEFAULT_THEME.text;
  table.querySelectorAll("th, td").forEach(cell => {
    cell.style.borderColor = config.text || DEFAULT_THEME.text;
  });

  chart.style.background = `linear-gradient(90deg, ${config.navbar || DEFAULT_THEME.navbar}, ${config.card || DEFAULT_THEME.card})`;
}

function setInputFields(config) {
  document.getElementById("backgroundColor").value = config.background || DEFAULT_THEME.background;
  document.getElementById("textColor").value = config.text || DEFAULT_THEME.text;
  document.getElementById("cardBackground").value = config.card || DEFAULT_THEME.card;
  document.getElementById("navbarBackground").value = config.navbar || DEFAULT_THEME.navbar;
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

function loadActiveProfile() {
  fetch("/system/themes/active")
    .then(res => res.json())
    .then(config => {
      if (!config) return;
      setInputFields(config);
      applyThemePreview(config);
    })
    .catch(err => console.warn("⚠️ Failed to load active theme:", err));
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("🎛️ Theme Builder loaded");

  loadPresets();
  loadActiveProfile();

  const backgroundColorInput = document.getElementById("backgroundColor");
  const textColorInput = document.getElementById("textColor");
  const cardBackgroundInput = document.getElementById("cardBackground");
  const navbarBackgroundInput = document.getElementById("navbarBackground");

  const colorInputs = [backgroundColorInput, textColorInput, cardBackgroundInput, navbarBackgroundInput];
  colorInputs.forEach(input => {
    input.addEventListener("input", () => {
      applyThemePreview(getThemeConfigFromUI());
    });
  });

  document.getElementById("presetList").addEventListener("change", e => {
    const selected = e.target.selectedOptions[0];
    if (!selected || !selected.dataset.config) return;
    const config = JSON.parse(selected.dataset.config);
    setInputFields(config);
    applyThemePreview(config);
  });

  document.getElementById("savePresetBtn").addEventListener("click", () => {
    const name = document.getElementById("presetName").value.trim();
    if (!name) return alert("Preset name required.");
    const config = getThemeConfigFromUI();

    // 🔁 Merge with existing
    fetch("/system/theme_config")
      .then(res => res.json())
      .then(existing => {
        existing = existing || {};
        existing[name] = config;

        return fetch("/system/theme_config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(existing)
        });
      })
      .then(() => {
        alert("✅ Preset saved!");
        loadPresets();
      });
  });

  document.getElementById("setActiveBtn").addEventListener("click", () => {
    const selected = document.getElementById("presetList").selectedOptions[0];
    if (!selected) return;
    const name = selected.value;

    fetch(`/system/themes/activate/${encodeURIComponent(name)}`, {
      method: "POST"
    }).then(() => alert(`✅ Theme '${name}' activated.`));
  });

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
        alert("🗑️ Preset deleted.");
        loadPresets();
      });
  });

  // 🔁 Reset to default button
  const resetBtn = document.getElementById("resetBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      setInputFields(DEFAULT_THEME);
      applyThemePreview(DEFAULT_THEME);
    });
  }
});
