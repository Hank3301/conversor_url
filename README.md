# Conversor de Links

Site para os amigos colarem um link de TikTok, YouTube, Instagram, Facebook, X ou
SoundCloud e baixarem o vídeo em MP4 ou o áudio em MP3, sem instalar nada.

> **Estado:** MVP funcional rodando localmente e testado de ponta a ponta
> (resolução de link, download MP4/MP3, progresso, cancelamento, limites e
> limpeza de disco). Ainda **não publicado** — o passo de deploy é a Fase 1 do
> [roadmap](docs/05-ROADMAP.md).

## Como rodar agora

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
```

Abre em <http://127.0.0.1:8000>. Requer Python 3.11+ e ffmpeg no PATH (já
instalados nesta máquina). O script cria o `.venv`, instala as dependências e
sobe o servidor.

## Estrutura

```
app/                 backend FastAPI
  config.py          limites lidos do ambiente
  security.py        allowlist de hosts, rate limit, cookies
  ytdlp.py           única camada que fala com o yt-dlp
  jobs.py            fila em memória, concorrência, limpeza
  main.py            rotas HTTP
web/                 frontend estático (HTML/CSS/JS, sem build)
scripts/             dev.ps1, cookies_b64.py
docs/                escopo, arquitetura, hospedagem, riscos, roadmap, backlog
Dockerfile           imagem de produção (ffmpeg + deno)
render.yaml          blueprint de deploy no Render
```

## Como funciona

1. `POST /api/resolve` valida o link contra uma allowlist de domínios e chama
   `yt-dlp -J` para ler título, duração, capa e **as resoluções que realmente
   existem** naquele vídeo.
2. `POST /api/download` enfileira um job (no máximo 2 simultâneos).
3. `GET /api/jobs/{id}/events` transmite o progresso por SSE.
4. `GET /api/jobs/{id}/file` entrega o arquivo e o diretório é apagado logo
   depois. **Nada fica armazenado.**

## Limites (padrão)

| Limite | Valor | Por quê |
|---|---|---|
| Duração | 45 min (20 no Render) | disco e tempo de CPU gratuitos |
| Tamanho | 2048 MB | evita encher o disco efêmero |
| Jobs simultâneos | 2 (1 no Render) | 512 MB de RAM |
| Análises | 10/min por IP | proteção contra abuso |
| Downloads | 3/10 min por IP | idem |
| Altura máxima | 2160 (1080 no Render) | CPU do host gratuito |

Tudo é ajustável por variável de ambiente — veja [.env.example](.env.example).

## Decisões que você precisa conhecer

- **Download direto, sem storage.** O arquivo é baixado para um diretório
  temporário, enviado ao navegador e apagado. Sem banco, sem S3, sem custo.
- **MP4 em H.264/AAC por padrão.** O yt-dlp é instruído a preferir esse codec
  porque abre em qualquer celular; 4K em VP9/AV1 continua disponível quando a
  pessoa escolhe essa qualidade.
- **deno na imagem Docker.** O YouTube passou a exigir um runtime JS para
  resolver desafios; sem isso a extração perde formatos.
- **Sem login.** O site é aberto, com rate limit por IP. Se virar público, ver
  [riscos](docs/04-RISCOS-E-LEGAL.md).

## Deploy

Guia completo, com alternativas e o que cada host gratuito realmente entrega:
[docs/03-HOSPEDAGEM-GRATIS.md](docs/03-HOSPEDAGEM-GRATIS.md).

## Aviso

Uso pessoal. Os vídeos pertencem aos autores originais e cada plataforma tem
seus próprios termos — leia [docs/04-RISCOS-E-LEGAL.md](docs/04-RISCOS-E-LEGAL.md)
antes de divulgar.
