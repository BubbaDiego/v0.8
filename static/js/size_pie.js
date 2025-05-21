// size_pie.js - render LONG vs SHORT size composition pie chart
window.addEventListener('DOMContentLoaded', () => {
  const data = window.sizeData?.series || [];
  const isZero = data.every(v => v === 0);
  const base = {
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

  let mode = 'donut';
  const chartEl = document.querySelector('#pieChartSize');
  const chart = new ApexCharts(chartEl, { ...base, chart: { type: mode, height: 260 } });
  chart.render();

  const btn = document.getElementById('togglePieMode');
  if (btn) {
    btn.addEventListener('click', () => {
      mode = mode === 'donut' ? 'pie' : 'donut';
      chart.updateOptions({ chart: { type: mode } });
    });
  }
});

