"""Deterministik yanıt metinleri (Türkçe). Sonuç sayıları yalnızca MCP aracının çıktısından gelir;
okunabilirlik için verilen yuvarlanmış değer "≈" ile işaretlenir ve tam değer yanında durur."""

import json

from gpower_clone.agent.rules import LABELS, MODE_LABELS


def _label(name):
    return LABELS.get(name, name)


def _fmt(value):
    if isinstance(value, float):
        return f"{value!r} (≈ {value:.4f})"
    return json.dumps(value, ensure_ascii=False)


def _inputs(fields):
    """fields: {alan: Mention}"""
    return "\n".join(f"  - {name} = {json.dumps(m.value, ensure_ascii=False)}  ← “{m.quote}”"
                     for name, m in fields.items())


def _notes(notes):
    return "".join(f"\nNot: {n}" for n in notes)


def mode_line(mode, source):
    return f"Mod: {mode} ({MODE_LABELS.get(mode, '')}) — {source}"


def result(mode, mode_source, fields, output, notes):
    lines = [
        mode_line(mode, mode_source),
        "Kullanılan girdiler:",
        _inputs(fields),
        "Sonuç (calculate_anova_oneway çıktısı, değiştirilmeden):",
        *(f"  - {k} = {_fmt(v)}" for k, v in output.items()),
    ]
    summary = _summary(mode, fields, output)
    if summary:
        lines.append(summary)
    return "\n".join(lines) + _notes(notes)


def _summary(mode, fields, out):
    if mode == "a-priori":
        return (f"Özet: hedef güce ulaşmak için toplam N = {out['n_total']} gerekir; "
                f"bu N ile ulaşılan güç {out['actual_power']:.4f} (≈).")
    if mode == "post-hoc":
        return f"Özet: verilen N ile ulaşılan güç {out['power']:.4f} (≈)."
    if mode == "compromise":
        return f"Özet: alpha {out['alpha']:.4f} (≈), güç {out['power']:.4f} (≈)."
    if mode == "criterion":
        return f"Özet: hedef güç için gereken alpha {out['alpha']:.4f} (≈)."
    if mode == "sensitivity":
        return f"Özet: saptanabilir en küçük etki büyüklüğü f {out['f']:.4f} (≈)."
    return None


def missing(mode, mode_source, missing_fields, fields, verbal_effect, notes):
    names = ", ".join(_label(f) for f in missing_fields)
    lines = [mode_line(mode, mode_source)]
    if fields:
        lines += ["Şimdiye kadar alınan değerler:", _inputs(fields)]
    if verbal_effect and "f" in missing_fields:
        lines.append(f"“{verbal_effect}” sözel bir etikettir; varsayılan bir f değerine çevirmiyorum.")
    lines.append(f"Hesaplama için eksik: {names}. Bu değer(ler)i belirtir misiniz?")
    return "\n".join(lines) + _notes(notes)


def ask_mode(modes_required, fields, candidates, notes):
    options = "\n".join(f"  - {m} ({MODE_LABELS.get(m, '')}): {', '.join(req)}"
                        for m, req in modes_required.items())
    lines = []
    if fields:
        lines += ["Alınan değerler:", _inputs(fields)]
    if candidates:
        lines.append("Verilen alanlarla uyumlu modlar: " + ", ".join(candidates) + ".")
    lines += ["Hangi analiz modunu kullanmak istiyorsunuz? Seçenekler ve gerekli parametreler:", options,
              "Gerekli mod ve parametreleri belirtir misiniz?"]
    return "\n".join(lines) + _notes(notes)


def clarify(conflicts, ambiguous, orphans, mode_conflict, notes):
    lines = ["Hesaplamadan önce şunların netleşmesi gerekiyor:"]
    for name, values in conflicts.items():
        shown = ", ".join(json.dumps(v, ensure_ascii=False) for v in values)
        lines.append(f"  - {_label(name)} için birden fazla değer verildi: {shown}. Hangisi geçerli?")
    if mode_conflict:
        lines.append(f"  - Birden fazla mod istendi: {', '.join(mode_conflict)}. Hangisini kullanalım?")
    for raw in ambiguous:
        lines.append(f"  - “{raw}” birden fazla parametreye bağlanabiliyor. Hangi parametrenin değeri?")
    for raw in orphans:
        lines.append(f"  - “{raw}” sayısının hangi parametreye ait olduğunu anlayamadım. Hangi parametre?")
    return "\n".join(lines) + _notes(notes)


def error(err, mode, missing_fields, notes):
    lines = [f"Araç hatası [{err.get('code')}] (alan: {err.get('field')}): {err.get('error')}"]
    if mode:
        lines.insert(0, f"Mod: {mode}")
    if err.get("field") and err.get("code") in ("INVALID_VALUE", "OUT_OF_RANGE", "INCONSISTENT"):
        lines.append(f"{_label(err['field'])} için geçerli bir değer belirtir misiniz?")
    elif err.get("code") == "UNKNOWN_PARAM":
        lines.append(f"“{err.get('field')}” bu analizde kullanılmadığı için çıkarıldı. "
                     "Devam etmek için kalan bilgileri onaylar ya da değiştirir misiniz?")
    elif err.get("code") == "NO_SOLUTION":
        lines.append("Girdilerden birini değiştirmek ister misiniz?")
    if missing_fields:
        lines.append("Ayrıca eksik: " + ", ".join(_label(f) for f in missing_fields) + ".")
    return "\n".join(lines) + _notes(notes)


def unsupported(quote, err, supported):
    lines = [f"“{quote}” bu uygulamada desteklenmiyor."]
    if err:
        lines.append(f"Araç yanıtı [{err.get('code')}] (alan: {err.get('field')}): {err.get('error')}")
    lines.append(_supported_text(supported))
    lines.append("Tek yönlü ANOVA ile devam etmek ister misiniz?")
    return "\n".join(lines)


def help_text(supported):
    return _supported_text(supported) + "\nÖrnek: “3 grup, f 0,25, alfa 0,05, güç 0,80 için a priori analiz”."


def _supported_text(supported):
    [family] = supported["supported"]
    modes = "\n".join(f"  - {m['mode']} ({MODE_LABELS.get(m['mode'], '')}): {', '.join(m['required_inputs'])}"
                      for m in family["modes"])
    return f"Desteklenen analiz: {family['test']} ({family['title']}). Modlar ve gerekli parametreler:\n{modes}"


def reset():
    return "Önceki değerler silindi. Yeni analizi yazabilirsiniz."
