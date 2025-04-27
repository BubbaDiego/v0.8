// === base.js ===

console.log('✅ base.js loaded');

// === Theme Handling ===
(function() {
  const body = document.body;
  const themeToggleButton = document.getElementById('themeToggleButton');
  const themeIcon = document.getElementById('themeIcon');

  function applyTheme(mode) {
    if (mode === 'dark') {
      body.classList.remove('light-bg');
      body.classList.add('dark-bg');
      if (themeIcon) {
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
      }
      const navbar = document.querySelector('.main-header.navbar');
      if (navbar) navbar.classList.remove('gradient-navbar');
    } else {
      body.classList.remove('dark-bg');
      body.classList.add('light-bg');
      if (themeIcon) {
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
      }
      const navbar = document.querySelector('.main-header.navbar');
      if (navbar && !navbar.classList.contains('gradient-navbar')) {
        navbar.classList.add('gradient-navbar');
      }
    }
  }

  const savedTheme = localStorage.getItem('preferredThemeMode');
  if (savedTheme) {
    applyTheme(savedTheme);
  } else {
    applyTheme('light');
  }

  if (themeToggleButton) {
    themeToggleButton.addEventListener('click', function() {
      const currentTheme = body.classList.contains('dark-bg') ? 'dark' : 'light';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('preferredThemeMode', newTheme);
    });
  }
})();

// === DOM Ready Logic ===
document.addEventListener('DOMContentLoaded', function() {
  console.log('✅ DOM fully loaded and parsed');

  // === Price Fetching for Title Bar ===
  async function fetchAndUpdatePrices() {
    const btcPriceSpan = document.getElementById('btcPrice');
    const ethPriceSpan = document.getElementById('ethPrice');
    const solPriceSpan = document.getElementById('solPrice');

    function showLoading() {
      if (btcPriceSpan) btcPriceSpan.textContent = 'Loading...';
      if (ethPriceSpan) ethPriceSpan.textContent = 'Loading...';
      if (solPriceSpan) solPriceSpan.textContent = 'Loading...';
    }

    function updatePriceElement(span, price) {
      if (span) {
        if (price !== undefined) {
          span.textContent = `$${price.toFixed(2)}`;
        } else {
          span.textContent = '--';
        }
      }
    }

    showLoading();

    try {
      const response = await fetch('/prices/api/data');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.mini_prices) {
        const btc = data.mini_prices.find(p => p.asset_type === 'BTC');
        const eth = data.mini_prices.find(p => p.asset_type === 'ETH');
        const sol = data.mini_prices.find(p => p.asset_type === 'SOL');

        updatePriceElement(btcPriceSpan, btc?.current_price);
        updatePriceElement(ethPriceSpan, eth?.current_price);
        updatePriceElement(solPriceSpan, sol?.current_price);
      }
    } catch (error) {
      console.error('Error fetching prices:', error);
      if (btcPriceSpan) btcPriceSpan.textContent = '--';
      if (ethPriceSpan) ethPriceSpan.textContent = '--';
      if (solPriceSpan) solPriceSpan.textContent = '--';
    }
  }

  // Fetch prices once after page load
  fetchAndUpdatePrices();

  // Optional: Refresh prices every 30 seconds
  setInterval(fetchAndUpdatePrices, 30000);
});
