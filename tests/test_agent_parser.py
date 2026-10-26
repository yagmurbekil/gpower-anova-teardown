"""Kural tabanlı ayrıştırıcı: TR/EN ifadeler, ondalık virgül, sıra, harf, çelişki, belirsizlik, biçim hataları."""

import pytest

from gpower_clone import cli
from gpower_clone.agent import rules
from gpower_clone.agent.parser import fold, parse


def values(text):
    return {t: [m.value for m in ms] for t, ms in parse(text).values().items()}


def single(text):
    vals = values(text)
    assert all(len(v) == 1 for v in vals.values()), vals
    return {t: v[0] for t, v in vals.items()}


# --- sözleşmeyle uyum ------------------------------------------------------------------------

def test_field_names_match_contract():
    assert set(rules.ANOVA_FIELDS) == {f for fields in cli.ANOVA_MODES.values() for f in fields}
    assert set(rules.MODE_RULES) == set(cli.ANOVA_MODES)
    assert rules.OTHER_CONTRACT_FIELDS == cli.CONTRACT_FIELDS - set(rules.ANOVA_FIELDS)
    assert set(rules.LABELS) == set(rules.ANOVA_FIELDS)


def test_contract_test_ids_for_unsupported_rules():
    ids = {v for _, v in rules.TEST_RULES if v is not None}
    assert ids <= cli.CONTRACT_TESTS_NOT_IMPLEMENTED


# --- Türkçe / İngilizce örnekler -------------------------------------------------------------

@pytest.mark.parametrize("text,expected,modes", [
    ("%80 güç için gereken örneklem sayısını hesapla.", {"power": 0.8}, ["a-priori"]),
    ("Üç grup, etki büyüklüğü 0,25, alfa 0,05 ve güç 0,80.",
     {"groups": 3, "f": 0.25, "alpha": 0.05, "power": 0.8}, []),
    ("Güç 0.90 olsun, alfa 0.01 olsun.", {"power": 0.9, "alpha": 0.01}, []),
    ("A priori analiz yap.", {}, ["a-priori"]),
    ("Post hoc power analysis.", {}, ["post-hoc"]),
    ("Effect size f is 0.25, alpha is 0.05.", {"f": 0.25, "alpha": 0.05}, []),
    ("There are four groups and I want 80 percent power.", {"groups": 4, "power": 0.8}, []),
    ("Compute the required sample size: 3 groups, f = 0.4, alpha = 0.05, power = 0.95.",
     {"groups": 3, "f": 0.4, "alpha": 0.05, "power": 0.95}, ["a-priori"]),
    ("Toplam 120 katılımcılı çalışmada f = 0.30 ve alpha = 0.05 iken gücüm ne olur?",
     {"n_total": 120, "f": 0.3, "alpha": 0.05}, ["post-hoc"]),
    ("5 grup, toplam N = 100, f = 0.25. β/α oranını 1 alırsam (compromise analizi)",
     {"groups": 5, "n_total": 100, "f": 0.25, "beta_alpha_ratio": 1}, ["compromise"]),
    ("5 grup ve toplam 100 katılımcıyla 0.95 güce ulaşmak için gereken alpha (criterion)",
     {"groups": 5, "n_total": 100, "power": 0.95}, ["criterion"]),
    ("alpha = 0.05 ve güç 0.95 için saptanabilecek en küçük etki büyüklüğü f nedir?",
     {"alpha": 0.05, "power": 0.95}, ["sensitivity"]),
    ("sensitivity analysis with n = 100 and k = 5", {"n_total": 100, "groups": 5}, ["sensitivity"]),
])
def test_examples(text, expected, modes):
    p = parse(text)
    assert single(text) == expected
    assert sorted(p.modes) == modes
    assert not p.ambiguous and not p.orphans and not p.tests


