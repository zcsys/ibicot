(() => {
  if (location.protocol === 'file:') {
    document.getElementById('kernel').textContent = 'Open with the launcher';
    document.getElementById('perf').textContent =
      'Serve the app with ./run.sh serve and open it in your browser.';
    document
      .querySelectorAll('button,input,select')
      .forEach((control) => (control.disabled = true));
    return;
  }
  const worker = new Worker('./worker.js');
  const $ = (id) => document.getElementById(id);

  // --- Intergalactic loading screen ---
  const LOADING_MESSAGES = [
    'Establishing uplink…',
    'Calibrating galactic markets…',
    'Waking 100,000 procurement agents…',
    'Spinning up 60,000 robotic firms…',
    'Aligning supply chains…',
    'Synchronizing sector indexes…',
  ];
  let loadingMsgIndex = 0;
  let loadingTimer = null;
  function loadingCycle() {
    if (loadingTimer) clearInterval(loadingTimer);
    loadingTimer = setInterval(() => {
      const el = $('loading');
      if (el && el.style.display !== 'none') {
        loadingMsgIndex = (loadingMsgIndex + 1) % LOADING_MESSAGES.length;
        $('loadingStatus').textContent = LOADING_MESSAGES[loadingMsgIndex];
      }
    }, 1500);
  }
  function showLoading(msg) {
    const el = $('loading');
    if (!el) return;
    if (msg) {
      $('loadingStatus').textContent = msg;
      loadingMsgIndex = -1;
    }
    el.classList.remove('fading');
    el.style.display = 'flex';
    loadingCycle();
  }
  function hideLoading() {
    const el = $('loading');
    if (!el) return;
    if (loadingTimer) { clearInterval(loadingTimer); loadingTimer = null; }
    el.classList.add('fading');
    setTimeout(() => { el.style.display = 'none'; }, 460);
  }

  const M = window.Phase0Model;
  const displayProduct = (code) => M.PRODUCTS.find((p) => p.code === code)?.name || M.T2_PRODUCTS.find((p) => p.code === code)?.name || code;
  const displayElement = code => M.ELEMENTS[['W','E','F','A'].indexOf(code)] || code;
  const controlId = () => $('playerTier').value === 'T2' ? Math.max(0, +$('t2PlayerCompany').value - 1) : +$('playerCompany').value;
  let t2Page = 0, t2Descending = false, controlDirty = false;
  const queryTier2 = () => worker.postMessage({ type: 'tier2Query', page: t2Page, search: $('t2Search').value,
    sector: $('t2SectorFilter').value, controller: $('t2ControllerFilter').value, sort: $('t2Sort').value, descending: t2Descending });
  const PARAMS = [
    'seed',
    'difficultyTarget', 'theta', 'sigma', 'difficultyMin', 'difficultyMax',
    't0Equity', 't0Capacity', 't0TargetInventory', 't0MaxInventory', 'baseCost', 't0Markup',
    'minWholesaleLot', 'inventoryCoverageTicks',
    't1Equity', 't1License', 't1Machinery', 't1Capacity', 't1MaterialCost', 't1Markup',
    't2Equity', 't2License', 't2MaterialCost', 'conversionFactor', 'storage',
    'consumerSearchOffers',
    'chokeMin', 'chokeMax', 'elasticity', 't2ReservationPremium',
    'pricingAggressiveness', 'alpha', 'wholesalePriceResponse', 'priceObservationTicks',
    'taumin', 'taumax', 'reliabilityAlpha', 'switchingStableBand',
  ];
  for (const [id, value] of Object.entries(M.ECONOMY_DEFAULTS)) if ($(id)) $(id).value = value;
  const productCodes = ['W', 'E', 'F', 'A', 'W+E', 'W+F', 'W+A', 'E+F', 'E+A', 'F+A'];
  function readCfg() {
    const c = { ...M.ECONOMY_DEFAULTS };
    for (const id of PARAMS) c[id] = +$(id).value;
    c.t2Machinery = { 3: +$('t2Machinery3').value, 4: +$('t2Machinery4').value, 5: +$('t2Machinery5').value };
    c.t2Capacity = { 3: +$('t2Capacity3').value, 4: +$('t2Capacity4').value, 5: +$('t2Capacity5').value };
    c.footprint = { ...M.ECONOMY_DEFAULTS.footprint };
    return c;
  }
  for (let i = 0; i < 1000; i++) {
    const o = document.createElement('option');
    o.value = i;
    o.textContent = `T1-${String(i + 1).padStart(4, '0')} · ${displayProduct(productCodes[Math.floor(i / 100)])}`;
    $('playerCompany').appendChild(o);
  }
  $('equipmentProduct').innerHTML = productCodes
    .slice(4)
    .map((x) => `<option value="${x}">${displayProduct(x)}</option>`)
    .join('');
  function sendSelect() {
    controlDirty = false;
    worker.postMessage({ type: 'select', tier: $('playerTier').value, id: controlId() });
  }
  $('playerCompany').addEventListener('change', sendSelect);
  $('t2PlayerCompany').addEventListener('change', sendSelect);
  $('t2PlayerCompany').addEventListener('input', () => { if ($('t2PlayerCompany').value) sendSelect(); });
  $('playerTier').addEventListener('change', () => {
    const tier = $('playerTier').value;
    const tier2 = tier === 'T2';
    $('playerCompany').hidden = tier2; $('playerCompanyLabel').hidden = tier2; $('t2ControlId').hidden = !tier2;
    populatePlayerCompany();
    sendSelect();
  });
  let latestSnapshot = null,
    companyDetailData = null,
    t0Page = 0,
    t1Page = 0,
    companyPageSize = 50,
    selectedTier = 'T1',
    selectedCompanyId = 0;
  function populatePlayerCompany() {
    const tier = $('playerTier').value;
    const sel = $('playerCompany');
    const current = sel.value;
    sel.innerHTML = '';
    if (tier === 'T0') {
      (latestSnapshot?.t0Companies || []).forEach((c) => {
        const o = document.createElement('option');
        o.value = c.id;
        o.textContent = `T0-${String(c.id + 1).padStart(2, '0')} · ${c.name}`;
        sel.appendChild(o);
      });
    } else {
      for (let i = 0; i < 1000; i++) {
        const o = document.createElement('option');
        o.value = i;
        o.textContent = `T1-${String(i + 1).padStart(4, '0')} · ${displayProduct(productCodes[Math.floor(i / 100)])}`;
        sel.appendChild(o);
      }
    }
    if (current) sel.value = current;
  }
  const expandedCompanies = { T0: new Set(), T1: new Set() };
  const tableSortColumns = {
    wholesale: ['name', 'difficulty', 'price', 'volume', 'revenue', 'cogs', 'grossProfit', 'hhi', 'reliability'],
    retail: [
      'name',
      'complexity',
      'retailPrice',
      'supplyCapacity',
      'readyStock',
      'volume',
      'consumerVolume',
      'intermediateVolume',
      'hhi',
      'potential',
      'active',
      'fulfilled',
      'fillRate',
      'stockUnmet',
    ],
    tierComparison: ['name','complexity','firms','cash','cashPerFirm','equity','inventory','bought','made','sold','revenue','revenuePerFirm','cogs','grossProfit','margin','reliability'],
    productCategories: ['name','tier','role','products','lines','machineryPrice','unitCapacity','avgPrice','avgUnitCost','capacity','utilization','readyStock','made','sold','soldPerLine','revenue','cogs','grossProfit','profitPerLine','margin','active','fillRate','stockUnmet'],
    tier2Products: ['name','code','complexity','needType','sector','primaryMaterial','recipe','firms','machineryPrice','avgPrice','avgUnitCost','productionCapacity','utilization','readyStock','made','sold','revenue','grossProfit','margin','active','fillRate','stockUnmet','hhi','reliability'],
    tier2Industries: ['name','description','products','lines','capacity','utilization','readyStock','made','sold','revenue','cogs','grossProfit','margin','active','fulfilled','fillRate','stockUnmet','volumeShare','reliability'],
    tier2Cohorts: ['name','firms','online','players','lines','cash','equipmentBookValue','equity','raw','inventory','capacity','utilization','made','sold','revenue','grossProfit','margin'],
    tier2Complexity: ['complexity','products','lines','capacity','utilization','readyStock','made','sold','revenue','grossProfit','margin','active','fillRate','volumeShare'],
    cohorts: [
      'name',
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
      'controller',
      'elements',
      'cash',
      'inventory',
      'equity',
      'production',
      'sold',
      'revenue',
      'cogs',
      'grossProfit',
      'avgPrice',
      'reliability',
    ],
    tier1Companies: [
      'name',
      'controller',
      'sector',
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
      hideLoading();
    }
    if (m.type === 'companyDetail') {
      companyDetailData = m.data;
      selectedTier = m.data?.tier || selectedTier;
      selectedCompanyId = m.data?.id ?? selectedCompanyId;
      renderCompanyTables();
    }
    if (m.type === 'actionResult') $('playerStatus').textContent = m.msg;
    if (m.type === 'equipmentResult')
      $('playerStatus').textContent = m.ok ? 'Equipment purchased.' : m.msg;
    if (m.type === 'licenseResult')
      $('ownershipStatus').textContent = m.ok ? `Tier ${m.tier} license acquired.` : (m.msg || 'License purchase failed.');
    if (m.type === 'houseResult')
      $('ownershipStatus').textContent = m.ok ? `House "${m.name}" founded.` : (m.msg || 'House founding failed.');
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
          x.sector.toLowerCase().includes(q) ||
          x.controller.toLowerCase().includes(q) ||
          x.equipment.map(displayProduct).join(' ').toLowerCase().includes(q)) &&
        (!cf || x.sector === cf) &&
        (!ctrl || x.controller === ctrl),
    );
  }
  function companyChartMarkup(id, tier) {
    const prefix = tier + 'Company' + id;
    const panels = [['Output', 'Production & sales · units / tick'],
      ['Finance', 'Revenue, COGS & gross profit · $ / tick'],
      ['Cash', 'Cash · $'], ['Equity', 'Book equity · $']];
    return '<p class="analytics-note">History starts when this company is expanded; up to 0xF0 reported ticks.</p><div class="analytics-grid">' +
      panels.map(([suffix, label]) => '<div><span class="chart-caption">' + label + '</span><div class="chart"><canvas id="' + prefix + suffix + '" role="img" aria-label="' + tier + ' company ' + label + '"></canvas></div></div>').join('') + '</div>';
  }
  function drawCompanyHistory(detail) {
    const prefix = detail.tier + 'Company' + detail.id, history = detail.history || [];
    drawLine(prefix + 'Output', history, ['made', 'sold'].map(key => history.map(point => point[key])), ['Production', 'Sales'], 0);
    const keys = ['revenue', 'cogs', 'grossProfit'];
    const labels = ['Revenue', 'COGS', 'Gross profit'];
    drawLine(prefix + 'Finance', history, keys.map(key => history.map(point => point[key])), labels, 0, true);
    drawLine(prefix + 'Cash', history, [history.map(point => point.cash)], ['Cash'], 0, true);
    drawLine(prefix + 'Equity', history, [history.map(point => point.equity)], ['Book equity'], 0, true);
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
      return `<tr class="company-detail-row"><td colspan="14"><div class="company-detail-inner">
      <div class="detail-section"><strong>${x.name} · current stocks & sell prices</strong></div>
      <table class="detail-table"><thead><tr><th>Element</th><th>Current stock</th><th>Unit cost</th><th>Sell price</th><th>Made / tick</th><th>Sold / tick</th><th>Revenue / tick</th><th>COGS / tick</th><th>Gross profit / tick</th><th>Reliability</th><th>Price stability</th></tr></thead>
      <tbody>${(d?.elementData || []).map((v) => `<tr><th>${v.element}</th><td>${fmtInt(v.stock)}</td><td>${fmt5(v.cost)}</td><td>${fmt5(v.price)}</td><td>${fmtInt(v.production)}</td><td>${fmtInt(v.sold)}</td><td>${fmtMoney(v.revenue, 0)}</td><td>${fmtMoney(v.cogs, 0)}</td><td>${fmtMoney(v.grossProfit, 0)}</td><td>${fmtFixed(v.reliability, 3)}</td><td>${fmtFixed(v.stability, 3)}</td></tr>`).join('')}</tbody></table>
      ${companyChartMarkup(x.id, "T0")}
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
      <tbody>${(d?.raw || []).map((v) => `<tr><th>${v.element}</th><td>${fmtInt(v.stock)}</td><td>${fmtUnitPrice(v.basis)}</td><td>${v.lastBuy == null ? '—' : fmt5(v.lastBuy)}</td><td>${fmtInt(v.inputNeed)}</td><td>${fmtInt(v.purchaseRequest)}</td><td>${v.preferredSupplier >= 0 ? 'T0-' + String(v.preferredSupplier + 1).padStart(2, '0') : '—'}</td></tr>`).join('')}</tbody></table>
      <div class="detail-section"><strong>Finished stocks & sell prices</strong></div>
      <table class="detail-table"><thead><tr><th>Product</th><th>Current stock</th><th>Unit cost</th><th>Sell price</th><th>Sales EMA</th><th>Orders EMA</th><th>Made / tick</th><th>Sold / tick</th><th>Revenue / tick</th><th>COGS / tick</th><th>Customer desired / tick</th><th>Customer fill</th><th>Stock unmet / tick</th><th>Reliability</th><th>Price stability</th></tr></thead>
      <tbody>${(d?.products || []).map((v) => `<tr><th>${displayProduct(v.product)}</th><td>${fmtInt(v.finished)}</td><td>${fmtUnitPrice(v.unitCost)}</td><td>${fmtUnitPrice(v.price)}</td><td>${fmtFixed(v.salesEMA, 2)}</td><td>${fmtFixed(v.demandEMA, 2)}</td><td>${fmtInt(v.made)}</td><td>${fmtInt(v.sold)}</td><td>${fmtMoney(v.revenue, 0)}</td><td>${fmtMoney(v.cogs, 0)}</td><td>${fmtInt(v.active)}</td><td>${pct(meaningfulRatio(v.fulfilled,v.active))}</td><td>${fmtInt(v.stockUnmet)}</td><td>${fmtFixed(v.reliability, 3)}</td><td>${fmtFixed(v.priceStability, 3)}</td></tr>`).join('')}</tbody></table>
      ${companyChartMarkup(x.id, "T1")}
    </div></td></tr>`;
    };

    $('tier0Companies').innerHTML = t0
      .map((x) => {
        const row = `<tr class="clickable-row${selectedTier === 'T0' && selectedCompanyId === x.id ? ' selected' : ''}" data-tier="T0" data-id="${x.id}">
      <th>▸ ${x.name}</th><td>${x.controller}</td><td>${x.elements.join(' · ')}</td><td>${fmtMoney(x.cash, 0)}</td><td>${fmtInt(x.inventory)}</td><td>${fmtMoney(x.equity, 0)}</td><td>${fmtInt(x.production)}</td><td>${fmtInt(x.sold)}</td><td>${fmtMoney(x.revenue, 0)}</td><td>${fmtMoney(x.cogs, 0)}</td><td>${fmtMoney(x.grossProfit, 0)}</td><td>${fmt5(x.avgPrice)}</td><td>${fmtFixed(x.reliability, 3)}</td></tr>`;
        return row + (exp0.has(x.id) ? detailT0(x) : '');
      })
      .join('');

    $('tier1Companies').innerHTML = t1slice
      .map((x) => {
        const row = `<tr class="clickable-row${selectedTier === 'T1' && selectedCompanyId === x.id ? ' selected' : ''}" data-tier="T1" data-id="${x.id}">
      <th>▸ ${x.name}</th><td>${x.controller}</td><td>${x.sector}</td><td>${x.equipment.map(displayProduct).join(' · ')}</td><td>${fmtMoney(x.cash, 0)}</td><td>${fmtInt(x.raw)}</td><td>${fmtInt(x.finished)}</td><td>${fmtInt(x.inventory)}</td><td>${fmtMoney(x.equity, 0)}</td><td>${fmtUnitPrice(x.price)}</td><td>${fmtInt(x.made)}</td><td>${fmtInt(x.sold)}</td><td>${fmtMoney(x.revenue, 0)}</td><td>${fmtMoney(x.grossProfit, 0)}</td><td>${fmtFixed(x.reliability, 3)}</td></tr>`;
        return row + (exp1.has(x.id) ? detailT1(x) : '');
      })
      .join('');

    for (const detail of Object.values(latestSnapshot.expandedDetails || {})) drawCompanyHistory(detail);
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
        `made: ${fmtInt(d.made)}`,
        `sold: ${fmtInt(d.sold)}`,
        `revenue: ${fmtMoney(d.revenue, 2)}`,
        `COGS: ${fmtMoney(d.cogs, 2)}`,
        `gross profit: ${fmtMoney(d.grossProfit, 2)}`,
        `capacity/tick: ${fmtInt(d.capacity)}`,
        `target inventory: ${fmtInt(d.targetInventory)}`,
        `max inventory: ${fmtInt(d.maxInventory)}`,
        `elements: ${d.elements.join(', ')}`,
      ];
      $('companyInspector').textContent = txt.join('\n');
      $('companyTxnInspector').textContent = d.elementData
        .map(
          (x) =>
            `${x.element}: stock ${Math.round(x.stock)}, cost ${fmtMoney(x.cost, 5)}, price ${fmtMoney(x.price, 5)}, made ${Math.round(x.production)}, sold ${Math.round(x.sold)}, revenue ${fmtMoney(x.revenue, 0)}, COGS ${fmtMoney(x.cogs, 0)}, gross profit ${fmtMoney(x.grossProfit, 0)}, rel ${x.reliability.toFixed(3)}, stability ${x.stability.toFixed(3)}, reliability attempts ${Math.round(x.reliabilityAttempts)}`,
        )
        .join('\n');
    } else {
      const txt = [
        `${d.name} · Tier 1`,
        `controller: ${d.controller}`,
        `online: ${d.online ? 'yes' : 'no'}`,
        `sector: ${d.sector}`,
        `cash: ${fmtMoney(d.cash, 2)}`,
        `equipment book: ${fmtMoney(d.equipmentBookValue, 2)}`,
        `equipment: ${d.equipment.map(displayProduct).join(', ')}`,
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
            `${x.element}: stock ${Math.round(x.stock)}, basis ${fmtUnitPrice(x.basis)}, last buy ${x.lastBuy == null ? '—' : fmt5(x.lastBuy)}, input need ${Math.round(x.inputNeed)}, request ${Math.round(x.purchaseRequest)}, preferred T0 ${x.preferredSupplier}`,
        )
        .join('\n');
      const prodTxt = d.products
        .map(
          (x) =>
            `${displayProduct(x.product)}: price ${fmtUnitPrice(x.price)}, unit cost ${fmtUnitPrice(x.unitCost)}, stock ${Math.round(x.finished)}, EMA ${x.salesEMA.toFixed(2)}, made ${Math.round(x.made)}, sold ${Math.round(x.sold)}, revenue ${fmtMoney(x.revenue, 0)}, COGS ${fmtMoney(x.cogs, 0)}, customer desired ${fmtInt(x.active)}, customer fill ${pct(meaningfulRatio(x.fulfilled,x.active))}, stock unmet ${fmtInt(x.stockUnmet)}, rel ${x.reliability.toFixed(3)}, stability ${x.priceStability.toFixed(3)}`,
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
  function fmtTick(value) { return String(Math.floor(value)); }
  function fmtMoney(x, d = 2) {
    return Number.isFinite(x) ? '$' + x.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d }) : '—';
  }
  function fmtUnitPrice(x) { return fmtMoney(x, Math.abs(x) < 1 ? 5 : 2); }
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
  const chartColors = ['#77b7ff', '#6fd08c', '#f2c15b', '#ef7b7b', '#b18cff', '#77d4d4'];
  function compactAxis(value, money = false) {
    if (!Number.isFinite(value)) return '—';
    const magnitude = Math.abs(value);
    const scale = magnitude >= 1e12 ? [1e12, 'T'] : magnitude >= 1e9 ? [1e9, 'B'] :
      magnitude >= 1e6 ? [1e6, 'M'] : magnitude >= 1e3 ? [1e3, 'k'] : [1, ''];
    return (money ? '$' : '') + (value / scale[0]).toLocaleString(undefined, { maximumFractionDigits: 2 }) + scale[1];
  }
  function drawLine(id, history, seriesList, labels, digits = 2, moneyAxis = false, percentAxis = false, zeroBaseline = true) {
    const cv = $(id);
    if (!cv) return;
    const r = cv.getBoundingClientRect(), dpr = devicePixelRatio || 1;
    if (r.width < 1 || r.height < 1) return;
    cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr);
    const g = cv.getContext('2d'), w = r.width, h = r.height, left = 74, right = w - 12;
    g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h);
    g.font = '11px system-ui';
    const exact = value => percentAxis ? pct(value) : moneyAxis ? fmtMoney(value, digits) : fmtFixed(value, digits);
    const colorFor = index => chartColors[labels[index].match(/^Tier ([012])$/)?.[1] ?? index % chartColors.length];
    const axis = value => percentAxis ? pct(value, 0) : Math.abs(value) >= 1000 ? compactAxis(value, moneyAxis) : moneyAxis ? fmtMoney(value, digits) : fmtFixed(value, digits);
    let legendX = left, legendY = 14;
    labels.forEach((label, i) => {
      const itemWidth = 30 + g.measureText(label).width;
      if (legendX + itemWidth > right && legendX > left) { legendX = left; legendY += 16; }
      g.strokeStyle = colorFor(i); g.lineWidth = 3;
      g.beginPath(); g.moveTo(legendX, legendY - 4); g.lineTo(legendX + 12, legendY - 4); g.stroke();
      g.fillStyle = '#c7d0da'; g.fillText(label, legendX + 17, legendY); legendX += itemWidth;
    });
    const vals = seriesList.flat().filter(Number.isFinite), top = legendY + 18, bottom = h - 30;
    cv.setAttribute('aria-label', cv.closest('.chart').previousElementSibling.textContent +
      (history.length ? '; latest tick ' + fmtTick(history.at(-1).tick) + ': ' + labels.map((label, i) => label + ' ' + exact(seriesList[i].at(-1))).join(', ') : '; no observations yet'));
    if (!vals.length || !history.length) {
      const tooltip = cv.parentElement.querySelector('.chart-tooltip');
      if (tooltip) tooltip.hidden = true;
      cv.onmousemove = null; cv.onmouseleave = null;
      g.fillStyle = '#9ca6b2'; g.fillText('No observations yet', left, top + 25); return;
    }
    let lo = Math.min(...vals), hi = Math.max(...vals);
    if (zeroBaseline) { lo = Math.min(0, lo); hi = Math.max(0, hi); }
    else { const padding = Math.max((hi - lo) * .08, Math.abs(hi) * .005, .001); lo = Math.max(0, lo - padding); hi += padding; }
    if (percentAxis) { lo = Math.min(0, lo); hi = Math.max(1, hi); }
    if (hi === lo) hi = lo + 1;
    const first = history[0].tick, last = history.at(-1).tick;
    const xAt = tick => left + (right - left) * (tick - first) / Math.max(1, last - first);
    const yAt = value => bottom - (bottom - top) * (value - lo) / (hi - lo);
    g.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const value = hi - (hi - lo) * i / 4, y = yAt(value);
      g.strokeStyle = '#2a303a'; g.beginPath(); g.moveTo(left, y); g.lineTo(right, y); g.stroke();
      g.fillStyle = '#9ca6b2'; g.textAlign = 'right'; g.fillText(axis(value), left - 8, y + 4);
    }
    if (lo < 0) { g.strokeStyle = '#768293'; g.beginPath(); g.moveTo(left, yAt(0)); g.lineTo(right, yAt(0)); g.stroke(); }
    seriesList.forEach((series, si) => {
      g.strokeStyle = colorFor(si); g.lineWidth = 1.8; g.beginPath();
      let connected = false;
      series.forEach((v, i) => {
        if (!Number.isFinite(v)) { connected = false; return; }
        const x = xAt(history[i].tick), y = yAt(v);
        if (connected) g.lineTo(x, y); else g.moveTo(x, y);
        connected = true;
      });
      g.stroke();
      if (series.filter(Number.isFinite).length === 1) {
        const i = series.findIndex(Number.isFinite);
        g.fillStyle = colorFor(si); g.beginPath(); g.arc(xAt(history[i].tick), yAt(series[i]), 3, 0, Math.PI * 2); g.fill();
      }
    });
    g.fillStyle = '#9ca6b2'; g.textAlign = 'left'; g.fillText('Tick ' + fmtTick(first), left, h - 9);
    if (last !== first) { g.textAlign = 'right'; g.fillText('Tick ' + fmtTick(last), right, h - 9); }
    g.textAlign = 'left';
    cv.setAttribute('aria-label', cv.closest('.chart').previousElementSibling.textContent +
      '; latest tick ' + fmtTick(last) + ': ' + labels.map((label, i) => label + ' ' + exact(seriesList[i].at(-1))).join(', '));
    let tooltip = cv.parentElement.querySelector('.chart-tooltip');
    if (!tooltip) { tooltip = document.createElement('div'); tooltip.className = 'chart-tooltip'; tooltip.hidden = true; cv.parentElement.appendChild(tooltip); }
    cv.onmousemove = event => {
      const target = first + Math.max(0, Math.min(1, (event.offsetX - left) / (right - left))) * (last - first);
      let index = 0;
      history.forEach((point, i) => { if (Math.abs(point.tick - target) < Math.abs(history[index].tick - target)) index = i; });
      tooltip.textContent = 'Tick ' + fmtTick(history[index].tick) + '\n' + labels.map((label, i) => label + ': ' + exact(seriesList[i][index])).join(' · ');
      tooltip.hidden = false;
    };
    cv.onmouseleave = () => { tooltip.hidden = true; };
  }
  function drawComparison(id, items, key, money = false, ratio = false, moneyDigits = 0) {
    const cv = $(id), r = cv.getBoundingClientRect(), dpr = devicePixelRatio || 1;
    if (r.width < 1 || r.height < 1) return;
    cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr);
    const g = cv.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, r.width, r.height);
    const values = items.map(item => item[key]), finite = values.filter(Number.isFinite);
    const lo = Math.min(0, ...finite), hi = Math.max(ratio ? 1 : 0, ...finite), span = Math.max(1e-9, hi - lo);
    const left = Math.min(155, r.width * .4), right = r.width - 90, row = (r.height - 44) / Math.max(1, items.length);
    const position = value => left + (right - left) * (value - lo) / span;
    g.font = '10px system-ui';
    items.forEach((item, i) => {
      const y = 14 + i * row, zero = position(0), value = values[i], end = position(value);
      if (Number.isFinite(value)) { g.fillStyle = value < 0 ? '#ef7b7b' : '#77b7ff'; g.fillRect(Math.min(zero, end), y, Math.abs(end - zero), row * .55); }
      g.fillStyle = '#c7d0da'; g.textAlign = 'right';
      let name = item.name;
      while (g.measureText(name).width > left - 14 && name.length > 2) name = name.slice(0, -2) + '…';
      g.fillText(name, left - 8, y + row * .45); g.textAlign = 'left';
      g.fillText(ratio ? pct(value) : money ? fmtMoney(value, moneyDigits) : compactAxis(value, false), right + 7, y + row * .45);
    });
    g.strokeStyle = '#768293'; g.beginPath(); g.moveTo(position(0), 10); g.lineTo(position(0), r.height - 30); g.stroke();
    const axis = value => money && moneyDigits === 5 && Math.abs(value) < 1000
      ? fmtMoney(value, moneyDigits) : compactAxis(value, money);
    g.fillStyle = '#9ca6b2'; g.fillText(axis(lo), left, r.height - 8);
    g.textAlign = 'right'; g.fillText(ratio ? pct(hi, 0) : axis(hi), right, r.height - 8); g.textAlign = 'left';
    cv.setAttribute('aria-label', cv.closest('.chart').previousElementSibling.textContent + ': ' + items.map(item => item.name + ' ' +
      (ratio ? pct(item[key]) : money ? fmtMoney(item[key], moneyDigits) : fmtInt(item[key]))).join(', '));
    cv.title = items.map(item => item.name + ': ' + (ratio ? pct(item[key]) : money ? fmtMoney(item[key], moneyDigits) : fmtInt(item[key]))).join('\n');
  }
  const meaningfulRatio = (numerator, denominator) => denominator > 0 ? numerator / denominator : NaN;
  function renderDashboard(s) {
    const t0 = s.tiers.t0, t1 = s.tiers.t1, t2 = s.tiers.t2, consumers = s.tiers.endUsers;
    const money = { economyCash: t0.cash + t1.cash + t2.cash, economyEquity: t0.equity + t1.equity + t2.equity,
      economySpending: consumers.revenue, t0Cash: t0.cash, t0Equity: t0.equity, t0Revenue: t0.revenue,
      t0COGS: t0.cogs, t0GrossProfit: t0.grossProfit,
      t1Cash: t1.cash, t1Equity: t1.equity, t1Revenue: t1.revenue, t1COGS: t1.cogs, t1GP: t1.grossProfit,
      retailRevenue: consumers.revenue };
    for (const [id, value] of Object.entries(money)) $(id).textContent = fmtMoney(value, 0);
    const integers = { economyInventory: t0.inventory + t1.inventory + t2.inventory, economyPurchases: consumers.fulfilled,
      t0Firms: t0.firms, t0Inventory: t0.inventory, t0Made: t0.made, t0Sold: t0.sold,
      t1Firms: t1.firms, t1Raw: t1.raw, t1Finished: t1.finished, t1Active: t1.activeFirms, t1Players: t1.players,
      t1Bought: t1.bought, t1Made: t1.made, t1Sold: t1.sold, t1ConsumerSold: sum(s.products.map(p => p.consumerVolume)),
      t1BusinessSold: sum(s.products.map(p => p.intermediateVolume)),
      t1CustomerDesired: t1.desired, t1CustomerFulfilled: t1.fulfilled, t1StockUnmet: t1.stockUnmet, consumerPopulation: consumers.population,
      consumerActivated: s.performance.activatedConsumers, demandPotential: consumers.potential, demandActive: consumers.active,
      demandPriceLost: consumers.priceLost, demandStockUnmet: consumers.stockUnmet, demandFulfilled: consumers.fulfilled, orders: consumers.orders };
    for (const [id, value] of Object.entries(integers)) $(id).textContent = fmtInt(value);
    const ratios = { fillRate: meaningfulRatio(consumers.fulfilled, consumers.active),
      unitFillRate: meaningfulRatio(consumers.fulfilled, consumers.active), orderFillRate: meaningfulRatio(consumers.fulfilledOrders, consumers.orders),
      priceLossShare: meaningfulRatio(consumers.priceLost, consumers.potential), stockUnmetShare: meaningfulRatio(consumers.stockUnmet, consumers.active),
      t0HHI: meaningfulRatio(sum(s.elements.filter(e => e.volume > 0).map(e => e.hhi)),s.elements.filter(e => e.volume > 0).length), t0Reliability: t0.reliability, t1Reliability: t1.reliability,
      t1CustomerFill: meaningfulRatio(t1.fulfilled,t1.desired), t1Margin: meaningfulRatio(t1.grossProfit, t1.revenue) };
    for (const [id, value] of Object.entries(ratios)) $(id).textContent = id === 't0HHI' ? fmtFixed(value, 3) : pct(value);
    $('wavg').textContent = s.wholesaleVolume > 0 ? fmtMoney(s.wholesaleAvg, 5) : '—';
    $('ravg').textContent = s.retailVolume > 0 ? fmtUnitPrice(s.retailAvg) : '—';
    $('ordersFulfilled').textContent = fmtInt(consumers.fulfilledOrders) + ' / ' + fmtInt(consumers.orders);
    const difficulty = Object.values(s.difficulty);
    $('gaiaRange').textContent = fmtFixed(Math.min(...difficulty), 3) + '–' + fmtFixed(Math.max(...difficulty), 3);
    $('t0DiffMean').textContent = fmtFixed(sum(difficulty) / difficulty.length, 3);
    $('scaleCaption').textContent = fmtInt(t0.firms) + ' extraction firms · ' + fmtInt(t1.firms) + ' material firms · ' +
      fmtInt(t2.firms) + ' finished-goods firms · ' + fmtInt(consumers.population) + ' external procurement agents';
    $('demandCaption').textContent = fmtInt(consumers.fulfilled) + ' / ' + fmtInt(consumers.active) + ' desired units fulfilled this tick';
    const hist = s.analyticsHistory || [], scope = $('overviewTier').value;
    const tiers = scope ? [scope] : ['t0', 't1', 't2'];
    for (const [id, key, moneyAxis] of [['cashChart', 'cash', true], ['equityChart', 'equity', true], ['inventoryChart', 'inventory', false],
      ['productionChart', 'made', false], ['salesChart', 'sold', false], ['producerRevenueChart', 'revenue', true]])
      drawLine(id, hist, tiers.map(tier => hist.map(point => point.tiers[tier][key])), tiers.map(tier => 'Tier ' + tier.slice(1)), 0, moneyAxis);
    drawLine('gaiaChart', hist, [0, 1, 2, 3].map(i => hist.map(point => point.difficulty[i])), M.ELEMENTS, 3, false, false, false);
    drawLine('wholesaleChart', hist, [0, 1, 2, 3].map(i => hist.map(point => point.elementPrices[i])), M.ELEMENTS, 5, true, false, false);
    for (const tier of ['t0', 't1']) {
      drawLine(tier + 'OutputChart', hist, ['made', 'sold'].map(key => hist.map(point => point.tiers[tier][key])), ['Production', 'Sales'], 0);
      drawLine(tier + 'FinanceChart', hist, ['revenue', 'cogs', 'grossProfit'].map(key => hist.map(point => point.tiers[tier][key])), ['Revenue', 'COGS', 'Gross profit'], 0, true);
    }
    const product = $('t1PriceProduct').value;
    drawLine('retailChart', hist, product !== '' ? [hist.map(point => point.materialPrices[+product])] :
      [hist.map(point => sum(point.materialPrices.slice(0, 4)) / 4), hist.map(point => sum(point.materialPrices.slice(4)) / 6)],
      product !== '' ? [M.PRODUCTS[+product].name] : ['C-1 mean market price', 'C-2 mean market price'], 5, true, false, false);
    drawComparison('cohortChart', s.cohorts.map(c => ({...c, name: c.sector})), 'grossProfit', true);
    drawComparison('revenueChart', s.cohorts.map(c => ({...c, name: c.sector})), 'revenue', true);
    drawLine('demandChart', hist, ['potential', 'active', 'fulfilled'].map(key => hist.map(point => point.tiers.endUsers[key])), ['Latent', 'Desired', 'Fulfilled'], 0);
    drawLine('consumerFillChart', hist, ['active', 'orders'].map((key, i) => hist.map(point => meaningfulRatio(point.tiers.endUsers[i ? 'fulfilledOrders' : 'fulfilled'], point.tiers.endUsers[key]))), ['Unit fulfillment', 'Order fulfillment'], 1, false, true);
    drawLine('consumerSpendingChart', hist, [hist.map(point => point.tiers.endUsers.revenue)], ['Spending'], 0, true);
  }
  function renderComparisons(s) {
    const moneyKeys = new Set(['cash','cashPerFirm','equity','revenue','revenuePerFirm','cogs','grossProfit','machineryPrice','avgPrice','avgUnitCost','profitPerLine']);
    const ratioKeys = new Set(['margin','utilization','fillRate','reliability']);
    const cells = (row, keys) => keys.map(key => {
      const value = row[key];
      const text = value == null ? '—' : typeof value === 'string' ? value :
        ratioKeys.has(key) ? pct(value) : moneyKeys.has(key) ? (['avgPrice','avgUnitCost'].includes(key) ? fmtUnitPrice(value) : fmtMoney(value,key==='profitPerLine'?2:0)) :
        key === 'soldPerLine' ? fmtFixed(value, 2) : fmtInt(value);
      return '<td>' + text + '</td>';
    }).join('');
    const tiers = ['t0','t1','t2'].map((key, index) => {
      const t = s.tiers[key];
      return { ...t, name: ['Tier 0 · Extraction','Tier 1 · Materials','Tier 2 · Galactic goods'][index],
        complexity: ['Raw elements','C-1–C-2','C-3–C-5'][index],
        bought: index === 0 ? null : t.bought,
        cashPerFirm: meaningfulRatio(t.cash, t.firms), revenuePerFirm: meaningfulRatio(t.revenue, t.firms),
        margin: meaningfulRatio(t.grossProfit, t.revenue),
        reliability: index === 2 ? meaningfulRatio(sum(s.tier2Products.map(p => p.reliability * p.firms)), sum(s.tier2Products.map(p => p.firms))) : t.reliability };
    });
    $('tierComparison').innerHTML = sortedTableRows('tierComparison', tiers).map(row => '<tr><th>' + row.name + '</th>' + cells(row, tableSortColumns.tierComparison.slice(1)) + '</tr>').join('');
    const categories = s.productCategories.map(row => ({ ...row,
      margin: meaningfulRatio(row.grossProfit, row.revenue), utilization: meaningfulRatio(row.made, row.capacity),
      avgPrice: row.lines ? row.avgPrice : NaN, avgUnitCost: row.lines ? row.avgUnitCost : NaN,
      active: row.active,
      fillRate: meaningfulRatio(row.fulfilled, row.active),
      stockUnmet: row.stockUnmet }));
    $('productCategories').innerHTML = sortedTableRows('productCategories', categories).map(row => '<tr><th>' + row.name + '</th>' + cells(row, tableSortColumns.productCategories.slice(1)) + '</tr>').join('');
    const metric = $('categoryMetric').value;
    $('categoryComparisonCaption').textContent = $('categoryMetric').selectedOptions[0].textContent;
    drawComparison('categoryComparisonChart', categories, metric,
      ['revenue','grossProfit','profitPerLine','machineryPrice','avgPrice','avgUnitCost'].includes(metric), ['margin','utilization','fillRate'].includes(metric), ['avgPrice','avgUnitCost'].includes(metric) ? 5 : metric==='profitPerLine' ? 2 : 0);
  }
  function renderOwnership(s) {
    const o = s.ownership;
    if (!o) return;
    $('ownershipLicenses').textContent = o.licenses.join(', ') || '—';
    $('t2LicenseCost').textContent = o.licenseCosts.T2 == null ? 'not for sale' : fmtMoney(o.licenseCosts.T2, 0);
    $('buyT2License').disabled = o.licenses.includes('T2');
    $('ownershipHouse').textContent = o.house ? o.house.name : 'None';
    $('foundHouse').disabled = !!o.house;
  }
  function render(s) {
    const engineActive = s.engine === 'python' || s.engine === 'source' || !!s.wasm;
    $('kernel').textContent = s.engine === 'python'
      ? 'Python engine active · Numba'
      : s.wasm
        ? 'Wasm active · legacy compatibility'
        : s.engine === 'source'
          ? 'Source engine active'
          : 'Engine inactive';
    $('kernel').className = 'pill ' + (engineActive ? 'ok' : 'err');
    $('tick').textContent = fmtTick(s.tick);
    $('month').textContent = s.calendar.month;
    $('generation').textContent = s.calendar.generationHex + '.' + s.calendar.year;
    $('tps').textContent = fmtFixed(s.tps, 1);
    renderDashboard(s);
    renderComparisons(s);
    $('wholesale').innerHTML = sortedTableRows('wholesale', s.elements)
      .map(
        (x) =>
          `<tr><th>${displayElement(x.code)}</th><td>${x.difficulty.toFixed(3)}</td><td>${fmtMoney(x.price, 5)}</td><td>${fmtInt(x.volume)}</td><td>${fmtMoney(x.revenue, 0)}</td><td>${fmtMoney(x.cogs, 0)}</td><td>${fmtMoney(x.grossProfit, 0)}</td><td>${x.volume > 0 ? x.hhi.toFixed(3) : "—"}</td><td>${x.reliability.toFixed(3)}</td></tr>`,
      )
      .join('');
    $('retail').innerHTML = sortedTableRows('retail', s.products)
      .map(
        (x) =>
          `<tr><th>${displayProduct(x.code)}</th><td>${x.complexity === 1 ? 'C-1 business inputs' : 'C-2 business inputs'}</td><td>${fmtUnitPrice(x.retailPrice)}</td><td>${fmtInt(x.supplyCapacity)}</td><td>${fmtInt(x.readyStock)}</td><td>${fmtInt(x.volume)}</td><td>${fmtInt(x.consumerVolume)}</td><td>${fmtInt(x.intermediateVolume)}</td><td>${x.volume > 0 ? x.hhi.toFixed(3) : "—"}</td><td>${x.potential == null ? "—" : fmtInt(x.potential)}</td><td>${fmtInt(x.active)}</td><td>${fmtInt(x.fulfilled)}</td><td>${pct(meaningfulRatio(x.fulfilled,x.active))}</td><td>${fmtInt(x.stockUnmet)}</td></tr>`,
      )
      .join('');
    $('cohorts').innerHTML = sortedTableRows('cohorts', s.cohorts)
      .map(
        (x) =>
          `<tr><th>${x.sector}</th><td>${x.firms}</td><td>${x.equipment}</td><td>${fmtUnitPrice(x.avgPrice)}</td><td>${fmtUnitPrice(x.avgUnitCost)}</td><td>${fmtInt(x.finished)}</td><td>${fmtInt(x.inventory)}</td><td>${fmtMoney(x.cash, 0)}</td><td>${fmtMoney(x.equity, 0)}</td><td>${fmtInt(x.made)}</td><td>${fmtInt(x.sold)}</td><td>${fmtMoney(x.revenue, 0)}</td><td>${fmtMoney(x.grossProfit, 0)}</td><td>${x.reliability.toFixed(3)}</td><td>${s.products.find(p => p.code === x.code)?.volume > 0 ? pct(x.marketShare, 1) : "—"}</td></tr>`,
      )
      .join('');
    renderCompanyTables();
    renderTier2(s);
    renderOwnership(s);
    if (!controlDirty) { $('controller').value = s.selected.controller; $('online').value = String(s.selected.online); }
    const isT0 = s.selected.tier === 'T0';
    const displayCode = (x) => (isT0 ? displayElement(x) : displayProduct(x));
    const selectedProduct = $('playerProduct').value;
    const productOptions = s.selected.equipment.map((x) => `<option value="${x}">${displayCode(x)}</option>`).join('');
    if ($('playerProduct').innerHTML !== productOptions) $('playerProduct').innerHTML = productOptions;
    if (s.selected.equipment.includes(selectedProduct)) $('playerProduct').value = selectedProduct;
    const currentProduct = s.selected.products?.find((p) => (p.code || p.product) === $('playerProduct').value);
    if (!controlDirty && document.activeElement !== $('playerPrice')) $('playerPrice').value = (currentProduct?.price ?? s.selected.price ?? 1).toFixed(5);
    $('buyEquipment').hidden = isT0;
    $('equipmentProduct').hidden = isT0;
    const eligible = s.selected.tier === 'T2' ? s.selected.eligibleEquipment :
      M.PRODUCTS.filter((p) => !s.selected.equipment.includes(p.code)).map((p) => ({ ...p, price: p.equipmentPrice }));
    const machineryOptions = eligible.map((p) => `<option value="${p.code}">${p.name} · ${fmtMoney(p.price, 0)}</option>`).join('');
    const equipmentChoice = $('equipmentProduct').value;
    if ($('equipmentProduct').innerHTML !== machineryOptions) $('equipmentProduct').innerHTML = machineryOptions;
    if (eligible.some((p) => p.code === equipmentChoice)) $('equipmentProduct').value = equipmentChoice;
    $('playerStatus').textContent =
      `${s.selected.name} · ${fmtMoney(s.selected.cash, 2)} cash · eq ${fmtMoney(s.selected.eqBook, 2)}`;
  }
  function renderTier2(s) {
    const t2 = s.tiers.t2;
    $('t2Scale').textContent = `${fmtInt(t2.firms)} firms · ${fmtInt(t2.activeLines)} product lines`;
    for (const [id, value] of [['t2Cash',t2.cash],['t2Revenue',t2.revenue],['t2GP',t2.grossProfit],['t2COGS',t2.cogs],['t2Equity',t2.equity]]) $(id).textContent = fmtMoney(value,0);
    for (const [id, value] of [['t2Bought',t2.bought],['t2Raw',t2.inventory-t2.finished],['t2Finished',t2.finished],['t2Sold',t2.sold],['t2Made',t2.made],['t2Capacity',t2.capacity]]) $(id).textContent = fmtInt(value);
    $('t2Utilization').textContent = pct(t2.utilization); $('t2Margin').textContent = pct(meaningfulRatio(t2.grossProfit,t2.revenue)); $('t2Fill').textContent = pct(meaningfulRatio(t2.fulfilled,t2.desired));
    $('t2StockCoverage').textContent = t2.stockCoverage === null ? 'No sales yet' : `${t2.stockCoverage.toFixed(1)} ticks`;
    $('t2TradingFirms').textContent = `${fmtInt(t2.tradingFirms360)} / ${fmtInt(t2.firms)}`;
    const ratioKeys = new Set(['margin','utilization','fillRate','volumeShare','reliability']);
    const moneyKeys = new Set(['cash','equity','equipmentBookValue','machineryPrice','avgPrice','avgUnitCost','revenue','cogs','grossProfit']);
    const format = (key, value) => typeof value === 'string' ? value : ratioKeys.has(key) ? pct(value) :
      moneyKeys.has(key) ? (['avgPrice','avgUnitCost'].includes(key)?fmtUnitPrice(value):fmtMoney(value,0)) : key === 'hhi' ? fmtFixed(value,3) : fmtInt(value);
    const cells = (c, keys) => keys.map((key)=> {
      const value = key === 'margin' ? meaningfulRatio(c.grossProfit,c.revenue) :
        key === 'fillRate' ? meaningfulRatio(c.fulfilled,c.active) :
        key === 'volumeShare' && !t2.sold ? NaN : key === 'hhi' && !c.sold ? NaN :
        ['avgPrice','avgUnitCost'].includes(key) && !c.firms ? NaN : c[key];
      return '<td>'+format(key,value)+'</td>';
    }).join('');
    for (const [id, rows] of [['tier2Industries',s.tier2Industries],['tier2Cohorts',s.tier2Cohorts],['tier2Complexity',s.tier2Complexity]])
      $(id).innerHTML = sortedTableRows(id,rows).map((c)=>'<tr><th>'+c[tableSortColumns[id][0]]+'</th>'+cells(c,tableSortColumns[id].slice(1))+'</tr>').join('');
    const search = $('t2ProductSearch').value.toLowerCase(), complexity = $('t2ComplexityFilter').value, sector = $('t2ProductSector').value, need = $('t2ProductNeed').value;
    const products = s.tier2Products.filter((p)=>(!complexity || p.complexity === +complexity) && (!sector || p.sector === sector) && (!need || p.needType === need) && (p.code+' '+p.name+' '+p.needType+' '+p.kind+' '+p.sector+' '+p.recipe).toLowerCase().includes(search));
    $('t2ProductCount').textContent = products.length+' / '+s.tier2Products.length+' galactic goods';
    $('tier2Products').innerHTML = sortedTableRows('tier2Products',products).map((p)=>'<tr><th title="Recipe: '+p.recipe+'">'+p.name+'</th>'+cells(p,tableSortColumns.tier2Products.slice(1))+'</tr>').join('');
    const page = s.tier2Companies; t2Page = page.page;
    $('tier2Companies').innerHTML = page.rows.map((c)=>'<tr class="clickable-row" data-id="'+c.id+'"><th>'+c.name+'</th><td>'+c.sector+'</td><td>'+c.capability+'</td><td>'+c.controller+'</td><td>'+(c.controller==='BOT'?'Automated':c.online?'Online':'Offline')+'</td><td class="recipe-cell">'+c.products.map((p)=>p.name).join(', ')+'</td>'+
      cells(c,['cash','equipmentBookValue','equity','raw','finished','capacity','utilization','made','sold','revenue','grossProfit','margin','reliability'])+'<td><button data-control-id="'+c.id+'">Manage</button></td></tr>').join('');
    $('t2Page').textContent = 'Page '+(page.page+1)+' / '+Math.max(1,Math.ceil(page.total/page.pageSize))+' · '+fmtInt(page.total)+' firms';
    $('t2Prev').disabled = page.page === 0; $('t2Next').disabled = (page.page+1)*page.pageSize >= page.total;
    $('t2CompanyCharts').hidden = s.selected.tier !== 'T2';
    if (s.selected.tier === 'T2') {
      const c = s.selected;
      const metrics = [['Cash',fmtMoney(c.cash,0)],['Equipment book',fmtMoney(c.eqBook,0)],['Book equity',fmtMoney(c.equity,0)],
        ['Input stock',fmtInt(c.raw)],['Finished stock',fmtInt(c.finished)],['Capacity / tick',fmtInt(c.capacity)],
        ['Production utilization',pct(c.utilization)],['Realized margin',pct(meaningfulRatio(c.grossProfit,c.revenue))],['Stock sell-through',pct(meaningfulRatio(c.sold,c.sold+c.finished))]];
      $('t2CompanyDetail').innerHTML = '<strong>'+c.name+'</strong> · '+c.controller+' · '+(c.controller==='BOT'?'Automated':c.online?'Player online':'Player offline; automatic production')+' · Capability '+c.capability+' · '+c.lineCount+' / '+M.T2_MAX_PRODUCTS_PER_FIRM+' lines'+
        '<div class="stat-grid industry-kpis" style="margin:10px 0">'+metrics.map(([label,value])=>'<div class="stat"><span>'+label+'</span><b>'+value+'</b></div>').join('')+'</div>'+
        '<strong>Installed product lines</strong><div class="table-wrap industry-table"><table class="mini-table"><thead><tr><th>Product</th><th>Recipe</th><th>Complexity</th><th>Price</th><th>Unit cost</th><th>Capacity / tick</th><th>Utilization</th><th>Finished stock</th><th>Stock / sales EMA (ticks)</th><th>Made / tick</th><th>Sold / tick</th><th>Revenue / tick</th><th>COGS / tick</th><th>Gross profit / tick</th><th>Margin</th><th>Reliability</th></tr></thead><tbody>'+
        c.products.map((p)=>'<tr><th>'+p.name+'</th><td class="recipe-cell">'+p.recipe+'</td><td>'+p.complexity+'</td><td>'+fmtUnitPrice(p.price)+'</td><td>'+fmtUnitPrice(p.unitCost)+'</td><td>'+fmtInt(p.capacity)+'</td><td>'+pct(p.utilization)+'</td><td>'+fmtInt(p.finished)+'</td><td>'+(p.stockCoverage === null ? '—' : p.stockCoverage.toFixed(1))+'</td><td>'+fmtInt(p.made)+'</td><td>'+fmtInt(p.sold)+'</td><td>'+fmtMoney(p.revenue,0)+'</td><td>'+fmtMoney(p.cogs,0)+'</td><td>'+fmtMoney(p.grossProfit,0)+'</td><td>'+pct(meaningfulRatio(p.grossProfit,p.revenue))+'</td><td>'+pct(p.reliability)+'</td></tr>').join('')+'</tbody></table></div>'+
        '<p class="analytics-note">Gross margin = gross profit / revenue; stock sell-through = sales / (sales + remaining finished stock). Equipment is at book value; all inventory in book equity uses its acquisition or production cost basis.</p>'+
        '<strong>Inputs & upstream supplier relationships</strong><div class="table-wrap industry-table"><table class="mini-table"><thead><tr><th>Material</th><th>Source</th><th>Stock</th><th>Inventory basis / unit</th><th>Book value</th><th>Consumed / tick</th><th>Full-capacity need / tick</th><th>Full-capacity coverage (ticks)</th><th>Last supplier</th><th>Current quote</th><th>Supplier reliability</th></tr></thead><tbody>'+
        c.inputs.map((x)=>'<tr><th>'+x.name+'</th><td>'+x.sourceTier+'</td><td>'+fmtInt(x.stock)+'</td><td>'+fmtUnitPrice(x.basis)+'</td><td>'+fmtMoney(x.value,0)+'</td><td>'+fmtInt(x.consumed)+'</td><td>'+fmtInt(x.capacityNeed)+'</td><td>'+x.capacityCoverage.toFixed(1)+'</td><td>'+(x.supplierName || 'No successful supplier yet')+'</td><td>'+(x.supplierPrice===null?'—':fmtUnitPrice(x.supplierPrice))+'</td><td>'+(x.supplierReliability===null?'—':pct(x.supplierReliability))+'</td></tr>').join('')+'</tbody></table></div>';
      const history = s.tier2CompanyHistory;
      $('t2CompanyHistoryNote').textContent = c.name+' · history starts when selected; '+fmtTick(history.length)+' / 240 reported ticks retained. Switching companies starts a fresh history.';
      drawLine('tier2CompanyOutputChart',history,[history.map((x)=>x.made),history.map((x)=>x.sold)],['Made','Sold'],0);
      drawLine('tier2CompanyFinanceChart',history,[history.map((x)=>x.revenue),history.map((x)=>x.cogs),history.map((x)=>x.grossProfit)],['Revenue','COGS','Gross profit'],0,true);
      drawLine('tier2CompanyBalanceChart',history,[history.map((x)=>x.cash)],['Cash'],0,true);
      drawLine('tier2CompanyEquityChart',history,[history.map((x)=>x.equity)],['Book equity'],0,true);
    } else {
      $('t2CompanyDetail').textContent = 'Select a Tier 2 company row or use Selected company control to inspect its portfolio, inputs and performance.';
    }
    const selectedSector = $('t2IndustrySector').value;
    const history = s.analyticsHistory.map((x)=>selectedSector ? {tick:x.tick,...x.t2Industries.find((sector)=>sector.name===selectedSector)} :
      {tick:x.tick,made:x.t2Made,sold:x.t2Sold,active:x.t2Desired,revenue:x.t2Revenue,cogs:x.t2COGS,grossProfit:x.t2GrossProfit,utilization:x.t2Utilization,fillRate:x.t2FillRate,fulfilled:x.t2Fulfilled});
    drawLine('tier2SalesChart',history,[history.map((x)=>x.made),history.map((x)=>x.sold),history.map((x)=>x.active)],['Made','Sold','Desired'],0);
    drawLine('tier2FinanceChart',history,[history.map((x)=>x.revenue),history.map((x)=>x.cogs),history.map((x)=>x.grossProfit)],['Revenue','COGS','Gross profit'],0,true);
    drawLine('tier2OperationsChart',history,[history.map((x)=>x.utilization),history.map((x)=>meaningfulRatio(x.fulfilled,x.active))],['Utilization','Fulfillment'],0,false,true);
    const comparison = $('t2SectorMetric').value;
    $('t2ComparisonCaption').textContent = 'Sector ' + $('t2SectorMetric').selectedOptions[0].textContent.toLowerCase();
    drawComparison('tier2SectorChart',s.tier2Industries.map(row => ({ ...row, fillRate: meaningfulRatio(row.fulfilled,row.active) })),comparison,
      ['revenue','grossProfit'].includes(comparison),['utilization','fillRate'].includes(comparison));
    const p = s.performance;
    $('perf').textContent = p.lastTickMs.toFixed(1)+' ms / tick · '+(p.stateBytes/1048576).toFixed(1)+' MB state · '+fmtInt(p.activatedConsumers)+' active external buyers';
  }
  $('t1PriceProduct').innerHTML += M.PRODUCTS.map((p,i)=>`<option value="${i}">${p.name}</option>`).join('');
  for (const id of ['overviewTier','t1PriceProduct']) $(id).addEventListener('change',()=>{if(latestSnapshot)renderDashboard(latestSnapshot);});
  $('categoryMetric').addEventListener('change',()=>{if(latestSnapshot)renderComparisons(latestSnapshot);});
  $('t2ProductNeed').innerHTML += M.T2_NEED_TYPES.map(form=>`<option>${form}</option>`).join('');
  $('t2ProductSector').innerHTML += M.T2_SECTORS.map(s=>`<option>${s}</option>`).join('');
  $('t2NeedOverview').innerHTML = M.T2_SECTORS.map(sector =>
    '<button type="button" data-catalogue-sector="'+sector+'">'+sector+' · '+M.T2_PRODUCTS.filter(p=>p.sector===sector).length+'</button>').join('');
  $('t2NeedOverview').addEventListener('click',event=>{
    const sector=event.target.closest('[data-catalogue-sector]')?.dataset.catalogueSector;
    if(sector){$('t2ProductSector').value=sector;if(latestSnapshot)renderTier2(latestSnapshot);}
  });
  $('recipePoolSummary').textContent = M.T2_PRODUCTS.length+' invented goods · '+M.T2_UNINVENTED_PRODUCTS.length+' reserved recipes · '+[3,4,5].map(c=>M.T2_COMPLEXITY_COUNTS[c-1]+' C-'+c).join(' · ');
  $('t2SectorFilter').innerHTML += M.T2_SECTORS.map((s)=>`<option>${s}</option>`).join('');
  $('t2IndustrySector').innerHTML += M.T2_SECTORS.map((s)=>`<option>${s}</option>`).join('');
  for (const id of ['t2IndustrySector','t2SectorMetric']) $(id).addEventListener('change',()=>{if(latestSnapshot)renderTier2(latestSnapshot);});
  let analyticsResizeFrame;
  const dashboardHeader = document.querySelector('header'), dashboardNav = document.querySelector('.dashboard-nav');
  const navigationResize = new ResizeObserver(() => {
    document.documentElement.style.setProperty('--dashboard-header-height', dashboardHeader.getBoundingClientRect().height + 'px');
    document.documentElement.style.setProperty('--dashboard-nav-height', dashboardNav.getBoundingClientRect().height + 'px');
  });
  navigationResize.observe(dashboardHeader); navigationResize.observe(dashboardNav);
  window.addEventListener('resize',()=>{cancelAnimationFrame(analyticsResizeFrame);analyticsResizeFrame=requestAnimationFrame(()=>{if(latestSnapshot)render(latestSnapshot);});});
  for (const id of ['t2Search','t2SectorFilter','t2ControllerFilter','t2Sort']) $(id).addEventListener('change',()=>{ t2Page=0; queryTier2(); });
  let t2SearchTimer;
  $('t2Search').addEventListener('input',()=>{clearTimeout(t2SearchTimer);t2SearchTimer=setTimeout(()=>{t2Page=0;queryTier2();},150);});
  $('t2Order').onclick=()=>{t2Descending=!t2Descending; $('t2Order').textContent=t2Descending?'Descending':'Ascending'; queryTier2();};
  $('t2Prev').onclick=()=>{t2Page=Math.max(0,t2Page-1); queryTier2();};
  $('t2Next').onclick=()=>{t2Page++; queryTier2();};
  $('t2ResetFilter').onclick=()=>{for(const id of ['t2Search','t2SectorFilter','t2ControllerFilter'])$(id).value='';t2Page=0;queryTier2();};
  for (const id of ['t2ProductSearch','t2ComplexityFilter','t2ProductSector','t2ProductNeed']) $(id).addEventListener('input',()=>{if(latestSnapshot)renderTier2(latestSnapshot);});
  $('tier2Companies').addEventListener('click',(event)=>{
    const row=event.target.closest('[data-id]');if(!row)return;
    $('playerTier').value='T2';$('t2PlayerCompany').value=+row.dataset.id+1;
    $('playerCompany').hidden=true;$('playerCompanyLabel').hidden=true;$('t2ControlId').hidden=false;
    sendSelect();
  });
  for (const id of ['controller','online','playerPrice']) for (const event of ['input','change']) $(id).addEventListener(event,()=>{controlDirty=true;});
  $('playerProduct').addEventListener('change',()=>{
    const p=latestSnapshot?.selected.products?.find((p)=>(p.code||p.product)===$('playerProduct').value);
    if(p)$('playerPrice').value=p.price.toFixed(5);
  });
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
    '<option value="">All sectors</option>' +
    M.T2_SECTORS.map((sector) => `<option value="${sector}">${sector}</option>`).join('');
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
  $('reset').onclick = () => {
    showLoading('Re-initializing the galactic economy…');
    worker.postMessage({ type: 'reset', cfg: readCfg() });
  };
  $('applyParams').onclick = () => {
    showLoading('Recalibrating parameters…');
    worker.postMessage({ type: 'applyConfig', cfg: readCfg() });
  };
  $('applyPlayer').onclick = () => {
    controlDirty = false;
    worker.postMessage({
      type: 'player',
      id: controlId(),
      tier: $('playerTier').value,
      controller: $('controller').value,
      online: $('online').value === 'true',
      code: $('playerProduct').value,
      price: +$('playerPrice').value,
    });
  };
  $('buyEquipment').onclick = () => {
    worker.postMessage({
      type: 'buyEquipment',
      id: controlId(),
      tier: $('playerTier').value,
      code: $('equipmentProduct').value,
    });
  };
  $('buyT2License').onclick = () => worker.postMessage({ type: 'buyLicense', tier: 'T2' });
  $('foundHouse').onclick = () => worker.postMessage({ type: 'foundHouse', name: $('houseName').value });
  initializeTableSorting();
  if (location.protocol === 'file:')
    $('perf').textContent = 'Use a local web server for the multi-file worker build.';
  loadingCycle();
  worker.postMessage({ type: 'init', cfg: readCfg() });
})();
