// dashboard.js

console.log('✅ Dashboard.js Loaded!');

document.addEventListener('DOMContentLoaded', function () {

  // === LOADING OVERLAY ===
  const loadingOverlay = document.createElement('div');
  loadingOverlay.id = "loadingOverlay";
  loadingOverlay.style.position = "fixed";
  loadingOverlay.style.top = 0;
  loadingOverlay.style.left = 0;
  loadingOverlay.style.width = "100%";
  loadingOverlay.style.height = "100%";
  loadingOverlay.style.background = "rgba(255,255,255,0.8)";
  loadingOverlay.style.display = "flex";
  loadingOverlay.style.alignItems = "center";
  loadingOverlay.style.justifyContent = "center";
  loadingOverlay.style.zIndex = 9999;
  loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
  document.body.appendChild(loadingOverlay);

  // === THEME TOGGLE ===
  const toggleContainer = document.getElementById('toggleContainer');
  if (toggleContainer) {
    toggleContainer.addEventListener('click', () => {
      document.body.classList.toggle('dark-bg');
      document.body.classList.toggle('light-bg');
    });
  }

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
      if (timeLeft <= 0) timeLeft = totalTime;
    }, 1000);
  })();

  // === Table Sorting ===
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
        if (dir === "asc" && x.innerText.toLowerCase() > y.innerText.toLowerCase()) shouldSwitch = true;
        if (dir === "desc" && x.innerText.toLowerCase() < y.innerText.toLowerCase()) shouldSwitch = true;
        if (shouldSwitch) {
          rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
          switching = true;
          break;
        }
      }
      if (!switching && dir === "asc") {
        dir = "desc";
        switching = true;
      }
    }
  };

  const formatK = (num) => (num >= 1000 ? (num / 1000).toFixed(1) + 'k' : num.toString());

  function renderGraphChart(timestamps, values, collaterals) {
    const graphContainer = document.getElementById("graphChart");

    if (!timestamps || timestamps.length === 0 || !values || values.length === 0) {
      graphContainer.innerHTML = '<div style="text-align: center; padding: 2rem; font-weight: bold; color: #555;">No graph data available</div>';
      graphContainer.classList.add("fade-in");
      document.getElementById("graphLoader").style.display = "none";
      return;
    }

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

    const chart = new ApexCharts(graphContainer, options);
    chart.render();
    graphContainer.classList.add("fade-in");
    document.getElementById("graphLoader").style.display = "none";
  }

  function renderPieCharts(size, collateral, longS, shortS, longC, shortC) {
    const sizeContainer = document.getElementById("pieChartSize");
    const collContainer = document.getElementById("pieChartCollateral");

    // --- Size Pie ---
    if (!size || size.length === 0 || (size[0] === 0 && size[1] === 0)) {
      sizeContainer.innerHTML = '<div style="text-align: center; padding: 2rem; font-weight: bold; color: #555;">No size data available</div>';
    } else {
      const sizeOptions = {
        chart: { type: 'pie', height: 200 },
        series: size,
        labels: ['Long', 'Short'],
        legend: { labels: { colors: ['#fff'] } },
        dataLabels: {
          enabled: true,
          style: { fontSize: '18px', colors: ['#fff'] },
          formatter: val => Math.round(val) + '%'
        }
      };
      new ApexCharts(sizeContainer, sizeOptions).render();
    }
    sizeContainer.classList.add("fade-in");

    // --- Collateral Pie ---
    if (!collateral || collateral.length === 0 || (collateral[0] === 0 && collateral[1] === 0)) {
      collContainer.innerHTML = '<div style="text-align: center; padding: 2rem; font-weight: bold; color: #555;">No collateral data available</div>';
    } else {
      const collOptions = {
        chart: { type: 'pie', height: 200 },
        series: collateral,
        labels: ['Long', 'Short'],
        legend: { labels: { colors: ['#fff'] } },
        dataLabels: {
          enabled: true,
          style: { fontSize: '18px', colors: ['#fff'] },
          formatter: val => Math.round(val) + '%'
        }
      };
      new ApexCharts(collContainer, collOptions).render();
    }
    collContainer.classList.add("fade-in");

    // Hide Pie spinners
    document.getElementById("pieSizeLoader").style.display = "none";
    document.getElementById("pieCollateralLoader").style.display = "none";

    // Fill totals
    document.getElementById("pieSizeTotals").innerText = `Long: ${longS} / Short: ${shortS}`;
    document.getElementById("pieCollateralTotals").innerText = `Long: ${longC} / Short: ${shortC}`;
  }

  // === Fetch and Render Data ===
  Promise.all([
    fetch(GRAPH_DATA_URL).then(r => r.json()),
    fetch(SIZE_COMPOSITION_URL).then(r => r.json()),
    fetch(COLLATERAL_COMPOSITION_URL).then(r => r.json())
  ])
  .then(([graphData, sizeData, collData]) => {
    renderGraphChart(graphData.timestamps, graphData.values, graphData.collateral);

    const longS = sizeData.series ? sizeData.series[0] : 0;
    const shortS = sizeData.series ? sizeData.series[1] : 0;
    const longC = collData.series ? collData.series[0] : 0;
    const shortC = collData.series ? collData.series[1] : 0;

    renderPieCharts(
      sizeData.series || [0, 0],
      collData.series || [0, 0],
      longS,
      shortS,
      longC,
      shortC
    );
  })
  .catch(err => {
    console.error("Dashboard chart error:", err);
  })
  .finally(() => {
    // ✅ Always remove loading overlay
    loadingOverlay.remove();
  });

});
