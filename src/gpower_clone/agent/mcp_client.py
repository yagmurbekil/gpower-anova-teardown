"""MCP istemci tarafı: bağlantı, araç keşfi ve araç çağrısı ayrı sınıflardadır."""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from mcp import Client, StdioServerParameters

_SRC_DIR = Path(__file__).resolve().parents[2]  # .../src (kaynak ağacından çalıştırma için)


def stdio_server_parameters():
    """`python -m gpower_clone.mcp_server` alt süreci. Ortam, SDK'nın güvenli değişken listesiyle
    sınırlıdır; kullanıcının diğer ortam değişkenleri sunucuya aktarılmaz."""
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "gpower_clone.mcp_server"],
        env={"PYTHONPATH": str(_SRC_DIR), "PYTHONIOENCODING": "utf-8"},
    )


class MCPConnection:
    """MCP oturumunu açar/kapatır. `target`: StdioServerParameters (varsayılan) ya da testlerde
    süreç içi bir `Server` örneği."""

    def __init__(self, target=None):
        self._target = target if target is not None else stdio_server_parameters()
        self._client = None

    async def __aenter__(self):
        self._client = Client(self._target)
        await self._client.__aenter__()
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        client, self._client = self._client, None
        try:
            return await client.__aexit__(exc_type, exc, tb)
        except BaseExceptionGroup as group:
            # SDK'nın görev grupları gövdedeki hatayı iç içe gruplara sarar;
            # yalnızca o hata varsa özgün istisnanın kendisi yayılsın.
            if exc is not None and _only_leaf(group) is exc:
                return False
            raise


def _only_leaf(exc):
    while isinstance(exc, BaseExceptionGroup) and len(exc.exceptions) == 1:
        exc = exc.exceptions[0]
    return exc


class ToolCatalog:
    """Sunucudaki araçları keşfeder ve Claude API araç tanımlarına çevirir."""

    def __init__(self, client):
        self._client = client
        self.tools = []

    async def discover(self):
        result = await self._client.list_tools()
        self.tools = [
            {"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
            for t in result.tools
        ]
        return self.tools

    @property
    def names(self):
        return [t["name"] for t in self.tools]


@dataclass
class ToolOutcome:
    name: str
    arguments: dict
    output: object  # aracın döndürdüğü JSON (değiştirilmeden)
    is_error: bool

    @property
    def text(self):
        return json.dumps(self.output, ensure_ascii=False)


class ToolInvoker:
    """Araç çağırır; sonucu yorumlamaz, yalnızca JSON'a çözer."""

    def __init__(self, client):
        self._client = client

    async def call(self, name, arguments):
        try:
            result = await self._client.call_tool(name, arguments)
        except Exception as exc:  # taşıma/protokol hatası: ajan bunu araç hatası olarak görür
            output = {"error": f"MCP çağrısı başarısız: {exc}", "code": "MCP_ERROR", "field": None}
            return ToolOutcome(name, arguments, output, True)
        output = result.structured_content
        if output is None:
            text = "".join(getattr(block, "text", "") for block in result.content)
            try:
                output = json.loads(text)
            except ValueError:
                output = {"text": text}
        return ToolOutcome(name, arguments, output, bool(result.is_error))
