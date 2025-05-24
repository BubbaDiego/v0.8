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
});
