"""Compare optimized allocation with the independently archived original solver."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path
import numpy as np
from .retail import solve_retail


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    with tarfile.open(a.archive) as tar:
        source = tar.extractfile('tools/buying_v2/retail.py').read()
    # Run the archived Python body independently, without compiling its current
    # dependency imports into a reference. The only decorator is identity here.
    namespace = {}
    exec(source.decode().replace('from .jit import njit', 'def njit(fn): return fn'), namespace)
    original = namespace['solve_retail']
    rng = np.random.default_rng(170331)
    for case in range(2000):
        n = int(rng.integers(1, 7))
        values = np.sort(rng.uniform(.01, 100, int(rng.integers(1, 25))))[::-1]
        prices = rng.uniform(.01, 100, n)
        if case % 5 == 0:
            prices[:] = prices[0]
        stock = rng.integers(0, 30, n)
        ids = rng.permutation(np.arange(n, dtype=np.int64))
        incumbent = int(rng.integers(-1, n))
        bid = int(rng.integers(0, 25))
        cash = float(rng.uniform(0, 2000))
        fee = float(rng.uniform(0, 100))
        demands = np.array([min(int(np.count_nonzero(values > price)), int(cash // price)) for price in prices])
        args = (values, prices, stock, ids, incumbent, bid, fee, cash, demands)
        before, after = original(*args), solve_retail(*args)
        np.testing.assert_array_equal(before[0], after[0])
        assert before[1:] == after[1:], (case, before, after)
    result = dict(status='pass', cases=2000, seed=170331,
                  sourceArchive=str(a.archive.resolve()), archivedSolverSHA256=hashlib.sha256(source).hexdigest(),
                  currentSolverSHA256=hashlib.sha256(Path(__file__).with_name('retail.py').read_bytes()).hexdigest(),
                  scope='Exact allocation/objective/cost/fee/preference comparison; not full-world timing.')
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
