/*************************************
 * Display Mode Functions
 *************************************/
function setDisplayMode(mode) {
  if (mode === 'full') {
    document.getElementById('positionInputRow').style.display = 'flex';
    document.getElementById('modifierRow').style.display = 'flex';
    document.getElementById('approachToggleRow').style.display = 'flex';
    document.getElementById('recommendationRow').style.display = 'flex';
    document.getElementById('outputRow').style.display = 'flex';
    document.getElementById('projectedOutputRow').style.display = 'flex';
  } else if (mode === 'gear') {
    document.getElementById('positionInputRow').style.display = 'none';
    document.getElementById('modifierRow').style.display = 'flex';
    document.getElementById('approachToggleRow').style.display = 'flex';
    document.getElementById('recommendationRow').style.display = 'flex';
    document.getElementById('outputRow').style.display = 'flex';
    document.getElementById('projectedOutputRow').style.display = 'flex';
  } else if (mode === 'test') {
    document.getElementById('positionInputRow').style.display = 'none';
    document.getElementById('modifierRow').style.display = 'none';
    document.getElementById('approachToggleRow').style.display = 'flex';
    document.getElementById('recommendationRow').style.display = 'flex';
    document.getElementById('outputRow').style.display = 'flex';
    document.getElementById('projectedOutputRow').style.display = 'flex';
  }
}

/*************************************
 * Variables & Position Data
 *************************************/
let referencePrice = 100;
let longLiquidation = null;
let shortLiquidation = null;
let lastComputedCurrentPrice = 0;
// longPositions and shortPositions should be defined globally

/*************************************
 * Load & Update Position Functions
 *************************************/
function loadLongPosition() {
  const selectedId = document.getElementById("longSelect").value;
  const pos = longPositions.find(p => p.id === selectedId);
  if (pos) {
    document.getElementById("longEntry").value = pos.entry_price;
    document.getElementById("longSize").value = pos.size;
    document.getElementById("longCollateral").value = pos.collateral || 0;
    document.getElementById("longLiqPrice").value = pos.liquidation_price || 0;
    longLiquidation = pos.liquidation_price;
    updateReferencePrice();
  }
}

function loadShortPosition() {
  const selectedId = document.getElementById("shortSelect").value;
  const pos = shortPositions.find(p => p.id === selectedId);
  if (pos) {
    document.getElementById("shortEntry").value = pos.entry_price;
    document.getElementById("shortSize").value = pos.size;
    document.getElementById("shortCollateral").value = pos.collateral || 0;
    document.getElementById("shortLiqPrice").value = pos.liquidation_price || 0;
    shortLiquidation = pos.liquidation_price;
    updateReferencePrice();
  }
}

/*************************************
 * Price Slider & Marker Functions
 *************************************/
function updateReferencePrice() {
  const longEntry = parseFloat(document.getElementById("longEntry").value) || 0;
  const shortEntry = parseFloat(document.getElementById("shortEntry").value) || 0;
  let currentPrice = 0;
  if (longEntry > 0 && shortEntry > 0) {
    currentPrice = (longEntry + shortEntry) / 2;
  } else if (longEntry > 0) {
    currentPrice = longEntry;
  } else if (shortEntry > 0) {
    currentPrice = shortEntry;
  }
  const slider = document.getElementById("priceSlider");
  if (longLiquidation && shortLiquidation) {
    slider.min = longLiquidation * 0.95;
    slider.max = shortLiquidation * 1.05;
  } else {
    slider.min = currentPrice * 0.75 * 0.95;
    slider.max = currentPrice * 1.25 * 1.05;
  }
  slider.value = currentPrice;
  lastComputedCurrentPrice = currentPrice;
  sliderChanged();
  updateEntryMarkers();
}

function sliderChanged() {
  const simPrice = parseFloat(document.getElementById("priceSlider").value);
  updatePriceTicks();
  updateMarker();
  updateLong(simPrice);
  updateShort(simPrice);
  updateHedgeRecommendations(simPrice);
  updateLongHeatIndex(simPrice);
  updateShortHeatIndex(simPrice);
  updateLongTravelPercent(simPrice);
  updateShortTravelPercent(simPrice);
  updateProjectedPositions(simPrice);
  updateLongSimHeatIndex(simPrice);
  updateShortSimHeatIndex(simPrice);
}

function updatePriceTicks() {
  if (longLiquidation) {
    document.getElementById("tickLeft").innerHTML =
      `<span style="font-size:1.2rem; font-weight:bold;">$${parseFloat(longLiquidation).toFixed(2)}</span><br><small>💧 Long Liquidation</small>`;
  }
  if (shortLiquidation) {
    document.getElementById("tickRight").innerHTML =
      `<span style="font-size:1.2rem; font-weight:bold;">$${parseFloat(shortLiquidation).toFixed(2)}</span><br><small>💧 Short Liquidation</small>`;
  }
}

function updateMarker() {
  const slider = document.getElementById("priceSlider");
  const simPrice = parseFloat(slider.value);
  const markerLeft = ((simPrice - parseFloat(slider.min)) / (parseFloat(slider.max) - parseFloat(slider.min))) * slider.getBoundingClientRect().width;
  const marker = document.getElementById("currentMarker");
  marker.style.left = markerLeft + "px";
  marker.innerHTML = "Price: $" + simPrice.toFixed(2);
}

