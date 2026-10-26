"""Kural tabanlı ajan + MCP: araç seçimi, sonuç aktarımı, eksik/çelişkili/hatalı girdi, çok turlu konuşma,
LLM/ağ bağımsızlığı, log maskeleme, Windows kod sayfası, determinizm ve değerlendirme düzeneği."""

import json
import os
import socket
import subprocess
import sys

import anyio
import pytest

from conftest import ROOT
from gpower_clone import cli
from gpower_clone.agent import evaluate
from gpower_clone.agent.audit import AuditLog, redact
from gpower_clone.agent.core import CALC_TOOL, SUPPORTED_TOOL, VALIDATE_TOOL, Agent
from gpower_clone.agent.mcp_client import MCPConnection, ToolInvoker, ToolOutcome, stdio_server_parameters
from gpower_clone.agent.rules import LABELS
from gpower_clone.mcp_server import build_server

ENV = {"PYTHONPATH": str(ROOT / "src")}


def converse(*questions, audit=None, invoker_wrapper=None):
    """Süreç içi MCP sunucusuyla tek konuşma; her tur için Reply listesi."""
    async def main():
        async with MCPConnection(build_server()) as client:
            invoker = ToolInvoker(client)
            agent = Agent(invoker_wrapper(invoker) if invoker_wrapper else invoker, audit)
            return [await agent.ask(q) for q in questions]
    return anyio.run(main)


def tools_used(reply):
    return [c.name for c in reply.tool_calls]


def engine(mode, **values):
    out, code = cli.run(["--test", "anova-oneway", "--mode", mode,
                         *sum(([f"--{k}", repr(v) if isinstance(v, float) else str(v)] for k, v in values.items()), [])])
    assert code == 0
    return out


# --- doğru araç, gerçek sonuç -----------------------------------------------------------------

def test_calculation_uses_mcp_tools_and_relays_engine_output():
    [r] = converse("Üç grup, etki büyüklüğü 0,25, alfa 0,05 ve güç 0,80.")
    assert r.status == "calculated" and r.mode == "a-priori"
    assert tools_used(r) == [SUPPORTED_TOOL, VALIDATE_TOOL, CALC_TOOL]
    [calc] = r.calculations
    assert calc.arguments == {"mode": "a-priori", "groups": 3, "f": 0.25, "alpha": 0.05, "power": 0.8}
    assert calc.output == r.result == engine("a-priori", f=0.25, alpha=0.05, power=0.8, groups=3)
    assert "n_total = 159" in r.text
    assert repr(calc.output["actual_power"]) in r.text  # tam değer metinde, değiştirilmeden


@pytest.mark.parametrize("text,mode,values", [
    ("Post hoc: 5 grup, toplam N = 100, f 0,25, alfa 0,05", "post-hoc",
     {"f": 0.25, "alpha": 0.05, "n_total": 100, "groups": 5}),
    ("compromise analizi: 5 grup, toplam N = 100, f = 0.25, β/α oranı 1", "compromise",
     {"f": 0.25, "beta_alpha_ratio": 1, "n_total": 100, "groups": 5}),
    ("criterion: 5 groups, total N = 100, f = 0.25, power = 0.95", "criterion",
     {"f": 0.25, "power": 0.95, "n_total": 100, "groups": 5}),
    ("sensitivity: 5 grup, toplam 100 katılımcı, alfa 0.05, güç 0.95", "sensitivity",
     {"alpha": 0.05, "power": 0.95, "n_total": 100, "groups": 5}),
])
def test_every_mode_through_agent(text, mode, values):
    [r] = converse(text)
    assert r.status == "calculated" and r.mode == mode
    assert r.result == engine(mode, **values)


def test_mode_inferred_only_from_exact_field_set():
    [r] = converse("Effect size f is 0.40, alpha is 0.05. There are four groups and I want 80 percent power.")
    assert r.mode == "a-priori" and r.result["n_total"] == 76
    assert "örtüşüyor" in r.text  # modun nereden çıkarıldığı yazılır


# --- eksik parametreler ----------------------------------------------------------------------

def test_missing_params_ask_without_calculation():
    [r] = converse("%80 güç için gereken örneklem sayısını hesapla.")
    assert r.status == "asked" and r.mode == "a-priori"
    assert r.missing == ["f", "alpha", "groups"]
    assert CALC_TOOL not in tools_used(r)
    assert "?" in r.text and all(LABELS[f] in r.text for f in r.missing)


