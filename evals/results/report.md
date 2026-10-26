# Kural tabanlı ajan değerlendirmesi

Ajan dil modeli kullanmaz; token veya API maliyeti yoktur ve raporlanmaz.

- Zaman: 2026-10-26T15:22:41+03:00
- Senaryo: 24 — başarılı 24, başarısız 0
  - temel: 10/10 başarılı
  - ek: 14/14 başarılı
- Determinizm (iki çalıştırmada aynı yanıtlar ve araç çağrıları): evet
- MCP çağrıları: 60 (taşıma hatası 0)

| Ölçüt | Sonuç |
|---|---|
| Parametre çıkarımı | 15/15 |
| Analiz modu tespiti | 15/15 |
| Doğru MCP aracı seçimi | 12/12 |
| Hesap çağrısının başarısı | 12/12 |
| Beklenen çıktıyla eşleşme (CONTRACT §6 toleransı) | 12/12 |
| MCP çıktısı = CLI stdout | 12/12 |
| Eksik alanların doğru tespiti | 3/3 |
| Kullanıcıya doğru soru sorulması | 7/7 |
| Çelişkili/geçersiz/desteklenmeyen girdinin tespiti | 8/8 |
| Eksik/hatalı girdide hesap yapılmaması | 12/12 |

| id | tür | sonuç | başarısız kontroller | araç çağrıları |
|---|---|---|---|---|
| Q01 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| Q02 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| Q03 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| Q04 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| Q05 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| Q06 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| Q07 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| Q08 | ask | ✓ | — | get_supported_analyses, validate_anova_input! |
| Q09 | ask | ✓ | — | get_supported_analyses, validate_anova_input! |
| Q10 | ask | ✓ | — | get_supported_analyses, validate_anova_input! |
| E01 | clarify | ✓ | — | get_supported_analyses |
| E02 | error | ✓ | — | get_supported_analyses, validate_anova_input! |
| E03 | error | ✓ | — | get_supported_analyses, validate_anova_input! |
| E04 | unsupported | ✓ | — | get_supported_analyses, validate_anova_input! |
| E05 | error | ✓ | — | get_supported_analyses, validate_anova_input! |
| E06 | ask_mode | ✓ | — | get_supported_analyses |
| E07 | calculate | ✓ | — | get_supported_analyses, validate_anova_input!, validate_anova_input!, validate_anova_input, calculate_anova_oneway |
| E08 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| E09 | error | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway! |
| E10 | clarify | ✓ | — | get_supported_analyses |
| E11 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| E12 | calculate | ✓ | — | get_supported_analyses, validate_anova_input, calculate_anova_oneway |
| E13 | calculate | ✓ | — | get_supported_analyses, validate_anova_input!, validate_anova_input, calculate_anova_oneway |
| E14 | clarify | ✓ | — | get_supported_analyses |

## Başarısız senaryolar

Yok.

## Komutlar

- `gpower-clone-eval  (eşdeğeri: python -m gpower_clone.agent.evaluate)`
- `Bu raporu üreten değerlendirme dışındaki testler (ayrıca çalıştırılır): pytest tests/test_agent.py tests/test_agent_parser.py tests/test_mcp_server.py`

`!` hata dönen araç çağrısıdır (hata beklenen senaryolarda doğru davranıştır). Ayrıntılı yanıtlar ve araç girdi/çıktıları `report.json` ile `agent_calls.jsonl` içindedir.
