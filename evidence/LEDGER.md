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
| E-004 | [REA] | `FUN_004ba550`, `PowerFAnovaGlobal` sınıfının vtable'ında yer alıyor | `xrefs`, `read_bytes` | vtable `0x5c8538`, slot 30, giriş adresi `0x5c85b0` | RTTI tip adı `0x60cb78` → nesne konum kaydı `0x5eeeac` → vtable öncesi işaretçi `0x5c8534` | Yüksek |
| E-005 | [REA] | Aynı sınıfın test ailesi adı "F tests" | `procedure_pseudo_code` | `FUN_004b7a30` (slot 31, giriş adresi `0x5c85b4`) | Fonksiyon aile adı olarak "F tests" metnini döndürüyor | Yüksek |
| E-006 | [REA] | Etki büyüklüğü diyaloğu sınıfı `CEff_F_Anova_Omni` adıyla mevcut (kapsam dışı) | `search_strings` | `0x5d006c`, RTTI `0x60d678` | Sınıf adı metni ve RTTI kaydı mevcut | Yüksek |
| E-007 | [INFERENCE] | `PowerFAnovaGlobal`, GUI'deki "ANOVA: Fixed effects, omnibus, one-way" testinin hesap sınıfıdır | E-003, E-004 | `0x5c8538` | Test adını döndüren metot bu sınıfın vtable'ında | Orta |

## `FUN_004b9f20` içinde yazılan sabit değerler

`FUN_004b9f20` (slot 3, giriş adresi `0x5c8544`): sınıfın yeni bir örneğini oluşturup vtable'ı `PowerFAnovaGlobal` olarak ayarlıyor ve
alanlara sabit değerler yazıyor. Değerler ikilideki IEEE-754 double sabitlerinden okundu (veri, kod değil).
E-061'e göre bu yazımlardan sonra aynı fonksiyonda kaynak nesnenin alanları kopyalanıyor. Bu nedenle E-010…E-014 değerlerinin
sınıfın genel varsayılanları olduğu bu defterdeki kanıtla gösterilmedi; yalnızca bu fonksiyonda yazıldıkları gözlendi.

| ID | Etiket | İddia | Adres | Gözlenen davranış | Güven |
|---|---|---|---|---|---|
| E-010 | [REA] | `FUN_004b9f20` alan `+0xb0`'a 0.05 yazıyor | `FUN_004b9f20` | Sabit `0x3fa999999999999a` (= 0.05) bu alana yazılıyor | Yüksek |
| E-011 | [REA] | `FUN_004b9f20` alan `+0xb8`'e 0.95 yazıyor | `FUN_004b9f20` | Sabit `0x3fee666666666666` (= 0.95) bu alana yazılıyor | Yüksek |
| E-012 | [REA] | `FUN_004b9f20` alan `+0xd8`'e 0.25 yazıyor | `FUN_004b9f20` | Sabit `0x3fd0000000000000` (= 0.25) bu alana yazılıyor | Yüksek |
| E-013 | [REA] | `FUN_004b9f20` alan `+0xe8`'e 100.0 yazıyor | `FUN_004b9f20` | Sabit `0x4059000000000000` (= 100.0) bu alana yazılıyor | Yüksek |
| E-014 | [REA] | `FUN_004b9f20` içinde grup sayısı ayarlayıcısı 5.0 ile çağrılıyor | `FUN_004b9f20` → `FUN_004ba660` (çağrı `0x4ba003`, E-061) | Ayarlayıcıya sabit `0x4014000000000000` (= 5.0) geçiriliyor. Çağrı yalnızca bu fonksiyonda, alan kopyalama adımından önce gözlendi; ardından `+0xf0` kaynak nesneden kopyalanıyor (E-061). 5.0'ın sınıfın genel varsayılan grup sayısı olduğu gösterilmedi | Yüksek (çağrı) |
| E-015 | [REA] | Bir `FDistribution` nesnesi oluşturulup sınıfın `+0x58` alanına bağlanıyor | `FUN_004b9f20` | F dağılımı nesnesi kuruluyor; işaretçisi `+0x58`'e konuyor | Yüksek |
| E-016 | [INFERENCE] | Alan anlamları: `+0xb0`=α, `+0xb8`=power, `+0xd8`=f, `+0xe8`=N toplam, `+0xf0`=k | E-010…E-014, E-020…E-025 | Değerler ve kullanıldıkları formüller | Orta |

