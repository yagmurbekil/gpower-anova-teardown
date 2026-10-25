# gpower-clone — anova-oneway

`CONTRACT.md` 1.0.0 arayüzüyle *F tests – ANOVA: Fixed effects, omnibus, one-way* güç analizi.
Python 3.14 + scipy 1.18. Bu sürümde yalnızca `--test anova-oneway` uygulanır; sözleşmedeki diğer aileler
`UNSUPPORTED` döndürür.

## Kurulum (tek komut)

```
pip install -e ".[test]"
```

Sabitlenmiş sürümler `requirements.txt` içindedir (`pip install -r requirements.txt` ile de kurulabilir).

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

## Testler

```
pytest                 # hepsi
pytest -m "not bonus"  # yalnızca zorunlu modlar
```

Testler CLI'yi alt süreçte (`python -m gpower_clone`) çalıştırır; kurulu komutu denemek için
`GPOWER_CLONE_CMD=gpower-clone pytest`.

## Belgeler

- `CONTRACT.md` — arayüz (yetkili kaynak)
- `SPEC.md` — davranış, bilinmeyenler; §F geçici uygulama kararları
- `oracle/` — sözleşme ve GUI referans vektörleri
