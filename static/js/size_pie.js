// size_pie.js - render LONG vs SHORT size composition pie chart
window.addEventListener('DOMContentLoaded', () => {
  const data = window.sizeData?.series || [];
  const isZero = data.every(v => v === 0);
  const options = {
    chart: { type: 'donut', height: 260 },
    labels: ['Long', 'Short'],
    series: isZero ? [1] : data,
    colors: isZero ? ['#ccc'] : ['#3498db', '#e74c3c'],
    legend: { position: 'bottom' },
    title: {
      text: 'Size Composition',
      align: 'center',
      style: { fontSize: '14px', fontWeight: 'bold' }
    },
    tooltip: { y: { formatter: val => `${val}%` } }
  };
  const chartEl = document.querySelector('#pieChartSize');
  const chart = new ApexCharts(chartEl, options);
  chart.render();

  // allow toggling donut vs pie
  const btn = document.getElementById('togglePieType');
  let donut = true;
  if (btn) {
    btn.addEventListener('click', () => {
      donut = !donut;
      chart.updateOptions({ chart: { type: donut ? 'donut' : 'pie' } });
      btn.textContent = donut ? 'Full Pie' : 'Donut';
    });
  }
});

