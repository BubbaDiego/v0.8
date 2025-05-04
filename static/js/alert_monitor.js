let alertData = [];
let sortKey = 'last_triggered';
let sortDirection = 'desc';

// Sanitize and normalize levels
function getSafeLevel(level) {
  const valid = ["High", "Medium", "Low", "Normal"];
  if (typeof level === "string" && valid.includes(level)) return level;
  return "Normal";
}

function getSafeStatus(status) {
  const valid = ["Active", "Inactive"];
  if (typeof status === "string" && valid.includes(status)) return status;
  return "Inactive";
}

async function fetchAlerts() {
  try {
    const res = await fetch("/alerts/monitor");
    const json = await res.json();
    alertData = json.alerts || [];
    renderTable();
  } catch (err) {
    console.error("Failed to fetch alerts:", err);
  }
}

function renderTable() {
  const filterLevel = document.getElementById("levelFilter").value;
  const tbody = document.querySelector("#alertTable tbody");
  tbody.innerHTML = "";

  let filtered = alertData.filter(a => {
    return !filterLevel || getSafeLevel(a.level) === filterLevel;
  });

  filtered.sort((a, b) => {
    const valA = a[sortKey] ?? '';
    const valB = b[sortKey] ?? '';
    if (typeof valA === "number" && typeof valB === "number") {
      return sortDirection === 'asc' ? valA - valB : valB - valA;
    }
    return sortDirection === 'asc'
      ? String(valA).localeCompare(String(valB))
      : String(valB).localeCompare(String(valA));
  });

  filtered.forEach(alert => {
    const row = document.createElement("tr");
    const level = getSafeLevel(alert.level);
    const status = getSafeStatus(alert.status);

    row.innerHTML = `
      <td>${alert.id}</td>
      <td>${alert.alert_type}</td>
      <td>${alert.trigger_value ?? "—"}</td>
      <td>${alert.evaluated_value ?? "—"}</td>
      <td><span class="badge level-${level}">${level}</span></td>
      <td><span class="badge status-${status}">${status}</span></td>
      <td>${alert.last_triggered ? new Date(alert.last_triggered).toLocaleString() : "—"}</td>
    `;
    tbody.appendChild(row);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  fetchAlerts();
  setInterval(fetchAlerts, 10000);

  document.getElementById("manualRefreshBtn").addEventListener("click", fetchAlerts);
  document.getElementById("levelFilter").addEventListener("change", renderTable);

  document.querySelectorAll(".click-sortable").forEach(th => {
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      if (key === sortKey) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        sortKey = key;
        sortDirection = 'asc';
      }
      renderTable();
    });
  });
});
