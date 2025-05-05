document.addEventListener("DOMContentLoaded", function() {
  const toggleAll = document.getElementById("toggleAllAlerts");
  const refreshButton = document.getElementById("refreshAlerts");

  if (toggleAll) {
    toggleAll.addEventListener("change", () => {
      const allDetails = document.querySelectorAll("details.info-box");
      allDetails.forEach(detail => {
        toggleAll.checked ? detail.setAttribute("open", "open") : detail.removeAttribute("open");
      });
    });
  }

  if (refreshButton) {
    refreshButton.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      try {
        refreshButton.classList.add("disabled");
        refreshButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        const response = await fetch("/alerts/refresh_alerts", { method: "POST" });
        const result = await response.json();

        if (result.success) {
          alert(result.message);
          window.location.reload();
        } else {
          alert("Error refreshing alerts: " + result.error);
        }
      } catch (err) {
        console.error("Refresh failed:", err);
        alert("Failed to refresh alerts. See console.");
      } finally {
        refreshButton.classList.remove("disabled");
        refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
      }
    });
  }
});