def test_no_mode_asks_for_mode():
    [r] = converse("ANOVA için güç analizi yap.")
    assert r.status == "asked" and r.needs_mode
    assert "Hangi analiz modunu kullanmak istiyorsunuz?" in r.text
    assert "Gerekli mod ve parametreleri belirtir misiniz?" in r.text
    assert tools_used(r) == [SUPPORTED_TOOL]


def test_partial_fields_without_mode_list_compatible_modes():
    [r] = converse("f 0,25 ve alfa 0,05")
    assert r.needs_mode and "a-priori, post-hoc" in r.text


def test_verbal_effect_size_is_not_converted():
    [r] = converse("Üç gruplu deneyde orta büyüklükte bir etki bekliyorum; alpha 0.05, güç 0.80. "
                   "Örneklem büyüklüğü ne olmalı?")
    assert r.missing == ["f"] and "varsayılan bir f değerine çevirmiyorum" in r.text
    assert "f" not in r.params


def test_multi_turn_completion_keeps_previous_values():
    r1, r2, r3 = converse("Dört grup ve %80 güç için gereken örneklem sayısını hesapla.", "f 0,25", "alfa 0,05")
    assert r1.missing == ["f", "alpha"] and r2.missing == ["alpha"]
    assert r2.params == {"groups": 4, "power": 0.8, "f": 0.25}
    assert r3.status == "calculated" and r3.result["n_total"] == 180
    assert CALC_TOOL not in tools_used(r1) + tools_used(r2)


def test_later_turn_updates_value_with_note_and_reset_clears():
    r1, r2, r3, r4 = converse("a priori: 4 grup, f 0.25, alfa 0.05, güç 0.8", "alfa 0,01 olsun", "sıfırla", "f 0.3")
    assert r1.result["n_total"] == 180
    assert r2.result == engine("a-priori", f=0.25, alpha=0.01, power=0.8, groups=4)
    assert "alpha 0.05 → 0.01 olarak güncellendi" in r2.text
    assert r3.status == "info" and r3.params == {}
    assert r4.needs_mode and r4.params == {"f": 0.3}


def test_per_group_n_becomes_total_when_groups_known():
    r1, r2 = converse("Sensitivity: her grupta 20 kişi, alfa 0.05, güç 0.95", "5 grup")
    assert r1.missing == ["n_total", "groups"]
    assert r2.status == "calculated" and r2.params["n_total"] == 100
    assert "n_total = 20 × 5 = 100" in r2.text


# --- çelişkili / belirsiz girdiler ------------------------------------------------------------

def test_conflicting_values_ask_without_tool_call():
    [r] = converse("Üç grup, f = 0.25, alfa 0.05 ve alfa 0.01, güç 0.80 ile a priori analiz yap.")
    assert r.status == "asked" and r.conflicts == {"alpha": [0.05, 0.01]}
    assert tools_used(r) == [SUPPORTED_TOOL]
    assert "Hangisi geçerli?" in r.text


def test_conflict_resolved_in_next_turn():
    _, r = converse("a priori, 3 grup, f 0.25, güç 0.8, alfa 0.05 ve alfa 0.01", "alfa 0.05")
    assert r.status == "calculated" and r.result["n_total"] == 159


def test_per_group_and_total_conflict():
    [r] = converse("post hoc: 4 grup, her grupta 20 kişi, toplam N = 100, f 0.25, alfa 0.05")
    assert r.conflicts == {"n_total": [100, 80]} and not r.calculations


def test_conflicting_modes_and_orphan_number():
    [r1] = converse("a priori ve post hoc analiz yap: 3 grup, f 0.25.")
    assert r1.conflicts == {"mode": ["a-priori", "post-hoc"]} and not r1.calculations
    [r2] = converse("3 grup, f 0.25, alfa 0.05, güç 0.8 ve 42 ile a priori analiz.")
    assert r2.ambiguous == ["42"] and not r2.calculations and "“42”" in r2.text


# --- sözleşme hata kodları ---------------------------------------------------------------------

