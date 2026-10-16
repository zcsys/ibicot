"""Small scripted workplace, independent of the economy's trading kernel.

SQLite owns player identity, employment, wallet and acquisition records.
The dashboard remains an administrative tool, not a player API.
"""
import copy
import math

import numpy as np
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from ..core import model as M
from . import players
from ..core.config import default_cfg
from ..core.accounting import company_earnings

OFFER_PRICE = 200_000.0
SALARY = 500.0


def market(rt):
    prices = rt.world.t1Price[0::M.NP]
    active = rt.world.t1Operates[0::M.NP].astype(bool)
    prices = prices[active & np.isfinite(prices) & (prices > 0)]
    raw_quotes = rt.world.t0Price[0::len(M.ELEMENTS)]
    raw_quotes = raw_quotes[np.isfinite(raw_quotes) & (raw_quotes > 0)]
    return {'rawPrice': float(np.mean(raw_quotes)) if len(raw_quotes) else rt.cfg['t1MaterialCost'],
            'capacity': M.refinery_capacity(M.PRODUCTS[0], rt.cfg),
            'storage': M.refinery_storage(rt.cfg, 0),
            'machinery': rt.cfg['footprint'][1],
            'conversion': M.conversion_cost(1, rt.cfg),
            'price': round(float(np.mean(prices)), 2) if len(prices) else None,
            'tick': rt.tick, 'running': rt.running, 'product': M.PRODUCTS[0]['name'],
            'label': 'Average asking price'}


def demo_market(tick=0):
    cfg = default_cfg()
    return {'rawPrice': 1.25, 'price': 2.32, 'tick': tick, 'running': True,
            'capacity': M.refinery_capacity(M.PRODUCTS[0], cfg),
            'storage': M.refinery_storage(cfg, 0), 'machinery': cfg['footprint'][1],
            'conversion': M.conversion_cost(1, cfg), 'product': M.PRODUCTS[0]['name'],
            'source': 'scripted', 'label': 'Simulated market price'}


def fluctuate(p):
    tick = p['period'] + 1
    previous = p['reference']
    reference = demo_market(tick)
    raw_target = 1.25 * (1 + .28 * math.sin(tick * .19) + .10 * math.sin(tick * .53))
    sale_target = 2.32 * (1 + .18 * math.sin(tick * .13 + .7) + .07 * math.sin(tick * .37))
    reference['rawPrice'] = round(.55 * previous['rawPrice'] + .45 * raw_target, 4)
    reference['price'] = round(.7 * previous['price'] + .3 * sale_target, 4)
    p['reference'] = reference
    p['marketHistory'].append(dict(reference))
    del p['marketHistory'][:-12]


def new_profile(reference):
    price = reference['price'] or 10.0
    return {'revision': 0, 'period': 0, 'wallet': 0.0, 'cash': 240000.0,
            'price': price, 'unitCost': reference.get('rawPrice', 1.25) + reference.get('conversion', .25),
            'stock': 12000, 'bonusPaid': 0.0, 'salaryPaid': 0.0,
            'last': None, 'history': [], 'marketHistory': [], 'reference': reference,
            'offer': None, 'owned': None, 'receipt': None}


def offer(rt, db):
    claimed = {r[0] for r in db.execute('SELECT company_id FROM ownership WHERE world=?', (players.world_key(),))}
    for cid in range(M.N1):
        if M.T1_FIRM_PRODUCT[cid] == 0 and cid not in claimed and (rt is None or not rt.world.t1Controller[cid]):
            return {'id': cid, 'name': M.t1_firm_name(cid), 'price': OFFER_PRICE,
                    'product': M.PRODUCTS[0]['name']}
    return None


def observe(rt, p):
    if p['owned'] is None:
        if p['reference'].get('source') != 'scripted':
            p['reference'] = demo_market(p['period'])
            p['marketHistory'] = []
        return p
    reference = market(rt)
    if reference['price'] is not None:
        p['reference'] = reference
        points = p['marketHistory']
        if not points or points[-1]['tick'] != reference['tick']:
            points.append(reference)
            del points[:-12]
    return p


