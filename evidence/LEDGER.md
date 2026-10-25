# Kanıt Defteri — anova-oneway

Hedef: `C:\GPower\GPower_3.1.9.7_143\GPowerNT.exe` (repo dışında)
SHA-256: `c63e6a133eb6372932f810c08cc33dc35a06d1ddb658f897bd6c34a754efc812` (oturum başında `sha256sum` ile ve REA `open_binary` ile ayrı ayrı doğrulandı)
Araç: REA → Ghidra 12.1.4 sağlayıcısı, x86 (PE32, machine 0x14c), image base `0x400000`
Oturum: 2026-10-25, `prompts/01-recon.md`

Adresler Ghidra sanal adresleridir. Fonksiyon adları (`FUN_...`) Ghidra'nın otomatik adlarıdır; PDB yüklenmedi.

**Yayın kuralı (CONTRACT, Etik niyet):** Bu defter decompile/pseudo-code çıktısı içermez. "Gözlenen davranış"
sütunu, REA ile gözlenen davranışın kendi sözlerimizle yazılmış kısa anlatımıdır. Adres, fonksiyon kimliği ve vtable
slotu izlenebilirlik için korunur. Ham REA çıktısı yalnızca repo dışındaki kanıt paketinde durur (bkz. "Ham kanıt").
2026-10-25 tarihinde önceki sürümdeki pseudo-code alıntıları bu anlatımlarla değiştirildi; kimlikler değişmedi.

Güven: **Yüksek** = doğrudan gözlem; **Orta** = gözlem + kısa çıkarım zinciri; **Düşük** = zayıf/dolaylı.

## Kimlik ve sınıf

| ID | Etiket | İddia | REA aracı | Adres / fonksiyon | Gözlenen davranış | Güven |
|---|---|---|---|---|---|---|
| E-001 | [REA] | İkili PE32, x86, MFC tabanlı GUI; 9116 prosedür, 2570 tanımlı dize | `open_binary`, `binary_overview`, `inspect_pe_resources` | — | Format pe32, makine kodu 0x14c; 89 diyalog kaynağı; MFC140U.DLL içe aktarımı | Yüksek |
| E-002 | [REA] | Test adı dizesi ikilide mevcut | `search_strings` | `0x5c9ae4` | Veri bölümünde "ANOVA: Fixed effects, omnibus, one-way" metni | Yüksek |
| E-003 | [REA] | Bu dizeye tek referans, test adını metin nesnesi olarak döndüren küçük bir fonksiyondan | `xrefs`, `procedure_pseudo_code` | `0x4ba58a` ∈ `FUN_004ba550` | Fonksiyon yalnızca test adını yeni bir metin nesnesine kopyalayıp döndürüyor; hesap yok | Yüksek |
| E-004 | [REA] | `FUN_004ba550`, `PowerFAnovaGlobal` sınıfının vtable'ında yer alıyor | `xrefs`, `read_bytes` | vtable `0x5c8538`, slot `0x5c85b0` | RTTI tip adı `0x60cb78` → nesne konum kaydı `0x5eeeac` → vtable öncesi işaretçi `0x5c8534` | Yüksek |
| E-005 | [REA] | Aynı sınıfın test ailesi adı "F tests" | `procedure_pseudo_code` | `FUN_004b7a30` (slot `0x5c85b4`) | Fonksiyon aile adı olarak "F tests" metnini döndürüyor | Yüksek |
| E-006 | [REA] | Etki büyüklüğü diyaloğu sınıfı `CEff_F_Anova_Omni` adıyla mevcut (kapsam dışı) | `search_strings` | `0x5d006c`, RTTI `0x60d678` | Sınıf adı metni ve RTTI kaydı mevcut | Yüksek |
| E-007 | [INFERENCE] | `PowerFAnovaGlobal`, GUI'deki "ANOVA: Fixed effects, omnibus, one-way" testinin hesap sınıfıdır | E-003, E-004 | `0x5c8538` | Test adını döndüren metot bu sınıfın vtable'ında | Orta |

## Başlangıç değerleri (kopyalama/kurulum yolu)

`FUN_004b9f20` (slot `0x5c8544`): sınıfın yeni bir örneğini oluşturup vtable'ı `PowerFAnovaGlobal` olarak ayarlıyor ve
alanlara sabit başlangıç değerleri yazıyor. Değerler ikilideki IEEE-754 double sabitlerinden okundu (veri, kod değil).

