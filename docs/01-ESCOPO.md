# 01 — Escopo

## Objetivo

Uma página única onde 5 a 15 amigos colam um link e baixam o vídeo (MP4) ou o
áudio (MP3). Sem cadastro, sem instalar app, funcionando no celular.

## Personas

| Persona | Necessidade |
|---|---|
| Amigo no celular | salvar um vídeo/áudio que viu no feed |
| Você (dono) | publicar barato, não virar suporte 24h |
| Estranho que achou o link | usar sem atrito, sem quebrar o serviço |

## Dentro do MVP

- Plataformas: TikTok, YouTube, Instagram, Facebook, X/Twitter, SoundCloud.
- Formatos: MP4 (resoluções que existirem no vídeo, até 4K) e MP3
  (128/192/320 kbps).
- Prévia com capa, título, autor e duração antes de baixar.
- Barra de progresso, cancelamento e mensagens de erro em português.
- Limites de duração, tamanho, concorrência e taxa por IP.
- Layout responsivo, tema escuro, sem dependências de frontend.

## Fora do MVP (consciente)

- Playlists e canais inteiros.
- Login, histórico, fila persistente entre reinícios.
- 8K, legendas, capítulos, escolha de faixa de áudio.
- Edição, corte, conversão para formatos exóticos (webm, flac, wav).
- Legendas em português no site (i18n).
- App nativo / PWA instalável.

## Matriz plataforma × recurso

Realidade medida no teste local (2026-11-16). "Cookies" = precisa de sessão
exportada para funcionar de forma confiável.

| Plataforma | Vídeo | Áudio | Precisa de cookies | Estabilidade |
|---|---|---|---|---|
| TikTok | sim | sim | não (maioria) | boa |
| YouTube | sim (até 4K) | sim | às vezes (IP de datacenter) | frágil em host grátis |
| Instagram | sim | sim | quase sempre | frágil |
| Facebook | sim | sim | às vezes | média |
| X/Twitter | sim | sim | às vezes | média |
| SoundCloud | não | sim | não | boa |

## Critérios de aceite do MVP

1. Colar um link do TikTok e baixar o MP4 em até 3 toques, no celular.
2. Colar um link do YouTube e receber MP3 192 kbps tocável em qualquer player.
3. Link inválido, de site não suportado ou vídeo longo demais gera mensagem
   clara — nunca erro genérico ou tela travada.
4. Dois downloads simultâneos não derrubam o servidor.
5. Depois de 10 minutos sem uso, o diretório temporário está vazio.
6. Cancelar no meio não deixa arquivo `.part` para trás.

## Métricas de sucesso

- 80% dos links colados chegam a um arquivo pronto.
- Nenhum incidente de disco cheio em 30 dias.
- Custo mensal: R$ 0.
