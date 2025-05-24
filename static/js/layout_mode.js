// Layout mode toggle script
console.log('layout_mode.js loaded');
const LAYOUT_MODES = ['wide-mode', 'fitted-mode', 'mobile-mode'];

function setLayoutMode(mode) {
  document.body.classList.remove(...LAYOUT_MODES);
  document.body.classList.add(mode);

  const buttons = document.querySelectorAll('.layout-btn[data-mode]');
  buttons.forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
  });

  localStorage.setItem('sonicLayoutMode', mode);
}

document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.layout-btn[data-mode]');
  let mode = localStorage.getItem('sonicLayoutMode') || LAYOUT_MODES[0];
  if (!LAYOUT_MODES.includes(mode)) mode = LAYOUT_MODES[0];
  setLayoutMode(mode);

  buttons.forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const mode = btn.getAttribute('data-mode');
      setLayoutMode(mode);
    });
  });
});
