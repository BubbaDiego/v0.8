<div class="common-box liquidation-box">
  <div class="chart-label">Liquidation Bar</div>

  <div class="liq-row">
    <img class="wallet-icon" src="/static/images/obivault.jpg" alt="ObiVault" />

    <div class="liq-progress-bar">
      <div class="liq-bar-container">
        <div class="liq-midline"></div>

        <!-- Positive travel -->
        <div class="liq-bar-fill positive" style="left:50%; width: 35%;">
          <div class="travel-text">35.0%</div>
        </div>
      </div>

      <div class="liq-flame-container">
        🔥
        <span class="heat-index-number">42</span>
      </div>
    </div>
  </div>

  <div class="liq-row">
    <img class="wallet-icon" src="/static/images/r2vault.jpg" alt="R2Vault" />

    <div class="liq-progress-bar">
      <div class="liq-bar-container">
        <div class="liq-midline"></div>

        <!-- Negative travel -->
        <div class="liq-bar-fill negative" style="right:50%; width: 20%;">
          <div class="travel-text">-20.0%</div>
        </div>
      </div>

      <div class="liq-flame-container">
        🔥
        <span class="heat-index-number">68</span>
      </div>
    </div>
  </div>
</div>

<style>
.common-box {
  background: #fff;
  padding: 1rem;
  border-radius: 0.75rem;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  margin-top: 1rem;
}

.chart-label {
  font-weight: bold;
  margin-bottom: 1rem;
  font-size: 1rem;
  color: #222;
}

.liq-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.wallet-icon {
  width: 32px;
  height: 32px;
  object-fit: cover;
  border-radius: 50%;
}

.liq-progress-bar {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.liq-bar-container {
  position: relative;
  flex-grow: 1;
  background: #e0e0e0;
  height: 20px;
  border-radius: 999px;
  overflow: hidden;
  margin-right: 10px;
}

.liq-midline {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #333;
  z-index: 5;
}

.liq-bar-fill {
  position: absolute;
  height: 100%;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
  min-width: 3.5rem;
  padding: 0 4px;
  color: white;
  transition: all 0.4s ease;
}

.liq-bar-fill.positive {
  background: repeating-linear-gradient(
    45deg, #28a745 0, #28a745 10px, #2ecc71 10px, #2ecc71 20px
  );
}

.liq-bar-fill.negative {
  background: repeating-linear-gradient(
    45deg, #dc3545 0, #dc3545 10px, #e74c3c 10px, #e74c3c 20px
  );
}

.liq-flame-container {
  position: relative;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ff5722;
  color: white;
  font-weight: bold;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  margin-left: 10px;
}

.heat-index-number {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.8rem;
}
</style>