def work(p, price, production=None):
    if p['owned'] is not None:
        raise ValueError('Your employment has ended.')
    if not math.isfinite(price) or not .01 <= price <= 1e9:
        raise ValueError('Enter a price between $0.01 and $1,000,000,000.')
    price = round(price, 2)
    # A single C1 T1 recipe: one Organics input produces one feedstock.
    # Counterparty demand remains scripted; no trades enter the shared world.
    ref = p['reference']
    cfg = default_cfg()
    storage = ref.get('storage', M.refinery_storage(cfg, 0))
    machinery = ref.get('machinery', cfg['footprint'][1])
    goods_space = storage - machinery
    target = math.floor(goods_space / 2)
    conversion = ref.get('conversion', .25)
    raw_price = ref.get('rawPrice', 1.25)
    capacity = math.floor(ref.get('capacity', 6000))
    production = p.get('productionTarget', capacity) if production is None else production
    if isinstance(production, bool) or not isinstance(production, int) or not 0 <= production <= capacity:
        raise ValueError('Production must be a whole number within the line capacity.')
    p['productionTarget'] = production
    if ref.get('source') == 'scripted':
        fluctuate(p)
        ref = p['reference']
        raw_price = ref['rawPrice']
    p.setdefault('raw', 0)
    p.setdefault('rawBasis', raw_price)
    p.setdefault('stockBasis', p['unitCost'])
    reference = ref['price'] or 10.0
    demand = math.floor(12000 / (1 + (price / reference) ** 2))
    # Purchase whole wholesale lots, within both cash and physical space.
    buy = max(0, min(target - p['raw'], goods_space - p['raw'] - p['stock'],
                     math.floor(max(0, p['cash'] - SALARY) / raw_price)))
    bought = math.floor(buy / 1000) * 1000
    if bought:
        p['rawBasis'] = (p['raw'] * p['rawBasis'] + bought * raw_price) / (p['raw'] + bought)
        p['raw'] += bought
        p['cash'] -= bought * raw_price
    p['unitCost'] = p['rawBasis'] + conversion
    made = max(0, min(production, p['raw'], target - p['stock'],
                      math.floor(max(0, p['cash'] - SALARY) / max(.01, conversion))))
    if price < p['unitCost']:
        made = 0
    if made:
        p['stockBasis'] = (p['stock'] * p['stockBasis'] + made * p['unitCost']) / (p['stock'] + made)
    p['raw'] -= made
    p['stock'] += made
    p['cash'] -= made * conversion
    sold = min(p['stock'], demand)
    revenue = sold * price
    cogs = sold * p['stockBasis']
    salary = min(SALARY, max(0, p['cash'] + revenue))
    p['cash'] += revenue - salary
    p['wallet'] = round(p['wallet'] + salary, 2)
    p['salaryPaid'] += salary
    p['stock'] -= sold
    p['price'] = price
    p['period'] += 1
    p['last'] = {'period': p['period'], 'price': price, 'sold': sold, 'made': made,
                 'revenue': revenue, 'cogs': cogs, 'bought': bought,
                 'salary': salary, 'profit': revenue - cogs - salary}
    p['history'].append(p['last'])
    del p['history'][:-120]


def bonus(p, amount):
    if p['owned'] is not None or p['period'] < 4:
        raise ValueError('Compensation controls are not available yet.')
    if not math.isfinite(amount) or amount <= 0 or round(amount, 2) > p['cash']:
        raise ValueError('Choose a bonus within the available company cash.')
    amount = round(amount, 2)
    if amount <= 0:
        raise ValueError('The minimum bonus is $0.01.')
    p['cash'] = round(p['cash'] - amount, 2)
    p['wallet'] = round(p['wallet'] + amount, 2)
    p['bonusPaid'] = round(p['bonusPaid'] + amount, 2)


