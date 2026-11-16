# 07 — Checklist de lançamento

Marque tudo antes de mandar o link para alguém. Se um item falhar, pare.

## Código

- [ ] `python -m compileall app` sem erro
- [ ] `.venv` fora do git e `.env` ignorado
- [ ] Nenhum cookie comitado (`git status` limpo de `cookies*.txt`)
- [ ] `MAX_HEIGHT=1080`, `MAX_CONCURRENT_JOBS=1`, `MAX_DURATION_MINUTES=20`
- [ ] Rate limit ativo (`RESOLVE_PER_MINUTE`, `DOWNLOADS_PER_10MIN`)

## Serviço

- [ ] `/api/health` responde `{"ok":true}`
- [ ] Página abre no celular e o layout não quebra
- [ ] Link do TikTok: resolve, baixa MP4, arquivo abre
- [ ] Link do YouTube: resolve e baixa MP3 192
- [ ] Link inválido e link de site não suportado: mensagem clara
- [ ] Cancelar no meio: status "cancelado", sem arquivo no disco
- [ ] Quarto download em 10 min: 429 com mensagem amigável
- [ ] Diretório temporário vazio depois de 10 min parado

## Comunicação

- [ ] Rodapé legal visível
- [ ] Amigos avisados de que o primeiro acesso pode demorar ~50 s
- [ ] Amigos avisados de que Instagram pode pedir cookies
- [ ] Você sabe onde ver o consumo de horas e banda do host

## Plano B pronto

- [ ] Cloudflare Tunnel instalado e testado no PC
- [ ] Você sabe refazer o deploy em 1 clique
- [ ] Você sabe o que fazer se o host suspender (migrar ou VPS)
