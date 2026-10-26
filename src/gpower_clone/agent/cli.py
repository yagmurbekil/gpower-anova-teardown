"""`gpower-clone-agent`: kural tabanlı doğal dil ajanı (LLM yok, API anahtarı ve ağ gerekmez).

    gpower-clone-agent "3 grup, f 0,25, alfa 0,05, güç 0,80 için a priori analiz"
    gpower-clone-agent             # etkileşimli oturum (boş satırla çıkış)
    echo ... | gpower-clone-agent  # stdin'in her satırı bir tur
"""

import argparse
import json
import sys

import anyio

from gpower_clone.agent.audit import DEFAULT_LOG_PATH, AuditLog
from gpower_clone.agent.core import CALC_TOOL, SUPPORTED_TOOL, VALIDATE_TOOL, Agent
from gpower_clone.agent.mcp_client import MCPConnection, ToolCatalog, ToolInvoker

EXIT_OK, EXIT_SETUP = 0, 2
REQUIRED_TOOLS = {CALC_TOOL, VALIDATE_TOOL, SUPPORTED_TOOL}


class SetupError(Exception):
    """MCP sunucusu beklenen araçları sunmuyor."""


def configure_output():
    """Yönlendirilmiş çıktı Windows'ta yerel kod sayfasıyla (ör. cp1254) yazılır; '≈', '→' gibi
    karakterler UnicodeEncodeError ile çökmesin, kodlanamayan karakter değiştirilsin."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


def print_reply(reply, out=None):
    out = out or sys.stdout
    print(reply.text, file=out)
    for call in reply.calculations:
        # Motor çıktısı, açıklama metninden bağımsız olarak değiştirilmeden basılır.
        print(f"[motor] {call.name} {json.dumps(call.arguments, ensure_ascii=False)}", file=out)
        print(f"        → {json.dumps(call.output, ensure_ascii=False)}", file=out)
    print(file=out)
    out.flush()


def _turns(first, once):
    if first:
        yield first
        if once:
            return
    if sys.stdin is None:
        return
    if sys.stdin.isatty():
        while True:
            try:
                line = input("soru> ").strip()
            except EOFError:
                return
            if not line:
                return
            yield line
    else:
        for line in sys.stdin:
            if line.strip():
                yield line.strip()


async def run_session(first, *, log_path, once, target=None):
    async with MCPConnection(target) as client:
        catalog = ToolCatalog(client)
        await catalog.discover()
        if missing := REQUIRED_TOOLS - set(catalog.names):
            raise SetupError(f"MCP sunucusunda beklenen araçlar yok: {sorted(missing)}")
        agent = Agent(ToolInvoker(client), AuditLog(log_path))
        for question in _turns(first, once):
            print_reply(await agent.ask(question))
    return EXIT_OK


def main(argv=None):
    configure_output()
    parser = argparse.ArgumentParser(prog="gpower-clone-agent", description=__doc__.splitlines()[0])
    parser.add_argument("question", nargs="*", help="doğal dilde istek (verilmezse etkileşimli ya da stdin)")
    parser.add_argument("--log", default=str(DEFAULT_LOG_PATH), help="araç çağrısı kaydı (JSONL)")
    parser.add_argument("--once", action="store_true", help="yalnızca verilen isteği yanıtla ve çık")
    args = parser.parse_args(argv)
    first = " ".join(args.question).strip() or None
    try:
        return anyio.run(lambda: run_session(first, log_path=args.log, once=args.once))
    except SetupError as exc:
        print(f"Kurulum hatası: {exc}", file=sys.stderr)
        return EXIT_SETUP
    except KeyboardInterrupt:
        return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