@pytest.mark.parametrize("text", [
    "alfa 0,05", "alfa 0.05", "ALFA 0,05", "Alpha = 0.05", "alpha: 0.05", "α = 0,05", "%5 anlamlılık düzeyi",
    "anlamlılık düzeyi 0.05", "ANLAMLILIK DÜZEYİ 0,05", "significance level of 0.05", "alpha   is   0.05",
    "yüzde 5 alfa", "5% significance",
])
def test_alpha_variants(text):
    assert single(text) == {"alpha": 0.05}


@pytest.mark.parametrize("text", ["güç 0,80", "GÜÇ %80", "power 0.8", "80 percent power", "%80'lik güç",
                                  "1-β = 0.80", "statistical power of 0.8", "gücü 0,8 olsun"])
def test_power_variants(text):
    assert single(text) == {"power": 0.8}


@pytest.mark.parametrize("text,n", [
    ("3 grup", 3), ("üç grup", 3), ("ÜÇ GRUP", 3), ("Beş gruplu", 5), ("dört diyet grubu", 4), ("four groups", 4),
    ("three-arm trial", 3), ("grup sayısı 6", 6), ("number of groups is 7", 7), ("k = 3", 3),
    ("dört farklı program", 4), ("üç öğretim yöntemini karşılaştıran", 3), ("compare three diets", 3),
])
def test_group_variants(text, n):
    assert single(text) == {"groups": n}


def test_order_and_spacing_do_not_matter():
    a = single("3 grup, f 0,25, alfa 0,05, güç 0,80")
    b = single("güç   0,80 ;  alfa 0,05 ,f=0,25 ve 3 grup.")
    assert a == b == {"groups": 3, "f": 0.25, "alpha": 0.05, "power": 0.8}


def test_turkish_dotted_i_folding_preserves_positions():
    text = "İKİ GRUP, ANLAMLILIK 0,05"
    assert len(fold(text)) == len(text)
    assert single(text) == {"groups": 2, "alpha": 0.05}


def test_trailing_punctuation_is_not_part_of_number():
    assert single("alfa 0,05, güç 0,80.") == {"alpha": 0.05, "power": 0.8}


def test_comma_breaks_keyword_binding():
    # "anlamlılık düzeyi, %80 güç": %80 alfaya bağlanmaz
    assert single("%5 anlamlılık düzeyi, %80 güç") == {"alpha": 0.05, "power": 0.8}


def test_per_group_n_is_separate_from_total():
    assert single("5 grup var ve her grupta 20 kişi") == {"groups": 5, "per_group": 20}
    assert single("20 participants per group, 4 groups") == {"per_group": 20, "groups": 4}


def test_effect_size_d_f2_are_not_f():
    p = parse("Cohen's d = 0.5, f2 = 0.15")
    assert not p.mentions
    assert {(m.target, m.value) for m in p.other} == {("d", 0.5), ("f2", 0.15)}


def test_beta_alpha_ratio_alpha_symbol_not_taken_as_alpha():
    assert single("β/α oranı 2") == {"beta_alpha_ratio": 2}


# --- tekrar, çelişki, belirsizlik --------------------------------------------------------------

def test_repeated_same_value_is_not_conflict():
    assert parse("alfa 0,05 ... alpha = 0.05").conflicts() == {}


def test_conflicting_values():
    assert parse("alfa 0,05 ve alfa 0,01").conflicts() == {"alpha": [0.05, 0.01]}


def test_conflicting_modes():
    assert sorted(parse("a priori ve post hoc").modes) == ["a-priori", "post-hoc"]


def test_orphan_number_is_reported():
    p = parse("3 grup, f 0.25 ve 42")
    assert p.orphans == ["42"]
    assert single("3 grup, f 0.25 ve 42") == {"groups": 3, "f": 0.25}


def test_number_words_outside_group_patterns_are_not_values():
    assert values("iki yöntem var") == {}


# --- biçim ve aralık hataları, bilinmeyen parametreler, desteklenmeyen analizler ---------------

