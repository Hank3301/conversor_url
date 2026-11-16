# 05 — Roadmap

Cada fase tem critério de saída. Não avance sem ele — é o que evita publicar um
site que quebra na mão do amigo.

## Fase 0 — MVP local ✅ concluída

Backend, frontend e limites prontos e testados de ponta a ponta.

**Provas:** `POST /api/resolve` devolve metadados reais de YouTube e TikTok;
MP4 360p H.264/AAC e MP3 128 kbps foram baixados e validados com `ffprobe`;
cancelamento mata o subprocesso e apaga o diretório; rate limit barra o 4º
pedido; URL de host não suportado e URL vazia retornam mensagens claras.

## Fase 1 — Publicar (1 noite)

1. `git init` + repositório privado.
2. Deploy no Render seguindo [03-HOSPEDAGEM-GRATIS](03-HOSPEDAGEM-GRATIS.md).
3. Ajustar limites: 1 job, 1080p, 20 min.
4. Testar no celular, na rede de casa.

**Saída:** link público funciona para TikTok e YouTube em 3 toques, no celular.

## Fase 2 — Confiabilidade (1 a 2 noites)

- Cookies de conta descartável em `COOKIES_B64` (YouTube/Instagram).
- Mensagens de erro específicas para "precisa de login" e "vídeo privado".
- Ping de 10 min (UptimeRobot grátis) contra o cold start.
- Log de uma linha por job (plataforma, duração, resultado) para enxergar falha.
- Rodapé com o aviso legal.

**Saída:** 10 links seguidos, de 3 plataformas, com no máximo 1 falha — e a
falha tem mensagem que o amigo entende.

## Fase 3 — Uso real (contínuo)

- Testar com 2 amigos de confiança por uma semana.
- Corrigir o que eles reclamarem antes de ampliar.
- Só então liberar para o grupo.

**Saída:** uma semana sem reclamação de "não funcionou".

## Fase 4 — Extras (opcional)

- Playlist e canal (baixar vários).
- PWA instalável + atalho na tela inicial.
- Escolher faixa de áudio e embutir capa no MP3.
- Contador de uso anônimo (só agregado).
- Migrar para VPS se o free tier apertar.

## Fora de escopo até doer

Login, histórico, editor de corte, legendas, app nativo, monetização.
