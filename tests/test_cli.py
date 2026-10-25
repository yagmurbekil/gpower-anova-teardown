"""CLI sözleşmesi: biçim, hata kodları, çıkış kodları, determinizm (CONTRACT §2, SPEC §A, §F)."""

import json
import shutil
import subprocess

import pytest

from conftest import run_cli

BASE = ("--test", "anova-oneway")
APRIORI = BASE + ("--mode", "a-priori", "--f", "0.25", "--alpha", "0.05", "--power", "0.95", "--groups", "5")
POSTHOC = BASE + ("--mode", "post-hoc", "--f", "0.25", "--alpha", "0.05", "--n_total", "100", "--groups", "5")


def assert_error(res, code, field, exit_code=2):
    assert res.returncode == exit_code, res.stdout + res.stderr
    lines = res.stdout.splitlines()
    assert len(lines) == 1, res.stdout
    out = json.loads(lines[0])
    assert set(out) == {"error", "code", "field"}
    assert isinstance(out["error"], str) and out["error"]
    assert out["code"] == code
    assert out["field"] == field


# --- başarılı çıktı biçimi -------------------------------------------------------------------

@pytest.mark.parametrize("args", [APRIORI, POSTHOC], ids=["a-priori", "post-hoc"])
def test_single_line_json_and_clean_stdout(args):
    res = run_cli(*args)
    assert res.returncode == 0
    assert res.stdout.endswith("\n") and res.stdout.count("\n") == 1
    out = json.loads(res.stdout)
    assert isinstance(out, dict)
    for key in ("df1", "df2") + (("n_total",) if "a-priori" in args else ()):
        assert type(out[key]) is int
    # tam sayı alanları "300.0" değil "300" olarak yazılır
    assert f'"df1": {out["df1"]},' in res.stdout and f'"df2": {out["df2"]},' in res.stdout


def test_apriori_required_fields_and_types():
    out = run_cli(*APRIORI).json
    assert set(out) >= {"ncp", "critical_f", "df1", "df2", "n_total", "actual_power"}
    assert all(type(out[k]) is int for k in ("df1", "df2", "n_total"))
    assert all(type(out[k]) is float for k in ("ncp", "critical_f", "actual_power"))


def test_posthoc_required_fields_and_types():
    out = run_cli(*POSTHOC).json
    assert set(out) >= {"ncp", "critical_f", "df1", "df2", "power"}
    assert all(type(out[k]) is int for k in ("df1", "df2"))


def test_full_double_precision_and_dot_separator():
    res = run_cli(*POSTHOC)
    out = res.json
    assert "," not in str(out["critical_f"])
    # 7 basamağa yuvarlanmamış: tam double repr ile yazılır
    assert json.dumps(out["critical_f"]) in res.stdout
    assert len(repr(out["critical_f"]).split(".")[1]) > 7
    assert "2.4674936" in res.stdout and "2,4674936" not in res.stdout


def test_deterministic_output():
    first, second = run_cli(*APRIORI), run_cli(*APRIORI)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout


def test_argument_order_does_not_matter():
    shuffled = ("--groups", "5", "--power", "0.95", "--mode", "a-priori", "--alpha", "0.05", "--f", "0.25",
                "--test", "anova-oneway")
    assert run_cli(*shuffled).stdout == run_cli(*APRIORI).stdout


def test_version():
    res = run_cli("--version")
    assert res.returncode == 0 and res.stdout.count("\n") == 1
    out = res.json
    assert out["contract_version"] == "1.0.0"
    assert isinstance(out["name"], str) and out["name"]
    assert isinstance(out["engine"], str) and "scipy" in out["engine"]


@pytest.mark.skipif(shutil.which("gpower-clone") is None, reason="gpower-clone konsol betiği kurulu değil")
def test_console_script_installed():
    proc = subprocess.run(["gpower-clone", *POSTHOC], capture_output=True, text=True)
    assert proc.returncode == 0
    assert proc.stdout == run_cli(*POSTHOC).stdout


# --- hata kodları ----------------------------------------------------------------------------

def test_missing_test():
    assert_error(run_cli("--mode", "a-priori"), "MISSING_PARAM", "test")


def test_missing_mode():
    assert_error(run_cli(*BASE, "--f", "0.25"), "MISSING_PARAM", "mode")


@pytest.mark.parametrize("drop", ["f", "alpha", "power", "groups"])
def test_missing_param_apriori(drop):
    args = list(APRIORI)
    i = args.index(f"--{drop}")
    del args[i:i + 2]
    assert_error(run_cli(*args), "MISSING_PARAM", drop)


def test_missing_param_posthoc_n_total():
    args = list(POSTHOC)
    i = args.index("--n_total")
    del args[i:i + 2]
    assert_error(run_cli(*args), "MISSING_PARAM", "n_total")


def test_unknown_param():
    assert_error(run_cli(*APRIORI, "--foo", "1"), "UNKNOWN_PARAM", "foo")


def test_irrelevant_param_for_mode():
    assert_error(run_cli(*POSTHOC, "--power", "0.8"), "UNKNOWN_PARAM", "power")


def test_param_from_other_family():
    assert_error(run_cli(*APRIORI, "--tails", "1"), "UNKNOWN_PARAM", "tails")


