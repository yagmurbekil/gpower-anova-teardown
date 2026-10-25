# 01 — Recon: tersine mühendislik ve kanıt toplama

Mevcut çalışma dizininde yerel Git deposu var. Önce `git rev-parse --show-toplevel` ve `git status --short` komutlarıyla depo kökünü ve durumunu doğrula. GitHub remote'u varmış gibi varsayma.

Bu oturum **1. ajan oturumu: tersine mühendislik ve kanıt toplama** olacak. Uygulama kodu yazmayacaksın.

### A. Araştırma promptunu kaydet

Aşağıdaki talimatları `prompts/01-recon.md` dosyasına kaydet. `prompts/` klasörü yoksa oluştur. Var olan dosyaları ezme; `prompts/01-recon.md` zaten varsa önce içeriğini incele.

### B. Görev

Ödev sözleşmesindeki `anova-oneway` ailesini araştır. Bu, çalışma varsayımıdır; atanan aile farklıysa dur ve bildir.

Hedef ikili:
`C:\GPower\GPower_3.1.9.7_143\GPowerNT.exe`

Beklenen SHA-256:
`C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812`

İnceleme başlamadan önce mevcut dosyanın SHA-256 değerini doğrula. Eşleşmezse dur ve kullanıcıya bildir. İkiliyi değiştirme, taşımama veya depoya kopyalama.

### C. REA'yı doğrula ve incele

1. Kullanılabilir REA araçlarının gerçek şemalarını ve gerekli argümanlarını keşfet. Araç isimlerini veya parametrelerini tahmin etme.
2. `open_binary` ile yalnızca yukarıdaki ikiliyi aç. Ardından mümkünse `binary_overview`, `inspect_pe_resources` ve `search_strings` kullan.
3. İkili 32 bit PE32/i386 olduğundan analiz mimarisini buna göre doğrula.
4. ANOVA, one-way, fixed effects, omnibus, F-test, effect size, alpha, power, noncentral F ve örneklem büyüklüğü hesaplamalarıyla ilgili bulguları araştır.
5. İlgili fonksiyonlar bulunursa `procedure_pseudo_code` veya `batch_decompile` kullan. Önce araçların şemalarını kontrol et; gereksiz yere tüm programı decompile etme.
6. REA bağlantısı koparsa hatayı olduğu gibi kaydet. Başarısız işlemi başarılıymış gibi gösterme.

### D. Kanıt ve spesifikasyon

Şu dosyaları hazırla:

- `evidence/LEDGER.md`: Her bulgu için benzersiz kimlik, iddia, kaynak, adres/fonksiyon, kısa kanıt ve güven düzeyi.
- `evidence/experiments.md`: G*Power GUI üzerinden yapılması gereken deneyler, gerçek girdiler, gözlemlenen çıktılar ve henüz yapılmamış deneyler.
- `SPEC.md`: Yalnızca doğrulanmış bulgular ve ödev sözleşmesine dayanarak davranış spesifikasyonu.
- `prompts/01-recon.md`: Bu araştırma talimatlarının kaydedilmiş kopyası.

Her iddiayı şu etiketlerden biriyle işaretle:
- `[REA]`: REA aracından doğrudan elde edilen kanıt.
- `[GUI]`: G*Power arayüzünde gerçekten gözlemlenen sonuç.
- `[CONTRACT]`: Ödev sözleşmesinin belirttiği gereklilik.
- `[INFERENCE]`: Kanıtlarla desteklenen yorum; doğrudan gözlem değildir.
- `[UNKNOWN]`: Henüz doğrulanmamış davranış.

Yalnızca `[REA]` olarak etiketlenebilecek gerçek REA bulguları öyle işaretlensin. Sözleşme bilgisini veya tahmini REA kanıtı gibi sunma.

### E. Matematiksel davranış

Sözleşmede belirtilen `anova-oneway` girdilerini, çıktılarını, serbestlik derecelerini, kritik F değerini, noncentrality parameter değerini ve gücü incele. G*Power'ın davranışı hakkında bir iddia, GUI veya ikili kanıtıyla doğrulanmadıysa bunu açıkça belirt.

Açık referans vektörlerini sözleşmeden alabilirsin; bunları kendi ölçümün gibi sunma. Yeni oracle sonuçları uydurma. G*Power GUI'de henüz ölçülmemiş sonuçlar için deney prosedürü yaz.

### F. Güvenlik ve temiz oda kuralları

- `src/` altında uygulama kodu yazma.
- `pytest` testleri veya hesaplama motoru oluşturma.
- `GPowerNT.exe` dosyasını repoya ekleme.
- Tam decompile çıktısını, büyük pseudo-code dökümlerini veya ham Ghidra/REA çıktısını repoya kaydetme.
- `evidence/` içine yalnızca gerekli, kısa, adresi/kaynağı belli kanıt parçalarını yaz.
- Mevcut kullanıcı dosyalarını silme veya üzerine yazma.
- Henüz commit atma.

### G. Bitiş raporu

İş sonunda şunları bildir:
1. Çalıştırılan gerçek REA araçları ve sonuçları.
2. Doğrulanmış bulgular ve adresleri.
3. Hâlâ bilinmeyen davranışlar.
4. Oluşturulan dosyalar.
5. `git status --short` çıktısı.
6. Bir sonraki GUI deneyleri için net talimatlar.

Önce araştırma promptunu kaydet; ardından aynı talimatları bu oturumda uygula.