| ID | Etiket | İddia | Adres | Gözlenen davranış | Güven |
|---|---|---|---|---|---|
| E-010 | [REA] | Alan `+0xb0` başlangıç değeri 0.05 | `FUN_004b9f20` | Sabit `0x3fa999999999999a` (= 0.05) bu alana yazılıyor | Yüksek |
| E-011 | [REA] | Alan `+0xb8` başlangıç değeri 0.95 | `FUN_004b9f20` | Sabit `0x3fee666666666666` (= 0.95) bu alana yazılıyor | Yüksek |
| E-012 | [REA] | Alan `+0xd8` başlangıç değeri 0.25 | `FUN_004b9f20` | Sabit `0x3fd0000000000000` (= 0.25) bu alana yazılıyor | Yüksek |
| E-013 | [REA] | Alan `+0xe8` başlangıç değeri 100.0 | `FUN_004b9f20` | Sabit `0x4059000000000000` (= 100.0) bu alana yazılıyor | Yüksek |
| E-014 | [REA] | Grup sayısı ayarlayıcısı 5.0 ile çağrılıyor | `FUN_004b9f20` → `FUN_004ba660` | Ayarlayıcıya sabit `0x4014000000000000` (= 5.0) geçiriliyor | Yüksek |
| E-015 | [REA] | Bir `FDistribution` nesnesi oluşturulup sınıfın `+0x58` alanına bağlanıyor | `FUN_004b9f20` | F dağılımı nesnesi kuruluyor; işaretçisi `+0x58`'e konuyor | Yüksek |
| E-016 | [INFERENCE] | Alan anlamları: `+0xb0`=α, `+0xb8`=power, `+0xd8`=f, `+0xe8`=N toplam, `+0xf0`=k | E-010…E-014, E-020…E-025 | Değerler ve kullanıldıkları formüller | Orta |

Not: Bu değerler G*Power'ın iç başlangıç durumudur. Sözleşme gereği CLI'de varsayılan değer **yoktur** (SPEC §A3).

## Hesaplama

| ID | Etiket | İddia | Adres | Gözlenen davranış | Güven |
|---|---|---|---|---|---|
| E-020 | [REA] | Grup ayarlayıcı: k'yı saklar ve pay df'yi k − 1 yapar | `FUN_004ba660` | Verilen değeri `+0xf0`'a; bir eksiğini `+0x88`'e ve F dağılımının birinci serbestlik derecesine yazıyor | Yüksek |
| E-021 | [REA] | df güncelleme: df1 = k − 1, df2 = N − k | `FUN_004b9e40` (slot `0x5c8658`, vtable+0x120) | `+0x88` ← k − 1 ve `+0x90` ← N − k hesaplanıp ikisi de dağılımın serbestlik derecelerine aktarılıyor | Yüksek |
| E-022 | [REA] | `FUN_00572840` bir sayının karesini döndürür | `FUN_00572840` | Tek double girdi, girdinin kendisiyle çarpımı döndürülüyor | Yüksek |
| E-023 | [REA] | Noncentrality: λ = f² · N | `FUN_004ba340` (slot `0x5c8588`, vtable+0x50) | Girdinin karesi (E-022) `+0xe8` alanındaki N ile çarpılıp döndürülüyor | Yüksek |
| E-024 | [REA] | Ters yön: N = λ / f² | `FUN_004ba5c0` (slot `0x5c858c`) | Girdi, `+0xd8` alanındaki f'nin karesine bölünüp döndürülüyor | Yüksek |
| E-025 | [REA] | Güç rutininin çağrı sırası | `FUN_004b8d50` (slot `0x5c8568`) | Sırasıyla: f, α ve N alanlara yazılıyor → df güncelleniyor (E-021) → dağılımın ncp'si 0 yapılıyor → 1 − α için dağılımın quantile metodu çağrılıp sonuç `+0x98`'e yazılıyor → ncp, E-023 ile hesaplanan λ'ya ayarlanıyor → 1 − (dağılımın `+0x98`'deki değerdeki CDF'si) döndürülüyor | Yüksek |
| E-026 | [INFERENCE] | Post-hoc güç = `1 − F_ncf(F_crit; k−1, N−k, λ = f²·N)`, `F_crit = F⁻¹(1−α; k−1, N−k)` | E-021…E-025 | Vtable slotlarının çağrı sırası; dağılım metotlarının anlamı kullanımdan çıkarıldı | Orta-Yüksek |
| E-027 | [REA] | Kritik F değeri `+0x98`'de saklanıyor; "Critical F" dizesi `0x5c5640`'ta | `FUN_004b8d50`, `search_strings`, `xrefs` | Quantile sonucu `+0x98`'e yazılıyor; dizeye tek referans `0x609420` (veri tablosu) | Yüksek (yazım) / Orta (GUI'ye bağlantı) |
| E-028 | [REA] | N'yi k'nın bir sonraki tam katına yukarı yuvarlayan metot | `FUN_004badb0` (slot `0x5c85ac`) | Girdi `+0xf0`'daki k'ya bölünüyor, yukarı yuvarlanıyor, tekrar k ile çarpılıyor | Yüksek |
| E-029 | [INFERENCE] | A priori modda toplam N, k'nın katına yuvarlanıyor (eşit grup boyutu) | E-028 | Hangi modda çağrıldığı izlenmedi | Orta |
| E-030 | [REA] | Bir arama aralığı `[k + 1, k + 100]` olarak kuruluyor | `FUN_004bae20` (slot `0x5c859c`) | `+0xf0`'daki k'ya 1 ve 100 eklenerek iki uç hesaplanıyor ve aralık ayarlayıcıya (`FUN_004962d0`) veriliyor | Yüksek |
| E-031 | [REA] | Başka bir aralık `[1e-6, 0.3]` olarak kuruluyor | `FUN_004bae00` (slot `0x5c85a0`) | Aynı aralık ayarlayıcıya sabit 1e-6 ve 0.3 uçları veriliyor | Yüksek |
| E-032 | [INFERENCE] | E-030 N araması için başlangıç aralığı; E-031 hassasiyet (f) araması için aralık | E-030, E-031 | Arama algoritması ve genişletme kuralı incelenmedi | Düşük |

