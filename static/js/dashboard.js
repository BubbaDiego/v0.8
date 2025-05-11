document.addEventListener("DOMContentLoaded", () => {
  renderGraph(graphData);
  renderPieCharts(sizeData, collateralData);
  // Optionally start freshness timer here
});

// =========================
// 📈 GRAPH - Portfolio Value Over Time
// =========================
function renderGraph(data) {
  const options = {
    chart: {
      type: "line",
      height: 300,
      toolbar: { show: false },
      zoom: { enabled: false }
    },
    series: [
      { name: "Total Value", data: data.values },
      { name: "Collateral", data: data.collateral }
    ],
    xaxis: {
      categories: data.timestamps,
      labels: { show: false }
    },
    stroke: { curve: "smooth", width: 3 },
    colors: ["#007bff", "#28a745"],
    grid: { borderColor: "#e0e0e0" },
    tooltip: { shared: true, intersect: false }
  };

  const chart = new ApexCharts(document.querySelector("#graphChart"), options);
  chart.render();

  const loader = document.getElementById("graphLoader");
  if (loader) loader.style.display = "none";
}

// =========================
// 🥧 PIE CHARTS - Size + Collateral Composition
// =========================
function renderPieCharts(size, collateral) {
  renderDonutChart("#pieChartSize", size.series, "Size Composition");
  renderDonutChart("#pieChartCollateral", collateral.series, "Collateral Composition");
}

// 🎯 Shared Donut Renderer + Spinner Cleanup
function renderDonutChart(selector, series, title) {
  const isZero = series.every(v => v === 0);
  const options = {
    chart: { type: "donut", height: 260 },
    labels: ["Long", "Short"],
    series: isZero ? [1] : series,
    colors: isZero ? ["#ccc"] : ["#3498db", "#e74c3c"],
    legend: { position: "bottom" },
    title: {
      text: title,
      align: "center",
      style: { fontSize: "14px", fontWeight: "bold" }
    },
    tooltip: {
      y: { formatter: val => `${val}%` }
    }
  };

  const chart = new ApexCharts(document.querySelector(selector), options);
  chart.render();

  if (selector === "#pieChartSize") {
    const loader = document.getElementById("pieSizeLoader");
    if (loader) loader.style.display = "none";
  } else if (selector === "#pieChartCollateral") {
    const loader = document.getElementById("pieCollateralLoader");
    if (loader) loader.style.display = "none";
  }
}