def acquire(rt, p, db, pid):
    if p['owned'] is not None:
        raise ValueError('You already own a company.')
    target = p['offer']
    if target is None or p['wallet'] < target['price']:
        raise ValueError('You need enough personal funds to buy an available company.')
    cid = target['id']
    if rt.world.t1Controller[cid] or db.execute(
            'SELECT 1 FROM ownership WHERE world=? AND tier=? AND company_id=?',
            (players.world_key(), 'T1', cid)).fetchone():
        raise ValueError('That company is no longer available. Refresh for a new offer.')
    price = float(rt.world.t1Price[cid * M.NP])
    db.execute('INSERT INTO ownership(world,tier,company_id,player_id,paid_cents,price) VALUES (?,?,?,?,?,?)',
               (players.world_key(), 'T1', cid, pid, round(target['price'] * 100), price))
    players.post_money(db, pid, 'company_purchase', -target['price'])
    p['wallet'] = round(p['wallet'] - target['price'], 2)
    p['owned'] = cid
    p['receipt'] = {**target, 'tick': rt.tick, 'paid': target['price']}


def public(rt, p):
    result = copy.deepcopy(p)
    cfg = rt.cfg if p['owned'] is not None else default_cfg()
    result['inventory'] = {
        'capacity': M.refinery_storage(cfg, 0),
        'groups': [
            {'label': 'Machinery', 'kind': 'machinery', 'space': cfg['footprint'][1]},
            {'label': 'Raw Organics', 'kind': 'raw', 'space': p.get('raw', 0)},
            {'label': 'Biochemical Feedstock', 'kind': 'finished', 'space': p['stock']},
        ]}
    if p['owned'] is not None:
        cid = p['owned']
        layout = rt._storage_view('t1', cid)
        result['inventory'] = {'capacity': layout['storageCapacitySpace'], 'groups': [
            {'label': 'Machinery', 'kind': 'machinery', 'space': layout['machinerySpace']},
            *[{'label': 'Raw ' + name, 'kind': 'raw', 'space': float(rt.world.raw[cid * len(M.ELEMENTS) + i])}
              for i, name in enumerate(M.ELEMENTS) if rt.world.raw[cid * len(M.ELEMENTS) + i] > 0],
            *[{'label': product['name'], 'kind': 'finished', 'space': float(rt.world.t1Fin[cid * M.NP + i]) * product['complexity']}
              for i, product in enumerate(M.PRODUCTS) if rt.world.t1Operates[cid * M.NP + i]],
        ]}
        result['company'] = {'name': M.t1_firm_name(cid), 'cash': float(rt.world.t1Cash[cid]),
                             'price': float(rt.world.t1Price[cid * M.NP]),
                             'stock': float(rt.world.t1Fin[cid * M.NP]),
                             'sold': float(rt.world.t1Sold[cid * M.NP]),
                             'netEarnings': float(company_earnings(rt.world, rt.cfg, 't1')[cid]) if rt.world.netEarningsAvailable else None,
                             'made': float(rt.lastTickT1Made[cid * M.NP]),
                             'capacity': float(M.refinery_capacity(M.PRODUCTS[0], rt.cfg)),
                             'unitCost': float(rt.world.t1UnitCost[cid * M.NP]), 'tick': rt.tick}
    return result


class Action(BaseModel):
    kind: str
    revision: int = Field(ge=0)
    amount: float = 0
    production: int | None = Field(default=None, ge=0, strict=True)
    name: str = Field(default="", max_length=60)


