(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const money = n => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD'}).format(n);
  const number = n => new Intl.NumberFormat('en-US').format(n);
  let state, busy = false;
  const text = (id, value) => { $(id).textContent = value; };
  const show = (id, visible) => { $(id).hidden = !visible; };
  function notice(message, error = false) { text('notice', message); $('notice').classList.toggle('error', error); }
  function renderMarket(reference, history) {
    text('reference', reference.price == null ? 'Unavailable' : money(reference.price));
    text('marketProduct', reference.product);
    text('marketSource', `Colony market · tick ${number(reference.tick)}${reference.running ? "" : " · paused"}`);
    const values = history.map(p => p.price);
    const low = Math.min(...values), high = Math.max(...values), span = high - low || 1;
    const coords = values.map((v, i) => `${values.length < 2 ? 140 : 5 + i / (values.length - 1) * 270},${55 - (v - low) / span * 45}`);
    $('spark').replaceChildren();
    if (coords.length > 1) {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      line.setAttribute('points', coords.join(' ')); line.setAttribute('fill', 'none');
      line.setAttribute('stroke', '#d7ed92'); line.setAttribute('stroke-width', '2'); $('spark').append(line);
    }
    text('marketTrend', values.length < 2 ? 'One observation so far. More market history appears as the colony advances.' : `${values.at(-1) >= values[0] ? '↑' : '↓'} ${money(Math.abs(values.at(-1) - values[0]))} since your first recent observation.`);
  }
  function render(s) {
    state = s;
    const owned = s.owned !== null, last = s.last;
    show('welcome', s.person.name === 'New arrival');
    show('workspace', s.person.name !== 'New arrival');
    text('personLabel', s.person.name); text('initial', s.person.name[0].toUpperCase());
    text('role', owned ? 'Company owner' : s.period >= 4 ? 'Manager · compensation authorized' : s.period >= 2 ? 'Pricing associate · financial access' : 'Pricing associate');
    text('wallet', money(s.wallet));
    text('companyCash', money(owned ? s.company.cash : s.cash));
    text('stock', number(owned ? s.company.stock : s.stock));
    text('sold', owned ? `#${number(s.company.tick)}` : last ? number(last.sold) : '—');
    text('salesLabel', owned ? 'Colony tick' : 'Last period sold');
    text('period', owned ? 'Operating company' : `Work period ${s.period + 1}`);
    text('product', `${s.reference.product} · Refining`);
    text('companyName', owned ? s.company.name : 'Meridian Works');
    text('companyKind', owned ? 'YOUR COMPANY' : 'YOUR EMPLOYER');
    $('price').value = (owned ? s.company.price : s.price).toFixed(2);
    text('workButton', owned ? 'Save selling price →' : 'Complete work period →');
    text('priceHint', owned ? 'This price applies to your company in the shared colony economy.' : 'Your quote applies to the next work period. Operations are handled for you.');
    text('headline', owned ? 'Your name. Your business.' : 'A desk. A price. A beginning.');
    text('chapter', owned ? 'PHASE 1 / COMPANY OWNER' : 'PHASE 0 / YOUR FIRST POSITION');
    text('introCopy', owned ? 'You’ve bought an operating company. Its cash, stock, and selling price now come from the colony economy.' : 'You’re on the pricing desk at Meridian Works. Set your asking price, then see how the next work period goes.');
    $('navWork').classList.toggle('active', !owned); $('navOwn').classList.toggle('active', owned);
    show('finances', !owned && s.period >= 2); show('compensation', !owned && s.period >= 4);
    show('historyCard', !owned && s.period >= 2); show('outcome', !owned && !!last);
    if (last) {
      text('outcome', `${number(last.sold)} units sold at ${money(last.price)}. ${money(last.salary)} salary paid to your personal account.${s.cash < s.unitCost ? ' Company cash is too low to replenish stock.' : ''}`);
      for (const id of ['revenue','cogs','salary','profit']) text(id, money(last[id]));
    }
    $('bonus').max = s.cash.toFixed(2);
    text('bonusHint', `${money(s.cash)} available in company cash. Bonuses paid to date: ${money(s.bonusPaid)}.`);
    $('history').replaceChildren(...[...s.history].reverse().map(row => {
      const tr = document.createElement('tr');
      for (const value of [row.period, money(row.price), number(row.sold), money(row.profit)]) {
        const td = document.createElement('td'); td.textContent = value; tr.append(td);
      } return tr;
    }));
    renderMarket(s.reference, s.marketHistory);
    try { localStorage.setItem('midbridge-market-brief', JSON.stringify({reference:s.reference, history:s.marketHistory})); } catch {}
    show('acquisition', !owned); show('receipt', owned);
    text('walletCaption', owned ? 'Employment ended' : 'Salary per work period');
    text('walletSalary', owned ? 'Owner' : money(500));
    if (owned) text('receiptCopy', `${s.receipt.name} acquired for ${money(s.receipt.paid)}. The purchase is recorded in your personal account.`);
    if (s.offer) {
      text('targetName', s.offer.name); text('targetProduct', s.offer.product);
      text('targetPrice', money(s.offer.price));
      $('progress').max = s.offer.price; $('progress').value = Math.min(s.wallet, s.offer.price);
      text('remaining', s.wallet >= s.offer.price ? 'Your personal funds cover this purchase.' : `${money(s.offer.price - s.wallet)} to go.`);
    } else { text('targetName', 'No companies available'); text('remaining', 'Check back after the market changes.'); }
    $('buy').disabled = busy || owned || !s.offer || s.wallet < s.offer.price;
    $('ledger').replaceChildren(...s.ledger.map(row => {
      const div = document.createElement('div'), label = document.createElement('span'), amount = document.createElement('strong');
      label.textContent = ({salary:'Salary', employment_bonus:'Performance bonus', company_purchase:'Company purchase'})[row.kind] || row.kind;
      amount.textContent = money(row.amount_cents / 100); div.append(label,amount); return div;
    }));
    if (!s.ledger.length) text('ledger', 'Your first payment will appear here.');
    text('connection', '● Connected'); text('saveStatus', 'Progress saved · Personal account');
  }
  async function load() {
    if (busy) return;
    try {
      const response = await fetch('/play-api/state', {cache:'no-store'});
      if (!response.ok) throw new Error('The colony service is unavailable. Try reconnecting.');
      render(await response.json()); notice('');
    } catch (error) {
      notice(error.message, true); text('connection', '○ Offline');
      text('saveStatus', 'Connection lost. Reconnect before making changes.');
      document.querySelectorAll('form button, #buy').forEach(b => b.disabled = true);
      try { const cached = JSON.parse(localStorage.getItem('midbridge-market-brief')); if(cached) { renderMarket(cached.reference, cached.history); text('marketSource', `Cached colony reference · tick ${cached.reference.tick}`); } } catch {}
    }
  }
  async function act(kind, amount = 0, name = '') {
    if (busy || !state) return;
    busy = true; document.querySelectorAll('button').forEach(b => b.disabled = true);
    try {
      const response = await fetch('/play-api/action', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind, amount, name, revision:state.revision})});
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Check the amount and try again.');
      render(data);
      notice(kind === 'buy' ? 'Acquisition complete. Welcome to ownership.' : kind === 'bonus' ? 'Bonus paid to your personal account.' : kind === 'name' ? 'Welcome to Meridian Works.' : kind === 'price' ? 'Selling price saved.' : data.period === 2 ? 'Financial statements are now available.' : data.period === 4 ? 'Your remit now includes compensation.' : 'Work period complete.');
      if (kind === 'bonus') $('bonus').value = '';
    } catch (error) { notice(error.message, true); }
    finally {
      busy = false; document.querySelectorAll('button').forEach(b => b.disabled = false);
      $('buy').disabled = !state.offer || state.owned !== null || state.wallet < state.offer.price;
    }
  }
  $('nameForm').addEventListener('submit', e => {e.preventDefault(); act('name',0,$('personName').value);});
  $('priceForm').addEventListener('submit', e => {e.preventDefault(); act(state.owned === null ? 'work' : 'price', Number($('price').value));});
  $('bonusForm').addEventListener('submit', e => {e.preventDefault(); act('bonus',Number($('bonus').value));});
  $('buy').addEventListener('click', () => act('buy'));
  $('refresh').addEventListener('click', async () => {await load(); if(state) {document.querySelectorAll('form button').forEach(b => b.disabled = false);}});
  load();
})();
