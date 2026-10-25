# 02 — Uygulama oturumu: `gpower-clone` / `anova-oneway`

Bu oturumda `CONTRACT.md` (sürüm 1.0.0) arayüzüne uyan hesaplama motorunu, CLI'yi ve testleri yaz.
Başlamadan önce `git rev-parse --show-toplevel` ve `git status --short` çalıştır. Remote varmış gibi davranma.

## Girdi belgeleri (yalnızca oku, değiştirme)

- `CONTRACT.md`: arayüzün tek yetkili kaynağı.
- `SPEC.md`: §A arayüzün özetidir. §B, §C ve §E davranışı ve bilinmeyenleri anlatır.
- `evidence/LEDGER.md`: kanıt kimlikleri (E-xxx, G-xxx, C-xxx).
- `oracle/public_vectors.jsonl`: sözleşmenin 25 açık vektörü `[CONTRACT]`.
- `oracle/anova-apriori.csv`: 30 A priori GUI vektörü `[GUI]`. Sütun eşlemesi: `k` = `groups`, `total_n` = `n_total`.
- `oracle/README.md`: aynı 30 vektör için görüntüden okunmuş ncp, critical_f, df1, df2 ve actual_power değerleri.

Bu oturumda değiştirilmeyecekler: `CONTRACT.md`, `oracle/` altındaki her şey (CSV, JSONL, PNG, README) ve `evidence/`.

## Temiz oda kuralları

- REA, Ghidra veya G*Power ikilisini kullanma. Repo dışındaki ham REA kanıt paketini açma.
- Hesabı yayımlanmış yöntemlerden ve SPEC'teki davranış anlatımından yaz. Pseudo-code kopyalama.
- Yeni GUI deneyi yapma, oracle sonucu uydurma.

## Teknoloji

- Python 3.14, scipy 1.18 (`scipy.stats.f`, `scipy.stats.ncf`), pytest 9.1. Bunlar `ENVIRONMENT_REPORT.md`'de doğrulandı.
- Sürümleri `requirements.txt` dosyasında sabitle.
- `pyproject.toml` içinde `gpower-clone` adlı bir console script tanımla.
- Kod `src/` altına, testler `tests/` altına gider.
- `README.md` kurulumu ve çalıştırmayı tek komutla göstersin (CONTRACT §2.1).

## Kapsam ve sıra

1. **Zorunlu:** `anova-oneway` için `a-priori` ve `post-hoc`, CLI, JSON çıktı, hata davranışı ve `--version`.
2. **Bonus:** `sensitivity`, `criterion`, `compromise`. Bunlara yalnızca 1. adımın bütün testleri geçtikten sonra, ayrı bir aşamada başla.
3. Sözleşmedeki diğer aileler (`t2-indep`, `t-paired`, `chi2-contingency`, `multireg-r2`) bu oturumun kapsamında değil. `UNSUPPORTED` döndür ve bunu rapora yaz. Bu aileler ekibin başka bir parçasına aitse kullanıcı karar verir.

## Hesap

Bu hesapların kaynağı `[REA]`, kanıtları E-020…E-026. Ayrıca `[GUI]` ile 30/30 vektörde tutarlı bulundular (G-003, G-004).

- `df1 = groups − 1`, `df2 = n_total − groups`
- `ncp = f² · n_total`
- `critical_f = f.isf(alpha, df1, df2)`. Tamamlayıcı kuyruk kullan, `ppf(1 − alpha)` kullanma.
- `power = ncf.sf(critical_f, df1, df2, ncp)`

**Bilinmeyen 1 — noncentral F'nin sayısal doğruluğu (SPEC U-2):** G*Power'ın algoritması bilinmiyor. scipy'nin `ncf` fonksiyonunu kullan ve sapmayı ölç. Toleransı gevşetme. Tolerans aşılıyorsa durumu rapora yaz.

**Bilinmeyen 2 — A priori N araması (SPEC U-1):** Aşağıdaki yaklaşım bir `[INFERENCE]`, doğrulanmış bir algoritma değil.

