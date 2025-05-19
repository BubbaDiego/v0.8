const alerts = [
  { asset: 'BTC', alert_type: 'TravelPercentLiquid', starting_value: 40000, trigger_value: 60000, evaluated_value: 52000, level: 'Medium', thresholds: { low: 45000, medium: 50000, high: 55000 }},
  { asset: 'ETH', alert_type: 'HeatIndex', starting_value: 1800, trigger_value: 2200, evaluated_value: 2000, level: 'Low', thresholds: { low: 1900, medium: 2100, high: 2150 }},
  { asset: 'SOL', alert_type: 'Profit', starting_value: 20, trigger_value: 15, evaluated_value: 17, level: 'Normal', thresholds: { low: 16, medium: 18, high: 20 }},
  { asset: 'AVAX', alert_type: 'TotalValue', starting_value: 12, trigger_value: 20, evaluated_value: 21, level: 'High', thresholds: { low: 15, medium: 18, high: 20 }},
];

const listEl = document.getElementById('alertList');
listEl.innerHTML = '';

alerts.forEach(alert => {
  const start = alert.starting_value ?? 0;
  const trigger = alert.trigger_value ?? 0;
  const current = alert.evaluated_value ?? 0;
  let travelPercent = 0;
  if (trigger !== start) {
    travelPercent = ((current - start) / (trigger - start)) * 100;
    travelPercent = Math.min(Math.max(travelPercent, -100), 100);
  }

  const flip = document.createElement('div');
  flip.className = 'alert-flip';
  flip.innerHTML = `
    <div class="flip-card-inner">
      <div class="flip-card-front">
        <div class="card-face-content">
          <img src="/static/images/${alert.asset?.toLowerCase() ?? 'unknown'}_logo.png" class="asset-icon" alt="${alert.asset || 'unknown'}" onerror="this.src='/static/images/unknown.png'">
          <div class="bar-card">
            <span style="font-size:1.01em;font-weight:500;min-width:120px;">${alert.alert_type || 'Unknown'}</span>
            <div class="liq-row">
              <div class="liq-bar-container">
                <div class="liq-midline"></div>
                <div class="liq-bar-fill ${travelPercent >= 0 ? 'positive' : 'negative'}"
                  style="${travelPercent >= 0
                    ? `left:50%;width:${travelPercent}%`
                    : `right:50%;width:${Math.abs(travelPercent)}%`}">
                  <span class="travel-text">${travelPercent.toFixed(1)}%</span>
                </div>
              </div>
              <div class="liq-level-badge level-${alert.level}">${alert.level.charAt(0)}</div>
            </div>
          </div>
          <span class="flip-hint">⤵ flip</span>
        </div>
      </div>
      <div class="flip-card-back">
        <div class="card-face-content">
          <div class="threshold-row">
            <span style="font-weight: 600;">Thresholds:</span>
            <span>Low: <b>${alert.thresholds?.low ?? '-'}</b></span>
            <span>Med: <b>${alert.thresholds?.medium ?? '-'}</b></span>
            <span>High: <b>${alert.thresholds?.high ?? '-'}</b></span>
          </div>
          <div class="value-row">
            <span>Eval: <b>${alert.evaluated_value}</b></span>
            <span>Trigger: <b>${alert.trigger_value}</b></span>
            <span>Start: <b>${alert.starting_value}</b></span>
          </div>
          <span class="flip-hint">⤴ flip back</span>
        </div>
      </div>
    </div>
  `;
  flip.addEventListener('click', () => {
    flip.classList.toggle('flipped');
  });
  listEl.appendChild(flip);
});
