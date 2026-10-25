# G*Power GUI Deneyleri — anova-oneway

## Kullanıcı tarafından sağlanan A priori vektörleri (2026-10-25 eklendi)

- Kaynak: **Kullanıcı tarafından sağlanan GUI gözlemleri.** Kullanıcı 30 A priori vektörünü daha önce
  G*Power 3.1.9.7 GUI'sinde çalıştırmış ve her biri için ekran görüntüsü almıştır. Çalıştırma tarihi ve
  kişisi kayıtlı değil; görüntü dosyalarının zaman damgası 2026-10-25 19:47–20:01.
- Veri: `oracle/anova-apriori.csv` (AN-001…AN-030), indeks: `oracle/README.md`.
- Görüntü kontrolü: 30/30 görüntü açılıp okundu. Test, mod, f, α, power, k ve Total sample size
  her satırda CSV ile aynı. Görüntülerde ayrıca λ, Critical F, df1, df2 ve Actual power okunup indekse yazıldı.
- Bu vektörler yalnızca **A priori** modunu kapsar. Aşağıdaki X-03 ve X-04 deneylerinin amacına kısmen
  karşılık gelirler (N'nin k'nın katı olması: 30/30 satırda geçerli). Post hoc, Sensitivity, Criterion,
  Compromise, varsayılanlar ve hata davranışı deneyleri (X-01, X-02, X-05…X-08) hâlâ yapılmadı.
  X-09 sözleşme gereği kapsam dışıdır.

## Planlanan deneyler

Durum: **Aşağıdaki deneylerin hiçbiri bu oturumda GUI'de yapılmadı.** Aşağıdaki "Gözlenen" sütunları boştur ve yalnızca
G*Power 3.1.9.7 (`C:\GPower\GPower_3.1.9.7_143\GPowerNT.exe`, SHA-256 `c63e6a13…efc812`) üzerinde
gerçekten okunan değerlerle doldurulmalıdır. Uydurma veya hesaplanmış değer yazılmaz.

## Genel prosedür

1. G*Power'ı aç. `Test family` = **F tests**.
2. `Statistical test` = **ANOVA: Fixed effects, omnibus, one-way**.
3. `Type of power analysis` seç (her deneyde belirtilir).
4. Girdileri tam olarak yaz, **Calculate**'e bas.
5. Çıktı panelindeki tüm alanları gösterilen tüm basamaklarla kopyala
   (Noncentrality parameter λ, Critical F, Numerator df, Denominator df, Total sample size, Actual power / Power).
6. Mümkünse `Protocol of power analyses` sekmesindeki metni de kaydet.
7. Sonucu bu dosyaya `[GUI]` etiketiyle, tarih ve deneyi yapan kişiyle yaz.

## Deneyler

### X-01 — Varsayılan değerler [UNKNOWN]
Amaç: Pencere ilk açıldığında gösterilen varsayılanları kaydetmek (E-010…E-014 ile karşılaştırma).
Girdi: Hiçbir şeye dokunmadan test ve "A priori" seçili halde alanları oku.
Gözlenen: _(boş)_

### X-02 — Post hoc güç, temel nokta [UNKNOWN]
Tür: Post hoc. Girdi: f = 0.25, α = 0.05, N = 180, k = 4.
Kaydedilecek: λ, Critical F, df1, df2, Power.
Kontrol: df1 = 3, df2 = 176 ve λ = 11.25 bekleniyor mu? (E-021, E-023'ten [INFERENCE]; GUI ile doğrulanacak.)
Gözlenen: _(boş)_

### X-03 — A priori N, varsayılanlarla [UNKNOWN]
Tür: A priori. Girdi: f = 0.25, α = 0.05, power = 0.95, k = 5.
Kaydedilecek: Total sample size, Actual power, λ, Critical F, df.
Kontrol: Total sample size k'nın katı mı? (E-028/E-029)
Gözlenen: _(boş)_

### X-04 — A priori N, k'nın katına yuvarlama sınaması [UNKNOWN]
Tür: A priori. Girdi: f = 0.40, α = 0.05, power = 0.80, k = 3; ardından k = 7.
Amaç: N'nin her durumda k'nın katı olup olmadığını görmek.
Gözlenen: _(boş)_

### X-05 — Sensitivity [UNKNOWN]
Tür: Sensitivity. Girdi: α = 0.05, power = 0.80, N = 120, k = 4.
Kaydedilecek: Effect size f, λ, Critical F, df.
Gözlenen: _(boş)_

### X-06 — Criterion [UNKNOWN]
Tür: Criterion. Girdi: f = 0.25, power = 0.80, N = 120, k = 4.
Kaydedilecek: α, Critical F, λ.
Gözlenen: _(boş)_

### X-07 — Compromise [UNKNOWN]
Tür: Compromise. Girdi: f = 0.25, β/α ratio = 1, N = 120, k = 4.
Kaydedilecek: α, β (power), Critical F.
Gözlenen: _(boş)_

### X-08 — Sınır ve hata davranışı [UNKNOWN]
Girdiler (her biri ayrı): k = 1; N ≤ k (ör. N = 4, k = 4); f = 0; α = 0 veya 1; power ≤ α.
Kaydedilecek: Hata mesajının tam metni veya üretilen çıktı.
Gözlenen: _(boş)_
Not (2026-10-25): Sözleşme §5 aralık dışı değerleri (k = 1, f = 0, α = 0/1) zaten `OUT_OF_RANGE` sayıyor.
Asıl önemli olan aralık **içindeki** durumlar: N ≤ k, power ≤ α, N k'nın katı değil, çok küçük f (SPEC §C).

### X-09 — Etki büyüklüğü diyaloğu (Determine =>) [KAPSAM DIŞI — isteğe bağlı]
Durum (2026-10-25): `CONTRACT.md` §1 "Determine" penceresini kapsam dışı sayıyor. Bu deney zorunlu kapsamdan
çıkarıldı; kayıt bilgi amaçlı korunuyor ve yapılması gerekmiyor.
"Effect size from means" ve "Effect size from variance" modlarında küçük bir örnek gir
(ör. k = 3, ortalamalar 1, 2, 3, n eşit, SD within = 2) ve hesaplanan f değerini kaydet.
Gözlenen: _(boş)_

## Referans vektörleri

Güncelleme (2026-10-25): `CONTRACT.md` (sürüm 1.0.0) proje köküne eklendi. §9'daki 25 açık vektör
`oracle/public_vectors.jsonl` dosyasına birebir aktarıldı (`[CONTRACT]`, LEDGER C-001…C-004). Bunlardan 5'i `anova-oneway`'e ait
(her moddan bir tane). Kullanıcının 30 GUI vektörü `oracle/anova-apriori.csv`'de ayrı tutuluyor ve `[CONTRACT]` olarak etiketlenmiyor.

Sözleşmenin açık vektörleri yalnızca N = 100, k = 5 (bonus/post-hoc) ve tek bir a-priori noktası içeriyor.
X-02, X-05, X-06 ve X-07 deneyleri farklı parametrelerle bu noktaları tamamlamak için hâlâ anlamlıdır.