function updateEntryMarkers() {
  const slider = document.getElementById("priceSlider");
  const sliderWidth = slider.getBoundingClientRect().width;
  const longEntry = parseFloat(document.getElementById("longEntry").value) || 0;
  const shortEntry = parseFloat(document.getElementById("shortEntry").value) || 0;
  if (longEntry) {
    const longMarkerLeft = ((longEntry - parseFloat(slider.min)) / (parseFloat(slider.max) - parseFloat(slider.min))) * sliderWidth;
    const longMarker = document.getElementById("entryMarkerLong");
    longMarker.style.left = longMarkerLeft + "px";
    longMarker.innerHTML = "Long Entry: $" + longEntry.toFixed(2);
  }
  if (shortEntry) {
    const shortMarkerLeft = ((shortEntry - parseFloat(slider.min)) / (parseFloat(slider.max) - parseFloat(slider.min))) * sliderWidth;
    const shortMarker = document.getElementById("entryMarkerShort");
    shortMarker.style.left = shortMarkerLeft + "px";
    shortMarker.innerHTML = "Short Entry: $" + shortEntry.toFixed(2);
  }
}

/*************************************
 * Current Positions: Update Outputs
 *************************************/
function updateLong(simPrice) {
  const longEntry = parseFloat(document.getElementById("longEntry").value) || 0;
  const longSize = parseFloat(document.getElementById("longSize").value) || 0;
  const collateral = parseFloat(document.getElementById("longCollateral").value) || 0;
  const fee = parseFloat(document.getElementById("feePercentage").value) || 0;
  let tokenCount = longEntry > 0 ? longSize / longEntry : 0;
  let pnl = (simPrice - longEntry) * tokenCount;
  let feeCost = (fee / 100) * longSize;
  let netValue = collateral + pnl - feeCost;

  if (longLiquidation && simPrice <= longLiquidation) {
    document.getElementById("longSimPrice").innerHTML =
      "<strong>Simulated Price: $" + simPrice.toFixed(2) + " (Liquidated)</strong>";
    document.getElementById("longCollateralDisplay").innerHTML =
      "<strong>Collateral: $" + collateral.toFixed(2) + "</strong>";
    document.getElementById("longValue").innerHTML =
      "<strong>Position Value: $0.00</strong>";
    document.getElementById("longPnL").innerHTML =
      "<strong>P&L: <span class='text-secondary'>Liquidated</span></strong>";
    document.getElementById("longSLTP").innerHTML =
      "<strong>Recommended: Liquidated</strong>";
    document.getElementById("longSafetyMargin").innerHTML =
      "<strong>Safety Margin: 0%</strong>";
    document.getElementById("longOutputCard").className =
      "card shadow-sm bg-secondary bg-opacity-25 border border-2 border-secondary reduced-height";
    document.getElementById("longCurrentSize").innerHTML =
      "<strong>Current Size: $0.00</strong>";
    return;
  }

  document.getElementById("longSimPrice").innerHTML =
    "<strong>Simulated Price: $" + simPrice.toFixed(2) + "</strong>";
  document.getElementById("longCollateralDisplay").innerHTML =
    "<strong>Collateral: $" + collateral.toFixed(2) + "</strong>";
  document.getElementById("longValue").innerHTML =
    "<strong>Position Value: $" + netValue.toFixed(2) + "</strong>";
  let pnlColor = (pnl - feeCost) >= 0 ? "text-success" : "text-danger";
  let bgClass = (pnl - feeCost) >= 0
    ? "bg-success bg-opacity-10 border border-2 border-success"
    : "bg-danger bg-opacity-10 border border-2 border-danger";
  document.getElementById("longPnL").innerHTML =
    "<strong>P&L: <span class='" + pnlColor + "'>" +
    ((pnl - feeCost) >= 0 ? "▲ " : "▼ ") + "$" +
    (pnl - feeCost).toFixed(2) + "</span></strong>";
  let recommendation = "";
  let recIcon = "";
  if (simPrice < longEntry) {
    recommendation = "Stop Loss at $" + simPrice.toFixed(2);
    recIcon = "▼ ";
  } else if (simPrice > longEntry) {
    recommendation = "Take Profit at $" + simPrice.toFixed(2);
    recIcon = "▲ ";
  } else {
    recommendation = "At Entry Price";
    recIcon = "— ";
  }
  document.getElementById("longSLTP").innerHTML =
    "<strong>Recommended: " + recIcon + recommendation + "</strong>";
  document.getElementById("longOutputCard").className =
    "card shadow-sm " + bgClass + " reduced-height";
  document.getElementById("longCurrentSize").innerHTML =
    "<strong>Current Size: $" + longSize.toFixed(2) + "</strong>";
  const longLiq = longLiquidation || (longEntry * 0.8);
  const longRange = longEntry - longLiq;
  const longSafety = simPrice - longLiq;
  const longMargin = longRange > 0 ? longSafety / longRange : 0;
  document.getElementById("longSafetyMargin").innerHTML =
    "<strong>Safety Margin: " + (longMargin * 100).toFixed(1) + "%</strong>";
}

