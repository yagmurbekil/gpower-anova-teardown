# SPEC — anova-oneway

G*Power 3.1.9.7: *F tests – ANOVA: Fixed effects, omnibus, one-way* için arayüz ve davranış spesifikasyonu.
Kanıt kimlikleri `evidence/LEDGER.md` içindeki satırlara karşılık gelir.

## 0. Kaynaklar ve etiketler

Resmi sözleşme: `CONTRACT.md`, sürüm **1.0.0** (2026-10-21). Sözleşme **arayüzü** tanımlar, **davranışı** tanımlamaz
(CONTRACT §0 notu); davranış `[REA]` ve `[GUI]` kanıtıyla keşfedilir.

| Etiket | Anlamı | Nerede |
|---|---|---|
| `[CONTRACT]` | `CONTRACT.md`'nin açıkça yazdığı gereklilik veya açık vektör | `CONTRACT.md`, `oracle/public_vectors.jsonl` |
| `[REA]` | REA/Ghidra ile ikiliden doğrudan gözlenen bulgu | `evidence/LEDGER.md` E-xxx |
| `[GUI]` | G*Power arayüzünde gözlenen değer (kullanıcının ekran görüntülerinden doğrulanmış) | `oracle/anova-apriori.csv`, `oracle/README.md`, LEDGER G-xxx |
| `[INFERENCE]` | Kanıtlara dayanan yorum; doğrudan gözlem değil | — |
| `[UNKNOWN]` | Henüz doğrulanmamış davranış | `evidence/experiments.md` |

Bir maddede birden çok etiket varsa her biri yalnızca kendi kaynağının söylediğini taşır.

---

## A. Arayüz (sözleşme)

### A1. Kapsam

- [CONTRACT] Test kimliği `anova-oneway` (K3); G*Power testi "F tests – ANOVA: Fixed effects, omnibus, one-way" (§4.3).
- [CONTRACT] Zorunlu modlar: `a-priori`, `post-hoc`. Bonus modlar: `compromise`, `criterion`, `sensitivity` (§1, §3).
- [CONTRACT] Etki büyüklüğü yalnızca doğrudan `--f` ile girilir. "Determine" penceresi, X-Y plot ve protokol çıktısı **kapsam dışıdır** (§1).
- [REA] İkilide bu test adı (`0x5c9ae4`) ve `PowerFAnovaGlobal` hesap sınıfı (vtable `0x5c8538`) bulunuyor (E-002…E-004).
- [INFERENCE] Bu test `PowerFAnovaGlobal` tarafından hesaplanıyor (E-007).

### A2. Komut

- [CONTRACT] Çağrı: `gpower-clone --test anova-oneway --mode <MODE_ID> [--<alan> <değer> ...]` (§2.1).
- [CONTRACT] Çalıştırılabilir dosyanın adı `gpower-clone`; dil serbest; README'de kurulum ve çalıştırma tek komutla gösterilir (§2.1).
- [CONTRACT] Sürüm sorgusu: `gpower-clone --version` → `{"contract_version": "1.0.0", "name": "<takım-adı>", "engine": "<dil ve sürüm>"}` (§2.2).

### A3. Parametre kuralları

- [CONTRACT] Her parametre `--<alan> <değer>` biçimindedir; alan adları §4 tablolarıyla **birebir** aynıdır (§2.1).
- [CONTRACT] **Varsayılan değer yoktur.** Mod için gerekli her alan açıkça verilmelidir; eksik alan hatadır (`MISSING_PARAM`) (§2.1).
  G*Power'ın iç başlangıç değerleri (§B1, E-010…E-014) CLI'de varsayılan olarak **kullanılmaz**.
- [CONTRACT] Tanınmayan alan ve modla ilgisiz alan (ör. `post-hoc` modunda `--power`) hatadır (`UNKNOWN_PARAM`) (§2.1, §2.4).
- [CONTRACT] Ondalık ayırıcı her zaman noktadır (`0.05`); işletim sistemi dil ayarından etkilenmez (§2.1).
- [CONTRACT] Bilinmeyen `--test` veya `--mode` → `UNSUPPORTED` (§2.4).

