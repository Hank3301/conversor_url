# 06 — Backlog

Prioridade: **P0** trava o uso, **P1** atrito real, **P2** conforto.
Esforço em noites de trabalho.

| # | Item | P | Esforço | Nota |
|---|---|---|---|---|
| 1 | Deploy no Render + teste no celular | P0 | 1 | Fase 1 |
| 2 | Cookies de conta descartável (`COOKIES_B64`) | P0 | 0,5 | YouTube/Instagram |
| 3 | Ping de 10 min contra cold start | P0 | 0,2 | UptimeRobot |
| 4 | Rodapé legal (feito no HTML, conferir no ar) | P0 | 0,1 | — |
| 5 | Erro específico: "precisa de login" | P1 | 0,5 | Instagram |
| 6 | Erro específico: "vídeo privado/removido" | P1 | 0,3 | — |
| 7 | Log de uma linha por job | P1 | 0,3 | diagnóstico |
| 8 | Testar com 2 amigos | P1 | 1 | Fase 3 |
| 9 | Thumbnail em `webp` com fallback `jpg` | P2 | 0,3 | i.ytimg devolve webp |
| 10 | Embutir capa e metadados no MP3 | P2 | 0,5 | `--embed-thumbnail` |
| 11 | Escolher faixa de áudio em vídeo dublado | P2 | 1 | raro no grupo |
| 12 | Playlist/canal | P2 | 2 | muda a fila |
| 13 | PWA instalável | P2 | 1 | atalho no celular |
| 14 | Contador anônimo de uso | P2 | 0,5 | decidir se vale |
| 15 | Testes automatizados dos helpers | P2 | 1 | `security`, `jobs` |
| 16 | Migrar para VPS | P2 | 2 | só se doer |

## Feito

- [x] Allowlist de hosts e normalização de URL
- [x] Rate limit por IP (análise e download, separados)
- [x] Resolve com metadados e resoluções reais
- [x] Fila com semáforo, cancelamento e limpeza de disco
- [x] SSE de progresso
- [x] MP4 H.264/AAC e MP3 com escolha de bitrate
- [x] UI responsiva em PT-BR com prévia, progresso e toasts
- [x] Dockerfile com ffmpeg + deno, `render.yaml`
- [x] `scripts/dev.ps1` e `scripts/cookies_b64.py`
- [x] Teste de ponta a ponta local (resolve, MP4, MP3, cancelar, 429)

## Como escolher a próxima tarefa

Pegue o menor número de P0 que ainda não está feito. Se nenhum P0 restar e a
Fase 3 não terminou, o trabalho é conversar com quem usa — não codar.