## Arayüz dizeleri (yalnızca varlık)

| ID | Etiket | Dize | Adres | Güven |
|---|---|---|---|---|
| E-040 | [REA] | `Number of groups` | `0x5c558c` | Yüksek |
| E-041 | [REA] | `Effect size f` / `Effect size f$^2$` | `0x5c55dc` / `0x5c55c8` | Yüksek |
| E-042 | [REA] | `Numerator df` / `Denominator df` | `0x5c556c` / `0x5c557c` | Yüksek |
| E-043 | [REA] | `Total sample size` / `Actual power` / `Power (1-$\beta$ err prob)` | `0x5c54e0` / `0x5c5658` / `0x5c54c4` | Yüksek |
| E-044 | [REA] | `Noncentrality parameter $\lambda$` | `0x5c55fc` | Yüksek |
| E-045 | [REA] | Analiz türleri: Post hoc / Criterion / Sensitivity / Compromise metinleri | `0x5c5368`, `0x5c53b0`, `0x5c53f8`, `0x5c5448`, `0x5c5248` | Yüksek |
| E-046 | [REA] | `Effect size from means`, `Effect size from variance`, `Variance within groups`, `Partial $\eta$$^2$` | `0x5d361e`, `0x5d3650`, `0x5d0768`, `0x5d0960` | Yüksek |

Not: E-040…E-046 dizelerin varlığını gösterir; hangisinin bu testin penceresinde gösterildiği GUI ile doğrulanmalıdır.

## Kullanıcı tarafından sağlanan GUI gözlemleri

Kaynak türü: **kullanıcı tarafından sağlanan GUI gözlemleri** (G*Power 3.1.9.7, A priori). `[REA]` değildir.
Veri `oracle/anova-apriori.csv`, indeks `oracle/README.md`. İki alt tür ayrı tutulur:

- **Kullanıcı bildirimi:** CSV'deki değerler (kullanıcının yazdığı tablo; satır sırası ve test adı yazımı kullanıcıya ait).
- **Görüntüden doğrulandı `[GUI]`:** Bu oturumda `oracle/screenshots/vektor-NN.png` dosyalarında gözle okunan değerler.

