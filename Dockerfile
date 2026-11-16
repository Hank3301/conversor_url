FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl unzip \
 && rm -rf /var/lib/apt/lists/*

# O YouTube exige um runtime JS (EJS) para liberar formatos. Sem deno,
# a extração degrada e o 1080p+ costuma sumir.
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh \
 && deno --version

WORKDIR /app

COPY requirements.txt .
# yt-dlp quebra toda semana quando a plataforma muda: sempre a nightly.
RUN pip install -r requirements.txt \
 && pip install -U --pre "yt-dlp[default]"

COPY app ./app
COPY web ./web

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
