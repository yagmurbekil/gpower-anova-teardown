"""Motor düzeyi kontroller (alt süreç olmadan)."""

import pytest

from conftest import load_gui_vectors
from gpower_clone import engine

GUI = load_gui_vectors()


@pytest.mark.parametrize("vector", GUI, ids=[v["id"] for v in GUI])
def test_apriori_is_smallest_multiple_of_groups(vector):
    """Seçilen N hedefi sağlar, bir önceki k katı (≥ 2k) sağlamaz [INFERENCE, SPEC U-1]."""
    inp = vector["input"]
    out = engine.a_priori(**inp)
    k = inp["groups"]
    assert out["n_total"] % k == 0
    assert out["actual_power"] >= inp["power"]
    if out["n_total"] > 2 * k:
        prev = engine.achieved_power(inp["f"], inp["alpha"], out["n_total"] - k, k)[4]
        assert prev < inp["power"]


def test_critical_f_uses_upper_tail():
    from scipy import stats

    assert engine.critical_f(0.05, 4, 95) == float(stats.f.isf(0.05, 4, 95))


def test_df_limit_boundary():
    """2⁶⁴ sınırı [INFERENCE, SPEC §F F-16]: altında değer aynen döner, sınırda NO_SOLUTION."""
    assert engine.degrees(2**64 + 4, 5) == (4, 2**64 - 1)
    assert engine.degrees(2**64, 2**64 - 1) == (2**64 - 2, 1)
    with pytest.raises(engine.NoSolution):
        engine.degrees(2**64 + 5, 5)
    with pytest.raises(engine.NoSolution):
        engine.degrees(2**64 + 2, 2**64 + 1)


def test_ncp_formula():
    out = engine.post_hoc(0.25, 0.05, 100, 5)
    assert out["ncp"] == 0.25**2 * 100
    assert (out["df1"], out["df2"]) == (4, 95)
