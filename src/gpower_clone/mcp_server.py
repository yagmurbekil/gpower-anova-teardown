"""MCP sunucusu (CONTRACT §7): CLI ile aynı alan adları, aynı JSON çıktı/hata, aynı motor.

Hesap ve doğrulama burada yeniden yazılmaz. Araç argümanları CLI'nin `--alan değer` argv biçimine
çevrilir ve `cli.run` / `cli.validate` çağrılır; böylece hata kodları, doğrulama sırası ve sayı biçimi
CLI ile birebir aynı kalır. Düşük seviyeli `Server` API'si kullanılır, çünkü MCPServer (eski FastMCP)
argümanları pydantic modeline süzer: tanınmayan alanları sessizce atar ve eksik alanlarda sözleşme dışı
bir hata metni üretir.

stdout yalnızca MCP protokolüne aittir; log ve uyarılar stderr'e gider.
"""

import json
import logging
import sys

import anyio
import mcp_types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from gpower_clone import CONTRACT_VERSION, NAME, cli

TEST_ID = "anova-oneway"

# CONTRACT §4.3 çıktı tablosu (zorunlu alanlar); yalnızca bilgi amaçlı, hesap motordan gelir.
OUTPUT_FIELDS = {
    "a-priori": ("ncp", "critical_f", "df1", "df2", "n_total", "actual_power"),
    "post-hoc": ("ncp", "critical_f", "df1", "df2", "power"),
    "compromise": ("ncp", "critical_f", "df1", "df2", "alpha", "beta", "power"),
    "criterion": ("ncp", "critical_f", "df1", "df2", "alpha"),
    "sensitivity": ("ncp", "critical_f", "df1", "df2", "f"),
}
REQUIRED_MODES = ("a-priori", "post-hoc")  # CONTRACT §3: diğerleri bonus

# CONTRACT §5 aralıkları (yalnızca anova-oneway alanları), şema ve bilgi metni için.
FIELD_INFO = {
    "f": ("number", "Etki büyüklüğü f (Cohen's f), > 0"),
    "alpha": ("number", "Anlamlılık düzeyi α, 0 < alpha < 1"),
    "power": ("number", "Hedef güç (1 − β), 0 < power < 1"),
    "beta_alpha_ratio": ("number", "β/α oranı (compromise modu), > 0"),
    "n_total": ("integer", "Toplam örneklem büyüklüğü N, tam sayı ≥ 2 (groups'tan büyük olmalı)"),
    "groups": ("integer", "Grup sayısı k, tam sayı ≥ 2"),
}

_VALUE_NOTE = (
    "Sayı olarak verin; CLI biçiminde metin ('0.05') de kabul edilir ve CLI ile aynı kurallarla "
    "doğrulanır (ondalık ayırıcı nokta, tam sayı alanlarında ondalık yok)."
)

log = logging.getLogger("gpower_clone.mcp_server")


# --- argüman → CLI argv ---------------------------------------------------------------------

def _to_text(value):
    """JSON değerini CLI'ye verilecek metne çevirir; dönüşüm CLI doğrulamasını atlatmaz."""
    if isinstance(value, bool):  # bool, int'in alt sınıfı; "1"e dönüşmesin
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)  # tam double; inf/nan → "inf"/"nan" → CLI INVALID_VALUE
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)  # liste/nesne → CLI INVALID_VALUE


def to_argv(arguments):
    """{alan: değer} → ["--alan", "değer", ...]. `null` değerli alan verilmemiş sayılır."""
    argv = []
    for key, value in (arguments or {}).items():
        if value is None:
            continue
        argv += [f"--{key}", _to_text(value)]
    return argv


def _with_default_test(arguments):
    args = dict(arguments or {})
    if args.get("test") is None:
        args = {"test": TEST_ID, **{k: v for k, v in args.items() if k != "test"}}
    return args


# --- araç gövdeleri (MCP'den bağımsız, test edilebilir) --------------------------------------

def power_analysis(arguments):
    """CONTRACT §7 aracı: (CLI stdout JSON nesnesi, CLI çıkış kodu)."""
    return cli.run(to_argv(arguments))


def calculate_anova_oneway(arguments):
    """`test` verilmezse anova-oneway kabul edilir; gerisi `power_analysis` ile aynı."""
    return power_analysis(_with_default_test(arguments))


def validate_anova_input(arguments):
    """Hesap yapmadan CLI doğrulamasını çalıştırır (test/mod, alanlar, biçim, aralık).

    INCONSISTENT (ör. power ≤ alpha, n_total ≤ groups) ve NO_SOLUTION motor içinde saptanır;
    bu yüzden burada değil, hesap sırasında raporlanır.
    """
    try:
        test, mode, values = cli.validate(cli.parse_args(to_argv(_with_default_test(arguments))))
    except cli.InputError as exc:
        return {"valid": False, "error": str(exc), "code": exc.code, "field": exc.field}, exc.exit_code
    except Exception as exc:  # beklenmeyen durum: iç hata
        print(f"gpower-clone-mcp: iç hata: {exc!r}", file=sys.stderr)
        return {"valid": False, "error": f"İç hata: {exc}", "code": "INTERNAL_ERROR", "field": None}, cli.EXIT_INTERNAL
    return {
        "valid": True,
        "test": test,
        "mode": mode,
        "inputs": values,
        "note": "Alan, biçim ve aralık kontrolleri geçti. Tutarlılık (INCONSISTENT) ve çözüm varlığı "
                "(NO_SOLUTION) hesap sırasında denetlenir.",
    }, cli.EXIT_OK


