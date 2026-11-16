# 02 — Arquitetura

## Visão

```
navegador
   │  1. cola link
   ▼
[frontend estático] ──POST /api/resolve──► [FastAPI]
   │                                          │ valida host (allowlist)
   │                                          │ yt-dlp -J (só metadados)
   │◄───────── título, capa, resoluções ──────┘
   │  2. escolhe formato
   ├──POST /api/download──► [fila: semáforo 2] ──► yt-dlp + ffmpeg
   │                              │                    │
   │◄── SSE de progresso ─────────┘                    ▼
   │                                            /tmp/conversor-url/<job>/
   ├──GET /api/jobs/{id}/file──► stream do arquivo ────┘
   │                               └─ apaga o diretório 5s depois
   ▼
arquivo salvo no dispositivo
```

## Componentes

| Componente | Papel | Por que assim |
|---|---|---|
| `security.normalize_url` | allowlist de domínios + limpeza de rastreadores | fecha SSRF: o yt-dlp nunca recebe host arbitrário |
| `security.RateLimiter` | janela deslizante em memória | sem Redis, sem custo |
| `ytdlp.probe` | metadados e resoluções reais | a UI só oferece o que existe (sem botão que falha) |
| `ytdlp.download` | única camada de subprocesso | fácil de trocar/limitar/testar |
| `jobs.JobManager` | fila, semáforo, TTL, SSE | estado em RAM basta para 15 amigos |
| `main` | rotas HTTP finas | regra de negócio não fica na rota |

## Por que sem banco de dados

O host gratuito não tem disco persistente. Um banco local (SQLite) seria
apagado a cada deploy e ainda assim não guardaria os arquivos. O estado útil
vive segundos: um job em andamento. Se o processo reiniciar no meio de um
download, o amigo só cola o link de novo — custo aceitável.

## Concorrência

- `asyncio.Semaphore(MAX_CONCURRENT_JOBS)` — fila real, não recusa.
- Cada job é uma `asyncio.Task` cancelável: o cancelamento mata o subprocesso
  (`proc.kill()` no `except CancelledError`) e apaga o diretório.
- SSE usa uma `Queue` por espectador, com descarte do evento mais antigo para
  nunca travar o produtor.

## Segurança

| Risco | Mitigação |
|---|---|
| SSRF | allowlist de hosts; URL normalizada antes de qualquer subprocesso |
| Comando injetado | `create_subprocess_exec` com lista de argumentos (sem shell) |
| Path traversal | nome do arquivo vem do yt-dlp, que roda em diretório próprio por job |
| Abuso de CPU | duração, tamanho, concorrência e rate limit por IP |
| Vazamento de cookies | cookies em arquivo temporário fora do repositório |
| XSS | título/capa inseridos via `textContent`/`src`, não `innerHTML` |
| CORS | liberado só para `FRONTEND_ORIGIN`, se definido |

## Limpeza de disco

Três redes de proteção: `_CleanupTask` apaga após o envio, `cancel()` apaga na
hora, e o coletor apaga jobs parados há mais de `JOB_TTL_MINUTES`. Disco
efêmero cheio é o modo de falha mais provável de um host gratuito.

## O que muda ao crescer

| Gatilho | Mudança |
|---|---|
| Mais de ~50 usuários/dia | fila externa + storage de objetos + link assinado |
| YouTube quebrando sempre | proxy residencial ou PO token provider próprio |
| Precisa de histórico | Postgres gerenciado e jobs persistentes |
| Precisa de 4K confiável | host pago com CPU dedicada (transcodificação real) |

## Dívida técnica assumida

- Estado em RAM: some no restart.
- Rate limit em RAM: não vale entre múltiplas instâncias.
- Sem testes automatizados de rede (dependem das plataformas).
- SSE por polling de fila, não push real de progresso do ffmpeg.
