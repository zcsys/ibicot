(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const money = value => new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(value);
  let state = null;
  let desiredPrice = null;
  let savedPrice = null;
  let desiredProduction = null;
  let busy = false;
  const number = value => Number.isFinite(value) ? new Intl.NumberFormat('en-US', {maximumFractionDigits:1}).format(value) : '—';
  // Weight the newest tick heavily, without smoothing the same tick twice.
  const EMA_ALPHA = 0.65;
  let salesEMA = null;
  let earningsEMA = null;
  let salesTick = -1;
  function observeSales(tick, sold, earnings) {
    if (tick < salesTick) { salesEMA = null; earningsEMA = null; salesTick = -1; }
    if (tick <= salesTick || !Number.isFinite(sold)) return;
    salesEMA = salesEMA === null ? sold : EMA_ALPHA * sold + (1 - EMA_ALPHA) * salesEMA;
    if (Number.isFinite(earnings)) {
      earningsEMA = earningsEMA === null ? earnings : EMA_ALPHA * earnings + (1 - EMA_ALPHA) * earningsEMA;
    } else {
      earningsEMA = null;
    }
    salesTick = tick;
  }

  function warnPrice() {
    if (!state) return;
    const cost = state.owned === null ? state.unitCost : state.company.unitCost;
    const below = desiredPrice < cost;
    $('priceWarning').hidden = !below;
    $('priceWarning').textContent = below ? `Below unit cost by ${money(cost - desiredPrice)} per unit.` : '';
  }

  function renderInventory(inventory) {
    if (!inventory) return;
    const colors = {machinery:'#89919b', raw:'#c99952', finished:'#75a1a2', empty:'#f2f2f2'};
    const occupied = inventory.groups.reduce((sum, group) => sum + group.space, 0);
    const groups = [...inventory.groups, {label:'Empty', kind:'empty', space:Math.max(0, inventory.capacity - occupied)}];
    const total = Math.max(inventory.capacity, occupied, 1);
    const boxes = [];
    const perBox = total / 80;
    for (let i = 0; i < 80; i++) {
      const box = document.createElement('span');
      box.className = 'inventory-box';
      let cursor = 0;
      const stops = [];
      for (const group of groups) {
        const start = Math.max(i * perBox, cursor);
        const end = Math.min((i + 1) * perBox, cursor + group.space);
        if (end > start) {
          const from = (start / perBox - i) * 100;
          const to = (end / perBox - i) * 100;
          stops.push(`${colors[group.kind]} ${from}% ${to}%`);
        }
        cursor += group.space;
      }
      box.style.background = stops.length > 1 ? `linear-gradient(to right, ${stops.join(', ')})` : stops.length ? stops[0].split(' ')[0] : colors.empty;
      boxes.push(box);
    }
    $('inventoryBoxes').replaceChildren(...boxes);
    $('storageTotal').textContent = `${number(occupied)} / ${number(inventory.capacity)} spaces`;
    $('inventoryBoxes').setAttribute('aria-label', groups.map(g => `${g.label}: ${number(g.space)} spaces`).join('; '));
    $('inventoryLegend').replaceChildren(...groups.map(group => {
      const item = document.createElement('span');
      const swatch = document.createElement('i');
      swatch.style.background = colors[group.kind];
      item.append(swatch, `${group.label} ${number(group.space)}`);
      return item;
    }));
  }

  function render(next) {
    state = next;
    const owned = state.owned !== null;
    $('reset').hidden = owned;
    $('reset').disabled = busy;
    const price = owned ? state.company.price : state.price;
    $('cash').textContent = money(owned ? state.company.cash : state.cash);
    if (desiredPrice === null) {
      desiredPrice = savedPrice = price;
      $('price').max = Math.max(.1, price * 4).toFixed(2);
      $('price').value = price;
    }
    $('priceValue').textContent = money(desiredPrice);
    $('price').disabled = false;
    if (owned) {
      if (state.company.tick > 0) observeSales(state.company.tick, state.company.sold, state.company.netEarnings);
    } else {
      if (state.period < salesTick) { salesEMA = null; earningsEMA = null; salesTick = -1; }
      for (const row of state.history) {
        if (row.period > salesTick) observeSales(row.period, row.sold, row.profit);
      }
    }
    $('sales').textContent = salesEMA === null ? '—' : number(Math.round(salesEMA));
    $('earnings').textContent = earningsEMA === null ? '—' : money(earningsEMA);
    $('earnings').classList.toggle('negative', earningsEMA !== null && earningsEMA < 0);
    renderInventory(state.inventory);
    warnPrice();
    $('productionControl').hidden = owned;
    if (!owned) {
      const capacity = Math.floor(state.reference.capacity ?? 6000);
      $('production').max = capacity;
      if (desiredProduction === null) desiredProduction = state.productionTarget ?? capacity;
      desiredProduction = Math.min(desiredProduction, capacity);
      $('production').value = desiredProduction;
      $('productionValue').textContent = `${number(desiredProduction)} units / tick`;
      $('production').disabled = false;
      const limited = state.last && state.last.made < (state.productionTarget ?? capacity);
      $('productionLimit').hidden = !limited;
      $('productionLimit').textContent = limited ? 'Production limited by inputs, cash, storage, or below-cost pricing.' : '';
    }
    $('unitCost').textContent = money(owned ? state.company.unitCost : state.unitCost);
    $('status').textContent = owned && !state.reference.running ? 'Paused' : '';
  }

  async function request(path, body) {
    const response = await fetch(`/play-api/${path}`, body ? {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)
    } : {cache:'no-store'});
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(typeof error.detail === 'string' ? error.detail : 'Connection lost. Retrying…');
    }
    return response.json();
  }

  async function update() {
    if (busy || document.hidden) return;
    busy = true;
    $('reset').disabled = true;
    try {
      if (!state) {
        render(await request('state'));
      } else if (state.owned === null) {
        render(await request('action', {kind:'work', amount:desiredPrice, production:desiredProduction, revision:state.revision}));
      } else if (desiredPrice !== savedPrice) {
        const submitted = desiredPrice;
        render(await request('action', {kind:'price', amount:submitted, revision:state.revision}));
        savedPrice = submitted;
      } else {
        render(await request('state'));
      }
    } catch (error) {
      $('status').textContent = error.message;
      // Reconcile after an uncertain write or a stale tab before sending again.
      state = null;
    } finally {
      busy = false;
      $('reset').disabled = !state;
    }
  }

  $('reset').addEventListener('click', async () => {
    if (busy || !state) return;
    busy = true;
    $('reset').disabled = true;
    try {
      const next = await request('action', {kind:'reset', revision:state.revision});
      desiredPrice = savedPrice = null;
      desiredProduction = null;
      salesEMA = null;
      earningsEMA = null;
      salesTick = -1;
      render(next);
      window.scrollTo({top:0, behavior:'instant'});
    } catch (error) {
      $('status').textContent = error.message;
      state = null;
    } finally {
      busy = false;
      $('reset').disabled = !state;
    }
  });

  $('production').addEventListener('input', () => {
    desiredProduction = Number($('production').value);
    $('productionValue').textContent = `${number(desiredProduction)} units / tick`;
  });
  $('price').addEventListener('input', () => {
    desiredPrice = Number($('price').value);
    $('priceValue').textContent = money(desiredPrice);
    warnPrice();
  });
  update();
  setInterval(update, 1000 / 1.3);
})();
