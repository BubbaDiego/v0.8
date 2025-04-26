// static/js/hedge_logic.js

const HedgeLogic = (function() {

  function calculateResults() {
    const longEntry = parseFloat(document.getElementById('longEntry').value) || 0;
    const longSize = parseFloat(document.getElementById('longSize').value) || 0;
    const shortEntry = parseFloat(document.getElementById('shortEntry').value) || 0;
    const shortSize = parseFloat(document.getElementById('shortSize').value) || 0;

    if (longEntry <= 0 || shortEntry <= 0 || longSize <= 0 || shortSize <= 0) {
      HedgeUI.renderResults(`<div class="alert alert-warning">⚠️ Please select and enter valid positions.</div>`);
      return;
    }

    const longValue = longEntry * (longSize / longEntry);
    const shortValue = shortEntry * (shortSize / shortEntry);

    const hedgeRatio = (longValue / shortValue).toFixed(2);

    let advice = "✅ Hedge is balanced.";
    if (hedgeRatio > 1.1) {
      advice = "⚠️ Long position is heavier. Consider adjusting short side.";
    } else if (hedgeRatio < 0.9) {
      advice = "⚠️ Short position is heavier. Consider adjusting long side.";
    }

    const resultHTML = `
      <div class="card p-3">
        <h5>📊 Hedge Summary</h5>
        <ul class="list-group list-group-flush">
          <li class="list-group-item">Long Value: $${longValue.toFixed(2)}</li>
          <li class="list-group-item">Short Value: $${shortValue.toFixed(2)}</li>
          <li class="list-group-item">Hedge Ratio: ${hedgeRatio}</li>
        </ul>
        <div class="mt-3 alert alert-info">${advice}</div>
      </div>
    `;

    HedgeUI.renderResults(resultHTML);
  }

  return {
    calculateResults,
  };
})();