### A4. Mod başına zorunlu girdiler ve çıktılar (§4.3)

| `MODE_ID` | Durum | Zorunlu girdiler | Zorunlu çıktılar |
|---|---|---|---|
| `a-priori` | Zorunlu | `f`, `alpha`, `power`, `groups` | `ncp`, `critical_f`, `df1`, `df2`, `n_total`, `actual_power` |
| `post-hoc` | Zorunlu | `f`, `alpha`, `n_total`, `groups` | `ncp`, `critical_f`, `df1`, `df2`, `power` |
| `compromise` | Bonus | `f`, `beta_alpha_ratio`, `n_total`, `groups` | `ncp`, `critical_f`, `df1`, `df2`, `alpha`, `beta`, `power` |
| `criterion` | Bonus | `f`, `power`, `n_total`, `groups` | `ncp`, `critical_f`, `df1`, `df2`, `alpha` |
| `sensitivity` | Bonus | `alpha`, `power`, `n_total`, `groups` | `ncp`, `critical_f`, `df1`, `df2`, `f` |

Alan ↔ G*Power etiketi [CONTRACT]: `f` = Effect size f · `groups` = Number of groups · `alpha` = α err prob ·
`power` = Power (1-β err prob) · `beta_alpha_ratio` = β/α ratio · `ncp` = Noncentrality parameter λ ·
`critical_f` = Critical F · `df1`/`df2` = Numerator df / Denominator df · `n_total` = Total sample size ·
`actual_power` = Actual power · `beta` = β err prob.

Proje içi adlandırma eşlemesi: bu dosyanın §B bölümünde ve `oracle/anova-apriori.csv`'de kullanılan
`k` = `groups`, `N` / `total_n` = `n_total`, CSV'deki `power` = girdi `power`. CSV sütun adları değiştirilmez;
eşleme test düzeneğinde yapılır.

### A5. Girdi aralıkları (§5)

| Alan | Tür | Aralık [CONTRACT] |
|---|---|---|
| `alpha` | ondalık | 0 < alpha < 1 |
| `power` | ondalık | 0 < power < 1 |
| `beta_alpha_ratio` | ondalık | > 0 |
| `f` | ondalık | > 0 |
| `n_total` | tam sayı | ≥ 2 |
| `groups` | tam sayı | ≥ 2 |

- [CONTRACT] Aralık dışı → `OUT_OF_RANGE` (§5).
- [CONTRACT] Sayı olmayan değer veya tam sayı beklenen yerde ondalık → `INVALID_VALUE` (§2.4).
- [CONTRACT] Aralığın **içindeki** bir değerin kabul edilip edilmeyeceğini G*Power'ın davranışı belirler (§5). → bkz. §C.

### A6. Başarılı çıktı (§2.3)

- [CONTRACT] `stdout`'a **tek satır JSON**; başka hiçbir şey yazılmaz. Log, uyarı ve ilerleme `stderr`'e.
- [CONTRACT] Çıkış kodu `0`.
- [CONTRACT] Sayılar JSON `number`, **tam double hassasiyetle**; yuvarlama yapılmaz.
- [CONTRACT] `n_total`, `df1`, `df2` JSON **tam sayısıdır** (`300`, `300.0` değil).
- [CONTRACT] §A4'teki alanlar zorunludur; fazladan alan yazılabilir, düzenek yok sayar.

### A7. Hata çıktısı ve çıkış kodları (§2.4)

- [CONTRACT] `stdout`'a tek satır JSON: `{"error": "<açıklama>", "code": "<KOD>", "field": "<alan>"}`.
  `error` insan içindir (Türkçe veya İngilizce). Düzenek önce `error` alanına, sonra `code`'a bakar.
- [CONTRACT] Çıkış kodu: `2` geçersiz girdi, `1` iç hata (hesap yapılamadı, beklenmeyen durum).

