"""Versioned, phase-specific seller observations; no demand inference or trades.

Each channel has fixed quotes and nonincreasing stock during its phase. Seller
columns are stable numeric identities, never display names. An absent offer or
zero discovery count is not evidence of zero latent demand.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from economy.core import model as M

VERSION = 1
FLOAT_FIELDS = ('quote', 'sold', 'closingStock')
COUNT_FIELDS = ('discoveries', 'fundedChecks', 'shortChecks')
ROW_FIELDS = (*FLOAT_FIELDS, *COUNT_FIELDS, 'offered')
ARRAY_FIELDS = (*ROW_FIELDS, 'ticks', 'product', 'owner')


def catalog_identity():
    data = dict(revision=M.CATALOG_REVISION, raw=M.ELEMENTS,
                t1=[p['catalogId'] for p in M.PRODUCTS],
                t2=[p['catalogId'] for p in M.T2_PRODUCTS])
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _integer(value, minimum=0):
    return (not isinstance(value, (bool, np.bool_))
            and isinstance(value, (int, np.integer)) and value >= minimum)


def _identities(values):
    values = np.asarray(values)
    if values.ndim != 1 or values.dtype.kind not in 'iu' or np.any(values < 0) or np.any(values > np.iinfo(np.int64).max):
        raise ValueError('seller identities must be nonnegative integer vectors')
    return values.astype(np.int64)


class SellerHistory:
    def __init__(self, window):
        if not _integer(window, 1):
            raise ValueError('history window must be a positive integer')
        self.window = int(window)
        self.catalog = catalog_identity()
        self.channels = {}

    def record(self, channel, tick, product, owner, offered, opening, closing,
               quote, sold, exposure, lot=1):
        if not isinstance(channel, str) or not channel or not _integer(tick, 1) or not _integer(lot, 1):
            raise ValueError('invalid phase history identity/timing')
        product = _identities(product)
        owner = _identities(owner)
        n = len(product)
        offered = np.asarray(offered)
        opening, closing, quote, sold, exposure = [np.asarray(x, dtype=np.float64)
            for x in (opening, closing, quote, sold, exposure)]
        if (owner.shape != (n,) or any(x.shape != (n,) for x in (offered, opening, closing, quote, sold))
                or exposure.shape != (3, n)):
            raise ValueError('invalid phase history dimensions')
        if np.any((offered != 0) & (offered != 1)):
            raise ValueError('invalid offered mask')
        offered = offered.astype(bool)
        if any(np.any(~np.isfinite(x)) or np.any(x < 0) for x in (opening, closing, sold, exposure)):
            raise ValueError('invalid phase resources or exposure')
        if (np.any(exposure != np.floor(exposure)) or np.any(exposure > np.iinfo(np.uint32).max)
                or np.any(exposure[2] > exposure[1]) or np.any(exposure[1] > exposure[0])):
            raise ValueError('invalid exposure counts')
        if np.any(~np.isfinite(quote[offered])) or np.any(quote[offered] <= 0):
            raise ValueError('invalid offered quote')
        if np.any(sold[~offered]) or np.any(exposure[:, ~offered]):
            raise ValueError('activity on a nonoffered seller')
        tolerance = 1e-6 + 1e-12 * np.maximum(np.abs(opening), np.abs(closing))
        if np.any(np.abs(opening - closing - sold) > tolerance):
            raise ValueError('phase stock/sales do not reconcile')
        if np.any((sold > 0) & (exposure[1] == 0)):
            raise ValueError('sale without a positive funded supplier check')
        old = self.channels.get(channel)
        if old is not None:
            if tick != old['lastTick'] + 1:
                raise ValueError('duplicate, missing or out-of-order phase tick')
            size = len(old['product'])
            if (n < size or not np.array_equal(product[:size], old['product'])
                    or not np.array_equal(owner[:size], old['owner']) or lot != old['lot']):
                raise ValueError('seller identity/lot changed; reset or explicit migration required')
        else:
            size = 0
            old = dict(product=np.empty(0, dtype=np.int64), owner=np.empty(0, dtype=np.int64),
                       lot=int(lot), ticks=np.zeros(self.window, dtype=np.int64),
                       cursor=0, lastTick=int(tick) - 1)
            for name in FLOAT_FIELDS:
                old[name] = np.empty((self.window, 0), dtype=np.float64)
            for name in COUNT_FIELDS:
                old[name] = np.empty((self.window, 0), dtype=np.uint32)
            old['offered'] = np.empty((self.window, 0), dtype=np.uint8)
        if n != size:
            for name in ROW_FIELDS:
                expanded = np.zeros((self.window, n), dtype=old[name].dtype)
                if name == 'quote':
                    expanded.fill(np.nan)
                expanded[:, :size] = old[name]
                old[name] = expanded
            old['product'] = product.copy()
            old['owner'] = owner.copy()
        pos = old['cursor']
        old['quote'][pos] = np.where(offered, quote, np.nan)
        old['sold'][pos] = sold
        old['closingStock'][pos] = closing
        for i, name in enumerate(COUNT_FIELDS):
            old[name][pos] = exposure[i]
        old['offered'][pos] = offered
        old['ticks'][pos] = tick
        old['lastTick'] = int(tick)
        old['cursor'] = (pos + 1) % self.window
        self.channels[channel] = old

    def view(self, channel):
        state = self.channels[channel]
        order = np.flatnonzero(state['ticks'] > 0)
        order = order[np.argsort(state['ticks'][order])]
        result = {name: state[name][order].copy() for name in (*ROW_FIELDS, 'ticks')}
        result.update(product=state['product'].copy(), owner=state['owner'].copy(), lot=state['lot'])
        return result

    def save(self, path):
        """Write a single exclusive NPZ sidecar, including its schema metadata."""
        data = {}
        channels = []
        for i, (name, state) in enumerate(sorted(self.channels.items())):
            self._validate_state(name, state)
            channels.append(dict(name=name, cursor=state['cursor'], lastTick=state['lastTick'], lot=state['lot']))
            for field in ARRAY_FIELDS:
                data[f'c{i}_{field}'] = state[field]
        meta = dict(version=VERSION, window=self.window, catalog=self.catalog, channels=channels)
        data['metadata'] = np.frombuffer(json.dumps(meta, sort_keys=True).encode(), dtype=np.uint8)
        path = Path(path)
        # Exclusive open never replaces evidence. Remove only this invocation's
        # partial output if serialization fails; metadata cannot detach from data.
        with path.open('xb') as stream:
            try:
                np.savez_compressed(stream, **data)
            except BaseException:
                path.unlink()
                raise

    def _validate_state(self, name, state):
        if (not isinstance(name, str) or not name or not _integer(state['cursor'])
                or state['cursor'] >= self.window or not _integer(state['lastTick'], 1)
                or not _integer(state['lot'], 1)):
            raise ValueError('invalid seller-history metadata')
        n = len(state['product'])
        dtypes = {**{f: np.dtype('float64') for f in FLOAT_FIELDS},
                  **{f: np.dtype('uint32') for f in COUNT_FIELDS}, 'offered': np.dtype('uint8'),
                  **{f: np.dtype('int64') for f in ('ticks', 'product', 'owner')}}
        for field in ARRAY_FIELDS:
            shape = (self.window, n) if field in ROW_FIELDS else ((self.window,) if field == 'ticks' else (n,))
            if state[field].shape != shape or state[field].dtype != dtypes[field]:
                raise ValueError('seller-history array shape/dtype mismatch')
        _identities(state['product'])
        _identities(state['owner'])
        ticks = state['ticks']
        # Cursor points at the oldest row (or the next unused row). This catches
        # valid-looking ticks with a corrupt cursor that would overwrite recent data.
        rotated = np.concatenate((ticks[state['cursor']:], ticks[:state['cursor']]))
        valid = rotated[rotated > 0]
        if (np.any(ticks < 0) or not len(valid) or valid[-1] != state['lastTick']
                or not np.array_equal(valid, np.arange(valid[0], valid[0] + len(valid)))
                or np.any(rotated[:self.window - len(valid)] != 0)
                or np.any(rotated[self.window - len(valid):] <= 0)):
            raise ValueError('invalid seller-history tick coverage/cursor')
        if any(np.any(~np.isfinite(state[f])) or np.any(state[f] < 0) for f in ('sold', 'closingStock')):
            raise ValueError('invalid seller-history values')
        if np.any(state['offered'] > 1):
            raise ValueError('invalid seller-history offered mask')
        if np.any(state['shortChecks'] > state['fundedChecks']) or np.any(state['fundedChecks'] > state['discoveries']):
            raise ValueError('invalid seller-history exposure ordering')
        offered = state['offered'].astype(bool)
        if (np.any(~np.isfinite(state['quote'][offered])) or np.any(state['quote'][offered] <= 0)
                or np.any(~np.isnan(state['quote'][~offered]))):
            raise ValueError('invalid seller-history quote')
        if any(np.any(state[f][~offered]) for f in ('sold', *COUNT_FIELDS)):
            raise ValueError('activity on a nonoffered seller')
        if np.any((state['sold'] > 0) & (state['fundedChecks'] == 0)):
            raise ValueError('sale without a positive funded supplier check')
        unused = ticks == 0
        if any(np.any(state[f][unused]) for f in ('sold', 'closingStock', *COUNT_FIELDS, 'offered')):
            raise ValueError('activity in an unused history row')

    @classmethod
    def load(cls, path, *, expected_tick=None, expected_channels=None):
        if expected_tick is not None and not _integer(expected_tick, 1):
            raise ValueError('invalid expected checkpoint tick')
        with np.load(path, allow_pickle=False) as data:
            metadata = data['metadata']
            if metadata.dtype != np.uint8 or metadata.ndim != 1:
                raise ValueError('invalid seller-history metadata encoding')
            meta = json.loads(metadata.tobytes())
            if type(meta.get('version')) is not int or meta['version'] != VERSION or meta.get('catalog') != catalog_identity():
                raise ValueError('incompatible seller-history schema/catalog')
            result = cls(meta['window'])
            expected = {'metadata'} | {f'c{i}_{f}' for i in range(len(meta['channels'])) for f in ARRAY_FIELDS}
            if len(data.files) != len(expected) or set(data.files) != expected:
                raise ValueError('seller-history array set mismatch')
            for i, entry in enumerate(meta['channels']):
                name = entry['name']
                if name in result.channels:
                    raise ValueError('duplicate seller-history channel')
                state = {f: data[f'c{i}_{f}'].copy() for f in ARRAY_FIELDS}
                state.update(cursor=entry['cursor'], lastTick=entry['lastTick'], lot=entry['lot'])
                result._validate_state(name, state)
                if expected_tick is not None and state['lastTick'] != expected_tick:
                    raise ValueError('seller-history checkpoint tick mismatch')
                result.channels[name] = state
        if expected_tick is not None and not result.channels:
            raise ValueError('empty seller history at checkpoint')
        if expected_channels is not None and set(result.channels) != set(expected_channels):
            raise ValueError('seller-history channel coverage mismatch')
        return result
