"""F ve noncentral F dağılım fonksiyonları, `scipy.special` üzerinden.

`import scipy.stats` tek başına ~1.3 s sürüyor ve CLI'nin 2 s sınırını (CONTRACT §2.1) zorluyor.
Buradaki üç fonksiyon, scipy 1.18.0'da `scipy.stats`'ın aynı çağrılarda izlediği yolu birebir izler:

    stats.f.isf(q, dfn, dfd)       → rv_continuous.isf → f_gen._isf = _ppf(1 − q) → special.fdtri
    stats.ncf.sf(x, dfn, dfd, nc)  → rv_continuous.sf  → ncf_gen._sf  → special._ufuncs._ncf_sf
    stats.ncf.cdf(x, dfn, dfd, nc) → rv_continuous.cdf → ncf_gen._cdf → special.ncfdtr

Parametre kontrolü (_argcheck), destek sınırları ve `np.asarray` dönüşümü de aynıdır. Eşdeğerlik
`tests/test_dist_equivalence.py` ile bit düzeyinde test edilir; `_ncf_sf` özel (private) bir scipy
fonksiyonu olduğundan scipy sürümü `requirements.txt` ve `pyproject.toml`'da sabitlenmiştir.
"""

import math

import numpy as np
from scipy import special
from scipy.special import _ufuncs

_NAN = math.nan
_INF = math.inf


def f_isf(q, dfn, dfd):
    """`scipy.stats.f.isf(q, dfn, dfd)` (skaler)."""
    q, dfn, dfd = (np.asarray(v) for v in (q, dfn, dfd))
    if not (dfn > 0 and dfd > 0) or not (0 <= q <= 1):
        return _NAN
    if q == 1:
        return 0.0  # destek alt sınırı
    if q == 0:
        return _INF  # destek üst sınırı
    return special.fdtri(dfn, dfd, 1.0 - q) * 1.0 + 0.0


def _ncf_valid(x, dfn, dfd, nc):
    return bool(dfn > 0 and dfd > 0 and nc >= 0) and not np.isnan(x)


def ncf_sf(x, dfn, dfd, nc):
    """`scipy.stats.ncf.sf(x, dfn, dfd, nc)` (skaler)."""
    x = np.asarray(x, dtype=np.promote_types(np.asarray(x).dtype, np.float64))
    dfn, dfd, nc = (np.asarray(v) for v in (dfn, dfd, nc))
    if not _ncf_valid(x, dfn, dfd, nc):
        return _NAN
    if x <= 0:
        return 1.0
    if x < _INF:
        return _ufuncs._ncf_sf(x, dfn, dfd, nc)
    return 0.0


def ncf_cdf(x, dfn, dfd, nc):
    """`scipy.stats.ncf.cdf(x, dfn, dfd, nc)` (skaler)."""
    x = np.asarray(x, dtype=np.promote_types(np.asarray(x).dtype, np.float64))
    dfn, dfd, nc = (np.asarray(v) for v in (dfn, dfd, nc))
    if not _ncf_valid(x, dfn, dfd, nc):
        return _NAN
    if x >= _INF:
        return 1.0
    if x > 0:
        return special.ncfdtr(dfn, dfd, nc, x)
    return 0.0
