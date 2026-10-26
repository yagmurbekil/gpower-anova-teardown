"""Kural tabanlı ajan: ayrıştır → durumu güncelle → MCP ile doğrula → hesapla → açıkla.

LLM yoktur; aynı konuşma geçmişi her zaman aynı yanıtı ve aynı araç çağrılarını üretir. Hesap ve
doğrulama yalnızca MCP araçlarıyla yapılır; modların gerekli alanları `get_supported_analyses`
aracından öğrenilir, hata kodları sunucudan geldiği gibi aktarılır.

Konuşma durumu (State) turlar arasında korunur:
- Yeni bir mesajda verilen değer öncekinin yerine geçer ve yanıtta "güncellendi" diye belirtilir.
- Aynı mesajda aynı alana farklı değerler verilirse o alan güncellenmez, hangisinin geçerli olduğu sorulur.
- Hesaplamadan sonra durum silinmez (ör. "alfa 0,01 olsun" ile yeniden hesap); "sıfırla" ile silinir.
- Araç bir alanı reddederse (INVALID_VALUE, OUT_OF_RANGE, INCONSISTENT, UNKNOWN_PARAM) o alan durumdan
  çıkarılır ve kullanıcıdan yenisi istenir.
"""

from dataclasses import dataclass, field

from gpower_clone.agent import response
from gpower_clone.agent.parser import Mention, parse

CALC_TOOL = "calculate_anova_oneway"
VALIDATE_TOOL = "validate_anova_input"
SUPPORTED_TOOL = "get_supported_analyses"
DROP_ON_ERROR = {"INVALID_VALUE", "OUT_OF_RANGE", "INCONSISTENT", "UNKNOWN_PARAM"}


@dataclass
class ToolCall:
    name: str
    arguments: dict
    output: object
    is_error: bool


@dataclass
class State:
    fields: dict = field(default_factory=dict)  # alan → Mention
    other: dict = field(default_factory=dict)   # ANOVA dışı parametre → Mention
    mode: str | None = None
    mode_quote: str | None = None
    per_group: Mention | None = None
    n_total_derived: bool = False


@dataclass
class Reply:
    text: str
    status: str                  # calculated | asked | error | unsupported | info
    mode: str | None = None
    params: dict = field(default_factory=dict)  # durumdaki ANOVA alanları (değerler)
    missing: list = field(default_factory=list)
    conflicts: dict = field(default_factory=dict)
    ambiguous: list = field(default_factory=list)
    needs_mode: bool = False
    error: dict | None = None
    result: dict | None = None
    tool_calls: list = field(default_factory=list)

    @property
    def calculations(self):
        return [c for c in self.tool_calls if c.name == CALC_TOOL and not c.is_error]