@pytest.mark.parametrize("text,code,field", [
    ("Üç grup, f = 0,25, alfa 1,5 ve güç 0,80 ile a priori analiz yap.", "OUT_OF_RANGE", "alpha"),
    ("4 grup, f = 0.25, alpha 0.0.5 ve power 0.8 için a priori.", "INVALID_VALUE", "alpha"),
    ("a priori: 3.5 grup, f 0.25, alfa 0.05, güç 0.8", "INVALID_VALUE", "groups"),
    ("One-way ANOVA, a priori: f = 0.25, alpha = 0.05, power = 0.8, 3 groups, two-tailed.", "UNKNOWN_PARAM", "tails"),
    ("a priori: 3 grup, f 0.25, alfa 0.05, güç 0.8, toplam N = 60", "UNKNOWN_PARAM", "n_total"),
    ("A priori analiz: 5 grup, f 0,25, alfa 0,05, güç 0,05.", "INCONSISTENT", "power"),
    ("post hoc: 5 grup, toplam N = 5, f 0.25, alfa 0.05", "INCONSISTENT", "n_total"),
    ("a priori: 5 grup, f 0.000001, alfa 0.05, güç 0.95", "NO_SOLUTION", None),
])
def test_contract_error_codes_are_relayed(text, code, field):
    [r] = converse(text)
    assert r.status == "error" and (r.error["code"], r.error["field"]) == (code, field)
    assert not r.calculations
    assert f"[{code}]" in r.text


def test_invalid_value_is_dropped_and_can_be_corrected():
    r1, r2 = converse("a priori: 3 grup, f 0.25, alfa 1,5, güç 0.8", "alfa 0,05")
    assert r1.error["code"] == "OUT_OF_RANGE" and "alpha" not in r1.params
    assert r2.status == "calculated" and r2.result["n_total"] == 159


def test_unsupported_analysis_relays_server_code():
    [r] = converse("İki bağımsız grup için t testi ile güç analizi yap, d = 0.5.")
    assert r.status == "unsupported" and r.error == {
        "code": "UNSUPPORTED", "field": "test",
        "error": "t2-indep bu uygulamada desteklenmiyor (yalnızca anova-oneway)"}
    assert tools_used(r) == [SUPPORTED_TOOL, VALIDATE_TOOL] and r.params == {}
    assert "anova-oneway" in r.text


def test_mcp_transport_error_is_reported():
    class FailingCalc:
        def __init__(self, inner):
            self.inner = inner

        async def call(self, name, arguments):
            if name == CALC_TOOL:
                return ToolOutcome(name, arguments, {"error": "pipe closed", "code": "MCP_ERROR", "field": None}, True)
            return await self.inner.call(name, arguments)

    [r] = converse("a priori: 3 grup, f 0.25, alfa 0.05, güç 0.8", invoker_wrapper=FailingCalc)
    assert r.status == "error" and r.error["code"] == "MCP_ERROR" and not r.calculations
    assert r.params == {"groups": 3, "f": 0.25, "alpha": 0.05, "power": 0.8}  # değerler kaybolmaz


def test_invoker_converts_transport_exception():
    class Broken:
        async def call_tool(self, name, arguments):
            raise ConnectionError("pipe closed")

    outcome = anyio.run(lambda: ToolInvoker(Broken()).call(CALC_TOOL, {}))
    assert outcome.is_error and outcome.output["code"] == "MCP_ERROR"


# --- determinizm ------------------------------------------------------------------------------

def test_same_conversation_is_deterministic():
    turns = ["Dört grup ve %80 güç için gereken örneklem sayısını hesapla.", "f 0,25", "alfa 1,5", "alfa 0,05"]
    runs = [converse(*turns) for _ in range(3)]
    flat = [[(r.text, r.status, [(c.name, c.arguments, c.output) for c in r.tool_calls]) for r in run] for run in runs]
    assert flat[0] == flat[1] == flat[2]


# --- LLM, API anahtarı ve ağ bağımsızlığı ------------------------------------------------------

def test_no_network_connections(monkeypatch):
    attempts = []
    real_connect = socket.socket.connect

    def guarded_connect(sock, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            attempts.append(address)
            raise OSError("ağ erişimi testte engellendi")
        return real_connect(sock, address)

    real_getaddrinfo = socket.getaddrinfo

    def guarded_getaddrinfo(host, *args, **kwargs):
        if host not in ("127.0.0.1", "::1", "localhost", None):
            attempts.append(host)
            raise OSError("DNS testte engellendi")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    r1, r2 = converse("a priori: 3 grup, f 0.25, alfa 0.05", "güç 0.8")
    assert r2.status == "calculated" and attempts == []


def _clean_env(tmp_path, **extra):
    env = {k: v for k, v in os.environ.items()
           if not any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "ANTHROPIC", "OPENAI"))}
    env.update(PYTHONPATH=str(ROOT / "src"), HOME=str(tmp_path), USERPROFILE=str(tmp_path), **extra)
    return env