@pytest.mark.parametrize("text,field,raw", [
    ("alpha 0.0.5", "alpha", "0.0.5"),
    ("f %25", "f", "%25"),          # yüzde yalnızca alpha/power'da kesre çevrilir
    ("groups = 3,5", "groups", 3.5),  # ondalık grup sayısı → sunucu INVALID_VALUE
])
def test_malformed_values_are_passed_raw(text, field, raw):
    assert single(text)[field] == raw


def test_out_of_range_value_is_extracted_not_corrected():
    assert single("alfa 1,5") == {"alpha": 1.5}
    assert single("güç %150") == {"power": 1.5}


@pytest.mark.parametrize("text,name", [
    ("two-tailed", "tails"), ("çift kuyruklu", "tails"), ("η² = 0.06", "eta_squared"),
    ("partial eta squared 0.06", "eta_squared"), ("x = 3", "x"), ("predictors = 3", "predictors"),
])
def test_unknown_parameters(text, name):
    assert name in {m.target for m in parse(text).other}


@pytest.mark.parametrize("text,test", [
    ("t testi yap", "t2-indep"), ("independent t-test", "t2-indep"), ("paired t-test", "t-paired"),
    ("eşleştirilmiş örneklem t testi", "t-paired"), ("ki-kare testi", "chi2-contingency"),
    ("chi-square", "chi2-contingency"), ("çoklu regresyon", "multireg-r2"),
])
def test_contract_families_not_implemented(text, test):
    assert parse(text).tests[0][0] == test


@pytest.mark.parametrize("text", ["iki yönlü ANOVA", "two-way ANOVA", "repeated measures ANOVA", "ANCOVA",
                                  "korelasyon", "Mann-Whitney"])
def test_non_contract_analyses_unsupported(text):
    p = parse(text)
    assert p.tests and p.tests[0][0] == p.tests[0][1]  # sözleşme kimliği uydurulmaz; ifade aynen gider
    assert not p.anova


def test_one_way_anova_is_supported():
    p = parse("tek yönlü ANOVA")
    assert p.anova and not p.tests


def test_verbal_effect_size():
    assert parse("orta büyüklükte bir etki").verbal_effect
    assert parse("medium effect").verbal_effect
    assert parse("en küçük etki büyüklüğü").verbal_effect is None
    assert values("orta büyüklükte bir etki") == {}


def test_reset_and_help():
    assert parse("sıfırla").reset and parse("Yeni analiz").reset and parse("reset").reset
    assert parse("yardım").help and parse("help").help


def _readme_examples():
    import re
    from conftest import ROOT

    text = (ROOT / "README.md").read_text(encoding="utf-8")
    section = text[text.index("### Tanınan ifadeler"):text.index("### Eksik, çelişkili")]
    for line in section.splitlines():
        if m := re.match(r"\| `([\w-]+)` \| (.*) \|$", line):
            for example in re.findall(r"`([^`]+)`", m.group(2)):
                yield pytest.param(m.group(1), example, id=f"{m.group(1)}:{example}")


@pytest.mark.parametrize("name,example", list(_readme_examples()))
def test_readme_expression_tables_are_true(name, example):
    """README'deki "Tanınan ifadeler" tablolarının her örneği belgelenen alana/moda bağlanır."""
    p = parse(example)
    if name in rules.ANOVA_FIELDS:
        assert list(values(example)) == [name] and len(values(example)[name]) == 1
    else:
        assert sorted(p.modes) == [name]


def test_readme_limitations_are_true():
    assert parse("güç, 0.8").orphans == ["0.8"]
    assert single("toplam 1.000 katılımcı") == {"n_total": 1.0}
    assert values("bir grup") == values("on grup") == values("one group") == {}


def test_parse_is_deterministic():
    text = "Üç grup, etki büyüklüğü 0,25, alfa 0,05 ve güç 0,80; ayrıca 7 ve two-tailed."
    first = parse(text)
    for _ in range(20):
        assert parse(text) == first