function updateShort(simPrice) {
  const shortEntry = parseFloat(document.getElementById("shortEntry").value) || 0;
  const shortSize = parseFloat(document.getElementById("shortSize").value) || 0;
  const collateral = parseFloat(document.getElementById("shortCollateral").value) || 0;
  const fee = parseFloat(document.getElementById("feePercentage").value) || 0;
  let tokenCount = shortEntry > 0 ? shortSize / shortEntry : 0;
  let pnl = (shortEntry - simPrice) * tokenCount;
  let feeCost = (fee / 100) * shortSize;
  let netValue = collateral + pnl - feeCost;

  if (shortLiquidation && simPrice >= shortLiquidation) {
    document.getElementById("shortSimPrice").innerHTML =
      "<strong>Simulated Price: $" + simPrice.toFixed(2) + " (Liquidated)</strong>";
    document.getElementById("shortCollateralDisplay").innerHTML =
      "<strong>Collateral: $" + collateral.toFixed(2) + "</strong>";
    document.getElementById("shortValue").innerHTML =
      "<strong>Position Value: $0.00</strong>";
    document.getElementById("shortPnL").innerHTML =
      "<strong>P&L: <span class='text-secondary'>Liquidated</span></strong>";
    document.getElementById("shortSLTP").innerHTML =
      "<strong>Recommended: Liquidated</strong>";
    document.getElementById("shortSafetyMargin").innerHTML =
      "<strong>Safety Margin: 0%</strong>";
    document.getElementById("shortOutputCard").className =
      "card shadow-sm bg-secondary bg-opacity-25 border border-2 border-secondary reduced-height";
    document.getElementById("shortCurrentSize").innerHTML =
      "<strong>Current Size: $0.00</strong>";
    return;
  }

  document.getElementById("shortSimPrice").innerHTML =
    "<strong>Simulated Price: $" + simPrice.toFixed(2) + "</strong>";
  document.getElementById("shortCollateralDisplay").innerHTML =
    "<strong>Collateral: $" + collateral.toFixed(2) + "</strong>";
  document.getElementById("shortValue").innerHTML =
    "<strong>Position Value: $" + netValue.toFixed(2) + "</strong>";
  let pnlColor = (pnl - feeCost) >= 0 ? "text-success" : "text-danger";
  let bgClass = (pnl - feeCost) >= 0
    ? "bg-success bg-opacity-10 border border-2 border-success"
    : "bg-danger bg-opacity-10 border border-2 border-danger";
  document.getElementById("shortPnL").innerHTML =
    "<strong>P&L: <span class='" + pnlColor + "'>" +
    ((pnl - feeCost) >= 0 ? "▲ " : "▼ ") + "$" +
    (pnl - feeCost).toFixed(2) + "</span></strong>";
  let recommendation = "";
  let recIcon = "";
  if (simPrice > shortEntry) {
    recommendation = "Stop Loss at $" + simPrice.toFixed(2);
    recIcon = "▲ ";
  } else if (simPrice < shortEntry) {
    recommendation = "Take Profit at $" + simPrice.toFixed(2);
    recIcon = "▼ ";
  } else {
    recommendation = "At Entry Price";
    recIcon = "— ";
  }
  document.getElementById("shortSLTP").innerHTML =
    "<strong>Recommended: " + recIcon + recommendation + "</strong>";
  document.getElementById("shortOutputCard").className =
    "card shadow-sm " + bgClass + " reduced-height";
  document.getElementById("shortCurrentSize").innerHTML =
    "<strong>Current Size: $" + shortSize.toFixed(2) + "</strong>";
  const shortLiq = shortLiquidation || (shortEntry * 1.2);
  const shortRange = shortLiq - shortEntry;
  const shortSafety = shortLiq - simPrice;
  const shortMargin = shortRange > 0 ? shortSafety / shortRange : 0;
  document.getElementById("shortSafetyMargin").innerHTML =
    "<strong>Safety Margin: " + (shortMargin * 100).toFixed(1) + "%</strong>";
}

/*************************************
 * Current Heat Index Calculations
 *************************************/
function updateLongHeatIndex(simPrice) {
  const longEntry = parseFloat(document.getElementById("longEntry").value) || 0;
  const longLiq = parseFloat(document.getElementById("longLiqPrice").value) || (longEntry * 0.8);
  const collateral = parseFloat(document.getElementById("longCollateral").value) || 0;
  const size = parseFloat(document.getElementById("longSize").value) || 0;
  let leverage = (collateral > 0) ? (size / collateral) : 0;
  if (longEntry <= 0 || longLiq <= 0 || collateral <= 0 || size <= 0) {
    document.getElementById("longHeatIndex").innerText = "N/A";
    document.getElementById("longHeatDTL").innerText = "N/A";
    document.getElementById("longHeatLev").innerText = "N/A";
    document.getElementById("longHeatCR").innerText = "N/A";
    return;
  }
  let ndl = (simPrice - longLiq) / (longEntry - longLiq);
  ndl = Math.max(0, Math.min(ndl, 1));
  let distanceFactor = 1 - ndl;
  let normalizedLeverage = leverage / 100;
  let collateralRatio = collateral / size;
  collateralRatio = Math.min(collateralRatio, 1);
  let riskCollateralFactor = 1 - collateralRatio;
  const distanceWeight = parseFloat(document.getElementById("distanceWeightInput").value) || 0.45;
  const leverageWeight = parseFloat(document.getElementById("leverageWeightInput").value) || 0.35;
  const collateralWeight = parseFloat(document.getElementById("collateralWeightInput").value) || 0.20;
  let composite = Math.pow(distanceFactor, distanceWeight)
                * Math.pow(normalizedLeverage, leverageWeight)
                * Math.pow(riskCollateralFactor, collateralWeight) * 100;
  document.getElementById("longHeatIndex").innerText = composite.toFixed(2);
  document.getElementById("longHeatDTL").innerText = distanceFactor.toFixed(2);
  document.getElementById("longHeatLev").innerText = leverage.toFixed(1);
  document.getElementById("longHeatCR").innerText = (collateralRatio * 100).toFixed(0);
}