def test_agent_cli_runs_without_api_key_and_without_llm_packages(tmp_path):
    """LLM SDK'ları içe aktarılamaz hâle getirilir; ajan stdio MCP sunucusuyla yine çalışır."""
    code = ("import sys\n"
            "for name in ('anthropic', 'openai', 'google.generativeai', 'mistralai', 'cohere', 'ollama'):\n"
            "    sys.modules[name] = None\n"
            "from gpower_clone.agent.cli import main\n"
            "rc = main(sys.argv[1:])\n"
            "bad = [n for n in sys.modules if n.split('.')[0] in ('anthropic', 'openai') and sys.modules[n]]\n"
            "assert not bad, bad\n"
            "sys.exit(rc)\n")
    proc = subprocess.run([sys.executable, "-c", code, "--once", "--log", str(tmp_path / "l.jsonl"),
                           "a priori: 4 grup, f 0,25, alfa 0,05, güç 0,80"],
                          capture_output=True, text=True, encoding="utf-8", timeout=120,
                          env=_clean_env(tmp_path, PYTHONIOENCODING="utf-8"))
    assert proc.returncode == 0, proc.stderr
    assert "n_total = 180" in proc.stdout and '"n_total": 180' in proc.stdout
    assert "Traceback" not in proc.stderr


def test_agent_cli_piped_multi_turn_on_turkish_windows_codepage(tmp_path):
    """Türkçe Windows'ta yönlendirilmiş çıktı cp1254'tür; '≈', '→' gibi karakterler çökertmemeli."""
    stdin = "Dört grup ve %80 güç için gereken örneklem sayısını hesapla.\nf 0,25\nalfa 0,05\n"
    proc = subprocess.run([sys.executable, "-m", "gpower_clone.agent", "--log", str(tmp_path / "l.jsonl")],
                          input=stdin.encode("cp1254"), capture_output=True, timeout=120,
                          env=_clean_env(tmp_path, PYTHONIOENCODING="cp1254"))
    out = proc.stdout.decode("cp1254")
    assert proc.returncode == 0, proc.stderr.decode("cp1254", "replace")
    assert out.count("Hesaplama için eksik") == 2 and "n_total = 180" in out
    assert len((tmp_path / "l.jsonl").read_text(encoding="utf-8").splitlines()) == 5


@pytest.mark.parametrize("module", ["gpower_clone.agent", "gpower_clone.agent.evaluate"])
def test_help_on_legacy_codepage(module, tmp_path):
    proc = subprocess.run([sys.executable, "-m", module, "--help"], capture_output=True, timeout=60,
                          env=_clean_env(tmp_path, PYTHONIOENCODING="cp1254"))
    assert proc.returncode == 0 and b"usage:" in proc.stdout


def test_no_llm_code_left_in_package():
    src = ROOT / "src" / "gpower_clone"
    assert not (src / "agent" / "llm.py").exists()
    text = "\n".join(p.read_text(encoding="utf-8") for p in src.rglob("*.py")).lower()
    for marker in ("import anthropic", "from anthropic", "api_key", "claude-", "tokens_out = r"):
        assert marker not in text, marker
    for path in ("pyproject.toml", "requirements.txt"):
        assert "anthropic" not in (ROOT / path).read_text(encoding="utf-8")


# --- denetim kaydı ve gizli bilgiler ----------------------------------------------------------

def test_audit_log_contract_format(tmp_path):
    log = tmp_path / "agent_calls.jsonl"
    converse("a priori: 3 grup, f 0.25, alfa 0.05, güç 0.8", audit=AuditLog(log))
    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [e["tool"] for e in entries] == [SUPPORTED_TOOL, VALIDATE_TOOL, CALC_TOOL]
    for e in entries:
        assert {"ts", "question", "tool_input", "tool_output", "tokens_in", "tokens_out"} <= set(e)
        assert (e["tokens_in"], e["tokens_out"]) == (0, 0) and e["agent"] == "rule-based"
    assert entries[-1]["tool_output"]["n_total"] == 159