| `code` | Anlamı [CONTRACT] |
|---|---|
| `MISSING_PARAM` | Mod için gerekli bir alan verilmedi |
| `UNKNOWN_PARAM` | Tanınmayan ya da bu modla ilgisiz alan |
| `INVALID_VALUE` | Sayı değil, tam sayı olması gereken yerde ondalık vb. |
| `OUT_OF_RANGE` | §A5 aralığının dışında |
| `INCONSISTENT` | Değerler tek tek geçerli ama birlikte anlamsız |
| `UNSUPPORTED` | Bilinmeyen `--test` ya da `--mode` |
| `NO_SOLUTION` | Girdiler geçerli ama G*Power da sonuç üretemiyor |

- [CONTRACT] Sözleşmedeki örnek hata: `{"error": "Power, alpha değerinden büyük olmalı", "code": "INCONSISTENT", "field": "power"}`.
  Bu bir **biçim örneğidir**; G*Power'ın `power ≤ alpha` girdisini gerçekten reddedip reddetmediği [UNKNOWN] (§C).

### A8. Çalışma koşulları (§2.1)

- [CONTRACT] **Deterministik:** aynı girdi her zaman aynı çıktıyı verir.
- [CONTRACT] **Süre:** her çağrı **2 saniye** içinde tamamlanır.
- [CONTRACT] **Ağ erişimi yoktur.**

### A9. Karşılaştırma ve kapı (§6)

- [CONTRACT] `n_total`, `df1`, `df2`: **tam eşleşme**.
- [CONTRACT] `ncp`, `critical_f`, `actual_power`, `power`, `alpha`, `beta`, `f`: |fark| ≤ 1e-6 **veya** göreli fark ≤ 1e-6.
- [CONTRACT] Hata beklenen vektör: `error` alanı var ve çıkış kodu ≠ 0; `code` eşleşirse ek puan.
- [CONTRACT] Referans, G*Power'ın protokolde gösterdiği 7 basamaklı değerdir.
- [CONTRACT] **Kapı:** gizli `a-priori` vektörlerinde `n_total` en az **%90** tam eşleşmeli; aksi hâlde MCP ve ajan bonusları puanlanmaz.

### A10. Bonus katmanlar (§7, §8) — bu aile için yalnızca not

- [CONTRACT] MCP aracı `power_analysis`: CLI ile aynı alan adları, aynı JSON çıktı/hata, aynı motor; 25 açık vektörde CLI = MCP eşdeğerlik testi zorunlu.
- [CONTRACT] Ajan, hesabı MCP aracına yaptırır; çağrılar `logs/agent_calls.jsonl`'a yazılır; yalnızca kurgusal senaryolar.

### A11. Etik kural

- [CONTRACT] Kaynak kod veya decompile çıktısı yayımlanmaz; hesap yayımlanmış yöntemlerden ve gözlenen davranıştan bağımsız olarak yeniden yazılır.
  Bu nedenle `evidence/LEDGER.md` yalnızca adres ve davranış anlatımı içerir; pseudo-code içermez.

---

## B. Davranış (G*Power)

### B1. Girdi alanlarının iç karşılıkları

| Sözleşme alanı | Sembol | Kanıt | Durum |
|---|---|---|---|
| `f` | f | E-012, E-023, E-024 | [REA] alan `+0xd8`; anlamı [INFERENCE] |
| `alpha` | α | E-010, E-025 | [REA] alan `+0xb0`; anlamı [INFERENCE] |
| `power` | 1−β | E-011 | [REA] alan `+0xb8`; anlamı [INFERENCE] |
| `n_total` | N | E-013, E-021 | [REA] alan `+0xe8`; anlamı [INFERENCE] |
| `groups` | k | E-014, E-020 | [REA] alan `+0xf0`; anlamı [INFERENCE] |

- [REA] İç nesnenin başlangıç değerleri: α = 0.05, power = 0.95, f = 0.25, N = 100, k = 5 (E-010…E-014).
  Bunlar **CLI varsayılanı değildir** (§A3).
- [UNKNOWN] GUI'de ilk açılışta görünen varsayılanlar (X-01). Sözleşme açısından gereksiz; yalnızca bilgi amaçlı.

### B2. Türetilen büyüklükler (tüm modlar)

