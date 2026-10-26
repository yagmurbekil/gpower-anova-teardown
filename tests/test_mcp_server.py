"""MCP sunucusu: araç kaydı/şemaları, motor üzerinden hesap, CLI ≡ MCP eşdeğerliği (CONTRACT §7)."""

import json
import os
import subprocess
import sys

import anyio
import pytest
from mcp import Client, StdioServerParameters

from conftest import BONUS_MODES, ROOT, assert_matches, load_public_vectors, run_cli, to_argv
from gpower_clone import cli, engine
from gpower_clone.mcp_server import OUTPUT_FIELDS, build_server

TOOL_NAMES = {"power_analysis", "calculate_anova_oneway", "validate_anova_input", "get_supported_analyses"}
APRIORI_ARGS = {"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5}


def mcp_session(fn):
    """Süreç içi MCP oturumunda `fn(client)` çalıştırır."""
    async def main():
        async with Client(build_server()) as client:
            return await fn(client)
    return anyio.run(main)


def call(name, arguments):
    return mcp_session(lambda c: c.call_tool(name, arguments))


def calls(name, argument_list):
    async def run(client):
        return [await client.call_tool(name, args) for args in argument_list]
    return mcp_session(run)


def text(result):
    assert len(result.content) == 1 and result.content[0].type == "text"
    return result.content[0].text


# --- kayıt ve şemalar ------------------------------------------------------------------------

@pytest.fixture(scope="module")
def tools():
    return {t.name: t for t in mcp_session(lambda c: c.list_tools()).tools}


def test_tools_registered(tools):
    assert set(tools) == TOOL_NAMES
    assert all(t.description for t in tools.values())


@pytest.mark.parametrize("name", ["power_analysis", "calculate_anova_oneway", "validate_anova_input"])
def test_calc_schema_uses_cli_field_names(tools, name):
    schema = tools[name].input_schema
    assert schema["type"] == "object"
    props = schema["properties"]
    assert set(props) == {"test", "mode", "f", "alpha", "power", "beta_alpha_ratio", "n_total", "groups"}
    assert props["mode"]["enum"] == list(cli.ANOVA_MODES)
    assert "integer" in props["groups"]["type"] and "integer" in props["n_total"]["type"]
    assert "number" in props["f"]["type"] and "number" in props["alpha"]["type"]
    for mode, fields in cli.ANOVA_MODES.items():
        assert mode in props["mode"]["description"] and all(f in props["mode"]["description"] for f in fields)


def test_required_fields(tools):
    assert tools["power_analysis"].input_schema["required"] == ["test", "mode"]  # CONTRACT §7
    assert tools["calculate_anova_oneway"].input_schema["required"] == ["mode"]
    assert tools["get_supported_analyses"].input_schema == {"type": "object", "properties": {},
                                                            "additionalProperties": False}


@pytest.mark.parametrize("name", sorted(TOOL_NAMES))
def test_schemas_close_unknown_fields(tools, name):
    assert tools[name].input_schema["additionalProperties"] is False


@pytest.mark.parametrize("name", ["power_analysis", "calculate_anova_oneway", "validate_anova_input"])
def test_schema_level_rejection(tools, name):
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(tools[name].input_schema)
    ok = {"test": "anova-oneway", **APRIORI_ARGS}
    assert validator.is_valid(ok)
    assert not validator.is_valid(dict(ok, foo=1))
    assert not validator.is_valid(dict(ok, tails=2))  # sözleşmenin başka ailesinin alanı


@pytest.mark.parametrize("tool", ["power_analysis", "calculate_anova_oneway"])
@pytest.mark.parametrize("extra", ["foo", "tails", "d"])
def test_unknown_field_rejected_by_server_even_if_schema_ignored(tool, extra):
    """Şemayı yok sayan istemci: alan sunucuya ulaşır, CLI ile aynı UNKNOWN_PARAM döner."""
    args = {"test": "anova-oneway", **APRIORI_ARGS, extra: 1}
    res = call(tool, args)
    assert _error(res) == ("UNKNOWN_PARAM", extra)
    assert text(res) + "\n" == run_cli(*to_argv(args)).stdout


# --- her mod motor üzerinden -----------------------------------------------------------------

def _anova_params():
    for v in load_public_vectors():
        marks = [pytest.mark.bonus] if v["input"]["mode"] in BONUS_MODES else []
        yield pytest.param(v, id=v["id"], marks=marks)


@pytest.mark.parametrize("tool", ["calculate_anova_oneway", "power_analysis"])
@pytest.mark.parametrize("vector", list(_anova_params()))
def test_every_mode_via_engine(vector, tool):
    args = dict(vector["input"])
    if tool == "calculate_anova_oneway":
        del args["test"]
    res = call(tool, args)
    assert not res.is_error, text(res)
    out = json.loads(text(res))
    assert res.structured_content == out
    assert_matches(out, vector["expected"], vector["id"])
    inputs = {k: v for k, v in vector["input"].items() if k not in ("test", "mode")}
    assert out == cli.compute(vector["input"]["mode"], inputs)  # aynı motor, aynı değer


def test_output_fields_table_matches_engine():
    vectors = {v["input"]["mode"]: v for v in load_public_vectors()}
    for mode, fields in OUTPUT_FIELDS.items():
        inputs = {k: v for k, v in vectors[mode]["input"].items() if k not in ("test", "mode")}
        assert tuple(cli.compute(mode, inputs)) == fields


# --- CLI ≡ MCP ------------------------------------------------------------------------------

def _all_public_vectors():
    with open(ROOT / "oracle" / "public_vectors.jsonl", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


ERROR_CASES = [
    {"test": "anova-oneway", "mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95},
    {"test": "anova-oneway", "mode": "post-hoc", "f": 0.25, "alpha": 0.05, "n_total": 100, "groups": 5, "power": 0.8},
    {"test": "anova-oneway", "mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5, "foo": 1},
    {"test": "anova-oneway", "mode": "a-priori", "f": 0.25, "alpha": 1.5, "power": 0.95, "groups": 5},
    {"test": "anova-oneway", "mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.05, "groups": 5},
    {"test": "anova-oneway", "mode": "a-priori", "f": 1e-6, "alpha": 0.05, "power": 0.95, "groups": 5},
    {"test": "anova-oneway", "mode": "post-hoc", "f": 0.25, "alpha": 0.05, "n_total": 5, "groups": 5},
    {"test": "anova-oneway", "mode": "post hoc"},
    {"test": "z-test", "mode": "a-priori"},
    {"mode": "a-priori"},
    {"test": "anova-oneway", "mode": "a-priori", "f": "0,05", "alpha": 0.05, "power": 0.95, "groups": 5},
    {"test": "anova-oneway", "mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5.0},
    {"test": "anova-oneway", "mode": "post-hoc", "f": 0.25, "alpha": 0.05, "n_total": "101", "groups": "5"},
]


@pytest.mark.parametrize("arguments", [v["input"] for v in _all_public_vectors()] + ERROR_CASES,
                         ids=[v["id"] for v in _all_public_vectors()] + [f"err-{i}" for i in range(len(ERROR_CASES))])
def test_cli_and_mcp_identical(arguments):
    """CONTRACT §7: 25 açık vektör (+ hata durumları) için CLI stdout satırı = MCP metin içeriği."""
    res = call("power_analysis", arguments)
    proc = run_cli(*to_argv(arguments))
    assert text(res) + "\n" == proc.stdout
    assert res.is_error == (proc.returncode != 0)


def test_calculate_anova_oneway_defaults_only_test():
    args = {"mode": "post-hoc", "f": 0.25, "alpha": 0.05, "n_total": 100, "groups": 5}
    assert text(call("calculate_anova_oneway", args)) == text(call("power_analysis", {"test": "anova-oneway", **args}))


# --- geçersiz/eksik girdiler, bilinmeyen mod ------------------------------------------------

def _error(res):
    assert res.is_error
    out = json.loads(text(res))
    assert set(out) == {"error", "code", "field"}
    return out["code"], out["field"]


@pytest.mark.parametrize("arguments,code,field", [
    ({"mode": "a-priori", "f": 0.25, "alpha": 0.05, "groups": 5}, "MISSING_PARAM", "power"),
    ({}, "MISSING_PARAM", "mode"),
    ({"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": None, "groups": 5}, "MISSING_PARAM", "power"),
    ({"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5, "tails": 2}, "UNKNOWN_PARAM", "tails"),
    ({"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5, "x": 1}, "UNKNOWN_PARAM", "x"),
    ({"mode": "a-priori", "f": "abc", "alpha": 0.05, "power": 0.95, "groups": 5}, "INVALID_VALUE", "f"),
    ({"mode": "a-priori", "f": True, "alpha": 0.05, "power": 0.95, "groups": 5}, "INVALID_VALUE", "f"),
    ({"mode": "a-priori", "f": [0.25], "alpha": 0.05, "power": 0.95, "groups": 5}, "INVALID_VALUE", "f"),
    ({"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5.5}, "INVALID_VALUE", "groups"),
    ({"mode": "a-priori", "f": -0.25, "alpha": 0.05, "power": 0.95, "groups": 5}, "OUT_OF_RANGE", "f"),
    ({"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 1}, "OUT_OF_RANGE", "groups"),
    ({"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.01, "groups": 5}, "INCONSISTENT", "power"),
    ({"mode": "a-priori", "f": 1e-6, "alpha": 0.05, "power": 0.95, "groups": 5}, "NO_SOLUTION", None),
    ({"mode": "anova"}, "UNSUPPORTED", "mode"),
    ({"test": "t2-indep", "mode": "a-priori"}, "UNSUPPORTED", "test"),
])
def test_calculate_errors(arguments, code, field):
    assert _error(call("calculate_anova_oneway", arguments)) == (code, field)


def test_unknown_tool():
    res = call("compute_t_test", {})
    assert res.is_error and json.loads(text(res))["code"] == "UNKNOWN_TOOL"


# --- doğrulama ve keşif araçları -------------------------------------------------------------

def test_validate_valid_does_not_compute():
    res = call("validate_anova_input", {"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5})
    assert not res.is_error
    out = res.structured_content
    assert out["valid"] is True and out["mode"] == "a-priori"
    assert out["inputs"] == {"f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5}
    assert "ncp" not in out and "n_total" not in out


@pytest.mark.parametrize("arguments,code,field", [
    ({"mode": "post-hoc", "f": 0.25, "alpha": 0.05, "groups": 5}, "MISSING_PARAM", "n_total"),
    ({"mode": "post-hoc", "f": 0.25, "alpha": 0, "n_total": 100, "groups": 5}, "OUT_OF_RANGE", "alpha"),
    ({"mode": "x"}, "UNSUPPORTED", "mode"),
    ({"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5, "n_total": 10},
     "UNKNOWN_PARAM", "n_total"),
])
def test_validate_errors(arguments, code, field):
    res = call("validate_anova_input", arguments)
    assert res.is_error
    out = res.structured_content
    assert out["valid"] is False and (out["code"], out["field"]) == (code, field)
    assert json.loads(text(res)) == out


def test_validate_agrees_with_cli_error():
    args = {"mode": "a-priori", "f": "0,25", "alpha": 0.05, "power": 0.95, "groups": 5}
    v = call("validate_anova_input", args).structured_content
    c = json.loads(text(call("calculate_anova_oneway", args)))
    assert (v["code"], v["field"], v["error"]) == (c["code"], c["field"], c["error"])


def test_supported_analyses():
    res = call("get_supported_analyses", {})
    assert not res.is_error
    out = res.structured_content
    assert out["contract_version"] == "1.0.0"
    [family] = out["supported"]
    assert family["test"] == "anova-oneway"
    modes = {m["mode"]: m for m in family["modes"]}
    assert set(modes) == set(cli.ANOVA_MODES)
    for mode, fields in cli.ANOVA_MODES.items():
        assert modes[mode]["required_inputs"] == list(fields)
        assert modes[mode]["status"] == ("bonus" if mode in BONUS_MODES else "required")
    assert set(out["not_implemented"]) == cli.CONTRACT_TESTS_NOT_IMPLEMENTED


def test_deterministic_and_no_engine_state():
    args = {"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.95, "groups": 5}
    first, second = calls("calculate_anova_oneway", [args, args])
    assert text(first) == text(second)
    assert engine.MAX_N_TOTAL == 10**9


# --- stdio taşıması --------------------------------------------------------------------------

_ENV = {"PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"}


def test_stdio_transport_end_to_end():
    params = StdioServerParameters(command=sys.executable, args=["-m", "gpower_clone.mcp_server"], env=_ENV)

    async def main():
        async with Client(params) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            res = await client.call_tool("calculate_anova_oneway", {"mode": "a-priori", "f": 0.25, "alpha": 0.05,
                                                                    "power": 0.95, "groups": 5})
            return names, res
    names, res = anyio.run(main)
    assert names == TOOL_NAMES
    assert text(res) + "\n" == run_cli("--test", "anova-oneway", "--mode", "a-priori", "--f", "0.25", "--alpha",
                                       "0.05", "--power", "0.95", "--groups", "5").stdout


def test_stdio_server_writes_nothing_but_protocol():
    # Girdi kapalıyken sunucu hiçbir protokol mesajı almaz; stdout boş kalmalı.
    proc = subprocess.run([sys.executable, "-m", "gpower_clone.mcp_server"], input="", capture_output=True,
                          text=True, env=dict(os.environ, **_ENV), timeout=60)
    assert proc.stdout == ""