function updateShortHeatIndex(simPrice) {
  const shortEntry = parseFloat(document.getElementById("shortEntry").value) || 0;
  const shortLiq = parseFloat(document.getElementById("shortLiqPrice").value) || (shortEntry * 1.2);
  const collateral = parseFloat(document.getElementById("shortCollateral").value) || 0;
  const size = parseFloat(document.getElementById("shortSize").value) || 0;
  let leverage = (collateral > 0) ? (size / collateral) : 0;
  if (shortEntry <= 0 || shortLiq <= 0 || collateral <= 0 || size <= 0) {
    document.getElementById("shortHeatIndex").innerText = "N/A";
    document.getElementById("shortHeatDTL").innerText = "N/A";
    document.getElementById("shortHeatLev").innerText = "N/A";
    document.getElementById("shortHeatCR").innerText = "N/A";
    return;
  }
  let ndl = (shortLiq - simPrice) / (shortLiq - shortEntry);
  ndl = Math.max(0, Math.min(ndl, 1));
  let distanceFactor = 1 - ndl;
  let normalizedLeverage = leverage / 100;
  let collateralRatio = collateral / size;
  collateralRatio = Math.min(collateralRatio, 1);
  let riskCollateralFactor = 1 - collateralRatio;
  const distanceWeight = parseFloat(document.getElementById("distanceWeightInput").value) || 0.45;
  const leverageWeight = parseFloat(document.getElementById("leverageWeightInput").value) || 0.35;
  const collateralWeight = parseFloat(document.getElementById("collateralWeightInput").value) || 0.20;
  let composite = Math.pow(distanceFactor, distanceWeight)
                * Math.pow(normalizedLeverage, leverageWeight)
                * Math.pow(riskCollateralFactor, collateralWeight) * 100;
  document.getElementById("shortHeatIndex").innerText = composite.toFixed(2);
  document.getElementById("shortHeatDTL").innerText = distanceFactor.toFixed(2);
  document.getElementById("shortHeatLev").innerText = leverage.toFixed(1);
  document.getElementById("shortHeatCR").innerText = (collateralRatio * 100).toFixed(0);
}

/*************************************
 * Simulated (Resulting) Heat Index Calculations
 *************************************/
function updateLongSimHeatIndex(simPrice) {
  const longEntry = parseFloat(document.getElementById("longEntry").value) || 0;
  const currentLongSize = parseFloat(document.getElementById("longSize").value) || 0;
  const currentCollateral = parseFloat(document.getElementById("longCollateral").value) || 0;
  const fee = parseFloat(document.getElementById("feePercentage").value) || 0;
  if (longEntry <= 0 || currentCollateral <= 0) {
    document.getElementById("longSimHeatIndex").innerText = "N/A";
    document.getElementById("longSimHeatDTL").innerText = "N/A";
    document.getElementById("longSimHeatLev").innerText = "N/A";
    document.getElementById("longSimHeatCR").innerText = "N/A";
    document.getElementById("longSimHeatCollateral").innerText = "0.00";
    return;
  }
  const simulatedSize = window.projectedLongSize || currentLongSize;
  let tokenCount = longEntry > 0 ? simulatedSize / longEntry : 0;
  let pnl = (simPrice - longEntry) * tokenCount;
  let feeCost = (fee / 100) * simulatedSize;
  let netValue = currentCollateral + pnl - feeCost;
  const longLiq = longLiquidation || (longEntry * 0.8);
  let ndl = (simPrice - longLiq) / (longEntry - longLiq);
  ndl = Math.max(0, Math.min(ndl, 1));
  let distanceFactor = 1 - ndl;
  let leverageSim = currentCollateral > 0 ? simulatedSize / currentCollateral : 0;
  let normalizedLeverage = leverageSim / 100;
  let collateralRatio = currentCollateral / simulatedSize;
  collateralRatio = Math.min(collateralRatio, 1);
  let riskCollateralFactor = 1 - collateralRatio;
  const distanceWeight = parseFloat(document.getElementById("distanceWeightInput").value) || 0.45;
  const leverageWeight = parseFloat(document.getElementById("leverageWeightInput").value) || 0.35;
  const collateralWeight = parseFloat(document.getElementById("collateralWeightInput").value) || 0.20;
  let compositeSim = Math.pow(distanceFactor, distanceWeight) *
                     Math.pow(normalizedLeverage, leverageWeight) *
                     Math.pow(riskCollateralFactor, collateralWeight) * 100;
  document.getElementById("longSimHeatIndex").innerText = compositeSim.toFixed(2);
  document.getElementById("longSimHeatDTL").innerText = distanceFactor.toFixed(2);
  document.getElementById("longSimHeatLev").innerText = leverageSim.toFixed(1);
  document.getElementById("longSimHeatCR").innerText = (collateralRatio * 100).toFixed(0);
  document.getElementById("longSimHeatCollateral").innerText = currentCollateral.toFixed(2);
}

