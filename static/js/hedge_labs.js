function loadHedges() {
  fetch('/sonic_labs/api/hedges')
    .then(resp => resp.json())
    .then(data => {
      const tbody = document.getElementById('hedgeTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';
      (data.hedges || []).forEach(h => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${h.id}</td><td>${h.positions.join(', ')}</td><td>${h.total_heat_index}</td>`;
        tbody.appendChild(tr);
      });
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
  const current = longEntry && shortEntry ? (longEntry + shortEntry) / 2 : longEntry || shortEntry || 0;
  slider.min = longLiq ? longLiq * 0.95 : current * 0.8;
  slider.max = shortLiq ? shortLiq * 1.05 : current * 1.2;
  slider.value = current;
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
    tr.innerHTML = `<td>${type}</td><td>${row.value}</td><td>${row.travel_percent}</td><td>${row.heat_index}</td>`;
    body.appendChild(tr);
  });
  if (data.totals) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<th>Total</th><th>${data.totals.total_value}</th><th>${data.totals.avg_travel_percent.toFixed(2)}</th><th>${data.totals.avg_heat_index.toFixed(2)}</th>`;
    body.appendChild(tr);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadHedges();
  const linkBtn = document.getElementById('linkHedgesBtn');
  const unlinkBtn = document.getElementById('unlinkHedgesBtn');
  const testBtn = document.getElementById('testCalcsBtn');
  if (linkBtn) linkBtn.addEventListener('click', () => postAction('/sonic_labs/api/link_hedges'));
  if (unlinkBtn) unlinkBtn.addEventListener('click', () => postAction('/sonic_labs/api/unlink_hedges'));
  if (testBtn) testBtn.addEventListener('click', () => {
    fetch('/sonic_labs/api/test_calcs').then(resp => resp.json()).then(res => {
      console.log('Calc Totals', res);
    });
  });

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
