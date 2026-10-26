"""Kural tabanlı ayrıştırıcının sözlüğü ve düzenli ifadeleri.

Alan adları CONTRACT §4.3'teki `anova-oneway` girdileridir (cli.ANOVA_MODES ile aynı); kullanıcıya
gösterilen adlar LABELS'tadır. Bütün desenler `parser.fold` ile "katlanmış" metne uygulanır: küçük harf,
ı/I/İ → i, tipografik kesme ve tire → ASCII. Bu yüzden desenlerde "ı" yerine "i" yazılır
(ör. "anlamlılık" → "anlamlilik"); ç, ğ, ö, ş, ü korunur.
"""

import re

# --- alanlar ----------------------------------------------------------------------------------

ANOVA_FIELDS = ("f", "alpha", "power", "beta_alpha_ratio", "n_total", "groups")
INTEGER_FIELDS = {"n_total", "groups"}
PERCENT_FIELDS = {"alpha", "power"}  # "%5", "yüzde 80", "80 percent" yalnızca bunlarda kesre çevrilir

LABELS = {
    "f": "etki büyüklüğü f",
    "alpha": "anlamlılık düzeyi α (alpha)",
    "power": "güç 1−β (power)",
    "beta_alpha_ratio": "β/α oranı (beta_alpha_ratio)",
    "n_total": "toplam örneklem büyüklüğü N (n_total)",
    "groups": "grup sayısı (groups)",
}

MODE_LABELS = {
    "a-priori": "gerekli örneklem büyüklüğü",
    "post-hoc": "ulaşılan güç",
    "compromise": "β/α oranından α ve güç",
    "criterion": "gerekli α",
    "sensitivity": "saptanabilir en küçük etki büyüklüğü",
}

# Sözleşmenin başka ailelerine ait alanlar (CONTRACT §4); anova-oneway'de UNKNOWN_PARAM'dır.
OTHER_CONTRACT_FIELDS = {"tails", "d", "dz", "w", "f2", "df", "n1", "n2", "ratio", "predictors"}

# `ad = değer` biçiminde yazılmış adların alan karşılıkları (katlanmış).
IDENT_ALIASES = {
    "f": "f", "alpha": "alpha", "alfa": "alpha", "α": "alpha", "power": "power", "güç": "power",
    "groups": "groups", "grup": "groups", "k": "groups", "n": "n_total", "n_total": "n_total",
    "beta_alpha_ratio": "beta_alpha_ratio",
}

# --- sayılar ----------------------------------------------------------------------------------

# Rakamla bitmeyen sondaki nokta/virgül sayıya dâhil değildir ("0,05," → "0,05"). Biçimi bozuk bir
# sayı ("0.0.5") yine tek parça yakalanır ve ham metin olarak sunucuya gider → INVALID_VALUE.
_NUM = r"[-+]?(?:\d[\d.,]*\d|\d)(?:e[-+]?\d+)?"
NUMBER = re.compile(
    rf"(?<![\w.,])(?P<pre>%\s*|yüzde\s+)?(?P<num>{_NUM})(?P<post>\s*%|\s+percent\b|\s+per\s+cent\b)?(?!\w)"
)
INT_TEXT = re.compile(r"[-+]?\d+")
DEC_TEXT = re.compile(r"[-+]?(?:\d+[.,]\d+(?:e[-+]?\d+)?|\d+e[-+]?\d+)")