function updateShortSimHeatIndex(simPrice) {
  const shortEntry = parseFloat(document.getElementById("shortEntry").value) || 0;
  const currentShortSize = parseFloat(document.getElementById("shortSize").value) || 0;
  const currentCollateral = parseFloat(document.getElementById("shortCollateral").value) || 0;
  const fee = parseFloat(document.getElementById("feePercentage").value) || 0;
  if (shortEntry <= 0 || currentCollateral <= 0) {
    document.getElementById("shortSimHeatIndex").innerText = "N/A";
    document.getElementById("shortSimHeatDTL").innerText = "N/A";
    document.getElementById("shortSimHeatLev").innerText = "N/A";
    document.getElementById("shortSimHeatCR").innerText = "N/A";
    document.getElementById("shortSimHeatCollateral").innerText = "0.00";
    return;
  }
  const simulatedSize = window.projectedShortSize || currentShortSize;
  let tokenCount = shortEntry > 0 ? simulatedSize / shortEntry : 0;
  let pnl = (shortEntry - simPrice) * tokenCount;
  let feeCost = (fee / 100) * simulatedSize;
  let netValue = currentCollateral + pnl - feeCost;
  const shortLiq = shortLiquidation || (shortEntry * 1.2);
  let ndl = (shortLiq - simPrice) / (shortLiq - shortEntry);
  ndl = Math.max(0, Math.min(ndl, 1));
  let distanceFactor = 1 - ndl;
  let leverageSim = currentCollateral > 0 ? simulatedSize / currentCollateral : 0;
  let normalizedLeverage = leverageSim / 100;
  let collateralRatio = currentCollateral / simulatedSize;
  collateralRatio = Math.min(collateralRatio, 1);
  let riskCollateralFactor = 1 - collateralRatio;
  const distanceWeight = parseFloat(document.getElementById("distanceWeightInput").value) || 0.45;
  const leverageWeight = parseFloat(document.getElementById("leverageWeightInput").value) || 0.35;
  const collateralWeight = parseFloat(document.getElementById("collateralWeightInput").value) || 0.20;
  let compositeSim = Math.pow(distanceFactor, distanceWeight)
                   * Math.pow(normalizedLeverage, leverageWeight)
                   * Math.pow(riskCollateralFactor, collateralWeight) * 100;
  document.getElementById("shortSimHeatIndex").innerText = compositeSim.toFixed(2);
  document.getElementById("shortSimHeatDTL").innerText = distanceFactor.toFixed(2);
  document.getElementById("shortSimHeatLev").innerText = leverageSim.toFixed(1);
  document.getElementById("shortSimHeatCR").innerText = (collateralRatio * 100).toFixed(0);
  document.getElementById("shortSimHeatCollateral").innerText = currentCollateral.toFixed(2);
}

/*************************************
 * Travel Percent Updates
 *************************************/
function updateLongTravelPercent(simPrice) {
  const longEntry = parseFloat(document.getElementById("longEntry").value) || 0;
  const longLiq = parseFloat(document.getElementById("longLiqPrice").value) || (longEntry * 0.8);
  if (longEntry > 0 && longLiq > 0 && longEntry !== longLiq) {
    const denom = Math.abs(longEntry - longLiq);
    const numer = simPrice - longEntry;
    const travelPercent = (numer / denom) * 100;
    document.getElementById("longTravelPercent").innerText = travelPercent.toFixed(2) + "%";
  } else {
    document.getElementById("longTravelPercent").innerText = "N/A";
  }
}

function updateShortTravelPercent(simPrice) {
  const shortEntry = parseFloat(document.getElementById("shortEntry").value) || 0;
  const shortLiq = parseFloat(document.getElementById("shortLiqPrice").value) || (shortEntry * 1.2);
  if (shortEntry > 0 && shortLiq > 0 && shortEntry !== shortLiq) {
    const denom = Math.abs(shortLiq - shortEntry);
    const numer = shortEntry - simPrice;
    const travelPercent = (numer / denom) * 100;
    document.getElementById("shortTravelPercent").innerText = travelPercent.toFixed(2) + "%";
  } else {
    document.getElementById("shortTravelPercent").innerText = "N/A";
  }
}

/*************************************
 * Hedge Recommendations
 *************************************/