def test_positional_argument():
    assert_error(run_cli(*APRIORI, "extra"), "UNKNOWN_PARAM", "extra")


@pytest.mark.parametrize("field,value", [
    ("alpha", "abc"),
    ("alpha", "0,05"),
    ("alpha", "nan"),
    ("f", "inf"),
    ("f", "1e400"),
    ("f", "1_0"),
    ("groups", "5.0"),
    ("groups", "5.5"),
    ("groups", "1e1"),
])
def test_invalid_value(field, value):
    args = list(APRIORI)
    args[args.index(f"--{field}") + 1] = value
    assert_error(run_cli(*args), "INVALID_VALUE", field)


def test_flag_without_value():
    assert_error(run_cli(*APRIORI[:-1]), "INVALID_VALUE", "groups")


def test_duplicate_flag():
    assert_error(run_cli(*APRIORI, "--f", "0.3"), "INVALID_VALUE", "f")


@pytest.mark.parametrize("field,value", [
    ("alpha", "0"), ("alpha", "1"), ("alpha", "-0.05"),
    ("power", "0"), ("power", "1.5"),
    ("f", "0"), ("f", "-0.25"),
    ("groups", "1"),
])
def test_out_of_range_apriori(field, value):
    args = list(APRIORI)
    args[args.index(f"--{field}") + 1] = value
    assert_error(run_cli(*args), "OUT_OF_RANGE", field)


def test_out_of_range_n_total():
    args = list(POSTHOC)
    args[args.index("--n_total") + 1] = "1"
    assert_error(run_cli(*args), "OUT_OF_RANGE", "n_total")


def test_inconsistent_power_not_above_alpha():
    args = list(APRIORI)
    args[args.index("--power") + 1] = "0.05"
    assert_error(run_cli(*args), "INCONSISTENT", "power")


@pytest.mark.parametrize("n_total", ["5", "3"])
def test_inconsistent_n_total_not_above_groups(n_total):
    args = list(POSTHOC)
    args[args.index("--n_total") + 1] = n_total
    assert_error(run_cli(*args), "INCONSISTENT", "n_total")


def test_unsupported_test():
    assert_error(run_cli("--test", "z-test", "--mode", "a-priori"), "UNSUPPORTED", "test")


@pytest.mark.parametrize("test", ["t2-indep", "t-paired", "chi2-contingency", "multireg-r2"])
def test_contract_families_not_implemented(test):
    assert_error(run_cli("--test", test, "--mode", "a-priori"), "UNSUPPORTED", "test")


def test_unsupported_mode():
    assert_error(run_cli(*BASE, "--mode", "post hoc"), "UNSUPPORTED", "mode")


def test_no_solution_exit_code_1():
    # Çok küçük f: gerekli N, MAX_N_TOTAL (1e9) sınırını aşar [INFERENCE, SPEC §F].
    args = list(APRIORI)
    args[args.index("--f") + 1] = "1e-6"
    assert_error(run_cli(*args), "NO_SOLUTION", None, exit_code=1)


def test_huge_n_total_posthoc_no_solution():
    # df2 ≥ 2⁶⁴ → NO_SOLUTION, INTERNAL_ERROR değil [INFERENCE, SPEC §F F-16]
    args = list(POSTHOC)
    args[args.index("--n_total") + 1] = str(10**20)
    assert_error(run_cli(*args), "NO_SOLUTION", None, exit_code=1)


def test_huge_groups_posthoc_no_solution():
    # df1 = groups − 1 ≥ 2⁶⁴, df2 = 1
    res = run_cli(*BASE, "--mode", "post-hoc", "--f", "0.25", "--alpha", "0.05",
                  "--n_total", str(10**20 + 1), "--groups", str(10**20))
    assert_error(res, "NO_SOLUTION", None, exit_code=1)


def test_df2_limit_boundary_posthoc():
    # df2 = 2⁶⁴ − 1 hâlâ hesaplanır; df2 = 2⁶⁴ NO_SOLUTION
    args = list(POSTHOC)
    args[args.index("--n_total") + 1] = str(2**64 + 4)
    res = run_cli(*args)
    assert res.returncode == 0, res.stdout
    assert res.json["df2"] == 2**64 - 1 and type(res.json["df2"]) is int
    args[args.index("--n_total") + 1] = str(2**64 + 5)
    assert_error(run_cli(*args), "NO_SOLUTION", None, exit_code=1)


@pytest.mark.bonus
@pytest.mark.parametrize("mode,extra", [
    ("sensitivity", ("--alpha", "0.05", "--power", "0.8")),
    ("criterion", ("--f", "0.25", "--power", "0.8")),
    ("compromise", ("--f", "0.25", "--beta_alpha_ratio", "1")),
])
def test_huge_n_total_bonus_no_solution(mode, extra):
    res = run_cli(*BASE, "--mode", mode, *extra, "--n_total", str(10**20), "--groups", "5")
    assert_error(res, "NO_SOLUTION", None, exit_code=1)


def test_posthoc_n_total_not_multiple_of_groups_is_computed():
    args = list(POSTHOC)
    args[args.index("--n_total") + 1] = "101"
    res = run_cli(*args)
    assert res.returncode == 0
    assert res.json["df2"] == 96