- [REA] `df1 = k − 1` (E-020, E-021). [GUI] 30/30 vektörde doğru (G-003). [CONTRACT] 5 açık vektörde `df1 = 4` (k = 5).
- [REA] `df2 = N − k` (E-021). [GUI] 30/30 (G-003). [CONTRACT] açık vektörlerde `df2 = 300` (N 305) ve `95` (N 100).
- [REA] `λ = f² · N` (E-022, E-023). [GUI] 30/30 (G-004). [CONTRACT] post-hoc/compromise/criterion vektörlerinde λ = 0.25²·100 = 6.25.
- [REA] Ters ilişki `N = λ / f²` (E-024).
- [REA] `F_crit = Q_F(1 − α; df1, df2)`, merkezi F dağılımında (ncp = 0 iken) (E-025).

### B3. `post-hoc` (zorunlu)

- [INFERENCE] `power = 1 − CDF_ncF(F_crit; df1, df2, λ)` (E-025, E-026).
  Çağrı sırası REA ile gözlendi; dağılım nesnesinin CDF/quantile/ncp-ayarı metotlarının anlamı kullanım biçiminden çıkarıldı, ayrıca decompile edilmedi.
- [CONTRACT] Açık vektör `anova-oneway/post-hoc`: f 0.25, α 0.05, N 100, k 5 → ncp 6.2500000, critical_f 2.4674936, df 4/95, power 0.4663312.
- [UNKNOWN] Noncentral F CDF'sinin sayısal algoritması ve doğruluğu. 1e-6 toleransı için kritik.

### B4. `a-priori` (zorunlu)

- [REA] Bir arama aralığı `[k + 1, k + 100]` kuruluyor (E-030).
- [REA] Sınıfta "N'yi k'nın bir sonraki katına yukarı yuvarla" davranışı var (E-028).
- [INFERENCE] Toplam N, k'nın katına yuvarlanır ve `actual_power` bu N ile hesaplanır (E-029).
- [GUI] 30/30 vektörde `n_total` k'nın katı ve `actual_power ≥ power` (G-005, G-006).
- [CONTRACT] Açık vektör `anova-oneway/a-priori`: f 0.25, α 0.05, power 0.95, k 5 → n_total 305, actual_power 0.9521313
  (kullanıcının AN-001 vektörüyle birebir aynı).
- **[UNKNOWN] En küçük uygun N algoritması.** Seçilen N'nin "power hedefini sağlayan en küçük k katı" olup olmadığı,
  aramanın türü (adım/bisection), durma ölçütü ve aralık genişletme kuralı doğrulanmadı (G-009, E-032).
  Kapı (§A9) doğrudan buna bağlıdır.

#### B4.1 A priori referans testleri

| Kaynak | Dosya | Kapsam | Etiket |
|---|---|---|---|
| Sözleşme açık vektörü | `oracle/public_vectors.jsonl` (`anova-oneway/a-priori`) | 1 vektör, tüm çıktı alanları | [CONTRACT] |
| Kullanıcı GUI vektörleri | `oracle/anova-apriori.csv` (AN-001…AN-030), indeks `oracle/README.md` | 30 vektör; CSV'de yalnızca `n_total`, diğer çıktılar README'de görüntüden okunmuş | [GUI] |

- Bu iki kaynak ayrı tutulur ve birbirinin yerine geçmez. 30 GUI vektörü **yalnızca a-priori** modunu kapsar;
  Post hoc ve bonus modların davranışını **doğrulamaz**.

### B5. Bonus modlar: `compromise`, `criterion`, `sensitivity`

- [REA] Bu analiz türlerine ait arayüz metinleri ikilide var (E-045).
- [REA] `[1e-6, 0.3]` aralığı kuran bir metot var (E-031); [INFERENCE] sensitivity araması için olabilir (E-032, düşük güven).
- [CONTRACT] Her mod için bir açık vektör var (`oracle/public_vectors.jsonl`):
  - `compromise`: f 0.25, β/α 1, N 100, k 5 → critical_f 1.4272492, alpha = beta 0.2309247, power 0.7690753.
  - `criterion`: f 0.25, power 0.95, N 100, k 5 → critical_f 0.6552638, alpha 0.6245994.
  - `sensitivity`: α 0.05, power 0.95, N 100, k 5 → ncp 19.5245874, critical_f 2.4674936, f 0.4418664.