function updateHedgeRecommendations(simPrice) {
  const targetMargin = parseFloat(document.getElementById("targetMarginInput").value) / 100;
  const adjustmentFactor = parseFloat(document.getElementById("adjustmentFactorInput").value);
  const longEntry = parseFloat(document.getElementById("longEntry").value) || 0;
  const shortEntry = parseFloat(document.getElementById("shortEntry").value) || 0;
  const longSize = parseFloat(document.getElementById("longSize").value) || 0;
  const shortSize = parseFloat(document.getElementById("shortSize").value) || 0;
  const longLiq = longLiquidation || (longEntry * 0.8);
  const shortLiq = shortLiquidation || (shortEntry * 1.2);
  const longRange = longEntry - longLiq;
  const shortRange = shortLiq - shortEntry;
  const longSafety = simPrice - longLiq;
  const shortSafety = shortLiq - simPrice;
  const longMarginCalc = longRange > 0 ? longSafety / longRange : 0;
  const shortMarginCalc = shortRange > 0 ? shortSafety / shortRange : 0;
  let longRec = "No long side adjustment recommended.";
  let shortRec = "No short side adjustment recommended.";
  const approach = document.querySelector('input[name="approach"]:checked').value;

  if (approach === "average") {
    if (longMarginCalc < targetMargin) {
      longRec = "Long side is at risk. Consider opening an additional long position of ~<strong>$" +
                (longSize * (targetMargin - longMarginCalc) * adjustmentFactor).toFixed(2) + "</strong>";
    } else if (longMarginCalc > targetMargin) {
      longRec = "Long side is in profit. To offset potential loss on the short side, consider increasing long exposure by ~<strong>$" +
                (longSize * (longMarginCalc - targetMargin) * adjustmentFactor).toFixed(2) + "</strong>";
    }
    if (shortMarginCalc < targetMargin) {
      shortRec = "Short side is at risk. Consider opening an additional short position of ~<strong>$" +
                 (shortSize * (targetMargin - shortMarginCalc) * adjustmentFactor).toFixed(2) + "</strong>";
    } else if (shortMarginCalc > targetMargin) {
      shortRec = "Short side is in profit. To offset potential loss on the long side, consider increasing short exposure by ~<strong>$" +
                 (shortSize * (shortMarginCalc - targetMargin) * adjustmentFactor).toFixed(2) + "</strong>";
    }
  } else if (approach === "pyramid") {
    if (longMarginCalc < targetMargin) {
      longRec = "Long side is at risk. Consider adding a pyramid long position of ~<strong>$" +
                (longSize * (targetMargin - longMarginCalc) * adjustmentFactor).toFixed(2) + "</strong>";
    } else if (longMarginCalc > targetMargin) {
      longRec = "Long side is in profit. Consider adding a pyramid long position of ~<strong>$" +
                (longSize * (longMarginCalc - targetMargin) * adjustmentFactor).toFixed(2) + "</strong>";
    }
    if (shortMarginCalc < targetMargin) {
      shortRec = "Short side is at risk. Consider adding a pyramid short position of ~<strong>$" +
                 (shortSize * (targetMargin - shortMarginCalc) * adjustmentFactor).toFixed(2) + "</strong>";
    } else if (shortMarginCalc > targetMargin) {
      shortRec = "Short side is in profit. Consider adding a pyramid short position of ~<strong>$" +
                 (shortSize * (shortMarginCalc - targetMargin) * adjustmentFactor).toFixed(2) + "</strong>";
    }
  } else if (approach === "equilibrium") {
    let rawLongRec = longSize * (targetMargin - longMarginCalc) * adjustmentFactor;
    let rawShortRec = shortSize * (targetMargin - shortMarginCalc) * adjustmentFactor;
    let dampening = 0.3;
    longRec = "Equilibrium adjustment: ~<strong>$" + (rawLongRec * dampening).toFixed(2) + "</strong>";
    shortRec = "Equilibrium adjustment: ~<strong>$" + (rawShortRec * dampening).toFixed(2) + "</strong>";
  }

  document.getElementById("longRecommendationBox").innerHTML =
    "<strong>Long Recommendation:</strong> " + longRec;
  document.getElementById("shortRecommendationBox").innerHTML =
    "<strong>Short Recommendation:</strong> " + shortRec;
}

/*************************************
 * Projected Positions with Slider Leverage and Approach Toggle
 *************************************/
