# Ortam Raporu — YZM301 Teardown Sprint (anova-oneway)

Hedef aile: `anova-oneway` (G*Power: F tests – ANOVA: Fixed effects, omnibus, one-way)
Tarih: 2026-10-25 · OS: Windows 11 Home Single Language 10.0.26200

## Doğrulanan araçlar

| Araç | Sürüm | Doğrulama |
|---|---|---|
| Git | depo başlatılmış (`master`), commit yok | `git status` |
| JDK | 27.0.1 (`JAVA_HOME=C:\Program Files\Java\jdk-27.0.1.0.3`) | `java -version`, `javac -version` |
| Python | 3.14.4 (`C:\Python314\python`) | `python --version` |
| pip | 26.0.1 | `pip --version` |
| scipy / numpy | 1.18.0 / 2.5.1 | import |
| pytest | 9.1.1 | `pip install pytest` sonrası import |
| Ghidra | 12.1.4 (`C:\Ghidra\ghidra_12.1.4_PUBLIC`, `GHIDRA_INSTALL_DIR` ayarlı) | `analyzeHeadless.bat` kullanım metnini yazdı |
| REA MCP | bağlı (`/mcp` ile yeniden bağlandı) | araç listesi keşfedildi |

scipy sağlama kontrolü: f = 0.25, k = 4, N = 180, α = 0.05 için
`ncf.sf(f.isf(0.05, 3, 176), 3, 176, λ = f²·N)` → güç = **0.8040**
(G*Power'ın bu girdiler için bilinen ≈ 0.80 sonucu ile uyumlu).

## Hedef ikili

- Yol: `C:\GPower\GPower_3.1.9.7_143\GPowerNT.exe` (repo dışında, commit edilmez)
- Sürüm: 3.1.9.7 (PE VersionInfo: FileVersion 3.1.9.7, ProductName "GPower 3.1.9.7")
- Biçim: PE32, Intel i386, Windows GUI, 4 bölüm
- Boyut: 2 287 616 bayt
- SHA-256: `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812`
- Aynı klasörde `VC_redist.x86.exe` var → 32-bit MSVC çalışma zamanı olası; Ghidra dili `x86:LE:32`

## Doğrulanamayanlar

- Ghidra ile gerçek içe aktarma/analiz: test edilmedi (JDK 27 uyumu bu adımda görülecek).
- REA ile işlevsel analiz: araçlar listeleniyor, ancak henüz hiçbir ikili açılıp analiz edilmedi.
- Maven, Gradle: kurulu değil.

## Riskler

- Ghidra 12.1.4 en az JDK 21 istiyor, üst sınır belirtmiyor; JDK 27 ile uyum ilk analizde doğrulanmalı.
- Diskte birden fazla Ghidra kopyası var (`C:\Ghidra` altında 12.1.4, `Downloads` altında 12.2 ve zip'ler); 12.1.4 kullanılacak.
- Python 3.14 / scipy 1.18 çok yeni; sürümler `requirements.txt` ile sabitlenmeli.
- Git boş klasörleri izlemez; `evidence/`, `oracle/`, `prompts/`, `src/`, `tests/` için `.gitkeep` gerekir.
- Java'da Apache Commons Math / Hipparchus noncentral F içermiyor; Java seçilirse elle yazılması gerekir.

## Teknoloji kararı

**Python + scipy (`f`, `ncf`) + pytest.**

| Ölçüt | Python + scipy | Java (JDK 27) |
|---|---|---|
| Dağılım fonksiyonları | `f`, `ncf` hazır ve doğrulandı | noncentral F yok |
| Kurulum | tamamlandı | Maven/Gradle yok |
| Çevrimdışı çalışma | evet | evet (bağımlılıksız ise) |
| Test edilebilirlik | pytest, tablo tabanlı testler | JUnit için derleme aracı gerekir |
| Risk | düşük | orta–yüksek |

## Repo hijyeni

G*Power ikilisi ve kurulum dosyaları, Ghidra projeleri (`*.gpr`, `*.rep/`), ham decompile
çıktıları (`decompiled/`, `analysis_tmp/`), loglar ve Python geçici dosyaları `.gitignore` ile
dışlanır. Yalnızca seçilmiş, kaynak adresli kısa kanıt alıntıları `evidence/` altında tutulur.
