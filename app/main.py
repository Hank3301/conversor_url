"""API do conversor.

Fluxo: /api/resolve (metadados) -> /api/download (cria job) ->
/api/jobs/{id}/events (SSE de progresso) -> /api/jobs/{id}/file (stream).
Nada é armazenado de forma permanente.
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import ytdlp
from .config import settings
from .jobs import manager
from .security import InvalidUrl, download_limiter, normalize_url, resolve_limiter

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager.start_cleaner()
    yield


app = FastAPI(title=settings.app_name, docs_url="/api/docs", lifespan=lifespan)

if settings.frontend_origin:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


def _too_many(seconds: int, detail: str) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail=detail,
        headers={"Retry-After": str(seconds)},
    )


class ResolveBody(BaseModel):
    url: str = Field(max_length=2048)


class DownloadBody(BaseModel):
    url: str = Field(max_length=2048)
    kind: str = Field(pattern="^(video|audio)$")
    height: int | None = None
    bitrate: int | None = None


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/api/resolve")
async def resolve(body: ResolveBody, request: Request) -> dict:
    try:
        url = normalize_url(body.url)
    except InvalidUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    wait = resolve_limiter.check(client_ip(request))
    if wait:
        raise _too_many(wait, f"Muitas análises. Tente em {wait}s.")

    try:
        info = await ytdlp.probe(url)
    except ytdlp.DownloadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if info.duration and info.duration > settings.max_duration_seconds:
        limit = settings.max_duration_seconds // 60
        raise HTTPException(
            status_code=413,
            detail=f"Vídeo com {info.duration // 60} min. O limite é {limit} min.",
        )

    heights = [h for h in info.heights if h <= settings.max_height]
    return {
        "url": info.webpage_url,
        "title": info.title,
        "uploader": info.uploader,
        "duration": info.duration,
        "thumbnail": info.thumbnail,
        "heights": heights,
        "bitrates": [320, 192, 128],
        "limits": {
            "max_duration_minutes": settings.max_duration_seconds // 60,
            "max_filesize_mb": settings.max_filesize_bytes // (1024 * 1024),
        },
    }


@app.post("/api/download")
async def start_download(body: DownloadBody, request: Request) -> dict:
    try:
        url = normalize_url(body.url)
    except InvalidUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    wait = download_limiter.check(client_ip(request))
    if wait:
        raise _too_many(wait, f"Limite de downloads atingido. Tente em {wait}s.")

    if body.kind == "video" and body.height and body.height not in settings.allowed_heights:
        raise HTTPException(status_code=400, detail="Altura de vídeo inválida.")
    if body.kind == "audio" and body.bitrate and body.bitrate not in ytdlp.AUDIO_BITRATES:
        raise HTTPException(status_code=400, detail="Bitrate inválido.")

    job = manager.create(
        url=url,
        kind=body.kind,
        title="processando",
        height=body.height,
        bitrate=body.bitrate,
    )
    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}")
async def job_status(job_id: str) -> dict:
    job = manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabalho não encontrado ou expirado.")
    return job.snapshot()


@app.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str) -> StreamingResponse:
    job = manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabalho não encontrado ou expirado.")

    async def stream():
        queue = manager.subscribe(job)
        try:
            yield f"data: {json.dumps(job.snapshot())}\n\n"
            if job.status in ("ready", "error", "canceled"):
                return
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=20)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                yield f"data: {json.dumps(data)}\n\n"
                if data["status"] in ("ready", "error", "canceled"):
                    return
        finally:
            manager.unsubscribe(job, queue)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/jobs/{job_id}/file")
async def job_file(job_id: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabalho não encontrado ou expirado.")
    if job.status != "ready" or not job.path or not os.path.isfile(job.path):
        raise HTTPException(status_code=409, detail="Arquivo ainda não está pronto.")

    manager.release(job)
    media = "audio/mpeg" if job.kind == "audio" else "video/mp4"

    return FileResponse(
        job.path,
        media_type=media,
        filename=job.filename or "download",
        background=_CleanupTask(job),
    )


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> dict:
    return {"canceled": manager.cancel(job_id)}


class _CleanupTask:
    """Apaga o diretório do job depois que o navegador termina de baixar."""

    def __init__(self, job) -> None:
        self.job = job

    async def __call__(self) -> None:
        await asyncio.sleep(5)
        import shutil

        shutil.rmtree(self.job.dir, ignore_errors=True)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


# Caminhos relativos no HTML: funcionam tanto aqui quanto num host estático
# (Cloudflare Pages), onde a pasta web/ é a raiz.
@app.get("/style.css")
async def stylesheet() -> FileResponse:
    return FileResponse(os.path.join(WEB_DIR, "style.css"), media_type="text/css")


@app.get("/app.js")
async def script() -> FileResponse:
    return FileResponse(
        os.path.join(WEB_DIR, "app.js"), media_type="text/javascript"
    )


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
