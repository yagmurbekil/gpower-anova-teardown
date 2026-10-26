"""Deterministik doğal dil ayrıştırıcısı: metin → alan değerleri, mod, analiz türü, belirsizlikler.

Hesap yapmaz ve değer uydurmaz; yalnızca metinde açıkça geçen sayıları bir alana bağlar. Her sayı için
bağlama önceliği (yüksekten düşüğe):
    3 — tam kalıp: "her grupta 20", "3 grup", "dört farklı ...", "üç ... karşılaştıran"
    2 — anahtar sözcük önce: "alfa 0,05", "power is 0.8", "n = 100"
    1 — anahtar sözcük sonra: "%80 güç", "0,25'lik etki büyüklüğü"
En yüksek öncelikte iki farklı alan aynı sayıyı istiyorsa sayı belirsizdir; hiçbir alana bağlanmayan sayı
"tanımlanamayan sayı" olarak raporlanır. Ajan her iki durumda da kullanıcıya sorar.
"""

from dataclasses import dataclass, field

from gpower_clone.agent import rules

TIER_SPECIAL, TIER_BEFORE, TIER_AFTER = 3, 2, 1

_FOLD = {"İ": "i", "I": "i", "ı": "i", "’": "'", "‘": "'", "`": "'", "´": "'", "−": "-", "–": "-", "—": "-"}


def fold(text):
    """Küçük harf + Türkçe i ve tipografi düzeltmesi; uzunluk korunur (konumlar özgün metne denk gelir)."""
    out = []
    for c in text:
        c = _FOLD.get(c, c)
        low = c.lower()
        out.append(low if len(low) == 1 else c)
    return "".join(out)


@dataclass(frozen=True)
class Mention:
    target: str     # sözleşme alanı, "per_group" ya da başka bir parametre adı
    value: object   # int | float | str (biçimi tanınmayan ham metin; sunucu INVALID_VALUE verir)
    quote: str      # özgün metindeki ifade
    start: int


@dataclass
class Parse:
    text: str
    mentions: list = field(default_factory=list)   # ANOVA alanları ve per_group
    other: list = field(default_factory=list)      # ANOVA dışı parametreler
    modes: dict = field(default_factory=dict)      # mod → [ifadeler]
    tests: list = field(default_factory=list)      # [(test değeri, ifade)] — desteklenmeyen analizler
    anova: bool = False
    ambiguous: list = field(default_factory=list)  # birden çok alana bağlanabilen sayılar
    orphans: list = field(default_factory=list)    # hiçbir alana bağlanamayan sayılar
    verbal_effect: str | None = None
    reset: bool = False
    help: bool = False

    def values(self):
        """hedef → farklı değerlerin sözü geçme sırasıyla listesi."""
        out = {}
        for m in sorted(self.mentions, key=lambda m: m.start):
            seen = out.setdefault(m.target, [])
            if not any(m.value == s.value for s in seen):  # 1 ile 1.0 aynı; ham metin yalnızca kendine eşit
                seen.append(m)
        return out

    def conflicts(self):
        return {t: [m.value for m in ms] for t, ms in self.values().items() if len(ms) > 1}

    @property
    def has_content(self):
        return bool(self.mentions or self.other or self.modes or self.tests or self.ambiguous or self.orphans)


@dataclass
class _Token:
    start: int
    end: int
    num_start: int
    num_end: int
    raw: str
    percent: bool


@dataclass
class _Keyword:
    target: str
    start: int
    end: int
    before: bool
    after: bool


def _convert(raw, percent, target):
    """Sayı metnini değere çevirir. Yüzde yalnızca alpha/power'da kesre dönüşür."""
    if percent and target not in rules.PERCENT_FIELDS:
        return f"%{raw}"
    if rules.INT_TEXT.fullmatch(raw):
        value = int(raw)
    elif rules.DEC_TEXT.fullmatch(raw):
        value = float(raw.replace(",", "."))
    else:
        return raw
    return value / 100 if percent else value


def _tokens(t):
    return [
        _Token(m.start(), m.end(), m.start("num"), m.end("num"), m.group("num"),
               bool(m.group("pre") or m.group("post")))
        for m in rules.NUMBER.finditer(t)
    ]


def _keywords(t):
    found = []
    for target, rule in rules.FIELD_RULES.items():
        spans = {}
        for pat in rule.before:
            for m in pat.finditer(t):
                spans.setdefault(m.span(), [False, False])[0] = True
        for pat in rule.after:
            for m in pat.finditer(t):
                spans.setdefault(m.span(), [False, False])[1] = True
        found += [_Keyword(target, s, e, b, a) for (s, e), (b, a) in spans.items()]
    for name, pats in rules.OTHER_RULES.items():
        for pat in pats:
            found += [_Keyword(name, m.start(), m.end(), True, False) for m in pat.finditer(t)]
    # Çakışan eşleşmelerde en uzunu kalır ("β/α oranı" içindeki "α", "f2" içindeki "f" gibi).
    found.sort(key=lambda k: (-(k.end - k.start), k.start))
    kept = []
    for k in found:
        if not any(k.start < o.end and o.start < k.end for o in kept):
            kept.append(k)
    return sorted(kept, key=lambda k: k.start)


