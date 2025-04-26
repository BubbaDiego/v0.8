// dashboard.js

console.log('✅ Dashboard.js Loaded!'); // HEARTBEAT

document.addEventListener('DOMContentLoaded', function () {

  // === THEME TOGGLE ===
  const toggleContainer = document.getElementById('toggleContainer');
  const statusBar = document.getElementById('statusBar');
  const pieBox = document.getElementById('pieBox');
  const graphBox = document.getElementById('graphBox');
  const miniTableBox = document.getElementById('miniTableBox');
  const liquidationBox = document.getElementById('liquidationBox');

  if (toggleContainer) {
    const sunIcon = `<svg viewBox="0 0 24 24" width="16" height="16" fill="white" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3" stroke="white" stroke-width="2"/><line x1="12" y1="21" x2="12" y2="23" stroke="white" stroke-width="2"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="white" stroke-width="2"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="white" stroke-width="2"/><line x1="1" y1="12" x2="3" y2="12" stroke="white" stroke-width="2"/><line x1="21" y1="12" x2="23" y2="12" stroke="white" stroke-width="2"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="white" stroke-width="2"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="white" stroke-width="2"/></svg>`;
    const moonIcon = `<svg viewBox="0 0 24 24" width="16" height="16" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M21 12.79A9 9 0 0 1 11.21 3 A7 7 0 0 0 12 17 a7 7 0 0 0 9 -4.21 z"/></svg>`;

    toggleContainer.innerHTML = moonIcon;

    toggleContainer.addEventListener('click', () => {
      [statusBar, pieBox, graphBox, miniTableBox, liquidationBox].forEach(box => {
        box.classList.toggle('dark-mode');
        box.classList.toggle('light-mode');
      });
      toggleContainer.innerHTML = document.body.classList.contains('dark-bg') ? moonIcon : sunIcon;
      document.body.classList.toggle('light-bg');
      document.body.classList.toggle('dark-bg');
    });
  }

  // === DISABLED: Countdown360 Plugin ===
  /*
  function startCountdown(selector, minutes, fillColor = '#8ac575') {
    const seconds = minutes * 60;
    $(selector).countdown360({
      radius: 24,
      seconds: seconds,
      fillStyle: fillColor,
      strokeStyle: '#477050',
      fontColor: '#ffffff',
      autostart: false,
      onComplete: function () {
        console.log(selector + ' countdown complete!');
      }
    }).start();
  }
  startCountdown('#sonic-timer-container', 5, '#b19cd9');
  startCountdown('#den-timer-container', 10);
  */

  // === Analog Price Timer ===
  (function priceAnalogTimer() {
    const totalTime = 60;
    let timeLeft = totalTime;
    const hand = document.querySelector('#price-timer-container .hand');
    if (!hand) return;

    function updateHand() {
      const angle = (360 * (totalTime - timeLeft)) / totalTime;
      hand.style.transform = `rotate(${angle}deg)`;
    }
    updateHand();
    setInterval(() => {
      timeLeft--;
      updateHand();
      if (timeLeft <= 0) {
        timeLeft = totalTime;
      }
    }, 1000);
  })();

  // === Table Sorting (Positions) ===
  window.sortTable = function (tableId, colIndex) {
    let table = document.getElementById(tableId);
    let switching = true;
    let dir = "asc";
    while (switching) {
      switching = false;
      let rows = table.rows;
      for (let i = 1; i < rows.length - 1; i++) {
        let shouldSwitch = false;
        let x = rows[i].getElementsByTagName("TD")[colIndex];
        let y = rows[i + 1].getElementsByTagName("TD")[colIndex];
        if (dir === "asc" && x.innerText.toLowerCase() > y.innerText.toLowerCase()) {
          shouldSwitch = true;
          break;
        }
        if (dir === "desc" && x.innerText.toLowerCase() < y.innerText.toLowerCase()) {
          shouldSwitch = true;
          break;
        }
      }
      if (shouldSwitch) {
        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
        switching = true;
      } else if (switching === false && dir === "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }

  // === Chart Render Functions ===
  const formatK = (num) => (num >= 1000 ? (num / 1000).toFixed(1) + 'k' : num.toString());

  function renderGraphChart(timestamps, values, collaterals) {
    if (!timestamps || !values) return;
    const options = {
      chart: { type: 'line', height: 300 },
      series: [
        { name: "Value", data: values },
        { name: "Collateral", data: collaterals || values.map(() => 0) }
      ],
      xaxis: {
        categories: timestamps.map(ts => {
          const d = new Date(ts);
          return `${(d.getHours() % 12 || 12)}:00 ${d.getHours() >= 12 ? 'PM' : 'AM'}`;
        }),
        labels: { style: { colors: '#fff' } }
      },
      yaxis: { labels: { style: { colors: '#fff' } } },
      stroke: { curve: 'smooth' },
      colors: ['#34a853', '#6234da'],
      legend: { labels: { colors: '#fff' } },
      tooltip: { theme: 'dark' }
    };
    const chart = new ApexCharts(document.querySelector("#graphChart"), options);
    chart.render();
  }

  function renderPieCharts(size, collateral, longS, shortS, longC, shortC) {
    const pieOptions = (series) => ({
      chart: { type: 'pie', height: 200 },
      series: series,
      labels: ['Long', 'Short'],
      legend: { labels: { colors: ['#fff'] } },
      dataLabels: {
        enabled: true,
        style: { fontSize: '18px', colors: ['#fff'] },
        formatter: val => Math.round(val) + '%'
      }
    });
    new ApexCharts(document.querySelector("#pieChartSize"), pieOptions(size)).render();
    new ApexCharts(document.querySelector("#pieChartCollateral"), pieOptions(collateral)).render();
    document.getElementById("pieSizeTotals").innerText = `Long: ${formatK(longS)} / Short: ${formatK(shortS)}`;
    document.getElementById("pieCollateralTotals").innerText = `Long: ${formatK(longC)} / Short: ${formatK(shortC)}`;
  }

  // === Fetch and Render Data ===
  Promise.all([
    fetch(GRAPH_DATA_URL).then(r => r.json()),
    fetch(SIZE_COMPOSITION_URL).then(r => r.json()),
    fetch(COLLATERAL_COMPOSITION_URL).then(r => r.json())
  ])
  .then(([graphData, sizeData, collData]) => {
    renderGraphChart(graphData.timestamps, graphData.values, graphData.collateral);
    renderPieCharts(
      sizeData.series || [0, 0],
      collData.series || [0, 0],
      sizeData.longAmount || 0,
      sizeData.shortAmount || 0,
      collData.longAmount || 0,
      collData.shortAmount || 0
    );

    // ✅ Hide Spinners
    document.getElementById("graphLoader").style.display = "none";
    document.getElementById("pieSizeLoader").style.display = "none";
    document.getElementById("pieCollateralLoader").style.display = "none";
  })
  .catch(err => {
    console.error("Dashboard chart error:", err);
  });

});
