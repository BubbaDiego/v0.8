console.log("🎨 theme_builder.js loaded");

// 🎨 Default fallback theme colors
const DEFAULT_THEME = {
  background: "#ffffff",
  text: "#111111",
  card: "#f0f0f0",
  navbar: "#fafafa"
};

// 🖼️ Live preview update for theme
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

// 🔧 Fill the color input fields
function setInputFields(config) {
  document.getElementById("backgroundColor").value = config.background || DEFAULT_THEME.background;
  document.getElementById("textColor").value = config.text || DEFAULT_THEME.text;
  document.getElementById("cardBackground").value = config.card || DEFAULT_THEME.card;
  document.getElementById("navbarBackground").value = config.navbar || DEFAULT_THEME.navbar;
}

// 🧠 Read the current color pickers into a config
function getThemeConfigFromUI() {
  return {
    background: document.getElementById("backgroundColor").value,
    text: document.getElementById("textColor").value,
    card: document.getElementById("cardBackground").value,
    navbar: document.getElementById("navbarBackground").value
  };
}

// 🔄 Load theme presets from the DB
function loadPresets() {
  fetch("/system/themes")
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

      if (presetList.options.length > 0) {
        presetList.selectedIndex = 0;
        const config = JSON.parse(presetList.options[0].dataset.config);
        setInputFields(config);
        applyThemePreview(config);
      }
    });
}

// 🔁 Load the currently active theme profile from the DB
function loadActiveProfile() {
  fetch("/system/themes/active")
    .then(res => res.json())
    .then(config => {
      console.log("🌈 Active theme profile:", config);
      if (!config) return;
      setInputFields(config);
      applyThemePreview(config);
    })
    .catch(err => console.warn("⚠️ Failed to load active theme:", err));
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("🎛️ Theme Builder ready");

  loadPresets();
  loadActiveProfile();

  const colorInputs = [
    "backgroundColor",
    "textColor",
    "cardBackground",
    "navbarBackground"
  ].map(id => document.getElementById(id));

  // 🖱️ Live preview while changing pickers
  colorInputs.forEach(input => {
    input.addEventListener("input", () => {
      applyThemePreview(getThemeConfigFromUI());
    });
  });

  // 🔁 Change preset from dropdown
  document.getElementById("presetList").addEventListener("change", e => {
    const selected = e.target.selectedOptions[0];
    if (!selected || !selected.dataset.config) return;
    const config = JSON.parse(selected.dataset.config);
    setInputFields(config);
    applyThemePreview(config);
  });

  // 💾 Save preset to DB
  document.getElementById("savePresetBtn").addEventListener("click", () => {
    const name = document.getElementById("presetName").value.trim();
    if (!name) return alert("Please enter a preset name.");

    const config = getThemeConfigFromUI();

    fetch("/system/themes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [name]: config })
    })
      .then(res => res.json())
      .then(() => {
        alert("✅ Preset saved!");
        loadPresets();
      });
  });

  // 🌟 Activate selected preset
  document.getElementById("setActiveBtn").addEventListener("click", () => {
    const selected = document.getElementById("presetList").selectedOptions[0];
    if (!selected) return;
    const name = selected.value;

    fetch(`/system/themes/activate/${encodeURIComponent(name)}`, {
      method: "POST"
    }).then(() => {
      alert(`✅ Theme '${name}' activated.`);
      location.reload(); // 🔁 required for site-wide effect
    });
  });

  // 🗑️ Delete a preset
  document.getElementById("deletePresetBtn").addEventListener("click", () => {
    const selected = document.getElementById("presetList").selectedOptions[0];
    if (!selected) return;
    const name = selected.value;

    if (!confirm(`Are you sure you want to delete '${name}'?`)) return;

    fetch(`/system/themes/${encodeURIComponent(name)}`, {
      method: "DELETE"
    }).then(() => {
      alert("🗑️ Preset deleted.");
      loadPresets();
    });
  });

  // 🔄 Reset button
  const resetBtn = document.getElementById("resetBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      setInputFields(DEFAULT_THEME);
      applyThemePreview(DEFAULT_THEME);
    });
  }
});
