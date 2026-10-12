/* Net profit: gross profit + switching income - switching expense - storage expense.
 * The legacy config stores an annual per-unit rate; cash settles every tick.
 * The backend allocates each company's actual period postings
 * to its own lines, then reduces it into market groups. Legacy snapshots use
 * the rate-based fallback below; current snapshots always supply actual expense.
 */
(function (root) {
  'use strict';
  function apply(row, rent) {
    if (!row || !Number.isFinite(row.grossProfit)) return;
    rent = row.storageRentExpense ?? rent;
    row.allocatedRentPerTick = rent;
    row.netProfit = row.netEarningsAvailable === false ? null : row.grossProfit + (row.switchingIncome ?? 0) - (row.switchingExpense ?? 0) - rent;
    row.netMargin = row.netProfit != null && row.revenue > 0 ? row.netProfit / row.revenue : null;
    if (row.lines != null) row.netProfitPerLine = row.netProfit != null && row.lines ? row.netProfit / row.lines : null;
  }
  function company(row, cfg, tier) {
    if (!row) return;
    const rent = row.storageRentExpense ?? (tier === 'T0' || (row.equity != null && row.equity < 2000000) ? 0 : (row.annualStorageRent ?? ((cfg.storage || 0) * (cfg.storageRentPerUnitYear || 0))) / 360);
    apply(row, rent);
    const lines = row.products || row.elementData || [];
    for (const line of lines) {
      line.switchingIncome = (row.switchingIncome ?? 0) / lines.length;
      line.switchingExpense = (row.switchingExpense ?? 0) / lines.length;
      line.netEarningsAvailable = row.netEarningsAvailable;
      if (!Number.isFinite(line.grossProfit) && Number.isFinite(line.revenue) && Number.isFinite(line.cogs)) line.grossProfit = line.revenue - line.cogs;
      apply(line, lines.length ? rent / lines.length : 0);
    }
  }
  function snapshot(s) {
    const cfg = s.cfg;
    const rent = (cfg.storage || 0) * (cfg.storageRentPerUnitYear || 0) / 360;
    const t1Lines = s.productCategories.filter(c => c.complexity === 1 || c.complexity === 2).reduce((n,c) => n+c.lines, 0);
    const t2Lines = s.tiers.t2.activeLines;
    const lineRent = { t1: t1Lines ? rent*s.tiers.t1.firms/t1Lines : 0,
                       t2: t2Lines ? rent*s.tiers.t2.firms/t2Lines : 0 };
    for (const tier of ['t0','t1','t2']) apply(s.tiers[tier], tier === 't0' ? 0 : rent*s.tiers[tier].firms);
    for (const row of s.productCategories) apply(row, row.complexity === 0 ? 0 : row.lines*lineRent[row.complexity < 3 ? 't1' : 't2']);
    for (const row of s.elements) apply(row, 0);
    for (const row of s.tier2Products) apply(row, row.firms*lineRent.t2);
    for (const key of ['tier2Industries','tier2Complexity']) for (const row of s[key]) apply(row, row.lines*lineRent.t2);
    for (const key of ['cohorts','tier2Cohorts']) for (const row of s[key]) apply(row, row.firms*rent);
    for (const row of s.t0Companies) company(row,cfg,'T0');
    for (const row of s.companies) company(row,cfg,'T1');
    for (const row of s.tier2Companies.rows) company(row,cfg,'T2');
    company(s.selected,cfg,s.selected.tier);
    for (const row of Object.values(s.expandedDetails || {})) company(row,cfg,row.tier);
    return s;
  }
  root.EconomyProfitability = { snapshot, company, apply };
  if (typeof module !== 'undefined') module.exports = root.EconomyProfitability;
})(globalThis);
