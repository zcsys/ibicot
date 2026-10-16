"""FastAPI + WebSocket service: the Python economy kernel backend for the
browser UI.

Serves the static front-end (HTML + JS) and exposes the dashboard's exact
message protocol over ``/ws``, so ``web/app.js`` runs unchanged via
``web/transport.js``. The tick is CPU-bound and runs in a single server-owned
scheduler task on the event loop (one world, one tick cadence).
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core import model as M
from .persistence import load_checkpoint, save_checkpoint
from .runtime import KernelRuntime, _STATS_DIR
from .scheduler import FIXED_DELAY_S
from .onboarding import create_router
from .players import sync_ownership

ROOT = Path(__file__).resolve().parents[2]  # repository root
WEB_DIR = ROOT / 'web'                       # front-end static files

app = FastAPI(title='Star Business — economy kernel', version='0.1.8')

_runtime: KernelRuntime | None = None


def runtime() -> KernelRuntime:
    global _runtime
    if _runtime is None:
        # The server owns the initial configuration; browser attachment is read-only.
        cfg = json.loads(os.environ.get('ECONOMY_CFG', '{}'))
        candidate = KernelRuntime(cfg)
        sync_ownership(candidate)
        _runtime = candidate
    return _runtime


@app.get('/health')
async def health():
    rt = runtime()
    return {'status': 'ok', 'tick': rt.tick, 'engine': 'python'}


@app.get('/snapshot')
async def snapshot():
    return runtime().publish()


class CheckpointRequest(BaseModel):
    path: str


@app.post('/checkpoint/save')
async def checkpoint_save(req: CheckpointRequest):
    rt = runtime()
    save_checkpoint(req.path, rt.cfg, rt.tick, rt.world, rt.state, rt.checkpoint_metadata())
    return {'ok': True, 'path': req.path, 'tick': rt.tick}


@app.post('/checkpoint/load')
async def checkpoint_load(req: CheckpointRequest):
    global _runtime
    cfg, tick, world, scalars = load_checkpoint(req.path)
    rt = KernelRuntime.__new__(KernelRuntime)
    rt.cfg, rt.world, rt.tick = cfg, world, tick
    rt.month = tick // M.MONTH
    rt.running = False
    rt.mode = 'fixed'
    rt.targetTPS = 30
    metadata = scalars.pop('runtimeMetadata', {})
    rt.state = scalars
    rt.selectedTierControl = 'T1'
    rt.selectedId = 0
    rt.selectedT2Id = 0
    rt.selectedT0Id = 0
    rt.lastSnapshot = None
    rt.lastReportAt = time.monotonic()
    rt.lastReportTick = 0
    rt.analyticsHistory = []
    rt.tier2CompanyHistory = []
    rt.tier2HistoryCompany = -1
    rt.watchedCompanies = {'T0': set(), 'T1': set()}
    rt.watchedCompanyHistory = {}
    rt.tickStats = {'steps': 0, 'lastTickMs': 0.0, 'totalTickMs': 0.0}
    rt.adminAccounting = {'equipmentSinks': 0, 'sequence': 0, 'lastEquipmentReceipt': None}
    rt.playerLicenses = set(M.PROGRESSION_DEFAULTS['startingLicenses'])
    rt.playerHouse = None
    rt.ownershipAccounting = {'licensesSpent': 0, 'houseSpent': 0}
    rt.ownershipEnforced = True
    rt.tier2Query = {'page': 0, 'pageSize': 50, 'search': '', 'sector': '', 'controller': '', 'sort': 'id', 'descending': False}
    rt.statsLog = []
    rt.statsPath = _STATS_DIR / 'generation_run.jsonl'
    rt.targetTick = int(os.environ.get('ECONOMY_MAX_TICK', str(M.TIME['ticksPerGeneration'])) or 0)
    rt._init_admin()
    rt._init_analytics_scratch()
    rt.restore_metadata(metadata)
    rt.publish()
    if _runtime is None:
        _runtime = rt
    else:
        # Keep object identity: connected WebSockets hold this runtime reference.
        # Routes execute on the event loop, so no tick can interleave this swap.
        _runtime.pause()
        _runtime.__dict__.clear()
        _runtime.__dict__.update(rt.__dict__)
    sync_ownership(_runtime)
    _runtime.publish()
    return {'ok': True, 'path': req.path, 'tick': tick}


# Dashboard saves are named, immutable slots; the existing path-based API remains available.
DASHBOARD_SAVE_DIR = Path(os.environ.get('ECONOMY_SAVE_DIR', str(ROOT / 'saves')))

class DashboardSaveRequest(BaseModel):
    name: str

@app.get('/dashboard-saves')
async def dashboard_saves():
    entries = []
    for folder in DASHBOARD_SAVE_DIR.glob('*'):
        if not folder.is_dir() or not (folder / 'state.npz').is_file():
            continue
        try:
            uuid.UUID(folder.name)
            meta = json.loads((folder / 'state.json').read_text())
            entries.append(dict(id=folder.name, name=meta.get('saveName', 'Saved simulation'),
                                tick=meta['tick'], savedAt=(folder / 'state.json').stat().st_mtime))
        except (ValueError, KeyError, OSError):
            continue
    return sorted(entries, key=lambda x: x['savedAt'], reverse=True)

@app.post('/dashboard-saves')
async def dashboard_save(req: DashboardSaveRequest):
    name = req.name.strip()
    if not name or len(name) > 100:
        raise HTTPException(400, 'Enter a save name of 1–100 characters.')
    DASHBOARD_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    save_id = str(uuid.uuid4())
    temporary = DASHBOARD_SAVE_DIR / ('.' + save_id)
    temporary.mkdir()
    try:
        rt = runtime()
        stem = temporary / 'state'
        save_checkpoint(str(stem), rt.cfg, rt.tick, rt.world, rt.state, rt.checkpoint_metadata())
        meta = json.loads(stem.with_suffix('.json').read_text())
        meta['saveName'] = name
        stem.with_suffix('.json').write_text(json.dumps(meta))
        temporary.rename(DASHBOARD_SAVE_DIR / save_id)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return dict(id=save_id, name=name, tick=rt.tick)

@app.post('/dashboard-saves/{save_id}/load')
async def dashboard_load(save_id: str):
    try:
        save_id = str(uuid.UUID(save_id))
    except ValueError:
        raise HTTPException(404, 'Save not found.')
    stem = DASHBOARD_SAVE_DIR / save_id / 'state'
    if not stem.with_suffix('.json').is_file() or not stem.with_suffix('.npz').is_file():
        raise HTTPException(404, 'Save not found.')
    try:
        result = await checkpoint_load(CheckpointRequest(path=str(stem)))
    except (ValueError, AssertionError, KeyError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc
    await _manager.broadcast({'type': 'snapshot', 'data': runtime().lastSnapshot})
    return dict(tick=result['tick'], paused=True)


def _dispatch(rt: KernelRuntime, msg: dict) -> list[dict]:
    """Return the list of messages to send back for a command."""
    mtype = msg.get('type')
    if mtype == 'init':
        return [{'type': 'snapshot', 'data': rt.publish()}]
    if mtype == 'reset':
        rt.reset(msg.get('cfg') or rt.cfg)
        sync_ownership(rt)
        return [{'type': 'snapshot', 'data': rt.publish()}]
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
                             'grossProfit', 'netProfit', 'reliability') else 'id',
                         'descending': bool(msg.get('descending'))}
        return [{'type': 'snapshot', 'data': rt.publish()}]
    return [{'type': 'error', 'message': f'Unknown message type: {mtype}'}]


class _ConnectionManager:
    """All attached dashboard sockets; the scheduler broadcasts to all of them."""

    def __init__(self):
        self._ws: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        self._ws.add(ws)

    def disconnect(self, ws: WebSocket):
        self._ws.discard(ws)

    async def broadcast(self, message: dict):
        payload = None
        for ws in list(self._ws):
            try:
                if payload is None:
                    # Match Starlette's send_json wire representation, once
                    # for the entire broadcast rather than once per dashboard.
                    payload = json.dumps(message, separators=(',', ':'), ensure_ascii=False)
                await ws.send_text(payload)
            except Exception:  # noqa: BLE001 — drop sockets that died mid-send
                self._ws.discard(ws)


_manager = _ConnectionManager()
_scheduler_task: asyncio.Task | None = None


async def _scheduler():
    """The single server-owned run loop: one world, one tick cadence.

    ``rt.step()`` stays on the event loop so a checkpoint swap (which replaces
    the runtime's ``__dict__`` in place) can never interleave with a tick.
    """
    while True:
        rt = runtime()
        if not rt.running:
            await asyncio.sleep(0.05)
            continue
        started = time.monotonic()
        rt.step()
        rt.publish()
        await _manager.broadcast({'type': 'snapshot', 'data': rt.lastSnapshot})
        delay = 0.01 if rt.mode == 'max' else max(0.02, FIXED_DELAY_S - (time.monotonic() - started))
        await asyncio.sleep(delay)


def _ensure_scheduler():
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler())


@app.websocket('/ws')
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    rt = runtime()
    await _manager.connect(ws)
    try:
        while True:
            msg = await ws.receive_json()
            if msg.get('type') == 'run':
                rt.run(msg.get('mode') or 'fixed')
                _ensure_scheduler()
                await ws.send_json({'type': 'snapshot', 'data': rt.publish()})
                continue
            try:
                for resp in _dispatch(rt, msg):
                    await ws.send_json(resp)
            except Exception as exc:  # noqa: BLE001
                await ws.send_json({'type': 'error', 'message': str(exc)})
    except WebSocketDisconnect:
        pass
    finally:
        _manager.disconnect(ws)


app.include_router(create_router(runtime))

# Static front-end (mounted last so API/WS routes win).
app.mount('/', StaticFiles(directory=str(WEB_DIR), html=True), name='static')