- [INFERENCE] Bu vektörlerde ncp = f²·N ve df1/df2 §B2 ile tutarlıdır.
- **[UNKNOWN] Her üç modun algoritması** (kök bulma yöntemi, başlangıç aralığı, durma ölçütü, çözümsüzlük durumu) (X-05…X-07).
  Açık vektörler yalnızca birer noktadır; algoritmayı doğrulamaz.

### B6. Çıktı gösterimi

- [REA] Arayüz dizeleri mevcut: Noncentrality parameter λ, Critical F, Numerator df, Denominator df, Total sample size, Actual power (E-040…E-044).
- [GUI] A priori çıktı panelinde ondalıklar 7 basamakla gösteriliyor; grafik başlığında critical F 6 anlamlı basamakla (G-007).
- [CONTRACT] Uygulama yuvarlamaz; tam double yazar (§A6).

---

## C. Sınır girdileri ve hata davranışı

Sözleşme yalnızca §A5 aralıklarını sabitler. Aralık içindeki şu durumların G*Power'daki karşılığı ve hangi `code`'a
eşleneceği **[UNKNOWN]**'dur (X-08):

| Durum | §A5'e göre | G*Power davranışı | Sözleşme kodu |
|---|---|---|---|
| `n_total ≤ groups` (df2 ≤ 0) | geçerli aralık | [UNKNOWN] | [UNKNOWN] (`INCONSISTENT` veya `NO_SOLUTION` adayı) |
| `power ≤ alpha` | geçerli aralık | [UNKNOWN] | [UNKNOWN] (sözleşme örneği `INCONSISTENT` kullanıyor) |
| `n_total` k'nın katı değil (post-hoc/bonus) | geçerli aralık | [UNKNOWN] | [UNKNOWN] |
| a-priori'de çok küçük f (çok büyük N) | geçerli aralık | [UNKNOWN] | [UNKNOWN] (`NO_SOLUTION` adayı) |
| criterion/compromise'da çözümsüz durum | geçerli aralık | [UNKNOWN] | [UNKNOWN] |

- [REA] İkilide genel aralık mesajları var (ör. "Total sample size is outside the admissible range (", `0x5c6524`);
  bu teste bağlı oldukları doğrulanmadı.
- [CONTRACT] Gizli vektörler sınır değerler ve geçersiz girdiler içerir (§9).

---

## D. Kapsam dışı

- [CONTRACT] "Determine" etki büyüklüğü penceresi kapsam dışıdır (§1).
  [REA] `CEff_F_Anova_Omni` sınıfı ve "Effect size from means / from variance" metinleri mevcut (E-006, E-046);
  incelenmedi ve incelenmesi gerekmiyor. Deney X-09 **isteğe bağlı / kapsam dışı** olarak işaretlendi, kaydı korunuyor.
- [CONTRACT] X-Y plot ve protokol çıktısı kapsam dışıdır.

---

## E. Açık belirsizlikler (özet)

| # | Konu | Durum | Bağlı kanıt / deney |
|---|---|---|---|
| U-1 | A priori en küçük uygun N algoritması | [UNKNOWN] | G-009, E-030, E-032 |
| U-2 | Noncentral F CDF/quantile sayısal doğruluğu | [UNKNOWN] | E-025 |
| U-3 | Bonus modların algoritmaları | [UNKNOWN] | E-031, E-032, X-05…X-07 |
| U-4 | Aralık içi sınır girdileri ve hata kodu eşlemesi | [UNKNOWN] | §C, X-08 |
| U-5 | CSV test adı yazımı virgülsüz; sözleşme/GUI virgüllü | Adlandırma farkı, değer çelişkisi yok | `oracle/README.md` |

---

## F. Uygulama kararları (geçici)