def create_router(get_runtime):
    router = APIRouter(prefix='/play-api')

    def session(db, request, response, create=False):
        person, token = players.identity(db, request.cookies.get('midbridge_player'), create)
        if token:
            response.set_cookie('midbridge_player', token, httponly=True, samesite='strict',
                                secure=request.url.scheme == 'https', max_age=31536000)
        response.headers['Cache-Control'] = 'no-store'
        p = players.load_employment(db, person['id']) or new_profile(demo_market())
        rt = get_runtime() if p['owned'] is not None else None
        p['wallet'] = person['wallet_cents'] / 100
        observe(rt, p)
        if create and p['owned'] is None:
            if p['offer'] is None or db.execute('SELECT 1 FROM ownership WHERE world=? AND tier=? AND company_id=?', (players.world_key(), 'T1', p['offer']['id'])).fetchone():
                replacement = offer(rt, db)
                if replacement != p['offer']:
                    p['offer'] = replacement
                    p['revision'] += 1
        return rt, p, person

    def view(db, rt, p, person):
        result = public(rt, p)
        result['person'] = {'id': person['id'], 'name': person['name']}
        result['ledger'] = [dict(row) for row in db.execute(
            'SELECT kind,amount_cents,balance_cents,created_at FROM ledger WHERE player_id=? ORDER BY id DESC LIMIT 8', (person['id'],))]
        return result

    def prepare_runtime(request, force=False):
        if force:
            return get_runtime()
        with players.transaction() as db:
            try:
                person, _ = players.identity(db, request.cookies.get('midbridge_player'), False)
            except ValueError:
                return None
            profile = players.load_employment(db, person['id'])
        return get_runtime() if profile and profile['owned'] is not None else None

    @router.get('/state')
    async def state(request: Request, response: Response):
        prepare_runtime(request)
        with players.transaction() as db:
            rt, p, person = session(db, request, response, create=True)
            players.save_employment(db, person['id'], p)
            return view(db, rt, p, person)

    @router.post('/action')
    async def action(body: Action, request: Request, response: Response):
        # No awaits during settlement: world ticks and requests cannot interleave.
        rt = prepare_runtime(request, force=body.kind == 'buy')
        try:
            with players.transaction() as db:
                rt, p, person = session(db, request, response)
                pid = person['id']
                if body.revision != p['revision']:
                    raise HTTPException(409, 'This workplace changed in another tab. Refresh and try again.')
                before = p['wallet']
                if body.kind == 'name':
                    name = body.name.strip()
                    if not name:
                        raise ValueError('Enter your name.')
                    db.execute('UPDATE players SET name=? WHERE id=?', (name, pid))
                    person['name'] = name
                elif body.kind == 'reset':
                    if p['owned'] is not None:
                        raise ValueError('Reset is only available in the demo workplace.')
                    revision = p['revision']
                    players.post_money(db, pid, 'demo_reset', -before)
                    p = new_profile(demo_market())
                    p['revision'] = revision
                    p['offer'] = offer(rt, db)
                elif body.kind == 'work':
                    work(p, body.amount, body.production)
                    players.post_money(db, pid, 'salary', p['wallet'] - before)
                elif body.kind == 'bonus':
                    bonus(p, body.amount)
                    players.post_money(db, pid, 'employment_bonus', p['wallet'] - before)
                elif body.kind == 'buy':
                    rt = get_runtime()
                    acquire(rt, p, db, pid)
                elif body.kind == 'price' and p['owned'] is not None:
                    if not math.isfinite(body.amount) or not .01 <= body.amount <= 1e9:
                        raise ValueError('Enter a valid selling price.')
                    db.execute('UPDATE ownership SET price=? WHERE world=? AND player_id=? AND company_id=?',
                               (round(body.amount, 2), players.world_key(), pid, p['owned']))
                else:
                    raise ValueError('That action is not available.')
                p['revision'] += 1
                players.save_employment(db, pid, p)
            # SQLite commit is the durable authority. Reapply after restart if
            # interrupted between commit and this in-memory projection.
            if rt is not None:
                players.sync_ownership(rt)
            with players.transaction() as db:
                return view(db, rt, p, person)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    return router
