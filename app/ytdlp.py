"""Camada única de contato com o yt-dlp.

Regras de ouro:
* sempre `--no-playlist` (um link = um arquivo);
* sempre com limites de duração e tamanho;
* progresso lido de `--progress-template` (nada de parsear texto solto);
* o processo é cancelável.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import sys
from dataclasses import dataclass
from typing import Callable

from .config import USER_AGENT, settings
from .security import write_cookies_file

PROGRESS_PREFIX = "PROG|"
_OUTPUT_TEMPLATE = "%(title).100B [%(id)s].%(ext)s"

AUDIO_BITRATES = (320, 192, 128)


class DownloadError(RuntimeError):
    pass


@dataclass
class Probe:
    title: str
    uploader: str | None
    duration: int | None
    thumbnail: str | None
    webpage_url: str
    heights: tuple[int, ...]
    extractor: str


def _js_args() -> list[str]:
    """O YouTube exige um runtime JS para resolver os desafios (EJS).

    Sem isso a extração degrada e faltam formatos. deno é o preferido
    pelo yt-dlp; node serve como alternativa em desenvolvimento.
    """
    for runtime in ("deno", "node", "bun"):
        if shutil.which(runtime):
            return ["--js-runtimes", runtime]
    return []


def _base_args() -> list[str]:
    args = [
        "--no-playlist",
        "--no-warnings",
        "--no-mtime",
        "--newline",
        "--ignore-config",
        "--socket-timeout",
        "20",
        "--retries",
        "3",
        "--user-agent",
        USER_AGENT,
        "--max-filesize",
        str(settings.max_filesize_bytes),
        "--progress-template",
        "download:PROG|%(progress.downloaded_bytes)s|%(progress.total_bytes)s"
        "|%(progress.total_bytes_estimate)s",
        *_js_args(),
    ]
    cookies = write_cookies_file()
    if cookies:
        args += ["--cookies", cookies]
    if settings.proxy_url:
        args += ["--proxy", settings.proxy_url]
    return args


def _human_error(stderr: str) -> str:
    text = stderr.lower()
    if "sign in to confirm" in text or "not a bot" in text:
        return "O YouTube pediu verificação anti-robô. Tente de novo em instantes."
    if "private" in text or "login" in text:
        return "Conteúdo privado ou que exige login (cookies necessários)."
    if "max-filesize" in text or "larger than max" in text:
        mb = settings.max_filesize_bytes // (1024 * 1024)
        return f"Arquivo maior que o limite de {mb} MB."
    if "unsupported url" in text:
        return "O yt-dlp não reconhece esse link."
    if "http error 404" in text:
        return "Conteúdo não encontrado (404)."
    if "http error 429" in text or "rate limit" in text:
        return "A plataforma limitou as requisições. Aguarde alguns minutos."
    if "timed out" in text or "timeout" in text:
        return "A plataforma demorou demais para responder."
    if "no space left" in text:
        return "Disco do servidor cheio."
    return "Falha ao processar o link. Verifique se ele abre no navegador."


async def _run(args: list[str], on_line: Callable[[str], None] | None = None) -> str:
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "yt_dlp",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        # sem isso o progresso chega todo de uma vez no final
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    stderr_chunks: list[str] = []

    async def pump_stdout() -> None:
        assert proc.stdout
        while True:
            raw = await proc.stdout.readline()
            if not raw:
                break
            if on_line:
                on_line(raw.decode("utf-8", "replace").rstrip())

    async def pump_stderr() -> None:
        assert proc.stderr
        while True:
            raw = await proc.stderr.readline()
            if not raw:
                break
            stderr_chunks.append(raw.decode("utf-8", "replace"))

    try:
        await asyncio.gather(pump_stdout(), pump_stderr())
        code = await proc.wait()
    except asyncio.CancelledError:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
        raise
    stderr = "".join(stderr_chunks)

    if code != 0:
        if code in (2,) and "canceled" in stderr.lower():
            raise DownloadError("Cancelado.")
        raise DownloadError(_human_error(stderr))
    return stderr


def _clean_title(info: dict) -> str:
    title = (info.get("title") or info.get("description") or "video").strip()
    title = re.sub(r"\s+", " ", title)
    return title[:120] or "video"


async def probe(url: str) -> Probe:
    args = ["-J", "--skip-download", *_base_args(), url]
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "yt_dlp",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise DownloadError(_human_error(err.decode("utf-8", "replace")))

    import json

    try:
        info = json.loads(out.decode("utf-8", "replace"))
    except json.JSONDecodeError as exc:
        raise DownloadError("Resposta inesperada da plataforma.") from exc

    if info.get("_type") in ("playlist", "multi_video"):
        entries = [e for e in info.get("entries") or [] if e]
        if entries:
            info = entries[0]

    duration = info.get("duration")
    duration = int(duration) if isinstance(duration, (int, float)) else None

    formats = info.get("formats") or []
    heights = {
        int(f["height"])
        for f in formats
        if isinstance(f.get("height"), int) and f.get("vcodec") not in (None, "none")
    }
    available: list[int] = []
    for tier in settings.allowed_heights:
        if any(h >= tier for h in heights):
            available.append(tier)

    return Probe(
        title=_clean_title(info),
        uploader=info.get("uploader") or info.get("channel"),
        duration=duration,
        thumbnail=info.get("thumbnail"),
        webpage_url=info.get("webpage_url") or url,
        heights=tuple(available),
        extractor=(info.get("extractor_key") or info.get("extractor") or "").lower(),
    )


async def download(
    url: str,
    outdir: str,
    *,
    kind: str,
    height: int | None = None,
    bitrate: int | None = None,
    on_progress: Callable[[float | None], None] | None = None,
) -> str:
    """Baixa e devolve o caminho do arquivo final."""
    args = list(_base_args())
    args += ["-o", os.path.join(outdir, _OUTPUT_TEMPLATE)]

    if kind == "audio":
        quality = bitrate if bitrate in AUDIO_BITRATES else 192
        args += [
            "-f",
            "ba/b",
            "-S",
            "acodec:m4a,abr",
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            f"{quality}k",
        ]
    else:
        cap = min(height or 1080, settings.max_height)
        args += [
            "-f",
            f"bv*[height<={cap}]+ba/b[height<={cap}]/bv*+ba/b",
            # H.264 + AAC abre em qualquer navegador/celular. É preferência,
            # não filtro: 4K (VP9/AV1) continua disponível quando pedido.
            "-S",
            "vcodec:h264,res,acodec:m4a",
            "--merge-output-format",
            "mp4",
            "--remux-video",
            "mp4",
        ]

    def handle(line: str) -> None:
        if not on_progress or not line.startswith(PROGRESS_PREFIX):
            return
        parts = line.split("|")
        if len(parts) < 4:
            return
        try:
            done = float(parts[1])
            total = float(parts[2]) if parts[2] not in ("NA", "None", "") else None
            if total is None:
                est = parts[3]
                total = float(est) if est not in ("NA", "None", "") else None
        except ValueError:
            return
        if total and total > 0:
            on_progress(min(0.99, done / total))
        else:
            on_progress(None)

    await _run([*args, url], handle)

    files = [
        os.path.join(outdir, name)
        for name in os.listdir(outdir)
        if os.path.isfile(os.path.join(outdir, name))
    ]
    if not files:
        raise DownloadError("O download terminou sem gerar arquivo.")
    return max(files, key=os.path.getsize)
