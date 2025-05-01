// universal_bar.js

// Use limits passed from backend instead of hardcoding
const portfolioLimits = window.TOTAL_PORTFOLIO_LIMITS || {};

function getColor(value, thresholds, reverse = false) {
  const v = parseFloat(value);
  if (isNaN(v)) return 'red';
  if (!reverse) {
    if (v <= thresholds.low) return 'green';
    if (v <= thresholds.medium) return 'yellow';
    return 'red';
  } else {
    if (v >= thresholds.low) return 'green';
    if (v >= thresholds.medium) return 'yellow';
    return 'red';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.universal-item');

  items.forEach(item => {
    const title = item.querySelector('.title')?.textContent.trim().toLowerCase();
    const valueEl = item.querySelector('.value');
    if (!title || !valueEl || !(title in portfolioLimits)) return;

    const valueText = valueEl.textContent.trim();
    const numeric = parseFloat(valueText.replace(/[^0-9.\-]/g, ''));
    if (isNaN(numeric)) return;

    const thresholds = portfolioLimits[title];
    const isReverse = ['travel'].includes(title);
    const color = getColor(numeric, thresholds, isReverse);

    item.classList.remove('green', 'yellow', 'red');
    item.classList.add(color);
  });
});
