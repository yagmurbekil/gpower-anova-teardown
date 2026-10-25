"""Referans vektörleri: sözleşme [CONTRACT] ve kullanıcı GUI gözlemleri [GUI]. İki kaynak ayrı tutulur."""

import pytest

from conftest import BONUS_MODES, TIME_LIMIT_S, assert_matches, load_gui_vectors, load_public_vectors, run_cli, to_argv

PUBLIC = load_public_vectors()
GUI = load_gui_vectors()


def _public_params():
    for v in PUBLIC:
        marks = [pytest.mark.bonus] if v["input"]["mode"] in BONUS_MODES else []
        yield pytest.param(v, id=v["id"], marks=marks)


def test_public_vector_count():
    assert len(PUBLIC) == 5
    assert len(GUI) == 30


@pytest.mark.parametrize("vector", list(_public_params()))
def test_contract_vector(vector):
    res = run_cli(*to_argv(vector["input"]))
    assert res.returncode == 0, res.stdout + res.stderr
    assert_matches(res.json, vector["expected"], vector["id"])
    assert res.elapsed < TIME_LIMIT_S, f"{vector['id']}: {res.elapsed:.3f} s"


@pytest.mark.parametrize("vector", GUI, ids=[v["id"] for v in GUI])
def test_gui_apriori_vector(vector):
    res = run_cli("--test", "anova-oneway", "--mode", "a-priori", *to_argv(vector["input"]))
    assert res.returncode == 0, res.stdout + res.stderr
    out = res.json
    assert out["n_total"] == vector["expected"]["n_total"], f"{vector['id']}: n_total {out['n_total']}"
    assert_matches(out, vector["expected"], vector["id"])
    assert res.elapsed < TIME_LIMIT_S, f"{vector['id']}: {res.elapsed:.3f} s"
