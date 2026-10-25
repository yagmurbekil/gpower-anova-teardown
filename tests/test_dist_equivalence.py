"""`gpower_clone.dist` (scipy.special) ile `scipy.stats.f` / `scipy.stats.ncf` eşdeğerliği.

Karşılaştırma bit düzeyindedir (`repr` eşitliği; NaN ve ±0 dahil). İstisnalar türü ve mesajıyla
karşılaştırılır. Tolerans yoktur.
"""

import inspect
import math

import pytest
import scipy
from scipy import stats
from scipy.stats import _continuous_distns

from conftest import load_gui_vectors, load_public_vectors
from gpower_clone import dist, engine

STATS = {
    "f_isf": lambda q, dfn, dfd: stats.f.isf(q, dfn, dfd),
    "ncf_sf": lambda x, dfn, dfd, nc: stats.ncf.sf(x, dfn, dfd, nc),
    "ncf_cdf": lambda x, dfn, dfd, nc: stats.ncf.cdf(x, dfn, dfd, nc),
}
SPECIAL = {name: getattr(dist, name) for name in STATS}


def outcome(func, *args):
    try:
        return ("ok", repr(float(func(*args))))
    except Exception as exc:  # istisna da davranışın parçası
        return ("raise", type(exc).__name__, str(exc))


# --- 1. scipy iç yolu hâlâ dist.py'nin varsaydığı yol mu? ------------------------------------

def test_scipy_version_pinned():
    assert scipy.__version__ == "1.18.0"


def test_f_isf_path():
    f_gen = type(stats.f)
    # f_gen kendi _isf'ini tanımlamaz; genel _isf = _ppf(1 − q) kullanılır
    assert "_isf" not in vars(f_gen)
    assert f_gen._isf is stats.rv_continuous._isf
    assert "self._ppf(1.0-q, *args)" in inspect.getsource(f_gen._isf)
    assert "sc.fdtri(dfn, dfd, q)" in inspect.getsource(f_gen._ppf)
    assert f_gen._argcheck is stats.rv_continuous._argcheck


def test_ncf_sf_path():
    ncf_gen = type(stats.ncf)
    assert "scu._ncf_sf(x, dfn, dfd, nc)" in inspect.getsource(ncf_gen._sf)
    assert _continuous_distns.scu._ncf_sf is dist._ufuncs._ncf_sf
    assert _continuous_distns.sc.fdtri is dist.special.fdtri
    assert stats.ncf.a == 0 and stats.ncf.b == math.inf
    assert stats.f.a == 0 and stats.f.b == math.inf


@pytest.mark.bonus  # ncf_cdf yalnızca compromise modunda kullanılır
def test_ncf_cdf_path():
    ncf_gen = type(stats.ncf)
    assert "sc.ncfdtr(dfn, dfd, nc, x)" in inspect.getsource(ncf_gen._cdf)
    assert _continuous_distns.sc.ncfdtr is dist.special.ncfdtr


# --- 2. Izgara: uç değerler dahil, bit düzeyinde ----------------------------------------------

QS = [1e-300, 1e-12, 1e-6, 1e-3, 0.01, 0.05, 0.1, 0.2309247058976277, 0.5, 0.6245994480148784, 0.9,
      0.99, 1 - 1e-9, 1 - 2**-53, 0.0, 1.0, math.nan, -0.1, 1.1]
DFNS = [1, 2, 3, 4, 7, 99, 0]
DFDS = [1, 2, 50, 95, 300, 1860, 10**6, 10**9 - 5, 2**63 - 1, 2**63, 10**20, 0]
NCS = [0.0, 1e-24, 1e-12, 6.25, 19.0625, 100.0, 1e4, -1.0]
XS = [0.0, -1.0, 1e-300, 1e-8, 0.5, 2.4674936, 1e3, 1e12, math.inf, math.nan]


