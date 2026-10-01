(() => {
  if (location.protocol === 'file:') {
    document.getElementById('kernel').textContent = 'Open with the launcher';
    document.getElementById('perf').textContent =
      'Double-click Start Phase 0.command in this folder. Keep its Terminal window open while using the simulator.';
    document
      .querySelectorAll('button,input,select')
      .forEach((control) => (control.disabled = true));
    return;
  }
  const worker = new Worker('./phase0_economy_engine_worker.js');
  const $ = (id) => document.getElementById(id);
  const PARAMS = [
    'seed',
    'dbar',
    'theta',
    'sigma',
    'dmin',
    'dmax',
    'capacity',
    'targetInventory',
    'maxInventory',
    'baseCost',
    'retailTargetInventory',
    'retailMaxInventory',
    'basicEquipmentCapacity',
    'compoundEquipmentCapacity',
    'manufacturingCostPerUnit',
    'minWholesaleLot',
    'k',
    'alpha',
    'minMargin',
    'markup',
    'compoundMarkupPremium',
    'demandQtyMin',
    'demandQtyMax',
    'vmin',
    'vmax',
    'elasticityMin',
    'elasticityMax',
    'compoundDemandFactor',
    'compoundReservationPremium',
    'taumin',
    'taumax',
    'reliabilityAlpha',
    'switchingStableBand',
  ];
  const productCodes = ['W', 'E', 'F', 'A', 'W+E', 'W+F', 'W+A', 'E+F', 'E+A', 'F+A'];
  function readCfg() {
    const c = {};
    for (const id of PARAMS) c[id] = +$(id).value;
    c.buyersPerCompany = 50;
    c.retailInitialCash = 5000;
    c.initialCash = 1000000;
    return c;
  }
  for (let i = 0; i < 1000; i++) {
    const o = document.createElement('option');
    o.value = i;
    o.textContent = `T1-${String(i + 1).padStart(4, '0')} · ${productCodes[Math.floor(i / 100)]}`;
    $('playerCompany').appendChild(o);
  }
  $('equipmentProduct').innerHTML = productCodes
    .slice(4)
    .map((x) => `<option value="${x}">${x}</option>`)
    .join('');
  function sendSelect() {
    worker.postMessage({ type: 'select', id: +$('playerCompany').value });
  }
  $('playerCompany').addEventListener('change', sendSelect);
  let latestSnapshot = null,
    companyDetailData = null,
    t0Page = 0,
    t1Page = 0,
    companyPageSize = 50,
    selectedTier = 'T1',
    selectedCompanyId = 0;
  const expandedCompanies = { T0: new Set(), T1: new Set() };
  const tableSortColumns = {
    wholesale: ['code', 'difficulty', 'price', 'volume', 'hhi', 'reliability'],
    retail: [
      'code',
      'retailPrice',
      'supplyCapacity',
      'readyStock',
      'volume',
      'hhi',
      'potential',
      'active',
      'fulfilled',
      'fillRate',
      'stockUnmet',
    ],
    cohorts: [
      'code',
      'firms',
      'equipment',
      'avgPrice',
      'avgUnitCost',
      'finished',
      'inventory',
      'cash',
      'equity',
      'made',
      'sold',
      'revenue',
      'grossProfit',
      'reliability',
      'marketShare',
    ],
    tier0Companies: [
      'name',
      'elements',
      'cash',
      'inventory',
      'equity',
      'production',
      'sold',
      'revenue',
      'avgPrice',
      'reliability',
    ],
    tier1Companies: [
      'name',
      'controller',
      'native',
      'equipment',
      'cash',
      'raw',
      'finished',
      'inventory',
      'equity',
      'price',
      'made',
      'sold',
      'revenue',
      'grossProfit',
      'reliability',
    ],
  };
  const tableSort = Object.fromEntries(
    Object.entries(tableSortColumns).map(([table, columns]) => [
      table,
      { key: columns[0], direction: 1 },
    ]),
  );

  function compareTableValues(left, right) {
    const leftNumber = Number(left);
    const rightNumber = Number(right);
    if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber))
      return leftNumber - rightNumber;
    return String(left ?? '').localeCompare(String(right ?? ''), undefined, {
      numeric: true,
      sensitivity: 'base',
    });
  }

  function sortedTableRows(table, rows) {
    const { key, direction } = tableSort[table];
    return [...rows].sort(
      (left, right) =>
        direction * compareTableValues(left[key], right[key]) ||
        compareTableValues(left.name || left.code || left.id, right.name || right.code || right.id),
    );
  }

  function updateSortIndicators() {
    for (const [table, columns] of Object.entries(tableSortColumns)) {
      const headerCells = $(table).closest('table').querySelectorAll('thead th');
      headerCells.forEach((header, index) => {
        const active = columns[index] === tableSort[table].key;
        header.dataset.sortDirection = active
          ? tableSort[table].direction > 0
            ? 'ascending'
            : 'descending'
          : '';
        header.setAttribute('aria-sort', active ? header.dataset.sortDirection : 'none');
      });
    }
  }

  function initializeTableSorting() {
    for (const [table, columns] of Object.entries(tableSortColumns)) {
      const headerCells = $(table).closest('table').querySelectorAll('thead th');
      headerCells.forEach((header, index) => {
        const key = columns[index];
        if (!key) return;
        header.classList.add('sortable-header');
        header.tabIndex = 0;
        header.setAttribute('role', 'button');
        header.setAttribute('aria-label', `Sort by ${header.textContent.trim()}`);
        const sort = () => {
          const state = tableSort[table];
          state.direction = state.key === key ? -state.direction : 1;
          state.key = key;
          if (table === 'tier0Companies' || table === 'tier1Companies') t1Page = 0;
          updateSortIndicators();
          if (latestSnapshot) render(latestSnapshot);
        };
        header.addEventListener('click', sort);
        header.addEventListener('keydown', (event) => {
          if (event.key !== 'Enter' && event.key !== ' ') return;
          event.preventDefault();
          sort();
        });
      });
    }
    updateSortIndicators();
  }
  worker.onmessage = (e) => {
    const m = e.data;
    if (m.type === 'snapshot') {
      latestSnapshot = m.data;
      const key = selectedTier + ':' + selectedCompanyId;
      companyDetailData = m.data.expandedDetails?.[key] || companyDetailData;
      render(m.data);
    }
    if (m.type === 'companyDetail') {
      companyDetailData = m.data;
      selectedTier = m.data?.tier || selectedTier;
      selectedCompanyId = m.data?.id ?? selectedCompanyId;
      renderCompanyTables();
    }
    if (m.type === 'equipmentResult')
      $('playerStatus').textContent = m.ok ? 'Equipment purchased.' : m.msg;
    if (m.type === 'error') {
      const message = m.message || 'Worker error';
      $('kernel').textContent = 'Engine: error';
      $('kernel').className = 'pill err';
      $('perf').textContent = message;
      console.error(message);
    }
  };

  worker.onerror = (e) => {
    $('kernel').textContent = 'Engine: error';
    $('kernel').className = 'pill err';
    $('perf').textContent = e.message || 'Worker error';
  };
  function companyFilteredRows(tier) {
    if (!latestSnapshot) return [];
    if (tier === 'T0') {
      const q = ($('t0Search').value || '').trim().toLowerCase();
      return (latestSnapshot.t0Companies || []).filter(
        (x) =>
          !q ||
          x.name.toLowerCase().includes(q) ||
          x.elements.some((e) => e.toLowerCase().includes(q)),
      );
    }
    const q = ($('t1Search').value || '').trim().toLowerCase(),
      cf = $('t1CohortFilter').value,
      ctrl = $('t1ControllerFilter').value;
    return (latestSnapshot.companies || []).filter(
      (x) =>
        (!q ||
          x.name.toLowerCase().includes(q) ||
          x.native.toLowerCase().includes(q) ||
          x.controller.toLowerCase().includes(q) ||
          x.equipment.join(' ').toLowerCase().includes(q)) &&
        (!cf || x.native === cf) &&
        (!ctrl || x.controller === ctrl),
    );
  }
  function renderCompanyTables() {
    if (!latestSnapshot) return;
    const t0 = sortedTableRows('tier0Companies', companyFilteredRows('T0')),
      t1 = sortedTableRows('tier1Companies', companyFilteredRows('T1'));
    t1Page = Math.max(
      0,
      Math.min(t1Page, Math.floor(Math.max(0, t1.length - 1) / companyPageSize)),
    );
    const t1slice = t1.slice(t1Page * companyPageSize, t1Page * companyPageSize + companyPageSize);
    const exp0 = expandedCompanies.T0,
      exp1 = expandedCompanies.T1;

    const detailT0 = (x) => {
      const d =
        latestSnapshot?.expandedDetails?.['T0:' + x.id] ||
        (companyDetailData && companyDetailData.tier === 'T0' && companyDetailData.id === x.id
          ? companyDetailData
          : null);
      return `<tr class="company-detail-row"><td colspan="10"><div class="company-detail-inner">
      <div class="detail-section"><strong>${x.name} · current stocks & sell prices</strong></div>
      <table class="detail-table"><thead><tr><th>Element</th><th>Current stock</th><th>Unit cost</th><th>Sell price</th><th>Produced / tick</th><th>Sold</th><th>Revenue</th><th>Reliability</th><th>Price stability</th></tr></thead>
      <tbody>${(d?.elementData || []).map((v) => `<tr><th>${v.element}</th><td>${fmtInt(v.stock)}</td><td>${fmt5(v.cost)}</td><td>${fmt5(v.price)}</td><td>${fmtInt(v.production)}</td><td>${fmtInt(v.sold)}</td><td>${fmtMoney(v.revenue, 0)}</td><td>${fmtFixed(v.reliability, 3)}</td><td>${fmtFixed(v.stability, 3)}</td></tr>`).join('')}</tbody></table>
    </div></td></tr>`;
    };

    const detailT1 = (x) => {
      const d =
        latestSnapshot?.expandedDetails?.['T1:' + x.id] ||
        (companyDetailData && companyDetailData.tier === 'T1' && companyDetailData.id === x.id
          ? companyDetailData
          : null);
      return `<tr class="company-detail-row"><td colspan="15"><div class="company-detail-inner">
      <div class="detail-section"><strong>${x.name} · raw stocks & buy prices</strong></div>
      <table class="detail-table"><thead><tr><th>Input</th><th>Current stock</th><th>Average basis</th><th>Last buy</th><th>Input need</th><th>Request</th><th>Preferred supplier</th></tr></thead>
      <tbody>${(d?.raw || []).map((v) => `<tr><th>${v.element}</th><td>${fmtInt(v.stock)}</td><td>${fmtMoney(v.basis, 2)}</td><td>${v.lastBuy == null ? '—' : fmt5(v.lastBuy)}</td><td>${fmtInt(v.inputNeed)}</td><td>${fmtInt(v.purchaseRequest)}</td><td>${v.preferredSupplier >= 0 ? 'T0-' + String(v.preferredSupplier + 1).padStart(2, '0') : '—'}</td></tr>`).join('')}</tbody></table>
      <div class="detail-section"><strong>Finished stocks & sell prices</strong></div>
      <table class="detail-table"><thead><tr><th>Product</th><th>Current stock</th><th>Unit cost</th><th>Sell price</th><th>Sales EMA</th><th>Made / tick</th><th>Sold</th><th>Revenue</th><th>COGS</th><th>Reliability</th><th>Price stability</th></tr></thead>
      <tbody>${(d?.products || []).map((v) => `<tr><th>${v.product}</th><td>${fmtInt(v.finished)}</td><td>${fmtMoney(v.unitCost, 2)}</td><td>${fmtMoney(v.price, 2)}</td><td>${fmtFixed(v.salesEMA, 2)}</td><td>${fmtInt(v.made)}</td><td>${fmtInt(v.sold)}</td><td>${fmtMoney(v.revenue, 0)}</td><td>${fmtMoney(v.cogs, 0)}</td><td>${fmtFixed(v.reliability, 3)}</td><td>${fmtFixed(v.priceStability, 3)}</td></tr>`).join('')}</tbody></table>
    </div></td></tr>`;
    };

    $('tier0Companies').innerHTML = t0
      .map((x) => {
        const row = `<tr class="clickable-row${selectedTier === 'T0' && selectedCompanyId === x.id ? ' selected' : ''}" data-tier="T0" data-id="${x.id}">
      <th>▸ ${x.name}</th><td>${x.elements.join(' · ')}</td><td>${fmtMoney(x.cash, 0)}</td><td>${fmtInt(x.inventory)}</td><td>${fmtMoney(x.equity, 0)}</td><td>${fmtInt(x.production)}</td><td>${fmtInt(x.sold)}</td><td>${fmtMoney(x.revenue, 0)}</td><td>${fmt5(x.avgPrice)}</td><td>${fmtFixed(x.reliability, 3)}</td></tr>`;
        return row + (exp0.has(x.id) ? detailT0(x) : '');
      })
      .join('');

    $('tier1Companies').innerHTML = t1slice
      .map((x) => {
        const row = `<tr class="clickable-row${selectedTier === 'T1' && selectedCompanyId === x.id ? ' selected' : ''}" data-tier="T1" data-id="${x.id}">
      <th>▸ ${x.name}</th><td>${x.controller}</td><td>${x.native}</td><td>${x.equipment.join(' · ')}</td><td>${fmtMoney(x.cash, 0)}</td><td>${fmtInt(x.raw)}</td><td>${fmtInt(x.finished)}</td><td>${fmtInt(x.inventory)}</td><td>${fmtMoney(x.equity, 0)}</td><td>${fmtMoney(x.price, 2)}</td><td>${fmtInt(x.made)}</td><td>${fmtInt(x.sold)}</td><td>${fmtMoney(x.revenue, 0)}</td><td>${fmtMoney(x.grossProfit, 0)}</td><td>${fmtFixed(x.reliability, 3)}</td></tr>`;
        return row + (exp1.has(x.id) ? detailT1(x) : '');
      })
      .join('');

    $('t1Page').textContent =
      `${t1.length ? t1Page * companyPageSize + 1 : 0}–${Math.min(t1.length, (t1Page + 1) * companyPageSize)} of ${t1.length}`;
  }
  function renderCompanyInspector() {
    const d = companyDetailData;
    if (!d) {
      $('companyInspector').textContent = 'Select a company row.';
      $('companyTxnInspector').textContent = '—';
      return;
    }
    if (d.tier === 'T0') {
      const txt = [
        `${d.name} · Tier 0`,
        `status: ${d.status}`,
        `cash: ${fmtMoney(d.cash, 2)}`,
        `inventory: ${fmtInt(d.inventory)}`,
        `equity: ${fmtMoney(d.equity, 2)}`,
        `capacity/tick: ${fmtInt(d.capacity)}`,
        `target inventory: ${fmtInt(d.targetInventory)}`,
        `max inventory: ${fmtInt(d.maxInventory)}`,
        `elements: ${d.elements.join(', ')}`,
      ];
      $('companyInspector').textContent = txt.join('\n');
      $('companyTxnInspector').textContent = d.elementData
        .map(
          (x) =>
            `${x.element}: stock ${Math.round(x.stock)}, cost ${fmtMoney(x.cost, 5)}, price ${fmtMoney(x.price, 5)}, prod ${Math.round(x.production)}, sold ${Math.round(x.sold)}, revenue ${fmtMoney(x.revenue, 0)}, rel ${x.reliability.toFixed(3)}, stability ${x.stability.toFixed(3)}, reliability attempts ${Math.round(x.reliabilityAttempts)}`,
        )
        .join('\n');
    } else {
      const txt = [
        `${d.name} · Tier 1`,
        `controller: ${d.controller}`,
        `online: ${d.online ? 'yes' : 'no'}`,
        `native: ${d.native}`,
        `cash: ${fmtMoney(d.cash, 2)}`,
        `equipment book: ${fmtMoney(d.equipmentBookValue, 2)}`,
        `equipment: ${d.equipment.join(', ')}`,
        `inventory: ${fmtInt(d.inventory)}`,
        `equity: ${fmtMoney(d.equity, 2)}`,
        `made: ${fmtInt(d.made)}`,
        `sold: ${fmtInt(d.sold)}`,
        `revenue: ${fmtMoney(d.revenue, 2)}`,
        `COGS: ${fmtMoney(d.cogs, 2)}`,
        `gross profit: ${fmtMoney(d.grossProfit, 2)}`,
        `reliability: ${d.reliability.toFixed(3)}`,
      ];
      $('companyInspector').textContent = txt.join('\n');
      const rawTxt = d.raw
        .map(
          (x) =>
            `${x.element}: stock ${Math.round(x.stock)}, basis ${fmtMoney(x.basis, 2)}, last buy ${x.lastBuy == null ? '—' : fmt5(x.lastBuy)}, input need ${Math.round(x.inputNeed)}, request ${Math.round(x.purchaseRequest)}, preferred T0 ${x.preferredSupplier}`,
        )
        .join('\n');
      const prodTxt = d.products
        .map(
          (x) =>
            `${x.product}: price ${fmtMoney(x.price, 2)}, unit cost ${fmtMoney(x.unitCost, 2)}, stock ${Math.round(x.finished)}, EMA ${x.salesEMA.toFixed(2)}, made ${Math.round(x.made)}, sold ${Math.round(x.sold)}, revenue ${fmtMoney(x.revenue, 0)}, COGS ${fmtMoney(x.cogs, 0)}, rel ${x.reliability.toFixed(3)}, stability ${x.priceStability.toFixed(3)}`,
        )
        .join('\n');
      $('companyTxnInspector').textContent = `RAW\n${rawTxt}\n\nPRODUCTS\n${prodTxt}`;
    }
  }
  function requestCompanyDetail(tier, id) {
    selectedTier = tier;
    selectedCompanyId = id;
    worker.postMessage({
      type: 'watchCompanies',
      watches: { T0: Array.from(expandedCompanies.T0), T1: Array.from(expandedCompanies.T1) },
    });
    renderCompanyTables();
  }
  function fmt5(x) {
    return Number.isFinite(x) ? '$' + x.toFixed(5) : '—';
  }
  function fmt2(x) {
    return Number.isFinite(x) ? '$' + x.toFixed(2) : '—';
  }
  function fmtMoney(x, d = 2) {
    return Number.isFinite(x) ? '$' + x.toFixed(d) : '—';
  }
  function fmtInt(x) {
    const n = Number(x);
    return Number.isFinite(n) ? Math.round(n).toLocaleString() : '—';
  }
  function fmtFixed(x, d = 2) {
    const n = Number(x);
    return Number.isFinite(n) ? n.toFixed(d) : '—';
  }
  function pct(x, d = 1) {
    return Number.isFinite(x) ? (x * 100).toFixed(d) + '%' : '—';
  }
  function sum(o) {
    return Array.isArray(o) ? o.reduce((a, v) => a + Number(v || 0), 0) : 0;
  }
  function drawLine(id, history, seriesList, labels, digits = 2, moneyAxis = false) {
    const cv = $(id);
    if (!cv) return;
    const r = cv.getBoundingClientRect(),
      dpr = devicePixelRatio || 1;
    cv.width = Math.max(1, r.width * dpr);
    cv.height = Math.max(1, r.height * dpr);
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const w = r.width,
      h = r.height;
    g.clearRect(0, 0, w, h);
    if (!history.length || !seriesList.length) return;
    const colors = ['#77b7ff', '#6fd08c', '#f2c15b', '#ef7b7b', '#b18cff', '#77d4d4'];
    g.font = '11px system-ui';
    let legendX = 48,
      legendY = 12;
    labels.forEach((label, i) => {
      const itemWidth = 20 + g.measureText(label).width + 12;
      if (legendX + itemWidth > w - 8 && legendX > 48) {
        legendX = 48;
        legendY += 15;
      }
      g.strokeStyle = colors[i % colors.length];
      g.lineWidth = 3;
      g.beginPath();
      g.moveTo(legendX, legendY - 4);
      g.lineTo(legendX + 12, legendY - 4);
      g.stroke();
      g.fillStyle = '#c7d0da';
      g.fillText(label, legendX + 17, legendY);
      legendX += itemWidth;
    });
    const plotTop = legendY + 14,
      plotBottom = h - 32;
    const vals = [];
    for (const series of seriesList) for (const v of series) if (Number.isFinite(v)) vals.push(v);
    if (!vals.length) return;
    let mn = Math.min(...vals),
      mx = Math.max(...vals);
    if (mn === mx) {
      mn -= 1;
      mx += 1;
    }
    g.strokeStyle = '#2a303a';
    g.lineWidth = 1;
    for (let i = 0; i < 5; i++) {
      const yy = plotTop + (i * (plotBottom - plotTop)) / 4;
      g.beginPath();
      g.moveTo(44, yy);
      g.lineTo(w - 8, yy);
      g.stroke();
    }
    seriesList.forEach((series, si) => {
      g.strokeStyle = colors[si % colors.length];
      g.lineWidth = 1.8;
      g.beginPath();
      series.forEach((v, i) => {
        if (!Number.isFinite(v)) return;
        const x = 44 + ((w - 54) * i) / Math.max(1, history.length - 1),
          y = plotTop + (plotBottom - plotTop) * (1 - (v - mn) / (mx - mn));
        i ? g.lineTo(x, y) : g.moveTo(x, y);
      });
      g.stroke();
    });
    g.fillStyle = '#9ca6b2';
    const axis = moneyAxis ? fmtMoney : (v, d) => (Number.isFinite(v) ? v.toFixed(d) : '—');
    g.fillText(axis(mx, digits), 6, plotTop + 12);
    g.fillText(axis(mn, digits), 6, h - 4);
    g.fillText('t=' + history.at(-1).tick, w - 54, h - 4);
  }
  function drawBars(id, items, valueKey, labelKey, formatter) {
    const cv = $(id);
    if (!cv) return;
    const r = cv.getBoundingClientRect(),
      dpr = devicePixelRatio || 1;
    cv.width = Math.max(1, r.width * dpr);
    cv.height = Math.max(1, r.height * dpr);
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const w = r.width,
      h = r.height;
    g.clearRect(0, 0, w, h);
    if (!items.length) return;
    const vals = items.map((x) => Number(x[valueKey]) || 0),
      mx = Math.max(...vals, 1);
    const left = 48,
      right = 8,
      bottom = 28,
      top = 28;
    const slot = (w - left - right) / items.length;
    g.strokeStyle = '#2a303a';
    for (let i = 0; i < 4; i++) {
      const yy = top + (i * (h - top - bottom)) / 3;
      g.beginPath();
      g.moveTo(left, yy);
      g.lineTo(w - right, yy);
      g.stroke();
    }
    items.forEach((x, i) => {
      const bh = (h - top - bottom) * (vals[i] / mx),
        bx = left + i * slot + slot * 0.16,
        by = h - bottom - bh,
        bw = slot * 0.68;
      g.fillStyle = ['#77b7ff', '#6fd08c', '#f2c15b', '#ef7b7b', '#b18cff', '#77d4d4'][i % 6];
      g.fillRect(bx, by, bw, bh);
      g.fillStyle = '#9ca6b2';
      g.font = '10px system-ui';
      g.textAlign = 'center';
      g.fillText(x[labelKey], bx + bw / 2, h - 7);
    });
    g.textAlign = 'left';
    g.fillText(formatter(mx), 6, 12);
    g.fillText(valueKey === 'revenue' ? 'revenue / tick' : valueKey, 48, 12);
  }
  function drawCohortGrossProfit(id, cohorts) {
    const cv = $(id);
    if (!cv) return;
    const r = cv.getBoundingClientRect(),
      dpr = devicePixelRatio || 1;
    cv.width = Math.max(1, r.width * dpr);
    cv.height = Math.max(1, r.height * dpr);
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const w = r.width,
      h = r.height;
    g.clearRect(0, 0, w, h);
    const vals = cohorts.map((x) => x.grossProfit),
      mx = Math.max(...vals.map(Math.abs), 1),
      left = 52,
      right = 8,
      mid = h / 2,
      bottom = 24,
      slot = (w - left - right) / cohorts.length;
    g.strokeStyle = '#2a303a';
    g.beginPath();
    g.moveTo(left, mid);
    g.lineTo(w - right, mid);
    g.stroke();
    cohorts.forEach((x, i) => {
      const v = vals[i],
        bh = ((h - bottom - 18) * Math.abs(v)) / mx / 2,
        bx = left + i * slot + slot * 0.16,
        bw = slot * 0.68,
        by = v >= 0 ? mid - bh : mid;
      g.fillStyle = v >= 0 ? '#6fd08c' : '#ef7b7b';
      g.fillRect(bx, by, bw, bh);
      g.fillStyle = '#9ca6b2';
      g.font = '10px system-ui';
      g.textAlign = 'center';
      g.fillText(x.code, bx + bw / 2, h - 7);
    });
    g.textAlign = 'left';
    g.fillText(fmtMoney(mx, 0), 6, 12);
    g.fillText('gross profit / tick', 52, 12);
  }
  function render(s) {
    $('kernel').textContent = s.wasm
      ? 'Wasm active · legacy compatibility'
      : s.engine === 'source'
        ? 'Source engine active'
        : 'Engine inactive';
    $('kernel').className = 'pill ' + (s.wasm || s.engine === 'source' ? 'ok' : 'err');
    $('tick').textContent = s.tick;
    $('month').textContent = s.month;
    $('tps').textContent = fmtFixed(s.tps, 1);
    $('wavg').textContent = fmtMoney(s.wholesaleAvg, 5);
    $('ravg').textContent = fmtMoney(s.retailAvg, 2);
    $('wvol').textContent = Math.round(s.wholesaleVolume);
    $('rvol').textContent = Math.round(s.retailVolume);
    $('orders').textContent = Math.round(s.retailOrders);
    const t2 = s.tiers.t2,
      t1 = s.tiers.t1,
      t0 = s.tiers.t0;
    $('fillRate').textContent = pct(t2.unitFillRate);
    $('t1Equity').textContent = fmtMoney(t1.equity, 0);
    $('t1GP').textContent = fmtMoney(t1.grossProfit, 0);
    $('avgRel').textContent = pct((t0.reliability + t1.reliability) / 2, 1);
    const gaiaVals = [s.difficulty.Water, s.difficulty.Earth, s.difficulty.Fire, s.difficulty.Air];
    $('gaiaRange').textContent =
      `${fmtFixed(Math.min(...gaiaVals), 3)}–${fmtFixed(Math.max(...gaiaVals), 3)}`;
    $('t0Inventory').textContent = fmtInt(t0.inventory);
    $('t0Cash').textContent = fmtMoney(t0.cash, 0);
    $('t0Equity').textContent = fmtMoney(t0.equity, 0);
    $('t1Raw').textContent = Math.round(t1.raw).toLocaleString();
    $('t1Finished').textContent = Math.round(t1.finished).toLocaleString();
    $('t1Cash').textContent = fmtMoney(t1.cash, 0);
    $('t1Equity2').textContent = fmtMoney(t1.equity, 0);
    $('scaleCaption').textContent =
      `${fmtInt(t0.sold)} raw units sold · ${fmtInt(t1.sold)} finished units sold`;
    $('demandCaption').textContent =
      `${fmtInt(t2.fulfilled)} / ${fmtInt(t2.active)} desired units fulfilled`;
    $('demandPotential').textContent = fmtInt(t2.potential);
    $('demandActive').textContent = fmtInt(t2.active);
    $('demandPriceLost').textContent = fmtInt(t2.priceLost);
    $('demandStockUnmet').textContent = fmtInt(t2.stockUnmet);
    $('demandFulfilled').textContent = fmtInt(t2.fulfilled);
    $('unitFillRate').textContent = pct(t2.unitFillRate);
    $('orderFillRate').textContent = pct(t2.orderFillRate);
    $('t0DiffMean').textContent =
      fmtFixed(s.difficulty.Water, 3) +
      ' / ' +
      fmtFixed(s.difficulty.Earth, 3) +
      ' / ' +
      fmtFixed(s.difficulty.Fire, 3) +
      ' / ' +
      fmtFixed(s.difficulty.Air, 3);
    $('t0Sold').textContent = fmtInt(t0.sold);
    $('t0Revenue').textContent = fmtMoney(t0.revenue, 0);
    $('t0HHI').textContent = pct(t0.hhi.reduce((a, v) => a + v, 0) / 4, 1);
    $('t1Active').textContent = t1.activeFirms;
    $('t1Players').textContent = t1.players;
    $('t1Made').textContent = fmtInt(t1.made);
    $('t1Sold').textContent = fmtInt(t1.sold);
    $('t1Revenue').textContent = fmtMoney(t1.revenue, 0);
    $('t1COGS').textContent = fmtMoney(t1.cogs, 0);
    $('priceLossShare').textContent = pct(t2.priceLossShare);
    $('stockUnmetShare').textContent = pct(t2.stockUnmetShare);
    $('ordersFulfilled').textContent = `${fmtInt(t2.fulfilledOrders)} / ${fmtInt(t2.orders)}`;
    $('retailRevenue').textContent = fmtMoney(t2.revenue, 0);
    $('wholesale').innerHTML = sortedTableRows('wholesale', s.elements)
      .map(
        (x) =>
          `<tr><th>${x.code}</th><td>${x.difficulty.toFixed(3)}</td><td>${fmtMoney(x.price, 5)}</td><td>${fmtInt(x.volume)}</td><td>${x.hhi.toFixed(3)}</td><td>${x.reliability.toFixed(3)}</td></tr>`,
      )
      .join('');
    $('retail').innerHTML = sortedTableRows('retail', s.products)
      .map(
        (x) =>
          `<tr><th>${x.code}</th><td>${fmtMoney(x.retailPrice, 2)}</td><td>${fmtInt(x.supplyCapacity)}</td><td>${fmtInt(x.readyStock)}</td><td>${fmtInt(x.volume)}</td><td>${x.hhi.toFixed(3)}</td><td>${fmtInt(x.potential)}</td><td>${fmtInt(x.active)}</td><td>${fmtInt(x.fulfilled)}</td><td>${pct(x.fillRate)}</td><td>${fmtInt(x.stockUnmet)}</td></tr>`,
      )
      .join('');
    $('cohorts').innerHTML = sortedTableRows('cohorts', s.cohorts)
      .map(
        (x) =>
          `<tr><th>${x.code} · ${x.name}</th><td>${x.firms}</td><td>${x.equipment}</td><td>${fmtMoney(x.avgPrice, 2)}</td><td>${fmtMoney(x.avgUnitCost, 2)}</td><td>${fmtInt(x.finished)}</td><td>${fmtInt(x.inventory)}</td><td>${fmtMoney(x.cash, 0)}</td><td>${fmtMoney(x.equity, 0)}</td><td>${fmtInt(x.made)}</td><td>${fmtInt(x.sold)}</td><td>${fmtMoney(x.revenue, 0)}</td><td>${fmtMoney(x.grossProfit, 0)}</td><td>${x.reliability.toFixed(3)}</td><td>${pct(x.marketShare, 1)}</td></tr>`,
      )
      .join('');
    renderCompanyTables();
    const hist = s.analyticsHistory || [];
    drawLine(
      'inventoryChart',
      hist,
      [hist.map((x) => x.t0Inventory), hist.map((x) => x.t1Inventory)],
      ['T0 inventory', 'T1 inventory'],
      0,
      false,
    );
    drawLine(
      'equityChart',
      hist,
      [hist.map((x) => x.t0Equity), hist.map((x) => x.t1Equity)],
      ['T0 marked equity', 'T1 marked equity'],
      0,
      true,
    );
    drawLine(
      'demandChart',
      hist,
      [
        hist.map((x) => x.retailPotential),
        hist.map((x) => x.retailActive),
        hist.map((x) => x.retailFulfilled),
      ],
      ['potential', 'at price', 'fulfilled'],
      0,
      false,
    );
    drawLine('wholesaleChart', hist, [hist.map((x) => x.wholesaleAvg)], ['wholesale avg'], 5, true);
    drawLine('retailChart', hist, [hist.map((x) => x.retailAvg)], ['retail avg'], 2, true);
    drawCohortGrossProfit('cohortChart', s.cohorts);
    drawBars('revenueChart', s.cohorts, 'revenue', 'code', (v) => fmtMoney(v, 0));

    $('controller').value = s.selected.controller;
    $('online').value = String(s.selected.online);
    $('playerPrice').value = Number.isFinite(s.selected.price)
      ? s.selected.price.toFixed(2)
      : '1.00';
    $('playerProduct').innerHTML = s.selected.equipment
      .map((x) => `<option value="${x}">${x}</option>`)
      .join('');
    if (s.selected.equipment.length) $('playerProduct').value = s.selected.native;
    $('playerStatus').textContent =
      `${s.selected.name} · ${fmtMoney(s.selected.cash, 2)} cash · eq ${fmtMoney(s.selected.eqBook, 2)}`;
  }
  $('tier0Companies').addEventListener('click', (e) => {
    const r = e.target.closest('.clickable-row');
    if (!r) return;
    const id = +r.dataset.id;
    expandedCompanies.T0.has(id) ? expandedCompanies.T0.delete(id) : expandedCompanies.T0.add(id);
    requestCompanyDetail('T0', id);
  });
  $('tier1Companies').addEventListener('click', (e) => {
    const r = e.target.closest('.clickable-row');
    if (!r) return;
    const id = +r.dataset.id;
    expandedCompanies.T1.has(id) ? expandedCompanies.T1.delete(id) : expandedCompanies.T1.add(id);
    requestCompanyDetail('T1', id);
  });
  $('t0Search').addEventListener('input', () => {
    t0Page = 0;
    renderCompanyTables();
  });
  $('t1Search').addEventListener('input', () => {
    t1Page = 0;
    renderCompanyTables();
  });
  $('t1CohortFilter').innerHTML =
    '<option value="">All cohorts</option>' +
    productCodes.map((x) => `<option value="${x}">${x}</option>`).join('');
  $('t1CohortFilter').addEventListener('change', () => {
    t1Page = 0;
    renderCompanyTables();
  });
  $('t1ControllerFilter').addEventListener('change', () => {
    t1Page = 0;
    renderCompanyTables();
  });
  $('t0ResetFilter').onclick = () => {
    $('t0Search').value = '';
    t0Page = 0;
    renderCompanyTables();
  };
  $('t1ResetFilter').onclick = () => {
    $('t1Search').value = '';
    $('t1CohortFilter').value = '';
    $('t1ControllerFilter').value = '';
    t1Page = 0;
    renderCompanyTables();
  };
  $('t1Prev').onclick = () => {
    t1Page = Math.max(0, t1Page - 1);
    renderCompanyTables();
  };
  $('t1Next').onclick = () => {
    const n = companyFilteredRows('T1').length;
    t1Page = Math.min(Math.max(0, Math.ceil(n / companyPageSize) - 1), t1Page + 1);
    renderCompanyTables();
  };
  $('run').onclick = () => worker.postMessage({ type: 'run', mode: 'fixed' });
  $('runMax').onclick = () => worker.postMessage({ type: 'run', mode: 'max' });
  $('pause').onclick = () => {
    worker.postMessage({ type: 'pause' });
    $('perf').textContent = 'Paused';
  };
  $('step').onclick = () => worker.postMessage({ type: 'step' });
  $('reset').onclick = () => worker.postMessage({ type: 'reset', cfg: readCfg() });
  $('applyParams').onclick = () => worker.postMessage({ type: 'applyConfig', cfg: readCfg() });
  $('applyPlayer').onclick = () =>
    worker.postMessage({
      type: 'player',
      id: +$('playerCompany').value,
      controller: $('controller').value,
      online: $('online').value === 'true',
      code: $('playerProduct').value,
      price: +$('playerPrice').value,
    });
  $('buyEquipment').onclick = () =>
    worker.postMessage({
      type: 'buyEquipment',
      id: +$('playerCompany').value,
      code: $('equipmentProduct').value,
    });
  initializeTableSorting();
  if (location.protocol === 'file:')
    $('perf').textContent = 'Use a local web server for the multi-file worker build.';
  worker.postMessage({ type: 'init', cfg: readCfg() });
})();
