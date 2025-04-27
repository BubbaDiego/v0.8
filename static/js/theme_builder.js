// /static/js/theme_builder.js

console.log('✅ Theme Builder JS Loaded');

const backgroundColorPicker = document.getElementById('backgroundColor');
const textColorPicker = document.getElementById('textColor');
const cardBackgroundPicker = document.getElementById('cardBackground');
const navbarBackgroundPicker = document.getElementById('navbarBackground');
const presetNameInput = document.getElementById('presetName');
const presetList = document.getElementById('presetList');
const savePresetBtn = document.getElementById('savePresetBtn');
const setActiveBtn = document.getElementById('setActiveBtn');
const deletePresetBtn = document.getElementById('deletePresetBtn');

let currentThemes = {};

// Load existing themes
function loadThemes() {
  fetch('/theme/get')
    .then(res => res.json())
    .then(data => {
      currentThemes = data;
      updatePresetDropdown();
      applyTheme(data.profiles[data.selected_profile]);
      presetList.value = data.selected_profile;
    });
}

// Update dropdown
function updatePresetDropdown() {
  presetList.innerHTML = '';
  for (const name in currentThemes.profiles) {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    presetList.appendChild(opt);
  }
}

// Apply theme live
function applyTheme(theme) {
  if (!theme) return;
  document.body.style.backgroundColor = theme.background;
  document.body.style.color = theme.text;
  const cards = document.querySelectorAll('.common-box, .mini-table-box, .ledger-box');
  cards.forEach(c => c.style.backgroundColor = theme.card_background);
  const navbar = document.querySelector('.navbar');
  if (navbar) navbar.style.backgroundColor = theme.navbar_background;
}

// Save new preset
savePresetBtn.addEventListener('click', () => {
  const name = presetNameInput.value.trim();
  if (!name) return alert('Enter a preset name!');
  const colors = {
    background: backgroundColorPicker.value,
    text: textColorPicker.value,
    card_background: cardBackgroundPicker.value,
    navbar_background: navbarBackgroundPicker.value
  };

  fetch('/theme/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, colors })
  })
    .then(res => res.json())
    .then(() => {
      alert('Preset saved!');
      loadThemes();
    });
});

// Set active theme
setActiveBtn.addEventListener('click', () => {
  const name = presetList.value;
  if (!name) return;

  fetch('/theme/set_active', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  })
    .then(res => res.json())
    .then(() => {
      alert(`Theme '${name}' set as active.`);
      loadThemes();
    });
});

// Delete preset
deletePresetBtn.addEventListener('click', () => {
  const name = presetList.value;
  if (!name) return;
  if (!confirm(`Delete preset '${name}'?`)) return;

  fetch('/theme/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  })
    .then(res => res.json())
    .then(() => {
      alert('Preset deleted.');
      loadThemes();
    });
});

// Update live preview as you pick
[backgroundColorPicker, textColorPicker, cardBackgroundPicker, navbarBackgroundPicker].forEach(picker => {
  picker.addEventListener('input', () => {
    const preview = {
      background: backgroundColorPicker.value,
      text: textColorPicker.value,
      card_background: cardBackgroundPicker.value,
      navbar_background: navbarBackgroundPicker.value
    };
    applyTheme(preview);
  });
});

// Initialize
loadThemes();
