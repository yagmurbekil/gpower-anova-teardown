"""Ortak test düzeneği: CLI'yi alt süreçte çalıştırma, referans vektörleri, karşılaştırma kuralı."""

import csv
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ORACLE = ROOT / "oracle"
TIME_LIMIT_S = 2.0
TOL = 1e-6
INTEGER_FIELDS = {"n1", "n2", "n_total", "df", "df1", "df2"}
BONUS_MODES = {"compromise", "criterion", "sensitivity"}

# GPOWER_CLONE_CMD ile kurulu komut denenebilir (ör. "gpower-clone"); varsayılan kaynak ağacındaki modül.
_CMD = shlex.split(os.environ["GPOWER_CLONE_CMD"]) if os.environ.get("GPOWER_CLONE_CMD") else [
    sys.executable, "-m", "gpower_clone"
]
_ENV = dict(os.environ, PYTHONPATH=str(ROOT / "src"))

CALL_TIMES = []


class CliResult:
    def __init__(self, proc, elapsed):
        self.returncode = proc.returncode
        self.stdout = proc.stdout
        self.stderr = proc.stderr
        self.elapsed = elapsed

    @property
    def json(self):
        return json.loads(self.stdout)


def run_cli(*args):
    argv = [str(a) for a in args]
    start = time.perf_counter()
    proc = subprocess.run(_CMD + argv, capture_output=True, text=True, encoding="utf-8", env=_ENV, timeout=30)
    elapsed = time.perf_counter() - start
    CALL_TIMES.append((elapsed, " ".join(argv)))
    return CliResult(proc, elapsed)


def to_argv(inputs):
    argv = []
    for key, value in inputs.items():
        argv += [f"--{key}", repr(value) if isinstance(value, float) else str(value)]
    return argv


def assert_matches(actual, expected, label=""):
    """CONTRACT §6: tam sayılar birebir; ondalıklar |fark| ≤ 1e-6 ya da göreli fark ≤ 1e-6."""
    for key, exp in expected.items():
        assert key in actual, f"{label}: '{key}' alanı çıktıda yok"
        got = actual[key]
        if key in INTEGER_FIELDS:
            assert type(got) is int, f"{label}: {key} tam sayı değil ({got!r})"
            assert got == exp, f"{label}: {key} = {got}, beklenen {exp}"
        else:
            diff = abs(got - exp)
            rel = diff / abs(exp) if exp else float("inf")
            assert diff <= TOL or rel <= TOL, f"{label}: {key} = {got!r}, beklenen {exp}, |fark| {diff:.3e}"


def load_public_vectors(test="anova-oneway"):
    with open(ORACLE / "public_vectors.jsonl", encoding="utf-8") as fh:
        vectors = [json.loads(line) for line in fh if line.strip()]
    return [v for v in vectors if v["input"]["test"] == test]


def load_gui_vectors():
    """CSV (k → groups, total_n → n_total) + oracle/README.md tablosundaki görüntüden okunmuş çıktılar."""
    with open(ORACLE / "anova-apriori.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    extras = {}
    for line in (ORACLE / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("| AN-"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            ncp, crit, df1, df2, actual = (x.strip() for x in cells[-1].split("/"))
            extras[cells[0]] = {
                "ncp": float(ncp), "critical_f": float(crit), "df1": int(df1), "df2": int(df2),
                "actual_power": float(actual),
            }
    vectors = []
    for i, row in enumerate(rows, start=1):
        vid = f"AN-{i:03d}"
        vectors.append({
            "id": vid,
            "input": {"f": float(row["f"]), "alpha": float(row["alpha"]), "power": float(row["power"]),
                      "groups": int(row["k"])},
            "expected": {"n_total": int(row["total_n"]), **extras[vid]},
        })
    return vectors


def pytest_terminal_summary(terminalreporter):
    if CALL_TIMES:
        slowest, args = max(CALL_TIMES)
        terminalreporter.write_line(
            f"gpower-clone alt süreç çağrıları: {len(CALL_TIMES)}, en uzun {slowest:.3f} s ({args})"
        )


@pytest.fixture
def cli():
    return run_cli
