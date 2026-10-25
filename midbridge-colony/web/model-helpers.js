/* Browser helper for the current backend pricing contract; no catalog data. */
(function(root) {
  "use strict";
  const MIN_UNIT_PRICE = .01;
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const adaptivePrice = ({ oldPrice, profit, previousProfit, direction = 1,
    sales = 0, stock = 0, demand = 0, available = 0, stepScale = 1,
    marketPrice = null, band = .02, pricingAggressiveness = .35, response = .05 }) => {
    const bounded = x => Math.round(clamp(x, MIN_UNIT_PRICE, 1e9) * 100) / 100;
    const price = bounded(oldPrice);
    let nextDirection = direction < 0 ? -1 : 1, moved = false;
    if (demand > available + 1e-9) { nextDirection = 1; moved = true; }
    else if (marketPrice != null && marketPrice > 0) {
      if (price > marketPrice * (1 + band)) { nextDirection = -1; moved = true; }
      else if (price < marketPrice * (1 - band)) { nextDirection = 1; moved = true; }
    }
    if (!moved && Number.isFinite(previousProfit)) {
      const change = (profit - previousProfit) / Math.max(Math.abs(previousProfit), 1e-9);
      if (change < -.02) nextDirection *= -1;
      else if (change <= .02) return {price, direction: nextDirection, stepScale};
    }
    const scale = clamp(stepScale * (nextDirection !== direction ? 1 : 1.2), .01, 1);
    const next = bounded(price * Math.exp(nextDirection * clamp(pricingAggressiveness, 0, 1) * response * scale));
    if (next === price && nextDirection < 0) nextDirection = 1;
    return {price: next, direction: nextDirection, stepScale: scale};
  };
  root.Phase0Model = Object.freeze({adaptivePrice});
})(typeof self !== "undefined" ? self : globalThis);
