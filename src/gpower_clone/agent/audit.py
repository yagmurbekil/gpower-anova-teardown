"""Araç çağrısı denetim kaydı: `logs/agent_calls.jsonl` (CONTRACT §8), her MCP çağrısı bir satır.

Sözleşmedeki alanlar korunur. Ajan kural tabanlıdır ve dil modeli çağırmaz; `tokens_in`/`tokens_out`
yalnızca sözleşme biçimi için vardır ve her zaman 0'dır (ölçüm değildir).

Kayıt yazılmadan önce gizli görünen değerler maskelenir: yaygın API anahtarı biçimleri ve adı
KEY/TOKEN/SECRET/PASSWORD içeren ortam değişkenlerinin değerleri. Ortam değişkenleri kaydedilmez.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

DEFAULT_LOG_PATH = Path("logs") / "agent_calls.jsonl"
AGENT_KIND = "rule-based"
REDACTED = "[REDACTED]"
_KEY_RE = re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_\-]{8,}|\bgh[pousr]_[A-Za-z0-9]{20,}|\bAKIA[0-9A-Z]{16}\b")
_SECRET_ENV = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL", re.I)


def _secret_env_values():
    return sorted((v for k, v in os.environ.items() if _SECRET_ENV.search(k) and len(v) >= 8), key=len, reverse=True)


def redact(value, _secrets=None):
    """Yapı içindeki her metinden gizli bilgileri siler."""
    secrets = _secret_env_values() if _secrets is None else _secrets
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, REDACTED)
        return _KEY_RE.sub(REDACTED, value)
    if isinstance(value, dict):
        return {redact(k, secrets): redact(v, secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, secrets) for v in value]
    return value


class AuditLog:
    def __init__(self, path=DEFAULT_LOG_PATH):
        self.path = Path(path)

    def record(self, *, question, tool, tool_input, tool_output, is_error):
        entry = redact({
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "question": question,
            "tool": tool,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "is_error": is_error,
            "tokens_in": 0,
            "tokens_out": 0,
            "agent": AGENT_KIND,
        })
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry
