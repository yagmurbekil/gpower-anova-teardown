# Oracle — anova-oneway, A priori referans vektörleri

> Bu klasörde iki ayrı kaynak vardır ve birbirine karıştırılmaz:
> - `public_vectors.jsonl`: `CONTRACT.md` §9'daki 25 açık vektör, birebir kopya (`[CONTRACT]`, 5 aile × 5 mod).
> - `anova-apriori.csv` + `screenshots/`: kullanıcının 30 A priori GUI vektörü (`[GUI]`). Bu belgenin geri kalanı yalnızca bunları anlatır.

Kaynak: **Kullanıcı tarafından sağlanan GUI gözlemleri.** Kullanıcı bu 30 vektörü daha önce G*Power 3.1.9.7'de
"F tests – ANOVA: Fixed effects, omnibus, one-way", *A priori* modunda çalıştırmış ve ekran görüntülerini almıştır.
Değerler bu depoda yeniden hesaplanmadı.

- Veri: `anova-apriori.csv` (başlık + 30 veri satırı, SHA-256 `21ad6a25ff9ca2f0544585289f1edb7c302311fd882cd1825799f740cff4b74a`)
- Görüntüler: `screenshots/vektor-01.png` … `screenshots/vektor-30.png` (30 dosya, adlar değiştirilmedi)
- Kimlik kuralı: `AN-NNN` = CSV'nin NNN'inci **veri** satırı (başlık sayılmaz). Dosya satırı = NNN + 1.
- Eşleştirme kuralı: `vektor-NN.png` → `AN-0NN`. 30 dosyanın tamamı mevcut, adlar ardışık ve boşluksuz olduğu için kural uygulandı.

## Görüntü kontrolü (2026-10-25)

30 görüntünün hepsi açılıp okundu. Her görüntüde:
- Test family = `F tests`, Statistical test = `ANOVA: Fixed effects, omnibus, one-way`,
  Type of power analysis = `A priori: Compute required sample size – given α, power, and effect size`.
- Girdiler (f, α, power, Number of groups) ve "Total sample size" CSV satırıyla **birebir aynı**. Uyuşmazlık yok.

Adlandırma notu: GUI'deki test adı virgüllüdür (`ANOVA: Fixed effects, omnibus, one-way`); CSV'deki `statistical_test`
sütunu kullanıcının talimatıyla virgülsüz tutuldu (`ANOVA: Fixed effects omnibus one-way`). Değer farkı değil, yazım farkıdır.

## İndeks

"Görüntüden ek çıktılar" sütunu CSV'de bulunmayan, görüntüde okunan değerlerdir:
λ / Critical F / df1 / df2 / Actual power. Elle okunmuştur; basamaklar ekranda gösterildiği gibidir.

| ID | CSV satırı | f | α | power | k | total_n | Görüntü | Görüntü = CSV | Görüntüden ek çıktılar (λ / F_crit / df1 / df2 / actual power) |
|---|---|---|---|---|---|---|---|---|---|
| AN-001 | 2 | 0.25 | 0.05 | 0.95 | 5 | 305 | `screenshots/vektor-01.png` | ✓ | 19.0625000 / 2.4017397 / 4 / 300 / 0.9521313 |
| AN-002 | 3 | 0.10 | 0.01 | 0.80 | 2 | 1172 | `screenshots/vektor-02.png` | ✓ | 11.7200000 / 6.6565958 / 1 / 1170 / 0.8003199 |
| AN-003 | 4 | 0.40 | 0.10 | 0.95 | 3 | 84 | `screenshots/vektor-03.png` | ✓ | 13.4400000 / 2.3692989 / 2 / 81 / 0.9505096 |
| AN-004 | 5 | 0.40 | 0.10 | 0.95 | 8 | 128 | `screenshots/vektor-04.png` | ✓ | 20.4800000 / 1.7674758 / 7 / 120 / 0.9574575 |
| AN-005 | 6 | 0.25 | 0.05 | 0.80 | 3 | 159 | `screenshots/vektor-05.png` | ✓ | 9.9375000 / 3.0540042 / 2 / 156 / 0.8048873 |
| AN-006 | 7 | 0.25 | 0.05 | 0.80 | 4 | 180 | `screenshots/vektor-06.png` | ✓ | 11.2500000 / 2.6559389 / 3 / 176 / 0.8039869 |
| AN-007 | 8 | 0.25 | 0.05 | 0.80 | 5 | 200 | `screenshots/vektor-07.png` | ✓ | 12.5000000 / 2.4179625 / 4 / 195 / 0.8097710 |
| AN-008 | 9 | 0.25 | 0.05 | 0.90 | 3 | 207 | `screenshots/vektor-08.png` | ✓ | 12.9375000 / 3.0401584 / 2 / 204 / 0.9022417 |
| AN-009 | 10 | 0.25 | 0.05 | 0.90 | 4 | 232 | `screenshots/vektor-09.png` | ✓ | 14.5000000 / 2.6441945 / 3 / 228 / 0.9018055 |
| AN-010 | 11 | 0.25 | 0.01 | 0.80 | 3 | 228 | `screenshots/vektor-10.png` | ✓ | 14.2500000 / 4.7007255 / 2 / 225 / 0.8029054 |
| AN-011 | 12 | 0.25 | 0.01 | 0.90 | 4 | 316 | `screenshots/vektor-11.png` | ✓ | 19.7500000 / 3.8449692 / 3 / 312 / 0.9027905 |
| AN-012 | 13 | 0.25 | 0.01 | 0.95 | 5 | 400 | `screenshots/vektor-12.png` | ✓ | 25.0000000 / 3.3669554 / 4 / 395 / 0.9524917 |
| AN-013 | 14 | 0.10 | 0.05 | 0.80 | 2 | 788 | `screenshots/vektor-13.png` | ✓ | 7.8800000 / 3.8533168 / 1 / 786 / 0.8005931 |
| AN-014 | 15 | 0.10 | 0.05 | 0.80 | 3 | 969 | `screenshots/vektor-14.png` | ✓ | 9.6900000 / 3.0050418 / 2 / 966 / 0.8011010 |
| AN-015 | 16 | 0.10 | 0.05 | 0.90 | 4 | 1424 | `screenshots/vektor-15.png` | ✓ | 14.2400000 / 2.6111690 / 3 / 1420 / 0.9006522 |
| AN-016 | 17 | 0.10 | 0.05 | 0.95 | 5 | 1865 | `screenshots/vektor-16.png` | ✓ | 18.6500000 / 2.3767119 / 4 / 1860 / 0.9503488 |
| AN-017 | 18 | 0.40 | 0.05 | 0.80 | 2 | 52 | `screenshots/vektor-17.png` | ✓ | 8.3200000 / 4.0343097 / 1 / 50 / 0.8074866 |
| AN-018 | 19 | 0.40 | 0.05 | 0.80 | 3 | 66 | `screenshots/vektor-18.png` | ✓ | 10.5600000 / 3.1428085 / 2 / 63 / 0.8180744 |
| AN-019 | 20 | 0.40 | 0.05 | 0.80 | 4 | 76 | `screenshots/vektor-19.png` | ✓ | 12.1600000 / 2.7318070 / 3 / 72 / 0.8234006 |
| AN-020 | 21 | 0.40 | 0.05 | 0.90 | 3 | 84 | `screenshots/vektor-20.png` | ✓ | 13.4400000 / 3.1093105 / 2 / 81 / 0.9068362 |
| AN-021 | 22 | 0.40 | 0.05 | 0.95 | 4 | 112 | `screenshots/vektor-21.png` | ✓ | 17.9200000 / 2.6886915 / 3 / 108 / 0.9513019 |
| AN-022 | 23 | 0.15 | 0.05 | 0.80 | 3 | 432 | `screenshots/vektor-22.png` | ✓ | 9.7200000 / 3.0167494 / 2 / 429 / 0.8007663 |
| AN-023 | 24 | 0.15 | 0.05 | 0.85 | 4 | 552 | `screenshots/vektor-23.png` | ✓ | 12.4200000 / 2.6211675 / 3 / 548 / 0.8509641 |
| AN-024 | 25 | 0.20 | 0.05 | 0.80 | 3 | 246 | `screenshots/vektor-24.png` | ✓ | 9.8400000 / 3.0329694 / 2 / 243 / 0.8036584 |
| AN-025 | 26 | 0.20 | 0.05 | 0.90 | 4 | 360 | `screenshots/vektor-25.png` | ✓ | 14.4000000 / 2.6299872 / 3 / 356 / 0.9015736 |
| AN-026 | 27 | 0.30 | 0.05 | 0.80 | 3 | 111 | `screenshots/vektor-26.png` | ✓ | 9.9900000 / 3.0803869 / 2 / 108 / 0.8034951 |
| AN-027 | 28 | 0.30 | 0.05 | 0.90 | 5 | 180 | `screenshots/vektor-27.png` | ✓ | 16.2000000 / 2.4232862 / 4 / 175 / 0.9073603 |
| AN-028 | 29 | 0.35 | 0.05 | 0.80 | 2 | 68 | `screenshots/vektor-28.png` | ✓ | 8.3300000 / 3.9862695 / 1 / 66 / 0.8116461 |
| AN-029 | 30 | 0.35 | 0.01 | 0.90 | 3 | 147 | `screenshots/vektor-29.png` | ✓ | 18.0075000 / 4.7556359 / 2 / 144 / 0.9002016 |
| AN-030 | 31 | 0.50 | 0.05 | 0.95 | 4 | 76 | `screenshots/vektor-30.png` | ✓ | 19.0000000 / 2.7318070 / 3 / 72 / 0.9589579 |

## Doğrulama sonuçları (2026-10-25)

Betik repo dışında çalıştırıldı (scratchpad `validate_oracle.py`):

1. Başlık hariç veri satırı: **30**.
2. `f`, `alpha`, `power`, `k`, `total_n` sayısal olarak okunabiliyor; hata yok.
3. `k` ve `total_n` tam sayı; `total_n % k ≠ 0` olan satır **yok**.
4. Birebir yinelenen satır **yok**. (AN-003 ve AN-020 aynı k=3, total_n=84 değerlerini paylaşır ama α farklıdır.)
5. Satır sırası verilen referans tablosuyla **aynı**.
6. 30 görüntünün hepsi mevcut ve CSV girdileri + `total_n` ile uyuşuyor.
