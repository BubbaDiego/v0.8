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
    const title = item.dataset.title;
    const raw = parseFloat(item.dataset.raw);

    if (!title || isNaN(raw) || !(title in portfolioLimits)) return;

    const thresholds = portfolioLimits[title];
    const isReverse = ['travel'].includes(title);
    const color = getColor(raw, thresholds, isReverse);

    item.classList.remove('green', 'yellow', 'red');
    item.classList.add(color);
  });
});