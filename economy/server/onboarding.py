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

OFFER_PRICE = 200_000.0
SALARY = 500.0


def market(rt):
    prices = rt.world.t1Price[0::M.NP]
    active = rt.world.t1Operates[0::M.NP].astype(bool)
    prices = prices[active & np.isfinite(prices) & (prices > 0)]
    return {'price': round(float(np.mean(prices)), 2) if len(prices) else None,
            'tick': rt.tick, 'running': rt.running, 'product': M.PRODUCTS[0]['name'],
            'label': 'Average asking price'}


def new_profile(reference):
    price = reference['price'] or 10.0
    return {'revision': 0, 'period': 0, 'wallet': 0.0, 'cash': 240000.0,
            'price': price, 'unitCost': round(price * .55, 2),
            'stock': 12000, 'bonusPaid': 0.0, 'salaryPaid': 0.0,
            'last': None, 'history': [], 'marketHistory': [], 'reference': reference,
            'offer': None, 'owned': None, 'receipt': None}


def offer(rt, db):
    claimed = {r[0] for r in db.execute('SELECT company_id FROM ownership WHERE world=?', (players.world_key(),))}
    for cid in range(M.N1):
        if rt.world.t1Operates[cid * M.NP] and not rt.world.t1Controller[cid] and cid not in claimed:
            return {'id': cid, 'name': M.t1_firm_name(cid), 'price': OFFER_PRICE,
                    'product': M.PRODUCTS[0]['name']}
    return None


def observe(rt, p):
    reference = market(rt)
    if reference['price'] is not None:
        p['reference'] = reference
        points = p['marketHistory']
        if not points or points[-1]['tick'] != reference['tick']:
            points.append(reference)
            del points[:-12]
    return p


def work(p, price):
    if p['owned'] is not None:
        raise ValueError('Your employment has ended.')
    if not math.isfinite(price) or not .01 <= price <= 1e9:
        raise ValueError('Enter a price between $0.01 and $1,000,000,000.')
    price = round(price, 2)
    # Deliberately scripted demand, not live orders or a per-player economy.
    reference = p['reference']['price'] or 10.0
    demand = math.floor(12000 / (1 + (price / reference) ** 2))
    made = min(max(0, 12000 - p['stock']), math.floor(max(0, p['cash'] - SALARY) / max(.01, p['unitCost'])))
    production_cost = round(made * p['unitCost'], 2)
    stock = p['stock'] + made
    sold = min(stock, demand)
    revenue = round(sold * price, 2)
    salary = min(SALARY, max(0, round(p['cash'] - production_cost + revenue, 2)))
    p['cash'] = round(p['cash'] - production_cost + revenue - salary, 2)
    p['wallet'] = round(p['wallet'] + salary, 2)
    p['salaryPaid'] += salary
    p['stock'] = stock - sold
    p['price'] = price
    p['period'] += 1
    p['last'] = {'period': p['period'], 'price': price, 'sold': sold, 'made': made,
                 'revenue': revenue, 'cogs': round(sold * p['unitCost'], 2),
                 'salary': salary, 'profit': round(revenue - sold * p['unitCost'] - salary, 2)}
    p['history'].append(p['last'])
    del p['history'][:-12]


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
    if p['owned'] is not None:
        cid = p['owned']
        result['company'] = {'name': M.t1_firm_name(cid), 'cash': float(rt.world.t1Cash[cid]),
                             'price': float(rt.world.t1Price[cid * M.NP]),
                             'stock': float(rt.world.t1Fin[cid * M.NP]), 'tick': rt.tick}
    return result


class Action(BaseModel):
    kind: str
    revision: int = Field(ge=0)
    amount: float = 0
    name: str = Field(default="", max_length=60)


def create_router(get_runtime):
    router = APIRouter(prefix='/play-api')

    def session(db, request, response, create=False):
        rt = get_runtime()
        person, token = players.identity(db, request.cookies.get('midbridge_player'), create)
        if token:
            response.set_cookie('midbridge_player', token, httponly=True, samesite='strict',
                                secure=request.url.scheme == 'https', max_age=31536000)
        response.headers['Cache-Control'] = 'no-store'
        p = players.load_employment(db, person['id']) or new_profile(market(rt))
        p['wallet'] = person['wallet_cents'] / 100
        observe(rt, p)
        if create and p['owned'] is None:
            if p['offer'] is None or rt.world.t1Controller[p['offer']['id']]:
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

    @router.get('/state')
    async def state(request: Request, response: Response):
        # Initialize the runtime before acquiring the database lock.
        get_runtime()
        with players.transaction() as db:
            rt, p, person = session(db, request, response, create=True)
            players.save_employment(db, person['id'], p)
            return view(db, rt, p, person)

    @router.post('/action')
    async def action(body: Action, request: Request, response: Response):
        # No awaits during settlement: world ticks and requests cannot interleave.
        rt = get_runtime()
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
                elif body.kind == 'work':
                    work(p, body.amount)
                    players.post_money(db, pid, 'salary', p['wallet'] - before)
                elif body.kind == 'bonus':
                    bonus(p, body.amount)
                    players.post_money(db, pid, 'employment_bonus', p['wallet'] - before)
                elif body.kind == 'buy':
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
            players.sync_ownership(rt)
            with players.transaction() as db:
                return view(db, rt, p, person)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    return router