def _overlaps(start, end, spans):
    return any(start < e and s < end for s, e in spans)


def parse(text):
    t = fold(text)
    p = Parse(text=text)
    p.reset = bool(rules.RESET.search(t))
    p.help = bool(rules.HELP.search(t))

    test_spans = []
    for pat, value in rules.TEST_RULES:
        for m in pat.finditer(t):
            if not _overlaps(m.start(), m.end(), test_spans):
                test_spans.append(m.span())
                p.tests.append((value if value is not None else text[m.start():m.end()], text[m.start():m.end()]))
    p.anova = any(not _overlaps(m.start(), m.end(), test_spans) for m in rules.ANOVA_PATTERN.finditer(t))

    phrase_spans = list(test_spans)
    for mode, pats in rules.MODE_RULES.items():
        for pat in pats:
            for m in pat.finditer(t):
                p.modes.setdefault(mode, []).append(text[m.start():m.end()])
                phrase_spans.append(m.span())
    if m := rules.VERBAL_EFFECT.search(t):
        p.verbal_effect = text[m.start():m.end()]

    tokens = _tokens(t)
    keywords = _keywords(t)
    kw_spans = [(k.start, k.end) for k in keywords]
    claims = {i: [] for i in range(len(tokens))}  # belirteç → [(öncelik, hedef)]
    by_start = {tok.start: i for i, tok in enumerate(tokens)}

    def token_at(num_start, num_end):
        for i, tok in enumerate(tokens):
            if tok.num_start <= num_start and num_end <= tok.num_end:
                return i
        return None

    # 3 — tam kalıplar (sayı sözcükleri dâhil)
    word_mentions = []
    for target, pats in rules.SPECIAL_PATTERNS.items():
        for pat in pats:
            for m in pat.finditer(t):
                n = m.group("n")
                if n in rules.NUMBER_WORDS:
                    word_mentions.append(Mention(target, rules.NUMBER_WORDS[n], text[m.start():m.end()], m.start()))
                    kw_spans.append(m.span())
                elif (i := token_at(m.start("n"), m.end("n"))) is not None:
                    claims[i].append((TIER_SPECIAL, target, text[m.start():m.end()]))

    # 2 — anahtar sözcük önce
    for k in keywords:
        if not k.before:
            continue
        pos = rules.CONNECTOR.match(t, k.end).end()
        if (i := by_start.get(pos)) is not None:
            claims[i].append((TIER_BEFORE, k.target, text[k.start:tokens[i].end]))
    for m in rules.IDENT.finditer(t):
        if _overlaps(m.start("name"), m.end("name"), kw_spans + phrase_spans):
            continue
        name = m.group("name")
        if m.group("sep") == ":" and name not in rules.IDENT_ALIASES:
            continue
        target = rules.IDENT_ALIASES.get(name, name)
        if (i := by_start.get(m.end())) is not None:
            claims[i].append((TIER_BEFORE, target, text[m.start():tokens[i].end]))
            kw_spans.append((m.start("name"), m.end("name")))

    # 1 — anahtar sözcük sonra
    for i, tok in enumerate(tokens):
        gap_end = rules.AFTER_GAP.match(t, tok.end).end()
        for k in keywords:
            if k.after and k.start == gap_end:
                claims[i].append((TIER_AFTER, k.target, text[tok.start:k.end]))

    # Çözüm
    claimed_other = set()
    for i, tok in enumerate(tokens):
        if not claims[i]:
            if not _overlaps(tok.num_start, tok.num_end, kw_spans + phrase_spans):
                p.orphans.append(text[tok.start:tok.end].strip())
            continue
        top = max(c[0] for c in claims[i])
        best = [c for c in claims[i] if c[0] == top]
        targets = sorted({c[1] for c in best})
        if len(targets) > 1:
            p.ambiguous.append(text[tok.start:tok.end].strip())
            continue
        target, quote = targets[0], best[0][2]
        mention = Mention(target, _convert(tok.raw, tok.percent, target), quote, tok.start)
        if target in rules.ANOVA_FIELDS or target == "per_group":
            p.mentions.append(mention)
        else:
            p.other.append(mention)
            claimed_other.add(target)
    p.mentions += word_mentions

    # Değeri olmayan ANOVA dışı parametreler ("two-tailed", "η²"): ifadenin kendisi değerdir.
    for k in keywords:
        if k.target not in rules.ANOVA_FIELDS and k.target not in claimed_other:
            p.other.append(Mention(k.target, text[k.start:k.end], text[k.start:k.end], k.start))
            claimed_other.add(k.target)
    p.mentions.sort(key=lambda m: m.start)
    p.other.sort(key=lambda m: m.start)
    return p