Not: Bu değerler `FUN_004b9f20` içinde yazılan iç değerlerdir; genel varsayılan oldukları doğrulanmadı (yukarıdaki not). Sözleşme gereği CLI'de varsayılan değer **yoktur** (SPEC §A3).

## Hesaplama

| ID | Etiket | İddia | Adres | Gözlenen davranış | Güven |
|---|---|---|---|---|---|
| E-020 | [REA] | Grup ayarlayıcı: k'yı saklar ve pay df'yi k − 1 yapar | `FUN_004ba660` | Verilen değeri `+0xf0`'a; bir eksiğini `+0x88`'e ve F dağılımının birinci serbestlik derecesine yazıyor | Yüksek |
| E-021 | [REA] | df güncelleme: df1 = k − 1, df2 = N − k | `FUN_004b9e40` (slot 72, giriş adresi `0x5c8658`, vtable+0x120) | `+0x88` ← k − 1 ve `+0x90` ← N − k hesaplanıp ikisi de dağılımın serbestlik derecelerine aktarılıyor | Yüksek |
| E-022 | [REA] | `FUN_00572840` bir sayının karesini döndürür | `FUN_00572840` | Tek double girdi, girdinin kendisiyle çarpımı döndürülüyor | Yüksek |
| E-023 | [REA] | Noncentrality: λ = f² · N | `FUN_004ba340` (slot 20, giriş adresi `0x5c8588`, vtable+0x50) | Girdinin karesi (E-022) `+0xe8` alanındaki N ile çarpılıp döndürülüyor | Yüksek |
| E-024 | [REA] | Ters yön: N = λ / f² | `FUN_004ba5c0` (slot 21, giriş adresi `0x5c858c`) | Girdi, `+0xd8` alanındaki f'nin karesine bölünüp döndürülüyor | Yüksek |
| E-025 | [REA] | Güç rutininin çağrı sırası | `FUN_004b8d50` (slot 12, giriş adresi `0x5c8568`) | Sırasıyla: f, α ve N alanlara yazılıyor → df güncelleniyor (E-021) → dağılımın ncp'si 0 yapılıyor → 1 − α için dağılımın quantile metodu çağrılıp sonuç `+0x98`'e yazılıyor → ncp, E-023 ile hesaplanan λ'ya ayarlanıyor → 1 − (dağılımın `+0x98`'deki değerdeki CDF'si) döndürülüyor | Yüksek |
| E-026 | [INFERENCE] | Post-hoc güç = `1 − F_ncf(F_crit; k−1, N−k, λ = f²·N)`, `F_crit = F⁻¹(1−α; k−1, N−k)` | E-021…E-025 | Vtable slotlarının çağrı sırası; dağılım metotlarının anlamı kullanımdan çıkarıldı | Orta-Yüksek |
| E-027 | [REA] | Kritik F değeri `+0x98`'de saklanıyor; "Critical F" dizesi `0x5c5640`'ta | `FUN_004b8d50`, `search_strings`, `xrefs` | Quantile sonucu `+0x98`'e yazılıyor; dizeye tek referans `0x609420` (veri tablosu) | Yüksek (yazım) / Orta (GUI'ye bağlantı) |
| E-028 | [REA] | N'yi k'nın bir sonraki tam katına yukarı yuvarlayan metot | `FUN_004badb0` (slot 29, giriş adresi `0x5c85ac`) | Girdi `+0xf0`'daki k'ya bölünüyor, yukarı yuvarlanıyor, tekrar k ile çarpılıyor | Yüksek |
| E-029 | [INFERENCE] | A priori modda toplam N, k'nın katına yuvarlanıyor (eşit grup boyutu) | E-028 | Hangi modda çağrıldığı izlenmedi | Orta |
| E-030 | [REA] | Bir arama aralığı `[k + 1, k + 100]` olarak kuruluyor | `FUN_004bae20` (slot 25, giriş adresi `0x5c859c`) | `+0xf0`'daki k'ya 1 ve 100 eklenerek iki uç hesaplanıyor ve aralık ayarlayıcıya (`FUN_004962d0`) veriliyor | Yüksek |
| E-031 | [REA] | Başka bir aralık `[1e-6, 0.3]` olarak kuruluyor | `FUN_004bae00` (slot 26, giriş adresi `0x5c85a0`) | Aynı aralık ayarlayıcıya sabit 1e-6 ve 0.3 uçları veriliyor | Yüksek |
| E-032 | [INFERENCE] | E-030 N araması için başlangıç aralığı; E-031 hassasiyet (f) araması için aralık | E-030, E-031 | Arama algoritması ve genişletme kuralı incelenmedi | Düşük |