def supported_analyses():
    return {
        "contract_version": CONTRACT_VERSION,
        "name": NAME,
        "supported": [{
            "test": TEST_ID,
            "title": "F tests – ANOVA: Fixed effects, omnibus, one-way",
            "modes": [
                {
                    "mode": mode,
                    "status": "required" if mode in REQUIRED_MODES else "bonus",
                    "required_inputs": list(fields),
                    "outputs": list(OUTPUT_FIELDS[mode]),
                }
                for mode, fields in cli.ANOVA_MODES.items()
            ],
            "fields": {name: {"type": t, "description": d} for name, (t, d) in FIELD_INFO.items()},
        }],
        "not_implemented": sorted(cli.CONTRACT_TESTS_NOT_IMPLEMENTED),
        "notes": [
            "Varsayılan değer yoktur: modun her zorunlu alanı açıkça verilmelidir.",
            "Moda ait olmayan alan UNKNOWN_PARAM hatasıdır.",
            "Sayılar tam double hassasiyetle döner; yuvarlama yapılmaz.",
        ],
    }


# --- MCP katmanı -----------------------------------------------------------------------------

def _field_schema(name):
    kind, description = FIELD_INFO[name]
    return {"type": [kind, "string"], "description": f"{description}. {_VALUE_NOTE}"}


def _calc_schema(test_required):
    mode_desc = "; ".join(f"{m}: {', '.join(f)}" for m, f in cli.ANOVA_MODES.items())
    props = {
        "test": {"type": "string", "description": "Test ailesi. Desteklenen tek değer: anova-oneway."},
        "mode": {
            "type": "string",
            "enum": list(cli.ANOVA_MODES),
            "description": f"Analiz modu. Zorunlu alanlar — {mode_desc}.",
        },
    }
    props.update({name: _field_schema(name) for name in FIELD_INFO})
    # Şema tanınmayan alanları kapatır. SDK (stdio) girdiyi şemaya göre doğrulamaz; şemayı yok sayan bir
    # istemcinin gönderdiği alan yine cli.run'a ulaşır ve CLI gibi UNKNOWN_PARAM ile reddedilir.
    return {
        "type": "object",
        "properties": props,
        "required": ["test", "mode"] if test_required else ["mode"],
        "additionalProperties": False,
    }


_RESULT_DESC = (
    "Başarıda CLI'nin stdout JSON'u (ör. a-priori: ncp, critical_f, df1, df2, n_total, actual_power); "
    "hatada {error, code, field} ve isError=true. Kodlar: MISSING_PARAM, UNKNOWN_PARAM, INVALID_VALUE, "
    "OUT_OF_RANGE, INCONSISTENT, UNSUPPORTED, NO_SOLUTION, INTERNAL_ERROR."
)

TOOLS = [
    types.Tool(
        name="power_analysis",
        description="CONTRACT §7 aracı. CLI ile aynı alan adlarıyla güç analizi yapar; `test` ve `mode` "
                    "zorunludur. " + _RESULT_DESC,
        input_schema=_calc_schema(test_required=True),
    ),
    types.Tool(
        name="calculate_anova_oneway",
        description="Tek yönlü ANOVA (sabit etkiler, omnibus) güç analizi hesaplar. `test` verilmezse "
                    "anova-oneway kullanılır. Varsayılan değer yoktur; eksik alan MISSING_PARAM döner. "
                    + _RESULT_DESC,
        input_schema=_calc_schema(test_required=False),
    ),
    types.Tool(
        name="validate_anova_input",
        description="Girdileri hesaplamadan doğrular. Geçerliyse {valid: true, mode, inputs}; değilse "
                    "{valid: false, error, code, field} ve isError=true döner. Tutarlılık (INCONSISTENT) "
                    "hesap sırasında denetlenir.",
        input_schema=_calc_schema(test_required=False),
    ),
    types.Tool(
        name="get_supported_analyses",
        description="Desteklenen test ailesini, modları, her modun zorunlu girdilerini ve çıktı "
                    "alanlarını döndürür. Uygulanmayan sözleşme aileleri `not_implemented` altındadır.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    ),
]

_HANDLERS = {
    "power_analysis": power_analysis,
    "calculate_anova_oneway": calculate_anova_oneway,
    "validate_anova_input": validate_anova_input,
    "get_supported_analyses": lambda _arguments: (supported_analyses(), cli.EXIT_OK),
}


def tool_result(obj, exit_code):
    """Metin içeriği CLI stdout satırıyla aynıdır (sondaki satır sonu hariç)."""
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(obj, allow_nan=False))],
        structured_content=obj,
        is_error=exit_code != cli.EXIT_OK,
    )


async def _list_tools(ctx, params):
    return types.ListToolsResult(tools=TOOLS)


async def _call_tool(ctx, params):
    handler = _HANDLERS.get(params.name)
    if handler is None:
        obj = {"error": f"Bilinmeyen araç: {params.name!r}", "code": "UNKNOWN_TOOL", "field": None}
        return tool_result(obj, cli.EXIT_INPUT)
    arguments = params.arguments or {}
    # cli.run senkron ve bonus modlarda scipy importu ~1 s sürebilir; olay döngüsünü bloklamasın.
    obj, code = await anyio.to_thread.run_sync(handler, arguments)
    return tool_result(obj, code)


def build_server():
    return Server(
        NAME,
        version=CONTRACT_VERSION,
        instructions="anova-oneway güç analizi. Hesap yalnızca araçlar üzerinden yapılır; varsayılan değer "
                     "yoktur. Önce get_supported_analyses ile zorunlu alanları öğrenin.",
        on_list_tools=_list_tools,
        on_call_tool=_call_tool,
    )


async def serve_stdio():
    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    anyio.run(serve_stdio)


if __name__ == "__main__":
    main()
