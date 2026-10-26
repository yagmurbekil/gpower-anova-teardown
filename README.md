# gpower-clone — anova-oneway

`CONTRACT.md` 1.0.0 arayüzüyle *F tests – ANOVA: Fixed effects, omnibus, one-way* güç analizi.
Python 3.14 + scipy 1.18. Bu sürümde yalnızca `--test anova-oneway` uygulanır; sözleşmedeki diğer aileler
`UNSUPPORTED` döndürür.

## Kurulum (tek komut)

```
pip install -e ".[test]"
```

Bu komut CLI'yi, MCP sunucusunu, kural tabanlı ajanı (ikisi için de yalnızca `mcp==2.3.0`) ve test
bağımlılıklarını kurar. Yalnızca CLI için `pip install -e .`, MCP sunucusu ya da ajan için
`pip install -e ".[mcp]"` / `pip install -e ".[agent]"` yeterlidir. Sabitlenmiş sürümler `requirements.txt`
içindedir. Ajan dil modeli kullanmaz: API anahtarı, model hesabı ya da internet bağlantısı gerekmez.

Konsol komutları (`gpower-clone`, `gpower-clone-mcp`, `gpower-clone-agent`, `gpower-clone-eval`) pip'in
Scripts klasörüne kurulur. Kullanıcı kurulumunda bu klasör (ör. `%APPDATA%\Python\Python314\Scripts`) PATH'te
olmayabilir; o durumda her komutun `python -m ...` karşılığını kullanın (aşağıda ikisi de verilmiştir).

## Çalıştırma

```
gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 5
```
```json
{"ncp": 19.0625, "critical_f": 2.401739..., "df1": 4, "df2": 300, "n_total": 305, "actual_power": 0.952131...}
```

Kurulum yapmadan kaynak ağacından: `python -m gpower_clone ...` (`PYTHONPATH=src` ile).

| Mod | Zorunlu alanlar |
|---|---|
| `a-priori` | `f`, `alpha`, `power`, `groups` |
| `post-hoc` | `f`, `alpha`, `n_total`, `groups` |
| `compromise` (bonus) | `f`, `beta_alpha_ratio`, `n_total`, `groups` |
| `criterion` (bonus) | `f`, `power`, `n_total`, `groups` |
| `sensitivity` (bonus) | `alpha`, `power`, `n_total`, `groups` |

`gpower-clone --version` sözleşme sürümünü yazar. Hata durumunda stdout'a `{"error", "code", "field"}` yazılır;
çıkış kodu girdi hatasında 2, hesap yapılamadığında (`NO_SOLUTION`, iç hata) 1.

## MCP sunucusu (CONTRACT §7)

Standart MCP stdio taşıması. Depo kökünde (ya da paket kuruluysa herhangi bir dizinde):

```
gpower-clone-mcp
python -m gpower_clone.mcp_server      # eşdeğeri
```

Sunucu stdin/stdout üzerinden MCP istemcisiyle konuşur; elle başlatıldığında komut satırına bir şey yazmaz,
istemci bağlantısını bekler. stdout'a protokol mesajı dışında hiçbir şey yazılmaz (log ve uyarılar stderr'e).

**Bir MCP istemcisine bağlama.** Claude Code (terminalde, depo kökünde):

```
claude mcp add gpower-clone -- python -m gpower_clone.mcp_server
claude mcp add gpower-clone -e PYTHONPATH=<depo>/src -- python -m gpower_clone.mcp_server   # paket kurulu değilse
```

JSON yapılandırması kullanan istemciler (ör. Claude Desktop `claude_desktop_config.json`):

```json
{"mcpServers": {"gpower-clone": {"command": "python", "args": ["-m", "gpower_clone.mcp_server"]}}}
```

Paket kurulu değilse `"env": {"PYTHONPATH": "<depo>/src"}` ekleyin.

| Araç | Ne yapar |
|---|---|
| `power_analysis` | Sözleşmedeki araç: CLI ile aynı alan adları, `test` ve `mode` zorunlu |
| `calculate_anova_oneway` | Aynı hesap; `test` verilmezse `anova-oneway` |
| `validate_anova_input` | Hesap yapmadan doğrular → `{valid, mode, inputs}` ya da `{valid: false, error, code, field}` |
| `get_supported_analyses` | Desteklenen aile, modlar, zorunlu girdiler, çıktı alanları, uygulanmayan aileler |