| ID | Etiket | İddia | Kaynak | Kısa kanıt | Güven |
|---|---|---|---|---|---|
| G-001 | Kullanıcı bildirimi | 30 A priori vektörü: f, α, power, k → total_n | `oracle/anova-apriori.csv` AN-001…AN-030 | CSV SHA-256 `21ad6a25…cff4b74a` | Yüksek (bildirim) |
| G-002 | [GUI] | 30 görüntünün hepsinde test = "ANOVA: Fixed effects, omnibus, one-way", mod = A priori; girdiler ve Total sample size CSV ile aynı | `vektor-01.png`…`vektor-30.png` | `oracle/README.md` indeksi, sütun "Görüntü = CSV" | Yüksek |
| G-003 | [GUI] | Her görüntüde Numerator df = k − 1 ve Denominator df = total_n − k | 30 görüntü | ör. AN-004: k=8, N=128 → df 7 / 120 | Yüksek |
| G-004 | [GUI] | Her görüntüde λ = f² · total_n (ekranda 7 ondalıkla) | 30 görüntü | ör. AN-029: 0.35² · 147 = 18.0075 → ekranda 18.0075000 | Yüksek |
| G-005 | [GUI] | Her görüntüde total_n, k'nın tam katı | 30 görüntü | ör. AN-004: 128 = 16 · 8 | Yüksek |
| G-006 | [GUI] | Actual power her satırda hedef power'a eşit veya büyük | 30 görüntü | ör. AN-019: hedef 0.80, actual 0.8234006 | Yüksek |
| G-007 | [GUI] | Critical F, grafik başlığında 6 anlamlı basamakla, çıktı panelinde 7 ondalıkla gösteriliyor | 30 görüntü | ör. AN-001: "critical F = 2.40174" / 2.4017397 | Yüksek |
| G-008 | [INFERENCE] | G-003, G-004 ve G-005 sırasıyla E-021, E-023 ve E-028 ile tutarlıdır; çelişki yok | G-003…G-005, E-021/E-023/E-028 | — | Orta-Yüksek |
| G-009 | [UNKNOWN] | A priori aramasında N'nin "en küçük k katı" mı olduğu, yoksa başka bir kuralla mı seçildiği | — | Görüntüler yalnızca son N'yi gösteriyor; bir alt N'nin gücü gözlenmedi | — |

## Sözleşme açık vektörleri

Kaynak türü: **resmi sözleşme** (`CONTRACT.md` §9, sürüm 1.0.0). `[REA]` ve `[GUI]` değildir.

| ID | Etiket | İddia | Kaynak | Kısa kanıt | Güven |
|---|---|---|---|---|---|
| C-001 | [CONTRACT] | 25 açık vektör (5 aile × 5 mod) `oracle/public_vectors.jsonl`'a birebir aktarıldı | `CONTRACT.md` satır 343–367 | Dosya içeriği sözleşmedeki `jsonl` bloğuyla bayt bayt aynı; 25 satır, 25 benzersiz `id`; SHA-256 `4d6e696b…98a59e10` | Yüksek |
| C-002 | [CONTRACT] | `anova-oneway` için 5 vektörün girdi ve beklenen alan adları §4.3 tablosuyla aynı | `oracle/public_vectors.jsonl` | 5/5 modda alan kümeleri eşleşti | Yüksek |
| C-003 | [CONTRACT] + [GUI] | `anova-oneway/a-priori` açık vektörü, kullanıcının AN-001 vektörüyle tüm çıktı alanlarında aynı | C-001, `oracle/README.md` | ncp 19.0625000, critical_f 2.4017397, df 4/300, n_total 305, actual_power 0.9521313 | Yüksek |
| C-004 | [INFERENCE] | Diğer 4 anova vektörü E-021/E-023 ile tutarlı (df 4/95; λ = 0.25²·100 = 6.25; sensitivity'de λ = f²·100) | C-001, E-021, E-023 | Elle aritmetik kontrol; G*Power'da yeniden ölçülmedi | Orta-Yüksek |

## Ham kanıt

REA kanıt paketi repo dışında: `C:\Users\MEHMET~1\AppData\Local\Temp\claude\C--Users-MEHMETBEK-L-gpower-anova-teardown\a0a1942e-4888-4a9b-b83a-b35a7c64d5eb\scratchpad\rea-evidence-01-recon.json` (25 kayıt, 238 725 bayt). Repoya eklenmez.
