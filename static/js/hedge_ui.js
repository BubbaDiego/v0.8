// static/js/hedge_ui.js

const HedgeUI = (function() {

  function buildCalculator() {
    const container = document.getElementById('hedgeCalculatorContainer');
    container.innerHTML = `
      <div class="row">
        <div class="col-md-6">
          <div class="card p-3">
            <h5>Long Position 📈</h5>
            <select id="longSelect" class="form-select mb-2"></select>
            <input type="number" id="longEntry" class="form-control mb-2" placeholder="Entry Price ($)" readonly>
            <input type="number" id="longSize" class="form-control mb-2" placeholder="Size (USD)">
          </div>
        </div>
        <div class="col-md-6">
          <div class="card p-3">
            <h5>Short Position 📉</h5>
            <select id="shortSelect" class="form-select mb-2"></select>
            <input type="number" id="shortEntry" class="form-control mb-2" placeholder="Entry Price ($)" readonly>
            <input type="number" id="shortSize" class="form-control mb-2" placeholder="Size (USD)">
          </div>
        </div>
      </div>
      <div class="row mt-4">
        <div class="col">
          <button id="calculateButton" class="btn btn-primary w-100">Calculate Hedge 📊</button>
        </div>
      </div>
      <div id="resultSection" class="mt-4"></div>
    `;

    populatePositionSelectors();
    bindEvents();
  }

  function populatePositionSelectors() {
    const longSelect = document.getElementById('longSelect');
    const shortSelect = document.getElementById('shortSelect');

    HedgeData.getLongPositions().forEach(pos => {
      const option = document.createElement('option');
      option.value = pos.id;
      option.textContent = `${pos.asset_type} @ $${pos.entry_price}`;
      longSelect.appendChild(option);
    });

    HedgeData.getShortPositions().forEach(pos => {
      const option = document.createElement('option');
      option.value = pos.id;
      option.textContent = `${pos.asset_type} @ $${pos.entry_price}`;
      shortSelect.appendChild(option);
    });
  }

  function bindEvents() {
    document.getElementById('calculateButton').addEventListener('click', function() {
      HedgeLogic.calculateResults();
    });

    document.getElementById('longSelect').addEventListener('change', function() {
      const selectedId = this.value;
      const pos = HedgeData.getLongPositions().find(p => p.id === selectedId);
      if (pos) {
        document.getElementById('longEntry').value = pos.entry_price;
        document.getElementById('longSize').value = pos.size;
      }
    });

    document.getElementById('shortSelect').addEventListener('change', function() {
      const selectedId = this.value;
      const pos = HedgeData.getShortPositions().find(p => p.id === selectedId);
      if (pos) {
        document.getElementById('shortEntry').value = pos.entry_price;
        document.getElementById('shortSize').value = pos.size;
      }
    });
  }

  function renderResults(html) {
    document.getElementById('resultSection').innerHTML = html;
  }

  return {
    buildCalculator,
    renderResults,
  };
})();
