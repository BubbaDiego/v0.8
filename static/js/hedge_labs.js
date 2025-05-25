function loadHedges() {
  return fetch('/sonic_labs/api/hedges')
    .then(resp => resp.json())
    .then(data => {
      const tbody = document.getElementById('hedgeTableBody');
      if (tbody) {
        tbody.innerHTML = '';
        (data.hedges || []).forEach(h => {
          const tr = document.createElement('tr');
          const assetImg = `/static/images/${h.asset_image}`;
          const walletImg = `/static/images/${h.wallet_image}`;
          tr.innerHTML = `
            <td>
              <img class="asset-icon me-1" src="${assetImg}" alt="asset">
              <span class="mx-1">⛓️</span>
              <img class="wallet-icon ms-1" src="${walletImg}" alt="wallet">
            </td>
            <td>${h.positions.join(', ')}</td>
            <td>${h.total_heat_index}</td>`;
          tbody.appendChild(tr);
        });
      }
      window.initialHedges = data.hedges || [];
      return window.initialHedges;
    });
}

function postAction(url) {
  fetch(url, {method: 'POST'})
    .then(resp => resp.json())
    .then(() => loadHedges());
}

let currentHedgeId = null;
let hedgePositions = [];

function loadHedgePositions(id) {
  fetch(`/sonic_labs/api/hedge_positions?hedge_id=${id}`)
    .then(resp => resp.json())
    .then(data => {
      hedgePositions = data.positions || [];
      initSlider();
      updateEvaluation();
    });
}

function initSlider() {
  const slider = document.getElementById('priceSlider');
  if (!slider || hedgePositions.length === 0) return;
  slider.disabled = false;
  const long = hedgePositions.find(p => (p.position_type || '').toUpperCase() === 'LONG') || {};
  const short = hedgePositions.find(p => (p.position_type || '').toUpperCase() === 'SHORT') || {};
  const longLiq = parseFloat(long.liquidation_price) || 0;
  const shortLiq = parseFloat(short.liquidation_price) || 0;
  const longEntry = parseFloat(long.entry_price) || 0;
  const shortEntry = parseFloat(short.entry_price) || 0;
  const longCurrent = parseFloat(long.current_price) || longEntry;
  const shortCurrent = parseFloat(short.current_price) || shortEntry;
  const current =
    longCurrent && shortCurrent
      ? (longCurrent + shortCurrent) / 2
      : longCurrent || shortCurrent || 0;

  let min = longLiq ? longLiq * 0.95 : current * 0.8;
  let max = shortLiq ? shortLiq * 1.05 : current * 1.2;
  if (min > max) [min, max] = [max, min];
  slider.min = min;
  slider.max = max;
  const clamped = Math.min(Math.max(current, min), max);
  slider.value = clamped;
  document.getElementById('priceValue').textContent = 'Price: $' + current.toFixed(2);
}

function updateEvaluation() {
  const slider = document.getElementById('priceSlider');
  if (!slider || !currentHedgeId) return;
  const price = parseFloat(slider.value);
  document.getElementById('priceValue').textContent = 'Price: $' + price.toFixed(2);
  fetch(`/sonic_labs/api/evaluate_hedge?hedge_id=${currentHedgeId}&price=${price}`)
    .then(resp => resp.json())
    .then(data => updateTable(data));
}

function updateTable(data) {
  const body = document.querySelector('#evalTable tbody');
  if (!body) return;
  body.innerHTML = '';
  ['long', 'short'].forEach(type => {
    const row = data[type];
    if (!row) return;
    const tr = document.createElement('tr');
    const value = typeof row.value === 'number' ? row.value.toFixed(2) : row.value;
    const travel = typeof row.travel_percent === 'number' ? row.travel_percent.toFixed(2) : row.travel_percent;
    const liq = typeof row.liquidation_distance === 'number' ? row.liquidation_distance.toFixed(2) : row.liquidation_distance;
    const heat = typeof row.heat_index === 'number' ? row.heat_index.toFixed(2) : row.heat_index;
    tr.innerHTML = `<td>${type}</td><td>${value}</td><td>${travel}</td><td>${liq}</td><td>${heat}</td>`;
    body.appendChild(tr);
  });
  if (data.totals) {
    const tr = document.createElement('tr');
    const liqDistances = ['long', 'short']
      .map(t => data[t])
      .filter(r => r && r.liquidation_distance !== undefined)
      .map(r => parseFloat(r.liquidation_distance))
      .filter(v => !isNaN(v));
    const avgLiq = liqDistances.length ? (liqDistances.reduce((a, b) => a + b, 0) / liqDistances.length).toFixed(2) : '-';
    tr.innerHTML = `<th>Total</th><th>${data.totals.total_value}</th><th>${data.totals.avg_travel_percent.toFixed(2)}</th><th>${avgLiq}</th><th>${data.totals.avg_heat_index.toFixed(2)}</th>`;
    body.appendChild(tr);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadHedges().then((hedges) => {
    const select = document.getElementById('hedgeSelect');
    if (select && !select.value && hedges && hedges.length) {
      currentHedgeId = hedges[0].id;
      select.value = currentHedgeId;
      loadHedgePositions(currentHedgeId);
    }
  });
  const linkBtn = document.getElementById('linkHedgesBtn');
  const unlinkBtn = document.getElementById('unlinkHedgesBtn');
  if (linkBtn) linkBtn.addEventListener('click', () => postAction('/sonic_labs/api/link_hedges'));
  if (unlinkBtn) unlinkBtn.addEventListener('click', () => postAction('/sonic_labs/api/unlink_hedges'));

  const select = document.getElementById('hedgeSelect');
  const slider = document.getElementById('priceSlider');
  if (select) {
    select.addEventListener('change', () => {
      currentHedgeId = select.value;
      if (currentHedgeId) loadHedgePositions(currentHedgeId);
    });
  }
  if (slider) {
    slider.addEventListener('input', updateEvaluation);
  }
});