function updateProjectedPositions(simPrice) {
  const approach = document.querySelector('input[name="approach"]:checked').value;
  const sliderLeverage = parseFloat(document.getElementById("leverageSlider").value);

  /***** Projected Long ******/
  const longEntry = parseFloat(document.getElementById("longEntry").value) || 0;
  const longSize = parseFloat(document.getElementById("longSize").value) || 0;
  const fee = parseFloat(document.getElementById("feePercentage").value) || 0;
  const targetMargin = parseFloat(document.getElementById("targetMarginInput").value) / 100;
  const adjustmentFactor = parseFloat(document.getElementById("adjustmentFactorInput").value);
  const longLiq = parseFloat(document.getElementById("longLiqPrice").value) || (longEntry * 0.8);

  let longRange = longEntry - longLiq;
  let longSafety = simPrice - longLiq;
  let longMarginCalc = (longRange > 0) ? (longSafety / longRange) : 0;
  let recommendedLongExtra = 0;
  if (approach === "average") {
    if (longMarginCalc < targetMargin) {
      recommendedLongExtra = longSize * (targetMargin - longMarginCalc) * adjustmentFactor;
    }
    else if (longMarginCalc > targetMargin) {
      recommendedLongExtra = longSize * (longMarginCalc - targetMargin) * adjustmentFactor;
    }
  } else if (approach === "pyramid") {
    if (longMarginCalc < targetMargin) {
      recommendedLongExtra = longSize * (targetMargin - longMarginCalc) * adjustmentFactor;
    }
    else if (longMarginCalc > targetMargin) {
      recommendedLongExtra = longSize * (longMarginCalc - targetMargin) * adjustmentFactor;
    }
  } else if (approach === "equilibrium") {
    let rawRec = longSize * (targetMargin - longMarginCalc) * adjustmentFactor;
    let dampening = 0.3;
    recommendedLongExtra = rawRec * dampening;
  }
  const projectedLongSize = longSize + recommendedLongExtra;
  window.projectedLongSize = projectedLongSize;
  const projectedLongCollateral = projectedLongSize / sliderLeverage;
  let ndlLong = (simPrice - longLiq) / (longEntry - longLiq);
  ndlLong = Math.max(0, Math.min(ndlLong, 1));
  let distanceFactorLong = 1 - ndlLong;
  let normalizedLeverageLong = sliderLeverage / 100;
  let collateralRatioLong = projectedLongCollateral / projectedLongSize;
  collateralRatioLong = Math.min(collateralRatioLong, 1);
  let projectedHeatLong = Math.pow(distanceFactorLong, 0.45) *
                          Math.pow(normalizedLeverageLong, 0.35) *
                          Math.pow(1 - collateralRatioLong, 0.20) * 100;
  let tokenCountLongProjected = longEntry > 0 ? projectedLongSize / longEntry : 0;
  let pnlLongProjected = (simPrice - longEntry) * tokenCountLongProjected;
  let feeCostLongProjected = (fee / 100) * projectedLongSize;
  let netValueLongProjected = projectedLongCollateral + pnlLongProjected - feeCostLongProjected;
  document.getElementById("projectedLongSLTP").innerHTML =
    "<strong>Proposed New Size: $" + projectedLongSize.toFixed(2) + "</strong>";
  let longRangeProjected = longEntry - longLiq;
  let longSafetyProjected = simPrice - longLiq;
  let longMarginProjected = (longRangeProjected > 0) ? (longSafetyProjected / longRangeProjected) : 0;
  let projectedLongTravelPercent = "N/A";
  if (longEntry > 0 && longLiq > 0 && longEntry !== longLiq) {
    const denom = Math.abs(longEntry - longLiq);
    const numer = simPrice - longEntry;
    projectedLongTravelPercent = (numer / denom) * 100;
  }
  document.getElementById("projectedLongSimPrice").innerHTML =
    "<strong>Simulated Price: $" + simPrice.toFixed(2) + "</strong>";
  document.getElementById("projectedLongCollateralDisplay").innerHTML =
    "<strong>Collateral: $" + projectedLongCollateral.toFixed(2) + "</strong>";
  document.getElementById("projectedLongValue").innerHTML =
    "<strong>Position Value: $" + netValueLongProjected.toFixed(2) + "</strong>";
  document.getElementById("projectedLongPnL").innerHTML =
    "<strong>P&L: " + ((pnlLongProjected >= 0) ? "▲ " : "▼ ") +
    "$" + pnlLongProjected.toFixed(2) + "</strong>";
  document.getElementById("projectedLongSafetyMargin").innerHTML =
    "<strong>Safety Margin: " + (longMarginProjected * 100).toFixed(1) + "%</strong>";
  document.getElementById("projectedLongHeatIndex").innerText =
    projectedHeatLong.toFixed(2);
  let projectedLongBgClass = (pnlLongProjected >= 0)
    ? "bg-success bg-opacity-10 border border-2 border-success"
    : "bg-danger bg-opacity-10 border border-2 border-danger";
  document.getElementById("projectedLongOutputCard").className =
    "card shadow-sm " + projectedLongBgClass + " reduced-height";
  document.getElementById("projectedLongTravelPercent").innerText =
    (typeof projectedLongTravelPercent === "number")
      ? projectedLongTravelPercent.toFixed(2) + "%"
      : projectedLongTravelPercent;

  /***** Projected Short ******/
  const shortEntry = parseFloat(document.getElementById("shortEntry").value) || 0;
  const shortSize = parseFloat(document.getElementById("shortSize").value) || 0;
  const shortLiq = parseFloat(document.getElementById("shortLiqPrice").value) || (shortEntry * 1.2);
  let shortRange = shortLiq - shortEntry;
  let shortSafety = shortLiq - simPrice;
  let shortMarginCalc = (shortRange > 0) ? (shortSafety / shortRange) : 0;
  let recommendedShortExtra = 0;
  if (approach === "average") {
    if (shortMarginCalc < targetMargin) {
      recommendedShortExtra = shortSize * (targetMargin - shortMarginCalc) * adjustmentFactor;
    } else if (shortMarginCalc > targetMargin) {
      recommendedShortExtra = shortSize * (shortMarginCalc - targetMargin) * adjustmentFactor;
    }
  } else if (approach === "pyramid") {
    if (shortMarginCalc < targetMargin) {
      recommendedShortExtra = shortSize * (targetMargin - shortMarginCalc) * adjustmentFactor;
    } else if (shortMarginCalc > targetMargin) {
      recommendedShortExtra = shortSize * (shortMarginCalc - targetMargin) * adjustmentFactor;
    }
  } else if (approach === "equilibrium") {
    let rawShortRec = shortSize * (targetMargin - shortMarginCalc) * adjustmentFactor;
    let dampening = 0.3;
    recommendedShortExtra = rawShortRec * dampening;
  }
  const projectedShortSize = shortSize + recommendedShortExtra;
  window.projectedShortSize = projectedShortSize;
  const projectedShortCollateral = projectedShortSize / sliderLeverage;
  let ndlShort = (shortLiq - simPrice) / (shortLiq - shortEntry);
  ndlShort = Math.max(0, Math.min(ndlShort, 1));
  let distanceFactorShort = 1 - ndlShort;
  let normalizedLeverageShort = sliderLeverage / 100;
  let collateralRatioShort = projectedShortCollateral / projectedShortSize;
  collateralRatioShort = Math.min(collateralRatioShort, 1);
  let projectedHeatShort = Math.pow(distanceFactorShort, 0.45)
                         * Math.pow(normalizedLeverageShort, 0.35)
                         * Math.pow(1 - collateralRatioShort, 0.20) * 100;
  let tokenCountShortProjected = shortEntry > 0 ? projectedShortSize / shortEntry : 0;
  let pnlShortProjected = (shortEntry - simPrice) * tokenCountShortProjected;
  let feeCostShortProjected = (fee / 100) * projectedShortSize;
  let netValueShortProjected = projectedShortCollateral + pnlShortProjected - feeCostShortProjected;
  document.getElementById("projectedShortSLTP").innerHTML =
    "<strong>Proposed New Size: $" + projectedShortSize.toFixed(2) + "</strong>";
  let shortRangeProjected = shortLiq - shortEntry;
  let shortSafetyProjected = shortLiq - simPrice;
  let shortMarginProjected = (shortRangeProjected > 0) ? (shortSafetyProjected / shortRangeProjected) : 0;
  let projectedShortTravelPercent = "N/A";
  if (shortEntry > 0 && shortLiq > 0 && shortEntry !== shortLiq) {
    const denom = Math.abs(shortLiq - shortEntry);
    const numer = shortEntry - simPrice;
    projectedShortTravelPercent = (numer / denom) * 100;
  }
  document.getElementById("projectedShortSimPrice").innerHTML =
    "<strong>Simulated Price: $" + simPrice.toFixed(2) + "</strong>";
  document.getElementById("projectedShortCollateralDisplay").innerHTML =
    "<strong>Collateral: $" + projectedShortCollateral.toFixed(2) + "</strong>";
  document.getElementById("projectedShortValue").innerHTML =
    "<strong>Position Value: $" + netValueShortProjected.toFixed(2) + "</strong>";
  document.getElementById("projectedShortPnL").innerHTML =
    "<strong>P&L: " + ((pnlShortProjected >= 0) ? "▲ " : "▼ ") +
    "$" + pnlShortProjected.toFixed(2) + "</strong>";
  document.getElementById("projectedShortSafetyMargin").innerHTML =
    "<strong>Safety Margin: " + (shortMarginProjected * 100).toFixed(1) + "%</strong>";
  document.getElementById("projectedShortHeatIndex").innerText =
    projectedHeatShort.toFixed(2);
  let projectedShortBgClass = (pnlShortProjected >= 0)
    ? "bg-success bg-opacity-10 border border-2 border-success"
    : "bg-danger bg-opacity-10 border border-2 border-danger";
  document.getElementById("projectedShortOutputCard").className =
    "card shadow-sm " + projectedShortBgClass + " reduced-height";
  document.getElementById("projectedShortTravelPercent").innerText =
    (typeof projectedShortTravelPercent === "number")
      ? projectedShortTravelPercent.toFixed(2) + "%"
      : projectedShortTravelPercent;
  let currentLongSize = parseFloat(document.getElementById("longSize").value) || 0;
  let currentLongCollateral = parseFloat(document.getElementById("longCollateral").value) || 0;
  let longAddition = projectedLongSize - currentLongSize;
  let additionalCollateralLong = projectedLongCollateral - currentLongCollateral;
  let notionalAdditionLong = longAddition - additionalCollateralLong;
  let totalLongAddition = longAddition;
  document.getElementById("longSizeComposition").innerHTML =
    "Long Addition: <span class='collateral-value'>Collateral: $" + additionalCollateralLong.toFixed(2) + "</span>, " +
    "Notional: $" + notionalAdditionLong.toFixed(2) + ", " +
    "Total: $" + totalLongAddition.toFixed(2);
  let currentShortSize = parseFloat(document.getElementById("shortSize").value) || 0;
  let currentShortCollateral = parseFloat(document.getElementById("shortCollateral").value) || 0;
  let shortAddition = projectedShortSize - currentShortSize;
  let additionalCollateralShort = projectedShortCollateral - currentShortCollateral;
  let notionalAdditionShort = shortAddition - additionalCollateralShort;
  let totalShortAddition = shortAddition;
  document.getElementById("shortSizeComposition").innerHTML =
    "Short Addition: <span class='collateral-value'>Collateral: $" + additionalCollateralShort.toFixed(2) + "</span>, " +
    "Notional: $" + notionalAdditionShort.toFixed(2) + ", " +
    "Total: $" + totalShortAddition.toFixed(2);
}

