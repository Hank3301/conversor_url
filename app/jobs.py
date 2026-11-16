"""Fila de trabalhos em memória.

Sem banco de dados de propósito: com 5 a 15 amigos o estado cabe em RAM,
e um host gratuito reinicia do zero sem prejuízo (nada é persistente).
"""

from __future__ import annotations

import asyncio
import os
import secrets
import shutil
import tempfile
import time
from dataclasses import dataclass, field

from . import ytdlp
from .config import settings

ROOT_DIR = os.path.join(tempfile.gettempdir(), "conversor-url")


@dataclass
class Job:
    url: str
    kind: str
    title: str
    height: int | None = None
    bitrate: int | None = None
    id: str = field(default_factory=lambda: secrets.token_urlsafe(18))
    status: str = "queued"
    progress: float = 0.0
    error: str | None = None
    path: str | None = None
    filename: str | None = None
    size: int = 0
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    task: asyncio.Task | None = None
    _subscribers: list[asyncio.Queue] = field(default_factory=list)

    @property
    def dir(self) -> str:
        return os.path.join(ROOT_DIR, self.id)

    def snapshot(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "progress": round(self.progress, 4),
            "error": self.error,
            "title": self.title,
            "filename": self.filename,
            "size": self.size,
        }

    def publish(self) -> None:
        data = self.snapshot()
        for queue in list(self._subscribers):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                pass


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)
        self._cleaner: asyncio.Task | None = None

    # ---------- ciclo de vida ----------

    def start_cleaner(self) -> None:
        if self._cleaner is None or self._cleaner.done():
            self._cleaner = asyncio.create_task(self._clean_loop())

    async def _clean_loop(self) -> None:
        while True:
            await asyncio.sleep(120)
            cutoff = time.time() - settings.job_ttl_seconds
            for job in list(self._jobs.values()):
                if job.updated < cutoff and job.status in ("ready", "error", "canceled"):
                    self._discard(job)

    def _discard(self, job: Job) -> None:
        self._jobs.pop(job.id, None)
        shutil.rmtree(job.dir, ignore_errors=True)

    def create(self, *, url: str, kind: str, title: str, height=None, bitrate=None) -> Job:
        job = Job(url=url, kind=kind, title=title, height=height, bitrate=bitrate)
        self._jobs[job.id] = job
        job.task = asyncio.create_task(self._run(job))
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.status in ("ready", "error", "canceled"):
            return False
        job.status = "canceled"
        job.updated = time.time()
        job.publish()
        if job.task and not job.task.done():
            job.task.cancel()
        shutil.rmtree(job.dir, ignore_errors=True)
        return True

    def release(self, job: Job) -> None:
        """Chamado depois de enviar o arquivo ao navegador."""
        job.updated = time.time() - settings.job_ttl_seconds + 60

    async def _run(self, job: Job) -> None:
        try:
            async with self._semaphore:
                if job.status == "canceled":
                    return
                os.makedirs(job.dir, exist_ok=True)
                job.status = "downloading"
                job.progress = 0.02  # extração: barra fica indeterminada no front
                job.updated = time.time()
                job.publish()

                def on_progress(ratio: float | None) -> None:
                    if ratio is None:
                        job.progress = max(job.progress, 0.05)
                    else:
                        job.progress = max(job.progress, ratio)
                    job.updated = time.time()
                    job.publish()

                path = await ytdlp.download(
                    job.url,
                    job.dir,
                    kind=job.kind,
                    height=job.height,
                    bitrate=job.bitrate,
                    on_progress=on_progress,
                )

                job.status = "processing"
                job.progress = 0.99
                job.publish()

                job.path = path
                job.filename = os.path.basename(path)
                job.size = os.path.getsize(path)
                job.status = "ready"
                job.progress = 1.0
                job.updated = time.time()
                job.publish()
        except asyncio.CancelledError:
            job.status = "canceled"
            job.publish()
        except ytdlp.DownloadError as exc:
            job.status = "error"
            job.error = str(exc)
            job.updated = time.time()
            job.publish()
            shutil.rmtree(job.dir, ignore_errors=True)
        except Exception:
            job.status = "error"
            job.error = "Erro inesperado no servidor."
            job.updated = time.time()
            job.publish()
            shutil.rmtree(job.dir, ignore_errors=True)

    # ---------- SSE ----------

    def subscribe(self, job: Job) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=32)
        job._subscribers.append(queue)
        return queue

    def unsubscribe(self, job: Job, queue: asyncio.Queue) -> None:
        if queue in job._subscribers:
            job._subscribers.remove(queue)


manager = JobManager()