## Yuvarlama çağrı zinciri (oturum 2026-10-26)

Aynı ikili (SHA-256 yeniden doğrulandı), REA → Ghidra 12.1.4. Bu bölüm E-028/E-029'daki "hangi yoldan çağrıldığı" sorusunu
ve E-032'deki arama algoritması sorusunu kısmen yanıtlar. Önceki kimlikler değiştirilmedi; E-004, E-005, E-014, E-021, E-023…E-025,
E-028, E-030, E-031, E-010…E-013, E-063 ve `FUN_004b9f20` bölümü notlarının yalnızca ifadesi netleştirildi (slot/giriş adresi biçimi,
yazılan sabitlerin kapsamı). Slot numarası ile giriş adresi ayrı tutulur: slot n'nin giriş adresi = vtable başlangıcı `0x5c8538` + 4n;
"+0x…" biçimi vtable içi ofsettir; "→" sonrası adres, girişin gösterdiği fonksiyondur.

**[REA] — ikilide doğrudan gözlenen**

| ID | Etiket | İddia | Adres | Gözlenen davranış | Güven |
|---|---|---|---|---|---|
| E-050 | [REA] | `FUN_004badb0`'a doğrudan CALL yok; tüm referanslar veri | `xrefs` → `0x5c85ac`, `0x5c8954`, `0x5c91d0`, `0x5c9314`, `0x5c9458`, `0x5c959c`, `0x5c96d8` | Yedi referansın hepsi vtable verisi; `0x5c85ac`, `PowerFAnovaGlobal` slot 29'un giriş adresidir; diğer altısı başka sınıfların vtable'larında | Yüksek |
| E-051 | [REA] | `PowerFAnovaGlobal` vtable'ı 77 slotluk (0–76); ilgili slotlar ham bayttan okundu | `0x5c8538` (`read_bytes` 200 + 160 bayt) | Biçim: slot (ofset, giriş adresi) → hedef fonksiyon. 1 (+0x4, `0x5c853c`) → `0x496830`; 3 (+0xc, `0x5c8544`) → `0x4b9f20`; 12 (+0x30, `0x5c8568`) → `0x4b8d50`; 18 (+0x48, `0x5c8580`) → `0x496aa0`; 25 (+0x64, `0x5c859c`) → `0x4bae20`; **29 (+0x74, `0x5c85ac`) → `0x4badb0`**; 71 (+0x11c, `0x5c8654`) → `0x4968d0`; 76 (+0x130, `0x5c8668`) → `0x4ba660`. Slot 76'dan sonra (`0x5c866c`) RTTI işaretçisi `0x5eef00` geliyor | Yüksek |
| E-052 | [REA] | Slot 29 hedefi, E-028'deki yuvarlama metodu: sonuç = ⌈x / k⌉ · k | `FUN_004badb0`, alan `+0xf0` | Bölen ve çarpan aynı alan, `+0xf0`; bu alan E-020'deki grup ayarlayıcısıyla (slot 76) yazılıyor | Yüksek |
| E-053 | [REA] | `FUN_00496aa0` (slot 18, giriş adresi `0x5c8580`) üç double argümanı alanlara yazıyor, kök bulucuyu çağırıyor | `0x496aa0`–`0x496b15` | Argümanlar `+0xd8`, `+0xb0`, `+0xb8`'e yazılıyor; `+0x2ac` ← 0; slot 25 (+0x64) çağrılıyor (E-030 aralığı); `0x496b03`'te `FUN_004f9bb0` şu girdilerle çağrılıyor: `+0x68`/`+0x70` aralığı, sabit `0x5c3f48` (`0x3ddb7cdfd9d7bdbb` ≈ 1e-10) ve 300 (`0x12c`). Sonuç `+0xe8`'e yazılıyor | Yüksek |
| E-054 | [REA] | Yuvarlama, slot 29 üzerinden **dolaylı** çağrılıyor ve bir bayt bayrağına bağlı | `0x496b1d`, `0x496b28`, `0x496b30` | Yığındaki bayt argümanı (`EBP+0x20`) sıfır değilse vtable'dan +0x74 okunuyor, `+0xe8`'deki değerle çağrılıyor ve sonuç `+0xe8`'e geri yazılıyor | Yüksek |
| E-055 | [REA] | Alt sınır kıskacı ve ikinci yuvarlama çağrısı | `0x496b3d`, `0x496b47`, `0x496b5a`, `0x496b62` | Aralığın alt ucu (`+0x68`) `+0xe8`'den büyükse `+0xe8` ← alt uç; bayrak sıfır değilse slot 29 ikinci kez çağrılıyor | Yüksek |
| E-056 | [REA] | Son adım: güç yeniden hesaplanıyor, N döndürülüyor | `0x496b87`, `0x496b9d`, `0x496ba5` | Slot 12 (+0x30, `FUN_004b8d50`) `+0xd8`, `+0xb0` ve `+0xe8` ile çağrılıyor; sonuç `+0x108`'e yazılıyor; `+0xe8` döndürülüyor. Çağrı kuralı `RET 0x1c` (3 double + 1 dword) | Yüksek |
| E-057 | [REA] | Kök bulucunun hedef fonksiyonu: güç − `+0xb8` | `FUN_00496830` (slot 1, giriş adresi `0x5c853c`), `FUN_004968d0` (slot 71, giriş adresi `0x5c8654`) | Slot 1, `+0x2ac`'deki seçiciye göre dallanıyor. E-053 bunu 0 yaptığı için slot 71'e gidiyor. Slot 71, slot 12'yi (`+0xd8`, `+0xb0`, x) ile çağırıp sonuçtan `+0xb8`'i çıkarıyor | Yüksek |
| E-058 | [REA] | Aralık ayarlayıcı, hedef fonksiyonun işaret değişimini arıyor | `FUN_004962d0` (E-030'dan çağrılıyor) | Üst uçta hedef ≥ 0 ise aralığı alt uca doğru daraltıyor; değilse üst ucu 1.6 ile çarparak işaret değişene kadar genişletiyor. Uçları `+0x68`/`+0x70`'e yazıyor; alt uç verilen alt sınırın (k + 1) altına inmiyor | Yüksek |
| E-059 | [REA] | `FUN_004f9bb0` sürekli (tam sayı olmayan) bir kök döndüren yinelemeli kök bulucu | `FUN_004f9bb0` | Sabit ≈ 1.11e-16 (2⁻⁵³) kullanılıyor; yineleme üst sınırı parametreden alınıyor. Uçlarda işaret değişimi yoksa durum 1 yazıp **0** döndürüyor; üst sınıra ulaşırsa durum 2 yazıp son tahmini döndürüyor. Çağıranların durum alanını okuyup okumadığı doğrulanmadı. Algoritma adı için bkz. E-064 ([INFERENCE]) | Yüksek |
| E-060 | [REA] | `FUN_00496aa0`'a tek doğrudan kod referansı küçük bir sarmalayıcıdan | `0x4eaeaa` ∈ `FUN_004eae80` (50 bayt) | Sarmalayıcı aynı 3 double'ı ve bayrağı yeniden yığına koyup çağırıyor. Diğer 40 referans vtable verisi. Sarmalayıcının hangi sınıfa ait olduğu belirlenmedi | Yüksek (referans) |
| E-061 | [REA] | `0x4ba003`'teki `FUN_004ba660` çağrısı slot 3'teki fonksiyonda, alan kopyalama adımından önce; argüman sabit 5.0 | `FUN_004b9f20` (slot 3, giriş adresi `0x5c8544`), `0x4ba003` | Önce `+0xf0` ← 2.0 (`0x5c19c0`), vptr ← `0x5c8538`, sonra `FUN_004ba660(5.0)` (`0x5c19d8`). Ardından `0x4ba04a`–`0x4ba322` arasında kaynak nesnenin alanları kopyalanıyor; `+0xf0` dahil (`0x4ba15f`–`0x4ba167`). E-014'teki 5.0 bu çağrıdır; çağrı yalnızca bu fonksiyonda gözlendi. Fonksiyonun "kopyalama/klonlama" olarak adlandırılması E-065'te [INFERENCE] | Yüksek |

**[INFERENCE] — yorum; doğrudan kanıtlanmadı**

| ID | Etiket | İddia | Dayanak | Açıklama | Güven |
|---|---|---|---|---|---|
| E-062 | [INFERENCE] | `FUN_00496aa0`, A priori N çözücüsüdür: güç(N) = hedef denklemini sürekli çözer, bayrak açıksa k'nın katına yukarı yuvarlar, en az k + 1'e kıstırır | E-053…E-059 | Hedef fonksiyonu ve E-030 aralığı N aramasına uyuyor. GUI yolunun bayrağı sıfırdan farklı gönderiyor olabileceği de bir çıkarımdır (dolaylı dayanak E-067). **GUI'deki A priori yolunun bu fonksiyona ulaştığı ve bayrağın değeri kanıtlanmadı** (E-068, E-069) | Orta |
| E-063 | [INFERENCE] | Alan anlamları: `+0xb8` hedef güç, `+0xd8` f, `+0xb0` α, `+0xe8` N | E-016, E-025, E-057 | `+0xb8`'in hedef fonksiyonundan çıkarılan değer olduğu [REA]; "hedef güç" adı yorum. `+0xd8`/`+0xb0` sırası E-025'teki güç rutini sırası (f, α, N) ve E-010/E-012'de `FUN_004b9f20` içinde yazılan sabitlerle tutarlı | Orta |
| E-064 | [INFERENCE] | `FUN_004f9bb0`, Brent türü bir kök bulma yöntemidir | E-059 | Yapı (ikiye bölme + interpolasyon adımları, epsilon tabanlı tolerans) Brent yöntemine benziyor. Algoritma adı ikilide yok | Orta |
| E-065 | [INFERENCE] | `FUN_004b9f20` bir kopyalama/klonlama metodudur; sonuçtaki k, kaynak nesnenin k'sıdır | E-061 | 5.0 sabiti kopyalama adımında üzerine yazılıyor; "clone" adı yorum | Orta |
| E-066 | [INFERENCE] | Şu koşulların hepsi sağlanırsa ⌈N*/k⌉·k, gücü hedefe ulaşan en küçük k katına eşittir (N* sürekli kök): güç N'ye göre monoton artıyor, kök bulucu başarılı (durum 1 veya 2 değil) ve bayrak açık. Sayısal tolerans sınır durumlarında sonucu değiştirebilir: N* bir k katına çok yakınsa iki kural ayrışabilir (`0x5c3f48` sabitinin ≈ 1e-10 tolerans olduğu da varsayım). Bu matematiksel bir yorumdur; G*Power GUI davranışının doğrudan kanıtı değildir | E-052, E-053, E-059 | Başarısız kök bulma ayrı bir durumdur: işaret değişimi yoksa kök bulucu durum 1 yazıp 0 döndürür (E-059, [REA]). Çağıranın bunu hata olarak ele alıp almadığı doğrulanmadı. Kod akışından koşullu olarak çıkan sonuç: kıskaç k + 1 yapar (E-055), bayrak açıksa yuvarlama 2k verir. Bunun geçerli bir GUI sonucu olduğu gösterilmedi | Orta |

**[GUI] — kullanıcı gözlemleri**

| ID | Etiket | İddia | Kaynak | Açıklama | Güven |
|---|---|---|---|---|---|
| E-067 | [GUI] | 30 A priori vektörünün hepsinde N, k'nın tam katı | G-005, AN-001…AN-030 | Gözlem yalnızca son N'nin k'nın katı olduğunu gösterir. E-054'teki bayrağın GUI yolunda açık olmasıyla tutarlıdır ama bayrağın değerini tek başına **kanıtlamaz**; bu bağ E-062'de [INFERENCE]. GUI yolunun `FUN_00496aa0`'a ulaşıp ulaşmadığı [UNKNOWN] (E-068, E-069) | Yüksek (gözlem) / Orta (bayrağa dolaylı destek) |

**[UNKNOWN] — açık kalanlar**

| ID | Etiket | Soru | Durum | Kapatmak için gereken | — |
|---|---|---|---|---|---|
| E-068 | [UNKNOWN] | GUI'deki A priori "Calculate" işleyicisi slot 18'i (+0x48) hangi adreste çağırıyor? | Belirlenmedi. Bayt aramasında 26 `call [reg+0x48]` ve 100'ü aşkın `mov reg,[reg+0x48]` eşleşmesi var; bir kısmı Ghidra'nın fonksiyon tanımlamadığı bölgelerde (ör. `0x498c52`, `0x4b9802`, `0x4ba80e`). Hiçbiri incelenmedi | Diyaloğun komut işleyicisinden (düğme kimliği → mesaj haritası → işleyici) +0x48 çağrısına kadar izlemek; ya da çalışma zamanında `0x496aa0` ve `0x4badb0`'a kesme noktası koyup çağrı yığınını, `ECX`'teki vptr'yi (`0x5c8538` beklenir) ve bayrak baytını kaydetmek | — |
| E-069 | [UNKNOWN] | E-054'teki yuvarlama bayrağı GUI A priori yolunda sıfırdan farklı mı? | Sıfır olmayan değer geçiren bir çağıran bulunmadı. Tek doğrudan çağıran (E-060) bayrağı yalnızca aktarıyor | E-068 ile aynı | — |

Not: G-009 ("en küçük k katı" mı?) bu bölümle yalnızca kısmen yanıtlandı. `FUN_00496aa0` içinde tam sayı araması gözlenmedi;
sürekli kök + bayrağa bağlı yukarı yuvarlama var (E-053…E-055, [REA]). Bu kuralın "en küçük k katı" ile aynı sonucu vermesi
E-066'daki koşullara bağlı; kök bulma başarısız olduğunda ortaya çıkan 2k'nın geçerli bir sonuç olduğu gösterilmedi.
Bu fonksiyonun GUI A priori yolu olduğu ve bayrağın değeri E-068/E-069 kapanana kadar açıktır.

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

Oturum 2026-10-26 (E-050…E-069): Ham çıktı paket olarak dışa aktarılmadı; REA oturumu kapatıldı. İzlenebilirlik için
REA kanıt kimliklerinin (`evidence_id`) ilk 12 onaltılık hanesi:
`xrefs 0x4badb0` ev_d681a0950381 · vtable baytları ev_96cd975a4408, ev_95c242a619ee · sabitler `0x5c19a0` ev_47fed5b13cc2,
`0x5c3f48` ev_510e12dfef7e · `0x4ba003` konumu ev_a66cf292bfc2 · `FUN_004b9f20` assembly ev_dbc30c3cb02e ·
`FUN_00496aa0` assembly ev_1bc65f9ed801 · `xrefs 0x496aa0` ev_584562c8b964 · `FUN_004f9bb0` ev_c62ab9868b72 ·
`FUN_004bae20` ev_a46d38d9f8c7 · `FUN_00496830` ev_c2ba20f60a56 · `FUN_004968d0` ev_17e3b5ba3998 ·
`FUN_004962d0` ev_be7edc8ff35f · `0x4eaeaa` konumu ev_7b82a852ad80 · `FUN_004eae80` assembly ev_decf80f21456 ·
bayt aramaları +0x74 ev_63754ec67bd7, ev_8f0f700e2e81; +0x48 ev_6469fa746926, ev_0cc2369bb1fc.