/*************************************
 * Update Projected Heat Index (on leverage slider move)
 *************************************/
function updateProjectedHeatIndex() {
  const leverageSlider = document.getElementById("leverageSlider");
  const leverageValueDisplay = document.getElementById("leverageValue");
  let currentLeverage = parseFloat(leverageSlider.value);
  leverageValueDisplay.innerText = "Leverage: " + currentLeverage.toFixed(1) + "x";
  const simPrice = parseFloat(document.getElementById("priceSlider").value);
  updateProjectedPositions(simPrice);
}

/*************************************
 * Save Modifiers
 *************************************/
document.getElementById("saveModifiers").addEventListener("click", function() {
  const modifiers = {
    hedge_modifiers: {
      feePercentage: parseFloat(document.getElementById("feePercentage").value),
      targetMargin: parseFloat(document.getElementById("targetMarginInput").value),
      adjustmentFactor: parseFloat(document.getElementById("adjustmentFactorInput").value)
    },
    heat_modifiers: {
      distanceWeight: parseFloat(document.getElementById("distanceWeightInput").value),
      leverageWeight: parseFloat(document.getElementById("leverageWeightInput").value),
      collateralWeight: parseFloat(document.getElementById("collateralWeightInput").value)
    }
  };
  fetch("/sonic_labs/sonic_sauce", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(modifiers)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert("Modifiers saved successfully!");
    } else {
      alert("Error saving modifiers: " + data.error);
    }
  })
  .catch(err => {
    console.error("Error saving modifiers:", err);
    alert("Error saving modifiers. Check console for details.");
  });
});

/*************************************
 * Reset Price Functionality
 *************************************/
function resetPriceToCurrent() {
  const slider = document.getElementById("priceSlider");
  slider.value = lastComputedCurrentPrice;
  sliderChanged();
}