# Yalnızca grup sayısı kalıplarında kullanılır. "bir" (bir/one) ve "on" (İng. edat) belirsiz olduğu
# için listede yok; rakamla yazılmaları gerekir.
NUMBER_WORDS = {
    "iki": 2, "üç": 3, "dört": 4, "beş": 5, "alti": 6, "yedi": 7, "sekiz": 8, "dokuz": 9,
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
_NUMWORD = "|".join(sorted(NUMBER_WORDS, key=len, reverse=True))
# Ondalık da yakalanır ("3.5 grup" → groups = 3.5 → sunucu INVALID_VALUE, CLI'deki gibi).
_COUNT = rf"(?P<n>{_NUM}|{_NUMWORD})"

# Anahtar sözcük ile ardındaki sayı arasında yalnızca bunlar olabilir ("alpha is 0.05", "güç = 0,8").
# Virgül/nokta/noktalı virgül bağı koparır: "anlamlılık düzeyi, %80 güç" → %80 alfaya bağlanmaz.
CONNECTOR = re.compile(r"(?:[\s=:]+|\b(?:is|of|equals?|equal|to|at|be|değeri\w*|olarak)\b)*")
# Sayı ile ardındaki anahtar sözcük arasında ("%80 güç", "0,80'lik güç", "three-arm").
AFTER_GAP = re.compile(r"(?:'?(?:lik|luk|lük)\b)?[\s-]*")
# `ad = sayı` (ör. "n = 100", "x = 3"). Ad bir anahtar sözcüğün içindeyse yok sayılır. ":" yalnızca
# IDENT_ALIASES'taki adlarda ayırıcıdır; "planlıyorum: %5" gibi cümle iki noktaları parametre sayılmaz.
IDENT = re.compile(r"(?<![\w/])(?P<name>[^\W\d][\w]*)\s*(?P<sep>[=:])\s*(?=[-+%.\d])")


class FieldRule:
    """`before`: anahtar sözcük sayıdan önce ("alfa 0,05"); `after`: sayıdan sonra ("%80 güç")."""

    def __init__(self, before=(), after=()):
        self.before = [re.compile(p) for p in before]
        self.after = [re.compile(p) for p in after]


FIELD_RULES = {
    "f": FieldRule(
        before=[r"etki\s+büyüklüğü\w*(?:\s*\(?f\)?(?!\w))?", r"effect\s+size(?:\s*\(?f\)?(?!\w))?",
                r"cohen'?s\s+f(?![\w²^])", r"(?<![\w'/])f(?![\w'²^])"],
        after=[r"etki\s+büyüklüğü\w*"],
    ),
    "alpha": FieldRule(
        before=[r"(?<![/\w])α", r"alfa\w*", r"alpha\w*(?:\s+level)?",
                r"anlamlilik(?:\s+(?:düzeyi|seviyesi)\w*)?", r"significance(?:\s+level)?",
                r"type\s+i\s+error(?:\s+rate)?"],
        after=[r"anlamlilik(?:\s+(?:düzeyi|seviyesi)\w*)?", r"alfa\w*", r"alpha\w*", r"significance(?:\s+level)?"],
    ),
    "power": FieldRule(
        before=[r"istatistiksel\s+güç\w*", r"statistical\s+power", r"güç\w*", r"güc\w*", r"power",
                r"1\s*-\s*(?:β|beta)"],
        after=[r"güç\w*", r"güc\w*", r"power"],
    ),
    "beta_alpha_ratio": FieldRule(
        before=[r"β\s*/\s*α(?:\s+oran\w*)?", r"beta\s*/\s*alpha(?:\s+ratio)?", r"beta_alpha_ratio"],
    ),
    "n_total": FieldRule(
        before=[r"n_total",
                r"toplam(?:\s+(?:n|örneklem(?:\s+büyüklüğü\w*)?|katilimci(?:\s+sayisi\w*)?|kişi(?:\s+sayisi\w*)?))?",
                r"total(?:\s+(?:n|sample\s+size|sample|participants))?", r"örneklem\s+büyüklüğü\w*",
                r"sample\s+size"],
        after=[r"katilimci\w*", r"kişi\w*", r"denek\w*", r"participants?\b", r"subjects?\b", r"people\b"],
    ),
    "groups": FieldRule(
        before=[r"grup\s+sayisi\w*", r"grup\s+adedi\w*", r"number\s+of\s+groups", r"groups"],
    ),
}

# Sayı sözcüklerini de tanıyan, öncelikli tam kalıplar: hedef → desenler (`n` grubu sayıyı yakalar).
# "grubu", "grubunu": Türkçede ünsüz yumuşaması (p → b)
_GROUP_NOUN = r"(?:gru[pb]\w*|groups?|kol\w*|arms?|koşul\w*|conditions?)\b"
SPECIAL_PATTERNS = {
    "groups": [
        # "3 grup", "dört diyet grubu" (arada en çok bir sözcük), "three-arm"
        re.compile(rf"(?<![\w.,]){_COUNT}[\s-]+(?:[^\W\d]+\s+)?{_GROUP_NOUN}"),
        # "dört farklı egzersiz programı", "three different diets"
        re.compile(rf"(?<![\w.,]){_COUNT}\s+(?:farkli|different)\s+[^\W\d]+"),
        # "üç öğretim yöntemini karşılaştıran" (arada en çok iki sözcük), "compare three diets"
        re.compile(rf"(?<![\w.,]){_COUNT}\s+(?:[^\W\d]+\s+){{0,2}}karşilaştir\w*"),
        re.compile(rf"compar\w*\s+{_COUNT}\s+[^\W\d]+"),
    ],
    "per_group": [
        re.compile(rf"(?:her\s+grupta|her\s+gruba|grup\s+başina|grup\s+başi|per\s+group|in\s+each\s+group|"
                   rf"each\s+group\s+(?:has|with|of)?)\s*(?:n\s*=\s*)?(?P<n>{_NUM})(?!\w)"),
        re.compile(rf"(?<![\w.,])(?P<n>{_NUM})\s+(?:[^\W\d]+\s+)?(?:per\s+group|in\s+each\s+group|"
                   rf"her\s+grupta|grup\s+başina)"),
    ],
}

# Başka ailelerin ya da sözleşmede hiç olmayan parametrelerin anahtar sözcükleri. Değer verilmezse
# ifadenin kendisi değer olarak taşınır; sunucu her durumda UNKNOWN_PARAM döndürür.
OTHER_RULES = {
    "tails": [r"(?:one|two)[\s-]tailed", r"(?:tek|çift)\s+kuyruk\w*", r"tails?\b"],
    "d": [r"cohen'?s\s+d(?!\w)"],
    "dz": [r"cohen'?s\s+dz(?!\w)"],
    "w": [r"cohen'?s\s+w(?!\w)"],
    "f2": [r"(?<![\w'/])f(?:2|²|\^2)(?!\w)"],
    "predictors": [r"predictors?\b", r"yordayici\w*"],
    "eta_squared": [r"η\s*(?:²|2)", r"(?:kismi\s+|partial\s+)?eta[\s-]?(?:kare\w*|squared|sq|2|²)"],
}
OTHER_RULES = {name: [re.compile(p) for p in pats] for name, pats in OTHER_RULES.items()}

# --- analiz modu ------------------------------------------------------------------------------

MODE_RULES = {
    "a-priori": [
        r"a[\s-]?priori",
        r"kaç\s+(?:kişi|katilimci|denek|birey|örnek|gözlem)",
        r"(?:gerekli|gereken|required|needed|minimum)\s+(?:toplam\s+)?(?:örneklem|sample|katilimci)",
        r"örneklem\s+(?:büyüklüğü|sayisi|boyutu)\w*\s+(?:nedir|ne\s+olmali|hesapla|kaç|gerek)",
        r"how\s+many\s+(?:\w+\s+)?(?:participants|subjects|people|patients|observations|samples)",
        r"(?:calculate|compute|determine|find)\s+(?:the\s+)?(?:required\s+)?(?:total\s+)?sample\s+size",
        r"sample\s+size\s+(?:is\s+)?(?:needed|required)",
    ],
    "post-hoc": [
        r"post[\s-]?hoc",
        r"ulaş(?:ilan|tiği|ilacak|ilabilecek)\s+güç",
        r"achieved\s+power",
        r"güc(?:ü|üm|ümüz|ün)\s+(?:ne|nedir|kaç)",
        r"güç\s+(?:ne\s+olur|nedir|ne\s+kadar)",
        r"what\s+(?:is|would\s+be|will\s+be)\s+(?:the\s+|my\s+|our\s+)?(?:achieved\s+|statistical\s+)?power",
        r"how\s+much\s+power",
    ],
    "compromise": [r"compromise", r"uzlaşma"],
    "criterion": [r"criterion", r"kriter", r"(?:gerekli|gereken|required)\s+(?:alfa|alpha|α|anlamlilik)"],
    "sensitivity": [
        r"sensitivity", r"duyarlilik", r"en\s+küçük\s+etki", r"saptanabil\w*\s+en\s+küçük",
        r"(?:minimum|minimal|smallest)\s+(?:detectable\s+)?effect",
    ],
}
MODE_RULES = {mode: [re.compile(p) for p in pats] for mode, pats in MODE_RULES.items()}

# --- analiz türü ------------------------------------------------------------------------------

ANOVA_PATTERN = re.compile(r"anova|varyans\s+analizi|analysis\s+of\s+variance")

# (desen, test değeri). Değer None ise kullanıcının ifadesi test değeri olarak sunucuya gider;
# sunucu sözleşmedeki ailelere ve bilinmeyen testlere UNSUPPORTED döndürür.
TEST_RULES = [
    (r"(?:iki\s+yönlü|two[\s-]way|faktöriyel|factorial)\s+anova", None),
    (r"(?:tekrarli\s+ölçüm\w*|repeated[\s-]measures)(?:\s+anova)?", None),
    (r"ancova|manova|kovaryans\s+analizi", None),
    (r"(?:eşleştirilmiş|paired|bağimli)(?:\s+\w+){0,2}?\s+t[\s-]?test\w*", "t-paired"),
    (r"(?<!\w)t[\s-]?test\w*", "t2-indep"),
    (r"ki[\s-]?kare\w*|chi[\s-]?squared?|χ²|chi2|contingency|çapraz\s+tablo", "chi2-contingency"),
    (r"regresyon\w*|regression|r²", "multireg-r2"),
    (r"korelasyon\w*|correlation", None),
    (r"mann[\s-]whitney|wilcoxon|kruskal", None),
]
TEST_RULES = [(re.compile(p), value) for p, value in TEST_RULES]

# "en küçük etki büyüklüğü" (sensitivity sorusu) sözel bir etki etiketi değildir.
VERBAL_EFFECT = re.compile(r"(?<!en\s)(?:küçük|orta|büyük)\s+(?:büyüklükte\s+)?(?:bir\s+)?etki\w*|"
                           r"(?:small|medium|moderate|large)\s+effect")
RESET = re.compile(r"^\s*(?:sifirla|yeni\s+analiz|baştan\s+başla|reset|new\s+analysis)\b")
HELP = re.compile(r"^\s*(?:yardim|help|neler\s+destekleniyor|desteklenen\w*)\b")
