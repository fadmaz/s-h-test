import json
from typing import Optional

def log(message: str) -> None:
    print(message, flush=True)


def json_log(value: object) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        return repr(value)


def log_kv(tag: str, **kwargs) -> None:
    parts = []
    for key, value in kwargs.items():
        parts.append(f"{key}={json_log(value)}")
    log(f"{tag} " + " ".join(parts))


def printable_text_preview(data: Optional[bytes], limit: int = 240) -> str:
    if not data:
        return ""
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    text = text.replace("\r", " ").replace("\n", " ").replace("\x00", " ").strip()
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def hex_preview(data: Optional[bytes], limit: int = 240) -> str:
    if not data:
        return ""
    view = data[:limit]
    out = view.hex()
    if len(data) > limit:
        out += "…"
    return out


def log_payload_preview(tag: str, payload: Optional[bytes], **kwargs) -> None:
    log_kv(
        tag,
        payload_len=len(payload or b""),
        payload_text=printable_text_preview(payload),
        payload_hex=hex_preview(payload),
        **kwargs,
    )