@pytest.mark.parametrize("dfd", DFDS)
@pytest.mark.parametrize("dfn", DFNS)
def test_f_isf_grid(dfn, dfd):
    for q in QS:
        assert outcome(dist.f_isf, q, dfn, dfd) == outcome(STATS["f_isf"], q, dfn, dfd), (q, dfn, dfd)


@pytest.mark.parametrize("name", ["ncf_sf", pytest.param("ncf_cdf", marks=pytest.mark.bonus)])
@pytest.mark.parametrize("dfd", DFDS)
@pytest.mark.parametrize("dfn", DFNS)
def test_ncf_grid(name, dfn, dfd):
    crits = []
    for q in (1e-300, 1e-6, 0.05, 0.5, 0.95, 1 - 2**-53):
        res = outcome(STATS["f_isf"], q, dfn, dfd)
        if res[0] == "ok":
            crits.append(float(res[1]))
    for x in XS + crits:
        for nc in NCS:
            args = (x, dfn, dfd, nc)
            assert outcome(SPECIAL[name], *args) == outcome(STATS[name], *args), args


# --- 3. Motorun bütün hesap yolları ---------------------------------------------------------

def _cases():
    funcs = {"a-priori": engine.a_priori, "post-hoc": engine.post_hoc, "compromise": engine.compromise,
             "criterion": engine.criterion, "sensitivity": engine.sensitivity}
    for v in load_public_vectors():
        inp = {k: x for k, x in v["input"].items() if k not in ("test", "mode")}
        yield v["id"], funcs[v["input"]["mode"]], inp
    for v in load_gui_vectors():
        yield v["id"], engine.a_priori, v["input"]
    edge = [
        # a-priori: NO_SOLUTION (çok küçük f), INCONSISTENT, m = 2, uç alpha/power, büyük k
        (engine.a_priori, dict(f=1e-6, alpha=0.05, power=0.95, groups=5)),
        (engine.a_priori, dict(f=0.25, alpha=0.05, power=0.05, groups=5)),
        (engine.a_priori, dict(f=5.0, alpha=0.05, power=0.8, groups=2)),
        (engine.a_priori, dict(f=0.01, alpha=1e-10, power=1 - 1e-10, groups=2)),
        (engine.a_priori, dict(f=0.25, alpha=0.05, power=0.95, groups=10**9)),
        (engine.a_priori, dict(f=0.05, alpha=0.05, power=0.8, groups=1000)),
        # post-hoc: k katı olmayan N, çok büyük N (int64/uint64/object sınırları), uç alpha
        (engine.post_hoc, dict(f=0.25, alpha=0.05, n_total=101, groups=5)),
        (engine.post_hoc, dict(f=0.25, alpha=0.05, n_total=2**63 - 1, groups=5)),
        (engine.post_hoc, dict(f=0.25, alpha=0.05, n_total=2**63 + 4, groups=5)),
        (engine.post_hoc, dict(f=0.25, alpha=0.05, n_total=10**20, groups=5)),
        (engine.post_hoc, dict(f=0.25, alpha=1e-300, n_total=100, groups=5)),
        (engine.post_hoc, dict(f=10.0, alpha=0.05, n_total=100, groups=5)),
        (engine.post_hoc, dict(f=0.25, alpha=0.999999, n_total=6, groups=5)),
        (engine.post_hoc, dict(f=1e-200, alpha=0.05, n_total=100, groups=5)),
        (engine.post_hoc, dict(f=0.25, alpha=0.05, n_total=5, groups=5)),
        # 2⁶⁴ serbestlik derecesi sınırının iki yanı [INFERENCE, SPEC §F F-16]
        (engine.post_hoc, dict(f=0.25, alpha=0.05, n_total=2**64 + 4, groups=5)),   # df2 = 2⁶⁴ − 1: hesaplanır
        (engine.post_hoc, dict(f=0.25, alpha=0.05, n_total=2**64 + 5, groups=5)),   # df2 = 2⁶⁴: NO_SOLUTION
        (engine.post_hoc, dict(f=0.25, alpha=0.05, n_total=10**20 + 1, groups=10**20)),  # df1 ≥ 2⁶⁴
        (engine.sensitivity, dict(alpha=0.05, power=0.8, n_total=10**20, groups=5)),
        (engine.criterion, dict(f=0.25, power=0.8, n_total=10**20, groups=5)),
        (engine.compromise, dict(f=0.25, beta_alpha_ratio=1, n_total=10**20, groups=5)),
        # sensitivity
        (engine.sensitivity, dict(alpha=0.5, power=0.1, n_total=100, groups=5)),
        (engine.sensitivity, dict(alpha=0.05, power=0.999999, n_total=6, groups=5)),
        (engine.sensitivity, dict(alpha=1e-10, power=0.5, n_total=1000, groups=3)),
        (engine.sensitivity, dict(alpha=0.05, power=0.8, n_total=10**8, groups=2)),
        # criterion
        (engine.criterion, dict(f=0.25, power=1e-9, n_total=100, groups=5)),
        (engine.criterion, dict(f=0.25, power=0.999999, n_total=100, groups=5)),
        (engine.criterion, dict(f=5.0, power=0.5, n_total=100, groups=5)),
        (engine.criterion, dict(f=1e-6, power=0.5, n_total=10, groups=2)),
        # compromise
        (engine.compromise, dict(f=0.25, beta_alpha_ratio=1e-6, n_total=100, groups=5)),
        (engine.compromise, dict(f=0.25, beta_alpha_ratio=1e6, n_total=100, groups=5)),
        (engine.compromise, dict(f=3.0, beta_alpha_ratio=1, n_total=100, groups=5)),
        (engine.compromise, dict(f=1e-6, beta_alpha_ratio=1, n_total=10, groups=2)),
    ]
    for i, (func, inp) in enumerate(edge, start=1):
        yield f"edge-{i:02d}-{func.__name__}", func, inp


