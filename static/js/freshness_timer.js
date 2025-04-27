document.addEventListener('DOMContentLoaded', function () {

  const refreshInterval = 60000; // 1 minute

  let timers = {
    price: 150,
    position: 90,
    cyclone: 300
  };

  function formatTime(seconds) {
    let m = Math.floor(seconds / 60);
    let s = seconds % 60;
    return `${m}m ${s < 10 ? '0' : ''}${s}s`;
  }

  function formatTimestamp(isoStr) {
    if (!isoStr) return "N/A";
    const d = new Date(isoStr);
    let hours = d.getHours();
    let minutes = d.getMinutes();
    let ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    return `${hours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
  }

  function applyFreshnessVisuals(boxId, ageSeconds) {
  const box = document.getElementById(boxId);
  if (!box) return;

  const ageMinutes = ageSeconds / 60;

  box.classList.remove('fresh-pulse', 'warning-pulse', 'stale-pulse', 'fresh-gradient', 'warning-gradient', 'stale-gradient');

  if (ageMinutes < 5) {
    box.classList.add('fresh-pulse', 'fresh-gradient');
  } else if (ageMinutes < 10) {
    box.classList.add('warning-pulse', 'warning-gradient');
  } else {
    box.classList.add('stale-pulse', 'stale-gradient');
  }
}

  function updateCountdowns() {
    for (let key in timers) {
      if (timers[key] > 0) timers[key]--;

      const countdownEl = document.getElementById(`${key}Countdown`);
      if (countdownEl) {
        countdownEl.textContent = `Next in: ${formatTime(timers[key])}`;
      }

      applyFreshnessVisuals(`${key}Box`, `${key}Icon`, timers[key]);
    }
  }

  function fetchLedgerAges() {
    fetch('/api/ledger_ages')
      .then(response => response.json())
      .then(data => {
        if (data.price_age !== undefined) {
          timers.price = Math.max(180 - data.price_age, 0);
          document.getElementById('priceLast').textContent = `Last: ${formatTimestamp(data.price_last)}`;
        }
        if (data.position_age !== undefined) {
          timers.position = Math.max(120 - data.position_age, 0);
          document.getElementById('positionLast').textContent = `Last: ${formatTimestamp(data.position_last)}`;
        }
        if (data.cyclone_age !== undefined) {
          timers.cyclone = Math.max(300 - data.cyclone_age, 0);
          document.getElementById('cycloneLast').textContent = `Last: ${formatTimestamp(data.cyclone_last)}`;
        }
      })
      .catch(err => console.error('Ledger ages fetch error:', err));
  }

  fetchLedgerAges();
  updateCountdowns();
  setInterval(updateCountdowns, 1000);
  setInterval(fetchLedgerAges, refreshInterval);

});