`prompts/02-implement.md` oturumunda (2026-10-26) uygulanan kararlar. Hepsi **[INFERENCE]**'tır; G*Power davranışı
olarak doğrulanmadı (U-1, U-3, U-4). Yeni kanıt geldiğinde değiştirilecek.

| # | Durum | Karar | Etiket |
|---|---|---|---|
| F-1 | `n_total ≤ groups` (df2 ≤ 0), `n_total` alan her modda | `INCONSISTENT`, `field: n_total`, çıkış 2 | [INFERENCE] |
| F-2 | `a-priori`'de `power ≤ alpha` | `INCONSISTENT`, `field: power`, çıkış 2 (CONTRACT §2.4 örneğiyle uyumlu) | [INFERENCE] |
| F-3 | `post-hoc`/bonus modlarda `n_total` k'nın katı değil | Hesap olduğu gibi yapılır (df2 = N − k) | [INFERENCE] |
| F-4 | Arama veya kök bulma başarısız | `NO_SOLUTION`, `field: null`, çıkış 1 | [INFERENCE] |
| F-5 | A priori arama: `n_total = groups · m`, m = 2'den üstel genişletme + tam sayı ikili arama; güç N'de monoton kabul | `power(N) ≥ power` sağlayan en küçük m | [INFERENCE] (U-1) |
| F-6 | A priori üst sınır | N > 10⁹ gerekiyorsa `NO_SOLUTION` | [INFERENCE] |
| F-7 | `sensitivity` | `power(f) = power` kökü, `brentq`; aralık [1e-12, 1], üst uç 1e6'ya kadar ikiye katlanır. `power ≤ alpha` kök vermez → `NO_SOLUTION` | [INFERENCE] (U-3) |
| F-8 | `criterion` | `power(alpha) = power` kökü, `brentq`, aralık [1e-300, 1 − 2⁻⁵³] | [INFERENCE] (U-3) |
| F-9 | `compromise` | `beta(alpha) = beta_alpha_ratio · alpha` kökü, `brentq`, aynı aralık; `power = 1 − beta` | [INFERENCE] (U-3) |
| F-10 | Doğrulama sırası | test/mod → tanınmayan/ilgisiz alan → eksik alan → değer biçimi → aralık → tutarlılık; ilk hata raporlanır | [INFERENCE] |
| F-11 | Ayrıştırma | `--` ile başlamayan argüman → `UNKNOWN_PARAM` (`field` = argüman); değersiz bayrak ve aynı bayrağın tekrarı → `INVALID_VALUE`; `--alan=değer` biçimi desteklenmez (`UNKNOWN_PARAM`) | [INFERENCE] |
| F-12 | Sayı biçimi | Yalnızca ASCII rakam ve nokta; `0,05`, `1_000`, `nan`, `inf`, taşan değer (`1e400`) → `INVALID_VALUE`; tam sayı alanında `5.0` veya `1e1` → `INVALID_VALUE` | [INFERENCE] |
| F-13 | Sözleşmedeki diğer aileler (`t2-indep`, `t-paired`, `chi2-contingency`, `multireg-r2`) | `UNSUPPORTED`, `field: test` (bu oturumun kapsamı dışında) | [INFERENCE] |
| F-14 | Beklenmeyen iç hata | `code: INTERNAL_ERROR` (sözleşme tablosunda yok), `field: null`, çıkış 1 | [INFERENCE] |
| F-15 | `--version` | Yalnızca tek başına verildiğinde; `name` = `gpower-clone` (takım adı belirlenince değiştirilecek) | [INFERENCE] |
| F-16 | `df1 = groups − 1` veya `df2 = n_total − groups` ≥ 2⁶⁴ (ör. `n_total = 10^20`), `a-priori` dışındaki bütün modlar | Dağılım fonksiyonu çağrılmadan `NO_SOLUTION`, `field: null`, çıkış 1. Uygulamanın sayısal sınırıdır (numpy 2⁶⁴ ve üstünü object türüne çevirir); 2⁶⁴ − 1'e kadar hesap değişmeden yapılır. G*Power'ın kabul edilebilir N aralığı bilinmiyor (U-4; SPEC §C'deki "admissible range" mesajı) | [INFERENCE] |
