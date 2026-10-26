"""Kural tabanlı ajanın senaryo değerlendirmesi (`gpower-clone-eval`); LLM, API anahtarı ve ağ gerekmez.

    gpower-clone-eval                    # temel 10 + ek senaryolar; rapor evals/results/ altına
    gpower-clone-eval --check-expected   # yalnızca beklentilerin motorla tutarlılığı (ajan çalışmaz)

Her senaryo ajanla MCP (stdio) üzerinden iki kez çalıştırılır; ikinci çalıştırma determinizmi ölçer.
Başarılı her hesap, aynı girdilerle CLI alt sürecinde de çalıştırılır ve stdout satırı MCP metniyle
karşılaştırılır. Hiçbir sayı rapora çalıştırmadan yazılmaz.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import anyio

from gpower_clone.agent.audit import AuditLog
from gpower_clone.agent.cli import configure_output
from gpower_clone.agent.core import CALC_TOOL, VALIDATE_TOOL, Agent
from gpower_clone.agent.mcp_client import MCPConnection, ToolInvoker
from gpower_clone.agent.rules import LABELS
from gpower_clone.mcp_server import to_argv

ROOT = Path(__file__).resolve().parents[3]
QUESTIONS = ROOT / "evals" / "questions.jsonl"
EXTRA = ROOT / "evals" / "extra_questions.jsonl"
RESULTS = ROOT / "evals" / "results"
SRC = Path(__file__).resolve().parents[2]

TOL = 1e-6  # CONTRACT §6
INTEGER_FIELDS = {"n_total", "df1", "df2"}
COMPUTE_TOOLS = {CALC_TOOL, "power_analysis"}

METRICS = [  # (kontrol adı, rapordaki ad)
    ("params", "Parametre çıkarımı"),
    ("mode", "Analiz modu tespiti"),
    ("tool", "Doğru MCP aracı seçimi"),
    ("call_ok", "Hesap çağrısının başarısı"),
    ("oracle", "Beklenen çıktıyla eşleşme (CONTRACT §6 toleransı)"),
    ("cli_match", "MCP çıktısı = CLI stdout"),
    ("missing", "Eksik alanların doğru tespiti"),
    ("question", "Kullanıcıya doğru soru sorulması"),
    ("detection", "Çelişkili/geçersiz/desteklenmeyen girdinin tespiti"),
    ("no_calc", "Eksik/hatalı girdide hesap yapılmaması"),
]


def load_cases(path=QUESTIONS):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def turns(case):
    return case.get("turns") or [case["question"]]


def output_mismatches(actual, expected):
    """CONTRACT §6 kuralıyla uyuşmayan alanlar: tam sayılar birebir, ondalıklar 1e-6."""
    bad = []
    for key, exp in expected.items():
        got = actual.get(key) if isinstance(actual, dict) else None
        if got is None:
            bad.append(key)
        elif key in INTEGER_FIELDS:
            if got != exp:
                bad.append(key)
        else:
            diff = abs(got - exp)
            if not (diff <= TOL or (exp and diff / abs(exp) <= TOL)):
                bad.append(key)
    return bad


def params_match(arguments, expected):
    args = {k: v for k, v in arguments.items() if k != "test" or v != "anova-oneway"}
    return args == expected


def cli_stdout(arguments):
    """Aynı girdiyle gerçek CLI alt süreci (`python -m gpower_clone`)."""
    argv = to_argv({"test": "anova-oneway", **arguments})
    env = dict(os.environ, PYTHONPATH=str(SRC), PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, "-m", "gpower_clone", *argv], capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=60)
    return proc.stdout


def transcript(replies):
    return [{"text": r.text, "status": r.status,
             "tool_calls": [[c.name, c.arguments, c.output, c.is_error] for c in r.tool_calls]} for r in replies]


def score_case(case, replies, cli_runner=cli_stdout):
    last = replies[-1]
    calls = [c for r in replies for c in r.tool_calls]
    calc_calls = [c for c in calls if c.name == CALC_TOOL]
    checks = {}
    kind = case["kind"]
    if kind == "calculate":
        exp = case["expected_params"]
        last_calc = calc_calls[-1] if calc_calls else None
        checks["mode"] = last.mode == exp["mode"]
        checks["params"] = last_calc is not None and params_match(last_calc.arguments, exp)
        checks["tool"] = {c.name for c in calls if c.name in COMPUTE_TOOLS} == {case["expected_tool"]}
        checks["call_ok"] = last.status == "calculated" and bool(last.calculations)
        if checks["call_ok"]:
            ok = last.calculations[-1]
            checks["oracle"] = not output_mismatches(ok.output, case["expected_output"])
            checks["cli_match"] = cli_runner(ok.arguments) == json.dumps(ok.output, allow_nan=False) + "\n"
        else:
            checks["oracle"] = checks["cli_match"] = False
    elif kind == "ask":
        given = case["given_params"]
        checks["mode"] = last.mode == given["mode"]
        checks["params"] = last.params == {k: v for k, v in given.items() if k != "mode"}
        checks["missing"] = last.missing == case["missing"]
        checks["question"] = (last.status == "asked" and "?" in last.text
                              and all(LABELS[f] in last.text for f in case["missing"]))
        checks["no_calc"] = not calc_calls
    elif kind == "ask_mode":
        checks["question"] = last.status == "asked" and last.needs_mode and "?" in last.text
        checks["no_calc"] = not calc_calls
    elif kind == "clarify":
        if "expected_conflicts" in case:
            checks["detection"] = sorted(last.conflicts) == sorted(case["expected_conflicts"])
        else:
            checks["detection"] = last.ambiguous == case["expected_ambiguous"]
        checks["question"] = last.status == "asked" and "?" in last.text
        checks["no_calc"] = not calc_calls
    elif kind in ("error", "unsupported"):
        err = last.error or {}
        checks["detection"] = (last.status == kind and
                               {"code": err.get("code"), "field": err.get("field")} == case["expected_error"])
        checks["no_calc"] = not any(not c.is_error for c in calc_calls)
    else:
        raise ValueError(f"{case['id']}: bilinmeyen vaka türü {kind!r}")
    return {
        "id": case["id"], "kind": kind, "turns": turns(case), "checks": checks,
        "passed": all(checks.values()), "failed_checks": [k for k, v in checks.items() if not v],
        "transcript": transcript(replies),
    }


async def run_cases(cases, invoker, audit=None):
    out = {}
    for case in cases:
        agent = Agent(invoker, audit)  # her senaryo yeni konuşma
        out[case["id"]] = [await agent.ask(q) for q in turns(case)]
    return out


def summarize(rows, deterministic, mismatched, all_calls):
    def rate(key):
        relevant = [r for r in rows if key in r["checks"]]
        return {"ok": sum(1 for r in relevant if r["checks"][key]), "n": len(relevant)}

    transport_errors = sum(1 for c in all_calls if isinstance(c.output, dict) and c.output.get("code") == "MCP_ERROR")
    return {
        "scenarios": len(rows),
        "passed": sum(r["passed"] for r in rows),
        "failed": [r["id"] for r in rows if not r["passed"]],
        "metrics": {key: rate(key) for key, _ in METRICS},
        "mcp_calls_total": len(all_calls),
        "mcp_transport_errors": transport_errors,
        "deterministic": deterministic,
        "nondeterministic_cases": mismatched,
    }


def write_report(sets, summary, out_dir, commands):
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    rows = [r for _, set_rows in sets for r in set_rows]
    (out_dir / "report.json").write_text(json.dumps(
        {"generated": stamp, "agent": "rule-based", "summary": summary,
         "sets": {name: set_rows for name, set_rows in sets}}, ensure_ascii=False, indent=2), encoding="utf-8")

    def fmt(rate):
        return f"{rate['ok']}/{rate['n']}" if rate["n"] else "—"

    lines = ["# Kural tabanlı ajan değerlendirmesi", "",
             "Ajan dil modeli kullanmaz; token veya API maliyeti yoktur ve raporlanmaz.", "",
             f"- Zaman: {stamp}",
             f"- Senaryo: {summary['scenarios']} — başarılı {summary['passed']}, "
             f"başarısız {summary['scenarios'] - summary['passed']}"]
    for name, set_rows in sets:
        lines.append(f"  - {name}: {sum(r['passed'] for r in set_rows)}/{len(set_rows)} başarılı")
    lines += [f"- Determinizm (iki çalıştırmada aynı yanıtlar ve araç çağrıları): "
              f"{'evet' if summary['deterministic'] else 'hayır ' + str(summary['nondeterministic_cases'])}",
              f"- MCP çağrıları: {summary['mcp_calls_total']} (taşıma hatası {summary['mcp_transport_errors']})", "",
              "| Ölçüt | Sonuç |", "|---|---|"]
    lines += [f"| {label} | {fmt(summary['metrics'][key])} |" for key, label in METRICS]
    lines += ["", "| id | tür | sonuç | başarısız kontroller | araç çağrıları |", "|---|---|---|---|---|"]
    for r in rows:
        tools = ", ".join(f"{c[0]}{'!' if c[3] else ''}" for t in r["transcript"] for c in t["tool_calls"])
        lines.append(f"| {r['id']} | {r['kind']} | {'✓' if r['passed'] else '✗'} | "
                     f"{', '.join(r['failed_checks']) or '—'} | {tools} |")
    failures = [r for r in rows if not r["passed"]]
    lines += ["", "## Başarısız senaryolar", ""]
    if not failures:
        lines.append("Yok.")
    for r in failures:
        lines += [f"### {r['id']} ({r['kind']})", f"Başarısız kontroller: {', '.join(r['failed_checks'])}",
                  "Son yanıt:", "```", r["transcript"][-1]["text"], "```", ""]
    lines += ["", "## Komutlar", "", *(f"- `{c}`" for c in commands), "",
              "`!` hata dönen araç çağrısıdır (hata beklenen senaryolarda doğru davranıştır). Ayrıntılı "
              "yanıtlar ve araç girdi/çıktıları `report.json` ile `agent_calls.jsonl` içindedir.", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


async def run_eval(case_sets, out_dir, target=None, cli_runner=cli_stdout, commands=()):
    """case_sets: [(ad, vakalar)]. (satırlar, özet) döndürür ve raporu yazar."""
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "agent_calls.jsonl"
    log_path.unlink(missing_ok=True)
    all_cases = [c for _, cases in case_sets for c in cases]
    async with MCPConnection(target) as client:
        invoker = ToolInvoker(client)
        first = await run_cases(all_cases, invoker, AuditLog(log_path))
        second = await run_cases(all_cases, invoker)
    mismatched = [cid for cid in first if transcript(first[cid]) != transcript(second[cid])]
    sets = [(name, [score_case(c, first[c["id"]], cli_runner) for c in cases]) for name, cases in case_sets]
    rows = [r for _, set_rows in sets for r in set_rows]
    all_calls = [c for replies in first.values() for r in replies for c in r.tool_calls]
    summary = summarize(rows, not mismatched, mismatched, all_calls)
    write_report(sets, summary, out_dir, commands)
    return rows, summary


async def check_expected(cases, target=None):
    """Beklentilerin motorla tutarlılığı (ajan çalışmaz): (sorunlar, kontrol edilen, atlanan id'ler)."""
    problems, checked, skipped = [], [], []
    async with MCPConnection(target) as client:
        invoker = ToolInvoker(client)
        for case in cases:
            if case["kind"] == "calculate":
                outcome = await invoker.call(case["expected_tool"], case["expected_params"])
                if outcome.is_error:
                    problems.append(f"{case['id']}: araç hatası {outcome.output}")
                elif mism := output_mismatches(outcome.output, case["expected_output"]):
                    problems.append(f"{case['id']}: uyuşmayan alanlar {mism}")
            elif "expected_error" in case:
                tool = VALIDATE_TOOL if case["kind"] == "ask" else CALC_TOOL
                outcome = await invoker.call(tool, case["given_params"])
                got = {"code": outcome.output.get("code"), "field": outcome.output.get("field")}
                if not outcome.is_error or got != case["expected_error"]:
                    problems.append(f"{case['id']}: beklenen {case['expected_error']}, alınan {got}")
                elif case["kind"] == "ask" and case["missing"] != [case["expected_error"]["field"]]:
                    problems.append(f"{case['id']}: 'missing' ile expected_error.field tutarsız")
            else:
                skipped.append(case["id"])
                continue
            checked.append(case["id"])
    return problems, checked, skipped


def main(argv=None):
    configure_output()
    parser = argparse.ArgumentParser(prog="gpower-clone-eval", description=__doc__.splitlines()[0])
    parser.add_argument("--questions", default=str(QUESTIONS), help="temel senaryolar")
    parser.add_argument("--extra", default=str(EXTRA), help="ek senaryolar ('' ile atlanır)")
    parser.add_argument("--out", default=str(RESULTS))
    parser.add_argument("--check-expected", action="store_true",
                        help="ajanı çalıştırmadan beklentileri MCP üzerinden motorla karşılaştır")
    args = parser.parse_args(argv)
    case_sets = [("temel", load_cases(args.questions))]
    if args.extra:
        case_sets.append(("ek", load_cases(args.extra)))

    if args.check_expected:
        cases = [c for _, cs in case_sets for c in cs]
        problems, checked, skipped = anyio.run(check_expected, cases)
        for p in problems:
            print(p)
        bad = {p.split(":")[0] for p in problems}
        print(f"{len(checked) - len(bad & set(checked))}/{len(checked)} senaryonun beklentisi motorla uyumlu; "
              f"sunucu beklentisi olmayan (yalnızca ajan davranışı): {', '.join(skipped) or 'yok'}.")
        return 0 if not problems else 1

    extra_args = " ".join(argv if argv is not None else sys.argv[1:])
    commands = [f"gpower-clone-eval {extra_args}".strip() + "  (eşdeğeri: python -m gpower_clone.agent.evaluate)",
                "Bu raporu üreten değerlendirme dışındaki testler (ayrıca çalıştırılır): "
                "pytest tests/test_agent.py tests/test_agent_parser.py tests/test_mcp_server.py"]
    _, summary = anyio.run(lambda: run_eval(case_sets, Path(args.out), commands=commands))
    print(json.dumps({k: summary[k] for k in ("scenarios", "passed", "failed", "deterministic")},
                     ensure_ascii=False))
    print(f"Rapor: {Path(args.out) / 'report.md'}")
    return 0 if not summary["failed"] and summary["deterministic"] else 1


if __name__ == "__main__":
    sys.exit(main())
