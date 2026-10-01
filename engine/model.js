/*
 * Canonical, editable Phase 0 model primitives.
 *
 * This file deliberately contains no browser-runtime boundary code. The
 * source kernel imports these definitions; keeping them here makes
 * topology and economic rules reviewable and testable in ordinary JavaScript.
 */
(function (root) {
  'use strict';

  const ELEMENTS = Object.freeze(['Water', 'Earth', 'Fire', 'Air']);
  const PRODUCTS = Object.freeze([
    { code: 'W', name: 'Water', inputs: { Water: 1 }, equipmentPrice: 15000 },
    { code: 'E', name: 'Earth', inputs: { Earth: 1 }, equipmentPrice: 15000 },
    { code: 'F', name: 'Fire', inputs: { Fire: 1 }, equipmentPrice: 15000 },
    { code: 'A', name: 'Air', inputs: { Air: 1 }, equipmentPrice: 15000 },
    { code: 'W+E', name: 'AquaTerra', inputs: { Water: 1, Earth: 1 }, equipmentPrice: 25000 },
    { code: 'W+F', name: 'HydroFlame', inputs: { Water: 1, Fire: 1 }, equipmentPrice: 25000 },
    { code: 'W+A', name: 'AeroWater', inputs: { Water: 1, Air: 1 }, equipmentPrice: 25000 },
    { code: 'E+F', name: 'TerraFlame', inputs: { Earth: 1, Fire: 1 }, equipmentPrice: 25000 },
    { code: 'E+A', name: 'TerraAir', inputs: { Earth: 1, Air: 1 }, equipmentPrice: 25000 },
    { code: 'F+A', name: 'EmberWind', inputs: { Fire: 1, Air: 1 }, equipmentPrice: 25000 }
  ]);

  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const complexity = product => Object.keys(product.inputs).length;
  const demandAtPrice = (qMax, chokePrice, price, elasticity) =>
    qMax > 0 && chokePrice > 0 && price >= 0 && elasticity > 0
      ? qMax / (1 + Math.pow(price / chokePrice, elasticity)) : 0;
  const switchingCost = (reliability, minimum, maximum) =>
    minimum + (maximum - minimum) * clamp(reliability, 0, 1);
  const reliabilityScore = (fulfillment, priceStability, availability) =>
    0.5 * clamp(fulfillment, 0, 1) + 0.3 * clamp(priceStability, 0, 1) + 0.2 * clamp(availability, 0, 1);
  const nextReliability = (current, score, alpha) =>
    clamp(current + clamp(alpha, 0, 1) * (score - current), 0, 1);
  const wholesalePrice = ({ oldPrice, unitCost, request, fulfilled, k, minMargin, vmax }) => {
    const floor = unitCost * (1 + minMargin);
    if (request <= 0) return Math.max(floor, oldPrice);
    const unmet = clamp((request - fulfilled) / Math.max(1, request), -1, 1);
    return clamp(oldPrice * Math.exp(0.03 * k * unmet), floor, Math.max(floor, 2 * vmax));
  };
  const retailBotPrice = ({ oldPrice, finishedCost, stock, salesEMA, k, minMargin, vmax }) => {
    const floor = finishedCost * (1 + minMargin);
    const coverage = salesEMA > 0 ? stock / salesEMA : 0;
    const signal = clamp(0.5 * (1 - coverage / 3), -1, 1);
    return clamp(oldPrice * Math.exp(0.008 * k * signal), floor, Math.max(floor, 2 * vmax));
  };

  root.Phase0Model = Object.freeze({
    ELEMENTS, PRODUCTS, clamp, complexity, demandAtPrice, switchingCost,
    reliabilityScore, nextReliability, wholesalePrice, retailBotPrice
  });
})(typeof self !== 'undefined' ? self : globalThis);