- Uygulama yaklaşımı: `n_total = groups · m` olmak üzere, `power(n_total) ≥ power` koşulunu sağlayan en küçük `m` değerini ara.
- Arama `m = 2` ile başlasın (E-030 alt sınırı k+1; k'nın katı olan ilk değer 2k).
- Aralığı üstel olarak genişlet, ardından tam sayı ikili aramayla daralt. Güç N'ye göre monoton kabul ediliyor; bu da bir [INFERENCE].
- `actual_power`, seçilen `n_total` ile hesaplanır.
- Bir referans vektörü uyuşmazsa algoritmayı o vektöre göre gizlice ayarlama. Uyuşmazlığı ayrıntısıyla rapora yaz.

**Bilinmeyen 3 — bonus modlar (SPEC U-3):** Yaklaşımlar şunlar; hepsi [INFERENCE]:

- `sensitivity`: `power(f) = power` denkleminin f için kökü.
- `criterion`: `power(alpha) = power` denkleminin alpha için kökü.
- `compromise`: `beta(alpha) = beta_alpha_ratio · alpha` denkleminin alpha için kökü. Çıktılar `beta` ve `power = 1 − beta`.

Kök bulma için `scipy.optimize.brentq` kullan. Sonuçları yalnızca `public_vectors.jsonl` içindeki ilgili vektörle ölçebilirsin. Bu tek noktalık bir ölçümdür; raporda böyle anılmalı.

## CLI ve çıktı (CONTRACT §2–§6, SPEC §A)

- Argüman ayrıştırma katıdır.
  - Her mod için zorunlu alanlar SPEC §A4'teki gibidir. Varsayılan değer **yoktur**.
  - Eksik alan → `MISSING_PARAM`. Tanınmayan ya da modla ilgisiz alan → `UNKNOWN_PARAM`.
  - Bilinmeyen test veya mod → `UNSUPPORTED`.
- Sayı okuma işletim sisteminin dil ayarından bağımsız olmalı (`float()` kullan, `locale` kullanma).
  - Sayı olmayan değer, NaN, inf ve tam sayı alanında ondalık değer → `INVALID_VALUE`.
  - SPEC §A5'teki aralıkların dışı → `OUT_OF_RANGE`.
- Başarılı çıktı:
  - stdout'a tek satır JSON, `json.dumps(..., allow_nan=False)` ile. Ondalıklar tam double hassasiyetle yazılır.
  - `n_total`, `df1` ve `df2` Python `int` olmalı.
  - Çıkış kodu 0. Log ve uyarılar yalnızca stderr'e.
- Hata çıktısı: stdout'a `{"error", "code", "field"}`. Çıkış kodu girdi hatasında 2, iç hatada 1.
- `--version` → `{"contract_version": "1.0.0", "name": ..., "engine": ...}`.
- Sınır girdileri (SPEC §C) U-4 kapsamında bilinmiyor. Aşağıdaki kararları **geçici** olarak uygula ve her birini SPEC'e yeni bir "§F Uygulama kararları (geçici)" bölümünde [INFERENCE] etiketiyle yaz. SPEC'in diğer bölümlerine dokunma.
  - `n_total ≤ groups` → `INCONSISTENT`, `field: n_total`.
  - `power ≤ alpha` (a-priori) → `INCONSISTENT`, `field: power`. Bu, sözleşmedeki örnekle uyumlu.
  - Post-hoc'ta `n_total` k'nın katı değilse hesap olduğu gibi yapılır.
  - Arama veya kök bulma başarısız olursa → `NO_SOLUTION`.

## Ölçülebilir doğrulama (pytest)

1. **Sözleşme vektörleri:** `public_vectors.jsonl` içindeki 5 `anova-oneway` vektörü. Tam sayılar birebir eşleşmeli. Ondalıklarda |fark| ≤ 1e-6 ya da göreli fark ≤ 1e-6 olmalı (CONTRACT §6). Bonus vektörler ayrı işaretlensin, zorunlu testlerden ayrılabilsin.
2. **GUI vektörleri:** CSV'deki 30 satırın her birinde `n_total` birebir eşleşmeli. `oracle/README.md` tablosundaki ncp, critical_f, df1, df2 ve actual_power değerleri de aynı toleransla karşılaştırılsın. README'yi yalnızca oku.
3. **CLI sözleşmesi:**
   - Her hata kodu ve çıkış kodu için en az bir test.
   - Tek satır JSON; tam sayı alanlarının tipi.
   - stdout'un temiz kalması.
   - Ondalık ayırıcının nokta olması.
   - Aynı girdinin iki kez aynı çıktıyı vermesi.
4. **Süre:** En büyük N'ye sahip AN-016 dahil bütün vektörlerde, subprocess içinde her çağrı 2 saniyenin altında kalmalı.

## Bitiş raporu

- A priori `n_total` eşleşme oranını iki kaynak için ayrı ver: sözleşme 1/1 ve GUI x/30. Kapı (CONTRACT §6) %90.
- Ondalık alanlarda en büyük mutlak ve göreli sapmayı alan bazında ver.
- Başarısız testlerin çıktısını aynen aktar.
- En uzun çağrı süresini ver.
- Bonus modların sonuçlarını ayrı bir bölümde ver.
- Eklenen geçici kararları listele.
- `git status --short` çıktısını ekle.
- Commit atma, kullanıcı istemedikçe.