_BONUS_FUNCS = {engine.compromise, engine.criterion, engine.sensitivity}
CASES = [
    pytest.param(case, id=case[0], marks=[pytest.mark.bonus] if case[1] in _BONUS_FUNCS else [])
    for case in _cases()
]


def run_engine(func, inp):
    try:
        out = func(**inp)
        return ("ok", {k: (type(v).__name__, repr(v)) for k, v in out.items()})
    except Exception as exc:
        return ("raise", type(exc).__name__, str(exc), getattr(exc, "field", None))


@pytest.mark.parametrize("case", CASES)
def test_engine_paths_equivalent(case, monkeypatch):
    _, func, inp = case

    # a) scipy.special yolu; yapılan her dağılım çağrısı kaydedilir
    calls = []

    def recorder(name):
        original = SPECIAL[name]

        def wrapped(*args):
            calls.append((name, args))
            return original(*args)
        return wrapped

    for name in STATS:
        monkeypatch.setattr(dist, name, recorder(name))
    special_result = run_engine(func, inp)

    # b) aynı girdi, dağılımlar scipy.stats ile
    for name in STATS:
        monkeypatch.setattr(dist, name, STATS[name])
    stats_result = run_engine(func, inp)

    assert special_result == stats_result
    # Ön kontrolde (INCONSISTENT, MAX_N_TOTAL) reddedilen girdiler dağılım çağrısı yapmaz
    if special_result[0] == "ok":
        assert calls, "motor hiçbir dağılım fonksiyonunu çağırmadı"
    for name, args in calls:
        assert outcome(SPECIAL[name], *args) == outcome(STATS[name], *args), (name, args)


def test_engine_does_not_import_scipy_stats():
    import subprocess
    import sys

    from conftest import ROOT

    code = ("import sys; from gpower_clone import engine; engine.a_priori(0.25, 0.05, 0.95, 5); "
            "engine.post_hoc(0.25, 0.05, 100, 5); "
            "print(sorted(m for m in sys.modules if m in ('scipy.stats', 'scipy.optimize')))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")}, check=True)
    assert out.stdout.strip() == "[]"