class Agent:
    """Tek bir konuşma. `invoker`: mcp_client.ToolInvoker; `audit`: AuditLog ya da None."""

    def __init__(self, invoker, audit=None):
        self.invoker = invoker
        self.audit = audit
        self.state = State()
        self.supported = None
        self.modes = None  # mod → gerekli alanlar (sunucudan)

    async def _call(self, question, calls, name, arguments):
        outcome = await self.invoker.call(name, arguments)
        calls.append(ToolCall(outcome.name, outcome.arguments, outcome.output, outcome.is_error))
        if self.audit is not None:
            self.audit.record(question=question, tool=outcome.name, tool_input=outcome.arguments,
                              tool_output=outcome.output, is_error=outcome.is_error)
        return outcome

    async def _discover(self, question, calls):
        if self.modes is None:
            outcome = await self._call(question, calls, SUPPORTED_TOOL, {})
            if outcome.is_error:
                raise RuntimeError(f"{SUPPORTED_TOOL} başarısız: {outcome.output}")
            self.supported = outcome.output
            [family] = outcome.output["supported"]
            self.modes = {m["mode"]: m["required_inputs"] for m in family["modes"]}

    def _reply(self, text, status, calls, **kw):
        values = {k: m.value for k, m in self.state.fields.items()}
        kw.setdefault("mode", self.state.mode)
        return Reply(text=text, status=status, params=values, tool_calls=calls, **kw)

    def _drop(self, name):
        st = self.state
        if name in st.fields:
            if name == "n_total" and st.n_total_derived:
                st.per_group, st.n_total_derived = None, False
            del st.fields[name]
        elif name in st.other:
            del st.other[name]
        elif name == "mode":
            st.mode = st.mode_quote = None

    async def ask(self, question):
        calls, notes = [], []
        await self._discover(question, calls)
        p = parse(question)
        st = self.state

        if p.reset:
            self.state = st = State()
            if not p.has_content:
                return self._reply(response.reset(), "info", calls)
        if p.help and not p.has_content:
            return self._reply(response.help_text(self.supported), "info", calls)

        # Desteklenmeyen analiz: sunucunun UNSUPPORTED yanıtı aktarılır; değerler duruma alınmaz.
        if p.tests:
            test_value, quote = p.tests[0]
            outcome = await self._call(question, calls, VALIDATE_TOOL, {"test": test_value})
            err = _error(outcome.output) if outcome.is_error else None
            return self._reply(response.unsupported(quote, err, self.supported), "unsupported", calls, error=err)

        conflicts = p.conflicts()
        for target, mentions in p.values().items():
            if target in conflicts:
                continue
            m = mentions[0]
            if target == "per_group":
                st.per_group = m
                continue
            old = st.fields.get(target)
            if old is not None and old.value != m.value:
                notes.append(f"{target} {old.value!r} → {m.value!r} olarak güncellendi.")
            st.fields[target] = m
            if target == "n_total":
                st.n_total_derived = False
        for m in p.other:
            st.other[m.target] = m

        mode_conflict = sorted(p.modes) if len(p.modes) > 1 else []
        if len(p.modes) == 1:
            [(mode, quotes)] = p.modes.items()
            if st.mode and st.mode != mode:
                notes.append(f"mod {st.mode} → {mode} olarak güncellendi.")
            st.mode, st.mode_quote = mode, quotes[0]

        self._derive_n_total(conflicts, notes)
        if conflicts or mode_conflict or p.ambiguous or p.orphans:
            text = response.clarify(conflicts, p.ambiguous, p.orphans, mode_conflict, notes)
            return self._reply(text, "asked", calls, conflicts=dict(conflicts, **({"mode": mode_conflict}
                                                                                   if mode_conflict else {})),
                               ambiguous=p.ambiguous + p.orphans)

        # Mod: açıkça söylenen ya da verilen alanlarla birebir örtüşen tek mod.
        given = set(st.fields)
        mode, mode_source = st.mode, f"“{st.mode_quote}” ifadesinden"
        if mode is None:
            exact = [m for m, req in self.modes.items() if set(req) == given]
            if len(exact) == 1:
                mode, mode_source = exact[0], "verilen alanlar yalnızca bu modun gerekli alanlarıyla örtüşüyor"
            else:
                candidates = [m for m, req in self.modes.items() if given and given <= set(req)]
                text = response.ask_mode(self.modes, st.fields, candidates, notes)
                return self._reply(text, "asked", calls, needs_mode=True)

        required = self.modes[mode]
        missing = [f for f in required if f not in st.fields]
        args = {"mode": mode, **{k: m.value for k, m in st.fields.items()},
                **{k: m.value for k, m in st.other.items()}}

        validation = await self._call(question, calls, VALIDATE_TOOL, args)
        if validation.is_error:
            err = _error(validation.output)
            if err["code"] == "MISSING_PARAM":
                text = response.missing(mode, mode_source, missing, st.fields, p.verbal_effect, notes)
                return self._reply(text, "asked", calls, mode=mode, missing=missing)
            if err["code"] in DROP_ON_ERROR and err["field"]:
                self._drop(err["field"])
            return self._reply(response.error(err, mode, missing, notes), "error", calls, mode=mode,
                               missing=missing, error=err)

        calc = await self._call(question, calls, CALC_TOOL, args)
        if calc.is_error:
            err = _error(calc.output)
            if err["code"] in DROP_ON_ERROR and err["field"]:
                self._drop(err["field"])
            return self._reply(response.error(err, mode, [], notes), "error", calls, mode=mode, error=err)
        fields = {k: st.fields[k] for k in required}
        text = response.result(mode, mode_source, fields, calc.output, notes)
        return self._reply(text, "calculated", calls, mode=mode, result=calc.output)

    def _derive_n_total(self, conflicts, notes):
        """'Her grupta n kişi' ifadesi grup sayısıyla birlikte toplam N'ye çevrilir ve yanıtta belirtilir."""
        st = self.state
        pg, groups = st.per_group, st.fields.get("groups")
        if pg is None or groups is None or not (isinstance(pg.value, int) and isinstance(groups.value, int)):
            return
        total = pg.value * groups.value
        current = st.fields.get("n_total")
        if current is not None and not st.n_total_derived and current.value != total:
            conflicts["n_total"] = [current.value, total]
            return
        if current is not None and st.n_total_derived and current.value == total:
            return
        quote = f"{pg.quote} × {groups.value} grup"
        st.fields["n_total"] = Mention("n_total", total, quote, pg.start)
        st.n_total_derived = True
        notes.append(f"n_total = {pg.value} × {groups.value} = {total} (grup başına n × grup sayısı).")


def _error(output):
    return {"code": output.get("code"), "field": output.get("field"), "error": output.get("error")}
