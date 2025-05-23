// Layout mode toggle script
console.log('layout_mode.js loaded');
const LAYOUT_MODES = ['wide-mode', 'fitted-mode', 'mobile-mode'];
let layoutCurrent = 0;
function setLayoutMode(idx) {
  document.body.classList.remove(...LAYOUT_MODES);
  document.body.classList.add(LAYOUT_MODES[idx]);
  const label = document.getElementById('currentLayoutMode');
  if (label) label.innerText = LAYOUT_MODES[idx].replace('-mode', '');
  localStorage.setItem('sonicLayoutMode', idx);
}
document.addEventListener('DOMContentLoaded', function() {
  const btn = document.getElementById('layoutModeToggle');
  layoutCurrent = Number(localStorage.getItem('sonicLayoutMode')) || 0;
  setLayoutMode(layoutCurrent);
  if (btn) {
    btn.addEventListener('click', function() {
      layoutCurrent = (layoutCurrent + 1) % LAYOUT_MODES.length;
      setLayoutMode(layoutCurrent);
    });
  }
});
