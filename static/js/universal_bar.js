// universal_bar.js

document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.universal-item');

  items.forEach(item => {
    const valueEl = item.querySelector('.value');
    if (!valueEl) return;

    const text = valueEl.textContent.trim().toLowerCase();

    // Example: auto-color if no value or stale
    if (text === 'n/a' || text.includes('stale')) {
      item.classList.remove('green', 'yellow');
      item.classList.add('red');
    }

    // Extend: parse numeric age or health metrics and color dynamically
    // e.g., parseInt(text) > threshold → yellow or red
  });
});
