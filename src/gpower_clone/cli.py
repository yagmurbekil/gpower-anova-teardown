"""Komut satırı arayüzü (CONTRACT §2–§5, SPEC §A, §F).

stdout'a her durumda tek satır JSON yazılır; log ve uyarılar stderr'e gider.
Doğrulama sırası [INFERENCE, SPEC §F]: test/mod → tanınmayan/ilgisiz alan → eksik alan →
değer biçimi → aralık → tutarlılık → hesap.
"""

import json
import platform
import re
import sys

from gpower_clone import CONTRACT_VERSION, NAME

EXIT_OK, EXIT_INTERNAL, EXIT_INPUT = 0, 1, 2

# CONTRACT §4 tablolarındaki bütün alan adları (test/mode hariç).
CONTRACT_FIELDS = {
    "tails", "alpha", "power", "beta_alpha_ratio", "d", "ratio", "n1", "n2", "dz",
    "n_total", "f", "groups", "w", "df", "f2", "predictors",
}

# Sözleşmede tanımlı ama bu sürümde uygulanmayan aileler.
CONTRACT_TESTS_NOT_IMPLEMENTED = {"t2-indep", "t-paired", "chi2-contingency", "multireg-r2"}

# anova-oneway: mod → zorunlu girdi alanları (CONTRACT §4.3, SPEC §A4), tablo sırasıyla.
ANOVA_MODES = {
    "a-priori": ("f", "alpha", "power", "groups"),
    "post-hoc": ("f", "alpha", "n_total", "groups"),
    "compromise": ("f", "beta_alpha_ratio", "n_total", "groups"),
    "criterion": ("f", "power", "n_total", "groups"),
    "sensitivity": ("alpha", "power", "n_total", "groups"),
}

INTEGER_FIELDS = {"n_total", "groups"}

# Yalnızca ASCII rakamlar; ondalık ayırıcı nokta. float() tek başına "1_000", "nan", "∞" gibi
# biçimleri de kabul ettiği için önce bu kalıplarla süzülür.
_DECIMAL_RE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_INTEGER_RE = re.compile(r"[+-]?[0-9]+")


class InputError(Exception):
    def __init__(self, code, field, message, exit_code=EXIT_INPUT):
        super().__init__(message)
        self.code = code
        self.field = field
        self.exit_code = exit_code


def _emit(obj):
    sys.stdout.write(json.dumps(obj, allow_nan=False) + "\n")
    sys.stdout.flush()


def _error(code, field, message):
    return {"error": message, "code": code, "field": field}


def version_info():
    import scipy

    return {
        "contract_version": CONTRACT_VERSION,
        "name": NAME,
        "engine": f"Python {platform.python_version()}, scipy {scipy.__version__}",
    }


def parse_args(argv):
    """`--alan değer` çiftlerini sözlüğe çevirir. Değerler henüz metindir."""
    params = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if not token.startswith("--") or len(token) == 2:
            raise InputError("UNKNOWN_PARAM", token, f"Beklenmeyen argüman: {token!r}")
        name = token[2:]
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            raise InputError("INVALID_VALUE", name, f"--{name} için değer verilmedi")
        if name in params:
            raise InputError("INVALID_VALUE", name, f"--{name} birden fazla kez verildi")
        params[name] = argv[i + 1]
        i += 2
    return params


def _parse_value(name, text):
    if name in INTEGER_FIELDS:
        if not _INTEGER_RE.fullmatch(text):
            raise InputError("INVALID_VALUE", name, f"{name} tam sayı olmalı: {text!r}")
        return int(text)
    if not _DECIMAL_RE.fullmatch(text):
        raise InputError("INVALID_VALUE", name, f"{name} sayı olmalı (ondalık ayırıcı nokta): {text!r}")
    value = float(text)
    if value != value or value in (float("inf"), float("-inf")):
        raise InputError("INVALID_VALUE", name, f"{name} sonlu bir sayı olmalı: {text!r}")
    return value


def _check_range(name, value):
    """CONTRACT §5 / SPEC §A5 aralıkları."""
    if name in ("alpha", "power"):
        ok, rule = 0 < value < 1, "0 < değer < 1"
    elif name in ("f", "beta_alpha_ratio"):
        ok, rule = value > 0, "> 0"
    elif name in ("n_total", "groups"):
        ok, rule = value >= 2, "≥ 2"
    else:  # pragma: no cover - ANOVA_MODES dışında alan yok
        ok, rule = True, ""
    if not ok:
        raise InputError("OUT_OF_RANGE", name, f"{name} aralık dışında ({rule}): {value}")


def validate(params):
    """Ham parametreleri doğrular; (test, mode, sayısal girdiler) döndürür."""
    test = params.get("test")
    if test is None:
        raise InputError("MISSING_PARAM", "test", "--test verilmedi")
    if test in CONTRACT_TESTS_NOT_IMPLEMENTED:
        raise InputError("UNSUPPORTED", "test", f"{test} bu uygulamada desteklenmiyor (yalnızca anova-oneway)")
    if test != "anova-oneway":
        raise InputError("UNSUPPORTED", "test", f"Bilinmeyen test: {test!r}")

    mode = params.get("mode")
    if mode is None:
        raise InputError("MISSING_PARAM", "mode", "--mode verilmedi")
    if mode not in ANOVA_MODES:
        raise InputError("UNSUPPORTED", "mode", f"Bilinmeyen mod: {mode!r}")
    required = ANOVA_MODES[mode]

    for name in params:
        if name in ("test", "mode"):
            continue
        if name not in CONTRACT_FIELDS:
            raise InputError("UNKNOWN_PARAM", name, f"Tanınmayan alan: --{name}")
        if name not in required:
            raise InputError("UNKNOWN_PARAM", name, f"--{name} {mode} modunda kullanılmaz")

    for name in required:
        if name not in params:
            raise InputError("MISSING_PARAM", name, f"--{name} {mode} modunda zorunlu")

    values = {name: _parse_value(name, params[name]) for name in required}
    for name in required:
        _check_range(name, values[name])
    return test, mode, values


def compute(mode, values):
    from gpower_clone import engine

    func = {
        "a-priori": engine.a_priori,
        "post-hoc": engine.post_hoc,
        "compromise": engine.compromise,
        "criterion": engine.criterion,
        "sensitivity": engine.sensitivity,
    }[mode]
    try:
        return func(**values)
    except engine.Inconsistent as exc:
        raise InputError("INCONSISTENT", exc.field, str(exc)) from exc
    except engine.NoSolution as exc:
        raise InputError("NO_SOLUTION", None, str(exc), EXIT_INTERNAL) from exc


def run(argv):
    """(çıktı nesnesi, çıkış kodu) döndürür; hiçbir şey yazmaz."""
    if argv == ["--version"]:
        return version_info(), EXIT_OK
    try:
        params = parse_args(argv)
        _, mode, values = validate(params)
        result = compute(mode, values)
        json.dumps(result, allow_nan=False)  # NaN/inf sızmasını yazmadan önce yakala
        return result, EXIT_OK
    except InputError as exc:
        return _error(exc.code, exc.field, str(exc)), exc.exit_code
    except Exception as exc:  # beklenmeyen durum: iç hata
        print(f"gpower-clone: iç hata: {exc!r}", file=sys.stderr)
        return _error("INTERNAL_ERROR", None, f"İç hata: {exc}"), EXIT_INTERNAL


def main(argv=None):
    obj, code = run(sys.argv[1:] if argv is None else argv)
    _emit(obj)
    return code
