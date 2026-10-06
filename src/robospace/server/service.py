"""FastAPI + WebSocket service: the Python economy kernel backend for the
browser UI.

Serves the static front-end (HTML + JS) and exposes the JS worker's exact
message protocol over ``/ws``, so ``phase0_economy_engine_app.js`` runs
unchanged via the ``worker_bridge.js`` shim.  The tick is CPU-bound and runs
inline in the WebSocket handler (single-user local PoC), mirroring the
worker's single-threaded model.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core import model as M
from .persistence import load_checkpoint, save_checkpoint
from .runtime import KernelRuntime

ROOT = Path(__file__).resolve().parents[3]  # repository root
WEB_DIR = ROOT / 'web'                       # front-end static files

app = FastAPI(title='Robotic Space Generation — economy kernel', version='0.1.0')

_runtime: KernelRuntime | None = None


def runtime() -> KernelRuntime:
    global _runtime
    if _runtime is None:
        # Bootstrap with a tiny population so first connect is instant; the UI's
        # `init` message then resets to whatever population its config selects.
        cfg = json.loads(os.environ.get('ROBOSPACE_CFG', '{"endUserCount":100,"t2FirmCount":200}'))
        _runtime = KernelRuntime(cfg)
    return _runtime


@app.get('/health')
def health():
    rt = runtime()
    return {'status': 'ok', 'tick': rt.tick, 'engine': 'python'}


@app.get('/snapshot')
def snapshot():
    return runtime().publish()


class CheckpointRequest(BaseModel):
    path: str


@app.post('/checkpoint/save')
def checkpoint_save(req: CheckpointRequest):
    rt = runtime()
    save_checkpoint(req.path, rt.cfg, rt.tick, rt.W, rt.state)
    return {'ok': True, 'path': req.path, 'tick': rt.tick}


@app.post('/checkpoint/load')
def checkpoint_load(req: CheckpointRequest):
    global _runtime
    cfg, tick, W, scalars = load_checkpoint(req.path)
    rt = KernelRuntime.__new__(KernelRuntime)
    rt.cfg, rt.W, rt.tick = cfg, W, tick
    rt.month = tick // 30
    rt.running = False
    rt.mode = 'fixed'
    rt.targetTPS = 30
    rt.state = scalars
    rt.selectedTierControl = 'T1'
    rt.selectedId = 0
    rt.selectedT2Id = 0
    rt.lastSnapshot = None
    rt.lastReportAt = time.monotonic()
    rt.lastReportTick = 0
    rt.analyticsHistory = []
    rt.tier2CompanyHistory = []
    rt.tier2HistoryCompany = -1
    rt.watchedCompanies = {'T0': set(), 'T1': set()}
    rt.watchedCompanyHistory = {}
    rt.workerStats = {'steps': 0, 'lastTickMs': 0.0, 'totalTickMs': 0.0}
    rt.adminAccounting = {'equipmentSinks': 0, 'sequence': 0, 'lastEquipmentReceipt': None}
    rt.playerLicenses = set(M.PROGRESSION_DEFAULTS['startingLicenses'])
    rt.playerHouse = None
    rt.ownershipAccounting = {'licensesSpent': 0, 'houseSpent': 0}
    rt.ownershipEnforced = True
    rt.tier2Query = {'page': 0, 'pageSize': 50, 'search': '', 'sector': '', 'controller': '', 'sort': 'id', 'descending': False}
    rt._init_admin()
    rt._init_analytics_scratch()
    _runtime = rt
    return {'ok': True, 'path': req.path, 'tick': tick}


def _dispatch(rt: KernelRuntime, msg: dict) -> list[dict]:
    """Return the list of messages to send back for a command."""
    mtype = msg.get('type')
    if mtype == 'init':
        rt.reset(msg.get('cfg') or rt.cfg)
        return [{'type': 'snapshot', 'data': rt.lastSnapshot}]
    if mtype == 'reset':
        rt.reset(msg.get('cfg') or rt.cfg)
        return [{'type': 'snapshot', 'data': rt.lastSnapshot}]
    if mtype == 'pause':
        rt.pause()
        return [{'type': 'snapshot', 'data': rt.publish()}]
    if mtype == 'step':
        if not rt.running:
            rt.step()
        return [{'type': 'snapshot', 'data': rt.publish()}]
    if mtype == 'applyConfig':
        rt.apply_config(msg.get('cfg') or {})
        return [{'type': 'snapshot', 'data': rt.lastSnapshot}]
    if mtype == 'select':
        rt.select(msg.get('tier'), msg.get('id'))
        return [{'type': 'snapshot', 'data': rt.lastSnapshot}]
    if mtype == 'companyDetail':
        return [{'type': 'companyDetail', 'data': rt.company_detail(msg.get('tier'), msg.get('id'))}]
    if mtype == 'watchCompanies':
        rt.watch_companies(msg.get('watches'))
        return [{'type': 'snapshot', 'data': rt.lastSnapshot}]
    if mtype == 'setOwnershipEnforcement':
        rt.set_ownership_enforcement(msg.get('enforced'))
        return [{'type': 'snapshot', 'data': rt.lastSnapshot}]
    if mtype == 'buyLicense':
        return [{'type': 'snapshot', 'data': rt.publish()}, rt.buy_license(msg.get('tier'))]
    if mtype == 'foundHouse':
        return [{'type': 'snapshot', 'data': rt.publish()}, rt.found_house(msg.get('name'))]
    if mtype == 'player':
        rt.player(msg.get('tier'), msg.get('id'), msg.get('code'), msg.get('price'),
                  msg.get('online'), msg.get('controller'))
        return [{'type': 'snapshot', 'data': rt.lastSnapshot}]
    if mtype == 'buyEquipment':
        try:
            snap = rt.buy_equipment(msg.get('tier'), msg.get('id'), msg.get('code'))
            return [{'type': 'snapshot', 'data': snap}, {'type': 'equipmentResult', 'ok': True}]
        except Exception as exc:  # noqa: BLE001
            return [{'type': 'equipmentResult', 'ok': False, 'msg': str(exc)}]
    if mtype == 'tier2Query':
        rt.tier2Query = {'page': max(0, int(msg.get('page') or 0)), 'pageSize': 50,
                         'search': str(msg.get('search') or '')[:100],
                         'sector': str(msg.get('sector') or ''),
                         'controller': str(msg.get('controller') or ''),
                         'sort': msg.get('sort') if msg.get('sort') in (
                             'id', 'name', 'sector', 'cash', 'equity', 'inventory', 'raw',
                             'finished', 'capacity', 'utilization', 'margin', 'revenue',
                             'grossProfit', 'reliability') else 'id',
                         'descending': bool(msg.get('descending'))}
        return [{'type': 'snapshot', 'data': rt.publish()}]
    return [{'type': 'error', 'message': f'Unknown message type: {mtype}'}]


@app.websocket('/ws')
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    rt = runtime()
    try:
        while True:
            msg = await ws.receive_json()
            mtype = msg.get('type')
            if mtype == 'run':
                rt.run(msg.get('mode') or 'fixed')
                await ws.send_json({'type': 'snapshot', 'data': rt.publish()})
                await _run_loop(ws, rt)
                continue
            try:
                for resp in _dispatch(rt, msg):
                    await ws.send_json(resp)
            except Exception as exc:  # noqa: BLE001
                await ws.send_json({'type': 'error', 'message': str(exc)})
    except WebSocketDisconnect:
        pass


async def _run_loop(ws: WebSocket, rt: KernelRuntime):
    """Tick + publish + push snapshots, polling for control messages."""
    while rt.running:
        if rt.mode == 'max':
            # Run flat-out: one tick + one snapshot per iteration, so the UI data
            # updates at the tick rate rather than a throttled batch cadence.
            rt.step()
            rt.publish()
            await ws.send_json({'type': 'snapshot', 'data': rt.lastSnapshot})
            delay = 0.01
        else:
            started = time.monotonic()
            rt.step()
            rt.publish()
            await ws.send_json({'type': 'snapshot', 'data': rt.lastSnapshot})
            # Nominal 2 ticks/s: wait the remainder of a 500 ms period.
            delay = max(0.02, 0.5 - (time.monotonic() - started))
        try:
            pending = await asyncio.wait_for(ws.receive_json(), timeout=delay)
        except asyncio.TimeoutError:
            continue
        if pending.get('type') == 'run':
            # Switch mode on the fly (Run ⇄ Run Max) without leaving the loop.
            rt.run(pending.get('mode') or 'fixed')
            continue
        if pending.get('type') in ('pause', 'reset', 'init'):
            for resp in _dispatch(rt, pending):
                await ws.send_json(resp)
            return
        try:
            for resp in _dispatch(rt, pending):
                await ws.send_json(resp)
        except Exception as exc:  # noqa: BLE001
            await ws.send_json({'type': 'error', 'message': str(exc)})
    await ws.send_json({'type': 'snapshot', 'data': rt.publish()})


# Static front-end (mounted last so API/WS routes win).
app.mount('/', StaticFiles(directory=str(WEB_DIR), html=True), name='static')