Hesap ve doğrulama MCP katmanında yeniden yazılmaz: araç argümanları CLI'nin `--alan değer` biçimine
çevrilir ve `gpower_clone.cli.run` çağrılır. Bu yüzden araç sonucunun metin içeriği, aynı girdi için CLI'nin
stdout satırıyla birebir aynıdır (hata kodları, alan adları ve tam double sayılar dâhil). Hatada sonuç
`isError: true` taşır; `structuredContent` aynı JSON nesnesidir. Değerler JSON sayısı olarak verilmelidir;
CLI biçiminde metin (`"0.05"`) de kabul edilir ve CLI kurallarıyla doğrulanır (ör. `groups: 5.0` →
`INVALID_VALUE`, CLI'deki `--groups 5.0` gibi). `null` değerli alan verilmemiş sayılır.
Araç şemaları `additionalProperties: false` ile tanınmayan alanları kapatır. MCP SDK'sı (2.3.0, stdio) girdiyi
şemaya göre doğrulamadığından, şemayı yok sayan bir istemcinin gönderdiği alan sunucuya ulaşır ve CLI'deki gibi
`UNKNOWN_PARAM` ile reddedilir; girdiyi kendi tarafında doğrulayan bir istemci ise isteği hiç göndermeyebilir.

> Not: CONTRACT §7 "tek bir araç: `power_analysis`" der. `power_analysis` sözleşmeye birebir uyar; diğer üç
> araç bu teslimde istendiği için ek olarak sunulur ve aynı adaptörü kullanır.

Gerçek çağrı örnekleri (süreç içi MCP istemcisiyle alındı):

```
calculate_anova_oneway {"mode": "post-hoc", "f": 0.25, "alpha": 0.05, "n_total": 100, "groups": 5}
→ {"ncp": 6.25, "critical_f": 2.467493623449646, "df1": 4, "df2": 95, "power": 0.46633120262315364}

calculate_anova_oneway {"mode": "a-priori", "f": 0.25, "power": 0.9, "groups": 4}
→ isError: {"error": "--alpha a-priori modunda zorunlu", "code": "MISSING_PARAM", "field": "alpha"}
```

## Doğal dilli ajan (CONTRACT §8) — kural tabanlı

Ajan **dil modeli (LLM) kullanmaz**. İsteği düzenli ifadeler ve deterministik kurallarla ayrıştırır, MCP
sunucusuna istemci olarak bağlanır ve hesabı yalnızca MCP araçlarıyla yaptırır. API anahtarı, model hesabı ya
da internet bağlantısı gerekmez; aynı konuşma her zaman aynı yanıtı ve aynı araç çağrılarını üretir.

Akış: `get_supported_analyses` (modlar ve gerekli alanlar sunucudan öğrenilir) → metinden alanları çıkarma →
eksik/çelişkili/belirsiz bilgi varsa **soru sorma, hesap aracını çağırmama** → `validate_anova_input` →
`calculate_anova_oneway`. Hata kodları (`MISSING_PARAM`, `OUT_OF_RANGE`, `INVALID_VALUE`, `UNKNOWN_PARAM`,
`INCONSISTENT`, `NO_SOLUTION`, `UNSUPPORTED`) sunucudan geldiği gibi aktarılır.

| Modül (`src/gpower_clone/agent/`) | Görev |
|---|---|
| `rules.py` | TR/EN eş anlamlılar, mod ve analiz türü kalıpları, sayı biçimleri |
| `parser.py` | Metinden alan değerleri, mod, belirsiz sayılar, çelişkiler |
| `core.py` | Konuşma durumu, soru sorma kararı, MCP çağrıları |
| `response.py` | Deterministik Türkçe yanıt metinleri |
| `mcp_client.py` | Bağlantı, araç keşfi, araç çağrısı |
| `audit.py` | `logs/agent_calls.jsonl` ve gizli bilgi maskeleme |
| `evaluate.py` | Senaryo değerlendirmesi |

Depo kökünde çalıştırın (log `logs/agent_calls.jsonl`, bulunduğunuz dizine göre yazılır):

```
gpower-clone-agent "Üç grup, etki büyüklüğü 0,25, alfa 0,05 ve güç 0,80."
python -m gpower_clone.agent "..."        # eşdeğeri
gpower-clone-agent                        # etkileşimli oturum (soru> istemi); boş satırla çıkış
gpower-clone-agent --once "..."           # yalnızca verilen isteği yanıtla
gpower-clone-agent --log yol/calls.jsonl  # log dosyası
```

Etkileşimli değilken (ör. borudan) stdin'in her satırı bir turdur. Aşağıdaki çıktı gerçek bir çalıştırmadandır;
girdi satırları sırasıyla `ANOVA için güç analizi yap.`, `Dört grup ve %80 güç için gereken örneklem sayısını
hesapla.`, `f 0,25`, `alfa 0,05` idi (ilk yanıttaki mod listesi kısaltıldı):

```
Hangi analiz modunu kullanmak istiyorsunuz? Seçenekler ve gerekli parametreler:
  - a-priori (gerekli örneklem büyüklüğü): f, alpha, power, groups
  ...
Gerekli mod ve parametreleri belirtir misiniz?

Mod: a-priori (gerekli örneklem büyüklüğü) — “gereken örneklem” ifadesinden
Şimdiye kadar alınan değerler:
  - groups = 4  ← “Dört grup”
  - power = 0.8  ← “%80 güç”
Hesaplama için eksik: etki büyüklüğü f, anlamlılık düzeyi α (alpha). Bu değer(ler)i belirtir misiniz?

Mod: a-priori (gerekli örneklem büyüklüğü) — “gereken örneklem” ifadesinden
Şimdiye kadar alınan değerler:
  - groups = 4  ← “Dört grup”
  - power = 0.8  ← “%80 güç”
  - f = 0.25  ← “f 0,25”
Hesaplama için eksik: anlamlılık düzeyi α (alpha). Bu değer(ler)i belirtir misiniz?

Mod: a-priori (gerekli örneklem büyüklüğü) — “gereken örneklem” ifadesinden
Kullanılan girdiler:
  - f = 0.25  ← “f 0,25”
  - alpha = 0.05  ← “alfa 0,05”
  - power = 0.8  ← “%80 güç”
  - groups = 4  ← “Dört grup”
Sonuç (calculate_anova_oneway çıktısı, değiştirilmeden):
  - ncp = 11.25 (≈ 11.2500)
  - critical_f = 2.6559388770305596 (≈ 2.6559)
  - df1 = 3
  - df2 = 176
  - n_total = 180
  - actual_power = 0.8039869128651759 (≈ 0.8040)
Özet: hedef güce ulaşmak için toplam N = 180 gerekir; bu N ile ulaşılan güç 0.8040 (≈).
[motor] calculate_anova_oneway {"mode": "a-priori", "groups": 4, "power": 0.8, "f": 0.25, "alpha": 0.05}
        → {"ncp": 11.25, "critical_f": 2.6559388770305596, "df1": 3, "df2": 176, "n_total": 180, "actual_power": 0.8039869128651759}
```

Desteklenmeyen analiz (gerçek çıktı, `gpower-clone-agent --once "İki bağımsız grup için t testi yap"`; liste
kısaltıldı):

```
“t testi” bu uygulamada desteklenmiyor.
Araç yanıtı [UNSUPPORTED] (alan: test): t2-indep bu uygulamada desteklenmiyor (yalnızca anova-oneway)
...
Tek yönlü ANOVA ile devam etmek ister misiniz?
```

### Tanınan ifadeler

Alanlar ve modlar `CONTRACT.md` §4.3 ile aynıdır (`cli.ANOVA_MODES`); başka alan ya da mod eklenmez.

| Alan | Örnek ifadeler (büyük/küçük harf, ondalık virgül/nokta fark etmez) |
|---|---|
| `f` | `f 0,25`, `f = 0.25`, `etki büyüklüğü 0,25`, `effect size f is 0.25`, `Cohen's f 0.25` |
| `alpha` | `alfa 0,05`, `alpha = 0.05`, `α 0,05`, `%5 anlamlılık düzeyi`, `significance level of 0.05` |
| `power` | `güç 0,80`, `%80 güç`, `80 percent power`, `power 0.8`, `1-β = 0.80` |
| `groups` | `3 grup`, `üç grup`, `Beş gruplu`, `dört diyet grubu`, `four groups`, `three-arm`, `grup sayısı 3`, `k = 3`, `dört farklı program`, `üç yöntemi karşılaştıran` |
| `n_total` | `toplam 100 katılımcı`, `toplam N = 100`, `total N = 100`, `n = 100`, `sample size of 100` |
| `beta_alpha_ratio` | `β/α oranı 1`, `beta/alpha ratio 1` |

| Mod | Örnek ifadeler |
|---|---|
| `a-priori` | `a priori`, `kaç kişi`, `gereken örneklem`, `how many participants`, `compute the sample size` |
| `post-hoc` | `post hoc`, `ulaşılan güç`, `gücüm ne olur`, `achieved power`, `what is the power` |
| `compromise` | `compromise` |
| `criterion` | `criterion`, `kriter`, `gereken alpha`, `required alpha` |
| `sensitivity` | `sensitivity`, `duyarlılık`, `en küçük etki`, `minimum detectable effect` |

Mod yazılmazsa, verilen alanlar **yalnızca bir** modun gerekli alanlarıyla birebir örtüşüyorsa o mod kullanılır
ve yanıtta bunun nedeni yazılır; aksi hâlde mod sorulur.

### Eksik, çelişkili ve hatalı girdiler

- **Varsayılan değer yoktur.** Eksik alanlar adlarıyla sorulur; hesap aracı çağrılmaz. "Orta etki" gibi sözel
  etiketler f değerine çevrilmez.
- **Konuşma durumu korunur.** Sonraki mesajda verilen değer eksikleri tamamlar; önceki bir değeri yeni bir
  değerle değiştirirseniz yanıtta "… olarak güncellendi" yazar. Hesaptan sonra değerler kalır ("alfa 0,01
  olsun" yeniden hesaplar); `sıfırla` / `yeni analiz` / `reset` hepsini siler.
- **Aynı mesajda çelişki** (ör. `alfa 0,05 ve alfa 0,01`, ya da hem `a priori` hem `post hoc`): hangisinin
  geçerli olduğu sorulur. Hiçbir alana bağlanamayan ya da birden çok alana bağlanabilen sayı da sorulur.
- **Grup başına n** (`her grupta 20 kişi`): grup sayısı biliniyorsa `n_total = n × groups` olarak çevrilir ve
  yanıtta bu dönüşüm yazılır; açıkça verilen bir toplam N ile uyuşmazsa sorulur.
- **Biçim/aralık hataları** sunucuya olduğu gibi gönderilir ve sözleşmenin kodu aktarılır (`alfa 1,5` →
  `OUT_OF_RANGE`, `alpha 0.0.5` → `INVALID_VALUE`, `3.5 grup` → `INVALID_VALUE`). Reddedilen değer
  durumdan çıkarılır ve yenisi istenir.
- **Başka ailelerin parametreleri** (`two-tailed`, `Cohen's d`, `f2`, `η²`, `x = 3`) sunucuya gönderilir ve
  `UNKNOWN_PARAM` aktarılır. **Desteklenmeyen analizler** (t testi, ki-kare, regresyon, iki yönlü ANOVA,
  tekrarlı ölçümler, korelasyon…) için `UNSUPPORTED` aktarılır ve desteklenen modlar listelenir.

Her MCP çağrısı `logs/agent_calls.jsonl` dosyasına bir satır yazılır (`ts`, `question`, `tool`, `tool_input`,
`tool_output`, `is_error`, `tokens_in`, `tokens_out`, `agent`). CONTRACT §8 biçimi korunur; ajan dil modeli
çağırmadığı için `tokens_in`/`tokens_out` her zaman `0`'dır (ölçüm değildir). Yaygın anahtar biçimleri
(`sk-…`, `ghp_…`, `AKIA…`) ve adı KEY/TOKEN/SECRET/PASSWORD içeren ortam değişkenlerinin değerleri
`[REDACTED]` olarak maskelenir; ortam değişkenleri kaydedilmez. Yalnızca kurgusal senaryolar kullanın.

### Bilinen sınırlamalar

- Yalnızca tanımlı kalıplar tanınır. Farklı bir anlatımda (ör. sayının anahtar sözcükten virgülle ayrılması:
  `güç, 0.8`) ajan sayıyı sorar ya da alanı eksik sayar; tahmin etmez.
- Sayı sözcükleri yalnızca grup sayısında ve `iki`…`dokuz`, `two`…`ten` için tanınır; `bir`/`one` ve
  Türkçe `on` belirsiz olduğu için tanınmaz (rakamla yazın).
- Binlik ayırıcı desteklenmez: `1.000` ve `1,000` ondalık 1.0 okunur ve tam sayı alanlarında
  `INVALID_VALUE` ile reddedilir.
- Yanıtlar Türkçedir; İngilizce girdiler de Türkçe yanıtlanır.
- Değerlendirme setlerini ve kuralları aynı geliştirici yazdı; sonuçlar setteki ifadeler içindir, görülmemiş
  ifadelere genellemeyi ölçmez.

## Değerlendirme

- `evals/questions.jsonl` — **temel 10 senaryo**: 7 hesap (a-priori ×3, post-hoc, sensitivity, compromise,
  criterion) ve 3 eksik parametre (alpha yok, sözel etki büyüklüğü, grup sayısı yok).
- `evals/extra_questions.jsonl` — **14 ek senaryo**: çelişkili değer ve mod, belirsiz sayı, aralık dışı ve
  biçimi bozuk değer, `INCONSISTENT`, bilinmeyen parametre, desteklenmeyen analiz, mod sorusu, İngilizce,
  ondalık virgül/sıra/büyük harf, iki çok turlu tamamlama.

Hesap senaryolarının beklenen çıktıları bu koddan değil, `oracle/` GUI vektörlerinden (AN-005, AN-006,
AN-019, AN-029) ve CONTRACT §9 açık vektörlerinden alınmıştır; karşılaştırma CONTRACT §6 toleransıyla yapılır.

Depo kökünde:

```
gpower-clone-eval                    # 24 senaryo; rapor evals/results/report.md, report.json, agent_calls.jsonl
gpower-clone-eval --extra ""         # yalnızca temel 10 senaryo
gpower-clone-eval --check-expected   # ajanı çalıştırmadan beklentileri MCP üzerinden motorla karşılaştırır
python -m gpower_clone.agent.evaluate ...   # eşdeğeri
```

Değerlendirme ajanı stdio MCP sunucusuyla çalıştırır ve şunları ölçer: parametre çıkarımı, mod tespiti, doğru
MCP aracı, hesap çağrısının başarısı, beklenen çıktıyla eşleşme, **MCP çıktısı = CLI stdout** (her başarılı
hesap aynı girdiyle `python -m gpower_clone` alt sürecinde yeniden çalıştırılır), eksik alan tespiti, doğru soru,
çelişkili/geçersiz/desteklenmeyen girdinin tespiti, eksik/hatalı girdide hesap yapılmaması ve **determinizm**
(tüm senaryolar iki kez çalıştırılır, yanıtlar ve araç çağrıları karşılaştırılır). Tüm senaryolar geçer ve
çalıştırmalar aynıysa çıkış kodu 0, aksi hâlde 1'dir. Token ya da API maliyeti yoktur ve raporlanmaz.
Sonuçlar `evals/results/report.md` içindedir.

GUI karşılaştırması: beklenen değerler ekran görüntülerinden elle okunmuş 7 basamaklı değerlerdir
(`oracle/README.md`); G*Power'ın iç (tam double) değerleri bilinmez, 1e-6 toleransının altındaki farklar
ayırt edilemez.

## Testler

```
pytest                 # hepsi
pytest -m "not bonus"  # yalnızca zorunlu modlar
pytest tests/test_mcp_server.py tests/test_agent.py tests/test_agent_parser.py   # MCP ve ajan
```

Testler CLI'yi alt süreçte (`python -m gpower_clone`) çalıştırır; kurulu komutu denemek için
`GPOWER_CLONE_CMD=gpower-clone pytest`.

`tests/test_vectors.py` her CLI çağrısının duvar saati süresini CONTRACT §2.1'in 2 s sınırına karşı ölçer. Süre
makine yüküne duyarlıdır: geliştirme makinesinde (8 mantıksal çekirdek) boşta çağrı başına medyan 0,74 s /
en fazla 1,06 s ölçüldü ve dosya 3 ardışık çalıştırmada 36/36 geçti; aynı dosya 3 meşgul süreçle 35/36,
8 meşgul süreçle tüm süre testlerinde 2 s'yi aştı. Süre testlerini başka yük yokken çalıştırın.

- `test_mcp_server.py`: araç kaydı ve şemaları, her mod, 25 açık vektörde ve hata durumlarında CLI = MCP,
  bilinmeyen alanların şemada ve sunucuda reddi, stdio taşıması.
- `test_agent_parser.py`: TR/EN ifadeler, ondalık virgül/nokta, sıra, harf, Türkçe İ/ı, yüzde, sayı sözcükleri,
  tekrar/çelişki/belirsiz sayı, biçim hataları, bilinmeyen parametreler, desteklenmeyen analizler, determinizm.
- `test_agent.py`: gerçek MCP sunucusuyla doğru araç ve motorla aynı sonuç, eksikte hesap yapılmaması, çok turlu
  tamamlama, çelişkiler, sözleşme hata kodları, MCP hatası, LLM paketleri içe aktarılamazken ve API anahtarı
  yokken çalışma, ağ bağlantısı denemesi olmaması, log maskeleme, cp1254 konsol, determinizm, değerlendirme.

## Belgeler

- `CONTRACT.md` — arayüz (yetkili kaynak)
- `SPEC.md` — davranış, bilinmeyenler; §F geçici uygulama kararları
- `oracle/` — sözleşme ve GUI referans vektörleri
- `evals/` — ajan değerlendirme senaryoları ve raporu
