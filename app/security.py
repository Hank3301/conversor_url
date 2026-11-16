"""Validação de URL, rate limit e cookies.

A validação é por allowlist de host: o yt-dlp nunca recebe uma URL de
servidor arbitrário, o que fecha a porta para SSRF.
"""

from __future__ import annotations

import base64
import os
import tempfile
import time
from collections import defaultdict, deque
from urllib.parse import urlparse

from .config import ALLOWED_HOSTS, settings

MAX_URL_LENGTH = 2048


class InvalidUrl(ValueError):
    pass


def normalize_url(raw: str) -> str:
    """Devolve a URL canônica ou levanta InvalidUrl com motivo legível."""
    candidate = (raw or "").strip()
    if not candidate:
        raise InvalidUrl("Cole um link primeiro.")
    if len(candidate) > MAX_URL_LENGTH:
        raise InvalidUrl("Link longo demais.")

    lowered = candidate.lower()
    if lowered.startswith(("http://", "https://")):
        scheme, rest = candidate.split("://", 1)
        candidate = f"{scheme.lower()}://{rest}"
    elif "://" in candidate:
        raise InvalidUrl("Use um link http ou https.")
    else:
        candidate = "https://" + candidate

    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https"):
        raise InvalidUrl("Use um link http ou https.")

    host = (parsed.hostname or "").lower().removeprefix("www.")
    if not host:
        raise InvalidUrl("Não consegui ler o domínio do link.")

    for allowed in ALLOWED_HOSTS:
        if host == allowed or host.endswith("." + allowed):
            clean = parsed._replace(fragment="")
            # remove só rastreadores: nunca toca em "v" (YouTube) ou "story_fbid".
            if clean.query:
                pairs = [
                    pair
                    for pair in clean.query.split("&")
                    if pair.split("=", 1)[0]
                    not in {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                            "utm_content", "igshid", "igsh", "fbclid", "si", "_r", "_t"}
                ]
                clean = clean._replace(query="&".join(pairs))
            return clean.geturl()

    raise InvalidUrl(f"Site não suportado: {host}")


class RateLimiter:
    """Janela deslizante em memória. Suficiente para uso entre amigos."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> int:
        """Retorna quantos segundos faltam para liberar. 0 = liberado."""
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return max(1, int(self.window - (now - bucket[0])) + 1)
        bucket.append(now)
        return 0


resolve_limiter = RateLimiter(settings.resolve_per_minute, 60)
download_limiter = RateLimiter(settings.downloads_per_10min, 600)


def write_cookies_file() -> str | None:
    """Materializa COOKIES_B64 em um arquivo temporário.

    Cookies são o que destrava YouTube (bloqueio de datacenter) e Instagram.
    """
    raw = settings.cookies_b64
    if not raw:
        return None
    try:
        content = base64.b64decode(raw).decode("utf-8", "replace")
    except Exception:
        content = raw
    if "youtube.com" not in content and "\t" not in content:
        return None
    path = os.path.join(tempfile.gettempdir(), "conversor-cookies.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    return path
