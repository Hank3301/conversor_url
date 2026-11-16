"""Configuração central, lida de variáveis de ambiente.

Todos os limites existem para caber em um host gratuito (512 MB de RAM,
CPU compartilhada, disco efêmero) sem derrubar o serviço.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = "Conversor de Links"
    max_duration_seconds: int = field(
        default_factory=lambda: _int("MAX_DURATION_MINUTES", 45) * 60
    )
    max_filesize_bytes: int = field(
        default_factory=lambda: _int("MAX_FILESIZE_MB", 2048) * 1024 * 1024
    )
    max_concurrent_jobs: int = field(
        default_factory=lambda: _int("MAX_CONCURRENT_JOBS", 2)
    )
    job_ttl_seconds: int = field(
        default_factory=lambda: _int("JOB_TTL_MINUTES", 30) * 60
    )
    resolve_per_minute: int = field(
        default_factory=lambda: _int("RESOLVE_PER_MINUTE", 10)
    )
    downloads_per_10min: int = field(
        default_factory=lambda: _int("DOWNLOADS_PER_10MIN", 3)
    )
    max_height: int = field(default_factory=lambda: _int("MAX_HEIGHT", 2160))
    frontend_origin: str | None = os.getenv("FRONTEND_ORIGIN") or None
    proxy_url: str | None = os.getenv("PROXY_URL") or None
    cookies_b64: str | None = os.getenv("COOKIES_B64") or None

    @property
    def allowed_heights(self) -> tuple[int, ...]:
        tiers = (2160, 1440, 1080, 720, 480, 360)
        return tuple(h for h in tiers if h <= self.max_height)


settings = Settings()

# Hosts aceitos: qualquer subdomínio destes.
ALLOWED_HOSTS: tuple[str, ...] = (
    "youtube.com",
    "youtu.be",
    "youtube-nocookie.com",
    "tiktok.com",
    "instagram.com",
    "facebook.com",
    "fb.watch",
    "twitter.com",
    "x.com",
    "soundcloud.com",
    "snd.sc",
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
