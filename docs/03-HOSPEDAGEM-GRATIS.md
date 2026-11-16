# 03 — Hospedagem gratuita

## Resumo da decisão

**Backend no Render (plano free, Docker) + frontend servido pela mesma
instância.** Sem cartão, sem storage, sem banco.

**Plano B recomendado:** o mesmo backend rodando no seu PC com
**Cloudflare Tunnel** — de graça, sem cartão e com IP residencial (o que faz o
YouTube e o Instagram funcionarem bem melhor). Custo: o PC precisa estar ligado.

## O que cada opção gratuita realmente entrega

| Host | Cartão? | RAM/CPU | Dorme? | Disco | Veredito |
|---|---|---|---|---|---|
| **Render free** | não para criar | 512 MB / <1 CPU | sim, ~15 min | efêmero | ✅ escolhido para o MVP |
| **Cloudflare Tunnel + PC** | não | a do seu PC | não | o do seu PC | ✅ plano B, melhor taxa de sucesso |
| Koyeb free | sim (verificar) | 0,25 vCPU / 1 GB | sim | efêmero | alternativa razoável |
| Hugging Face Spaces | **sim, PRO** | — | — | — | ❌ deixou de ser grátis para Docker/Gradio (só Static Space grátis) |
| Vercel (serverless) | não | 1 GB / 10 s de CPU | n/a | efêmero | ⚠️ limite de 60 s e binário grande demais |
| Fly.io | sim | 256 MB | não | 3 GB | ⚠️ exige cartão |
| Oracle Cloud | sim | 1 GB | não | 200 GB | ⚠️ exige cartão, cadastro chato |
| GitHub Codespaces | não | 2 núcleos | 30 min | 32 GB | ⚠️ não é host, morre em 60 h/mês |
| Cloudflare Pages | não | estático | não | — | ✅ só para o frontend |

Detalhes do Render free que importam:

- 512 MB de RAM e **menos de 1 CPU** — por isso `MAX_CONCURRENT_JOBS=1`,
  `MAX_HEIGHT=1080` e `MAX_DURATION_MINUTES=20` no [render.yaml](../render.yaml).
- Dorme após ~15 min sem acesso. O primeiro acesso depois disso demora ~50 s.
- **750 horas de instância por mês.** 24/7 consome ~744 h, então um ping a cada
  10 min mantém tudo acordado sem estourar — mas sem cartão, ao passar do
  limite o Render **suspende** os serviços.
- 100 GB de banda de saída/mês. Para 15 amigos, sobra.
- Disco efêmero: nada sobrevive a um deploy.

## Passo a passo do deploy (Render)

1. `git init`, comite o projeto e crie um repositório **privado** no GitHub.
2. Em <https://dashboard.render.com>, `New > Blueprint`, aponte para o repo. O
   Render lê o `render.yaml` e monta o serviço.
3. (Opcional, recomendado para YouTube/Instagram) gere o secret:
   `python scripts/cookies_b64.py cookies.txt` e cole em `COOKIES_B64`.
   Exporte os cookies de uma **conta descartável**, não da sua principal.
4. Aguarde o build (~4 min: ffmpeg + deno). Teste `/api/health` → `{"ok":true}`.
5. Teste um link do TikTok. Depois um do YouTube. Se o YouTube falhar, é o
   IP de datacenter — veja "Quando o YouTube quebrar".

## Frontend separado (opcional)

Só vale se você quiser CDN e cache:

1. Publique a pasta `web/` na Cloudflare Pages (grátis, sem cartão).
2. Em `web/index.html`, troque `window.__API_BASE__ = ""` pela URL do Render.
   Os arquivos usam caminhos relativos, então nada mais precisa mudar.
3. No Render, defina `FRONTEND_ORIGIN=https://seu-projeto.pages.dev`.

## Quando o YouTube quebrar

Sintoma: "confirme que você não é um robô" ou lista de resoluções vazia.

Ordem de tentativas, da mais barata à mais cara:

1. Atualizar o yt-dlp (a imagem já instala a nightly no build; refaça o deploy).
2. Cookies de conta descartável em `COOKIES_B64`.
3. `PROXY_URL` residencial.
4. Migrar para o plano B: seu PC + Cloudflare Tunnel.

## Cloudflare Tunnel (plano B)

```powershell
# 1x
winget install --id Cloudflare.cloudflared
cloudflared tunnel login
cloudflared tunnel create conversor
cloudflared tunnel route dns conversor links.seudominio.com
# sempre que quiser publicar
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
cloudflared tunnel run --url http://127.0.0.1:8000 conversor
```

Vantagens: sem dormir, sem limite de RAM, IP residencial (YouTube e Instagram
aceitam muito melhor). Desvantagem: depende do PC ligado e da sua internet.

## Se um dia doer

O primeiro gasto que resolve quase tudo é um VPS de US$ 5–6/mês (Hetzner,
Contabo): RAM, CPU, disco e IP dedicado. O código não muda — só as variáveis
de ambiente e o `MAX_HEIGHT`. Hugging Face PRO (US$ 9/mês) também volta a
permitir Docker, mas com menos controle que um VPS.