def test_secrets_never_logged(tmp_path, monkeypatch):
    secret_env = "opaque-secret-value-123456"
    monkeypatch.setenv("MY_SERVICE_TOKEN", secret_env)
    key = "sk-proj-TESTSECRET0123456789"
    log = tmp_path / "agent_calls.jsonl"
    converse(f"anahtarım {key}, parola {secret_env}; a priori: 3 grup, f 0.25, alfa 0.05, güç 0.8",
             audit=AuditLog(log))
    content = log.read_text(encoding="utf-8")
    assert key not in content and "TESTSECRET" not in content and secret_env not in content
    assert "[REDACTED]" in content
    assert "MY_SERVICE_TOKEN" not in content and "PATH" not in content  # ortam değişkenleri yazılmaz


def test_redact_nested_structures(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "hunter2-hunter2")
    assert redact({"a": ["x hunter2-hunter2 y", {"k": "ghp_" + "a" * 30}]}) == {"a": ["x [REDACTED] y",
                                                                                     {"k": "[REDACTED]"}]}


def test_mcp_server_subprocess_receives_no_user_secrets(monkeypatch):
    monkeypatch.setenv("MY_SERVICE_TOKEN", "opaque-secret-value-123456")
    from mcp.client.stdio import get_default_environment

    merged = {**get_default_environment(), **(stdio_server_parameters().env or {})}
    assert "MY_SERVICE_TOKEN" not in merged and "opaque-secret-value-123456" not in merged.values()


# --- değerlendirme düzeneği -------------------------------------------------------------------

def test_eval_sets():
    core = evaluate.load_cases(evaluate.QUESTIONS)
    extra = evaluate.load_cases(evaluate.EXTRA)
    assert [c["id"] for c in core] == [f"Q{i:02d}" for i in range(1, 11)]
    assert len({c["id"] for c in core + extra}) == len(core) + len(extra)
    problems, checked, skipped = anyio.run(lambda: evaluate.check_expected(core + extra, target=build_server()))
    assert problems == [] and len(checked) == 20 and skipped == ["E01", "E06", "E10", "E14"]


def test_check_expected_detects_wrong_expectations():
    cases = {c["id"]: c for c in evaluate.load_cases()}
    wrong_calc = dict(cases["Q01"], expected_output=dict(cases["Q01"]["expected_output"], n_total=181))
    wrong_ask = dict(cases["Q08"], expected_error={"code": "MISSING_PARAM", "field": "power"})
    problems, _, _ = anyio.run(lambda: evaluate.check_expected([wrong_calc, wrong_ask], target=build_server()))
    assert [p.split(":")[0] for p in problems] == ["Q01", "Q08"]


def test_run_eval_report(tmp_path):
    sets = [("temel", evaluate.load_cases(evaluate.QUESTIONS)), ("ek", evaluate.load_cases(evaluate.EXTRA))]
    rows, summary = anyio.run(lambda: evaluate.run_eval(sets, tmp_path, target=build_server(),
                                                        commands=["pytest tests/test_agent.py"]))
    assert summary["scenarios"] == 24 and summary["failed"] == [] and summary["deterministic"]
    assert summary["metrics"]["cli_match"] == {"ok": 12, "n": 12}
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "24 — başarılı 24" in report and "pytest tests/test_agent.py" in report
    assert "API maliyeti yoktur" in report and "tokens" not in report.lower()
    assert (tmp_path / "agent_calls.jsonl").exists()


def test_scoring_rejects_guessing_and_wrong_params():
    cases = {c["id"]: c for c in evaluate.load_cases()}
    from gpower_clone.agent.core import Reply, ToolCall

    guessed = {"mode": "a-priori", "f": 0.25, "alpha": 0.05, "power": 0.9, "groups": 4}  # alpha uyduruldu
    out = engine("a-priori", f=0.25, alpha=0.05, power=0.9, groups=4)
    reply = Reply(text="N = 232", status="calculated", mode="a-priori", params=guessed,
                  tool_calls=[ToolCall(CALC_TOOL, guessed, out, False)], result=out)
    row = evaluate.score_case(cases["Q08"], [reply], cli_runner=lambda a: "")
    assert not row["passed"] and {"no_calc", "missing", "params"} <= set(row["failed_checks"])

    wrong = dict(cases["Q01"]["expected_params"], groups=3)
    out = engine("a-priori", f=0.25, alpha=0.05, power=0.8, groups=3)
    reply = Reply(text="", status="calculated", mode="a-priori", tool_calls=[ToolCall(CALC_TOOL, wrong, out, False)])
    row = evaluate.score_case(cases["Q01"], [reply], cli_runner=lambda a: json.dumps(out) + "\n")
    assert {"params", "oracle"} <= set(row["failed_checks"]) and row["checks"]["cli_match"]
