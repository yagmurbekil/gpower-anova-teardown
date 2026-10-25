"""anova-oneway hesap motoru (F tests – ANOVA: Fixed effects, omnibus, one-way).

Bağıntılar SPEC §B2 (kanıt E-020…E-026):
    df1 = groups − 1, df2 = n_total − groups, ncp = f² · n_total
    critical_f = Q_F(1 − alpha; df1, df2)   (tamamlayıcı kuyruk: f.isf; bkz. dist.py)
    power      = 1 − CDF_ncF(critical_f; df1, df2, ncp)

A priori N araması ve bonus modların kök bulma yaklaşımı [INFERENCE]'tır (SPEC U-1, U-3, §F).
"""

import math

from gpower_clone import dist

# A priori aramada denenebilecek en büyük toplam N [INFERENCE, SPEC §F].
MAX_N_TOTAL = 10**9

# df1/df2 için üst sınır (hariç) [INFERENCE, SPEC §F F-16].
DF_LIMIT = 2**64

# Kök bulma toleransları. Sözleşme toleransı 1e-6; kökü bunun çok altında daraltıyoruz.
_XTOL = 1e-15
_RTOL = 4 * 2.220446049250313e-16
_MAXITER = 500


class NoSolution(Exception):
    """Girdiler geçerli ama arama/kök bulma bir sonuç üretemedi (NO_SOLUTION)."""


class Inconsistent(Exception):
    """Değerler tek tek geçerli ama birlikte anlamsız (INCONSISTENT)."""

    def __init__(self, message, field):
        super().__init__(message)
        self.field = field


def _check_n(n_total, groups):
    if n_total <= groups:
        raise Inconsistent("n_total, groups değerinden büyük olmalı (df2 > 0)", "n_total")


def degrees(n_total, groups):
    df1, df2 = groups - 1, n_total - groups
    # 2⁶⁴ ve üstü serbestlik derecesi numpy'de object türüne düşer; dağılım fonksiyonları onu kabul etmez.
    # Uygulama sınırı [INFERENCE, SPEC §F F-16]; G*Power'ın kabul edilebilir N aralığı bilinmiyor (U-4).
    if df1 >= DF_LIMIT or df2 >= DF_LIMIT:
        raise NoSolution("Serbestlik derecesi 2^64 veya üstü; bu uygulamanın sayısal sınırı aşılıyor")
    return df1, df2


def critical_f(alpha, df1, df2):
    return float(dist.f_isf(alpha, df1, df2))


def _finite(x):
    if not math.isfinite(x):
        raise NoSolution("Sayısal hesap sonlu bir değer üretmedi")
    return x


def achieved_power(f, alpha, n_total, groups):
    """Verilen N için (ncp, critical_f, df1, df2, power)."""
    df1, df2 = degrees(n_total, groups)
    ncp = f * f * n_total
    crit = critical_f(alpha, df1, df2)
    power = float(dist.ncf_sf(crit, df1, df2, ncp))
    return ncp, crit, df1, df2, power


def _result(ncp, crit, df1, df2, **extra):
    out = {
        "ncp": _finite(float(ncp)),
        "critical_f": _finite(float(crit)),
        "df1": int(df1),
        "df2": int(df2),
    }
    for key, value in extra.items():
        out[key] = int(value) if key == "n_total" else _finite(float(value))
    return out


def post_hoc(f, alpha, n_total, groups):
    _check_n(n_total, groups)
    ncp, crit, df1, df2, power = achieved_power(f, alpha, n_total, groups)
    return _result(ncp, crit, df1, df2, power=power)


