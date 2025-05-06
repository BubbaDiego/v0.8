document.addEventListener("DOMContentLoaded", () => {
  renderGraph();
  renderPieCharts();
  // Removed startFreshnessTimer(); call — include it separately if needed
});

// =========================
// 📈 GRAPH - Portfolio Value Over Time
// =========================
function renderGraph() {
  fetch("/api/graph_data")
    .then(res => res.json())
    .then(data => {
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

      // ✅ Hide graph loader
      const loader = document.getElementById("graphLoader");
      if (loader) loader.style.display = "none";
    })
    .catch(err => console.error("❌ Failed to load graph data:", err));
}

// =========================
// 🥧 PIE CHARTS - Size + Collateral Composition
// =========================
function renderPieCharts() {
  fetch("/api/size_composition")
    .then(res => res.json())
    .then(data => {
      renderDonutChart("#pieChartSize", data.series, "Size Composition");
    })
    .catch(err => console.error("❌ Size Pie Error:", err));

  fetch("/api/collateral_composition")
    .then(res => res.json())
    .then(data => {
      renderDonutChart("#pieChartCollateral", data.series, "Collateral Composition");
    })
    .catch(err => console.error("❌ Collateral Pie Error:", err));
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

  // ✅ Hide matching loader manually
  if (selector === "#pieChartSize") {
    const loader = document.getElementById("pieSizeLoader");
    if (loader) loader.style.display = "none";
  } else if (selector === "#pieChartCollateral") {
    const loader = document.getElementById("pieCollateralLoader");
    if (loader) loader.style.display = "none";
  }
}