def a_priori(f, alpha, power, groups):
    """En küçük m ≥ 2 için n_total = groups · m, power(n_total) ≥ power [INFERENCE, SPEC U-1].

    Güç N'ye göre monoton kabul edilir [INFERENCE]: üstel genişletme + tam sayı ikili arama.
    """
    if power <= alpha:
        raise Inconsistent("Power, alpha değerinden büyük olmalı", "power")

    max_m = MAX_N_TOTAL // groups
    if max_m < 2:
        raise NoSolution("groups için izin verilen en büyük N aşılıyor")

    def reaches(m):
        p = achieved_power(f, alpha, groups * m, groups)[4]
        if math.isnan(p):
            raise NoSolution("Güç hesaplanamadı")
        return p >= power

    lo, hi = 1, 2  # değişmez: reaches(lo) yanlış kabul edilir (m = 1 → df2 = 0), reaches(hi) aranır
    while not reaches(hi):
        if hi >= max_m:
            raise NoSolution("Hedef güce izin verilen en büyük N içinde ulaşılamadı")
        lo, hi = hi, min(hi * 2, max_m)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if reaches(mid):
            hi = mid
        else:
            lo = mid

    n_total = groups * hi
    ncp, crit, df1, df2, actual = achieved_power(f, alpha, n_total, groups)
    return _result(ncp, crit, df1, df2, n_total=n_total, actual_power=actual)


def _brentq(func, lo, hi):
    try:
        f_lo, f_hi = func(lo), func(hi)
    except (ArithmeticError, ValueError) as exc:
        raise NoSolution(f"Kök aralığı değerlendirilemedi: {exc}") from exc
    if not (math.isfinite(f_lo) and math.isfinite(f_hi)) or f_lo * f_hi > 0:
        raise NoSolution("Kök aralığında işaret değişimi yok")
    if f_lo == 0:
        return lo
    if f_hi == 0:
        return hi
    from scipy import optimize  # yalnızca bonus modlar öder (~0.9 s import)

    try:
        root, info = optimize.brentq(
            func, lo, hi, xtol=_XTOL, rtol=_RTOL, maxiter=_MAXITER, full_output=True, disp=False
        )
    except (RuntimeError, ValueError) as exc:
        raise NoSolution(f"Kök bulunamadı: {exc}") from exc
    if not info.converged:
        raise NoSolution("Kök bulma yakınsamadı")
    return root


# α için açık aralığın kenarları; f.isf(0) = inf ve f.isf(1) = 0 olduğundan uçlar dışarıda kalır.
_ALPHA_LO = 1e-300
_ALPHA_HI = 1 - 2**-53


def sensitivity(alpha, power, n_total, groups):
    """power(f) = power denkleminin f için kökü [INFERENCE, SPEC U-3]."""
    _check_n(n_total, groups)
    df1, df2 = degrees(n_total, groups)
    crit = critical_f(alpha, df1, df2)

    def g(f):
        return float(dist.ncf_sf(crit, df1, df2, f * f * n_total)) - power

    lo, hi = 1e-12, 1.0
    while g(hi) < 0:
        if hi > 1e6:
            raise NoSolution("Hedef güce ulaştıran bir etki büyüklüğü bulunamadı")
        lo, hi = hi, hi * 2
    f = _brentq(g, lo, hi)
    return _result(f * f * n_total, crit, df1, df2, f=f)


def criterion(f, power, n_total, groups):
    """power(alpha) = power denkleminin alpha için kökü [INFERENCE, SPEC U-3]."""
    _check_n(n_total, groups)
    df1, df2 = degrees(n_total, groups)
    ncp = f * f * n_total

    def g(alpha):
        return float(dist.ncf_sf(critical_f(alpha, df1, df2), df1, df2, ncp)) - power

    alpha = _brentq(g, _ALPHA_LO, _ALPHA_HI)
    return _result(ncp, critical_f(alpha, df1, df2), df1, df2, alpha=alpha)


def compromise(f, beta_alpha_ratio, n_total, groups):
    """beta(alpha) = beta_alpha_ratio · alpha denkleminin alpha için kökü [INFERENCE, SPEC U-3]."""
    _check_n(n_total, groups)
    df1, df2 = degrees(n_total, groups)
    ncp = f * f * n_total

    def beta(alpha):
        return float(dist.ncf_cdf(critical_f(alpha, df1, df2), df1, df2, ncp))

    alpha = _brentq(lambda a: beta(a) - beta_alpha_ratio * a, _ALPHA_LO, _ALPHA_HI)
    b = beta(alpha)
    return _result(ncp, critical_f(alpha, df1, df2), df1, df2, alpha=alpha, beta=b, power=1 - b)
