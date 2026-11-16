# 04 — Riscos e legal

## Riscos técnicos

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| YouTube bloqueia IP de datacenter | alta | alto | cookies, proxy, plano B residencial; erro claro na UI |
| Instagram exige login | alta | médio | `COOKIES_B64`; documentado como limitação |
| yt-dlp quebra após mudança da plataforma | alta | alto | nightly no build; redeploy em 1 clique; `_human_error` traduz |
| Disco efêmero enche | média | alto | TTL, limpeza pós-envio, limite de tamanho |
| RAM estoura com 2 jobs de 4K | média | alto | 1 job e 1080p no Render |
| Host suspende por cota | média | alto | 750 h/mês, ping de 10 min, plano B pronto |
| Alguém descobre e abusa | média | médio | rate limit por IP, limites de duração/tamanho |
| Processo reinicia no meio | média | baixo | estado em RAM; o amigo recola o link |
| Cookies vazam | baixa | alto | conta descartável, secret no host, nunca no git |

## Riscos legais

O site **não hospeda nada**: baixa na hora e entrega. Ainda assim:

- **Direito autoral.** Baixar para uso pessoal é a zona confortável; repostar
  comercialmente exige olhar caso a caso. O site deve deixar claro que o
  conteúdo é dos autores.
- **Termos de uso das plataformas.** Nenhuma delas autoriza explicitamente
  download por terceiros. É tolerado na prática, não é direito garantido.
  YouTube e Instagram são os mais restritivos.
- **Marca.** "Conversor de Links" não usa logotipo de ninguém. Se publicar,
  evite nome/identidade visual que sugira vínculo oficial.
- **Dados pessoais (LGPD).** Coletamos só IP em memória para rate limit, sem
  persistir. Cookies de sessão ficam num arquivo temporário. Base legal:
  legítimo interesse; nada a declarar além de uma linha na política.
- **Retirada (DMCA).** Como nada fica armazenado, não há o que retirar — basta
  o autor pedir e o link deixar de funcionar naturalmente.

### Texto sugerido no rodapé

> Uso pessoal e educacional. Os vídeos e músicas pertencem aos seus autores.
> Este site não armazena arquivos: tudo é baixado na hora e apagado em seguida.

## Riscos de produto

- **Expectativa de 4K.** No celular quase ninguém precisa; no host grátis é
  lento. A UI deve mostrar a resolução real e sugerir 720p/1080p.
- **"Conversor" é nome impróprio.** Quase sempre há remux, não conversão. Se
  alguém pedir 4K de um vídeo 720p, o arquivo sai 720p — a UI avisa.
- **Viralizar.** 15 amigos viram 200 e o free tier não aguenta. Sinal claro:
  filas longas e 429. Resposta: VPS.

## Checklist antes de divulgar

- [ ] Rodapé com o aviso legal acima
- [ ] `MAX_HEIGHT=1080`, 1 job simultâneo, duração ≤ 20 min
- [ ] Rate limit ativo e testado
- [ ] Cookies de conta descartável, nunca a principal
- [ ] Repositório privado (o `render.yaml` não tem segredo, mas o histórico sim)
- [ ] Alguém avisado de que o primeiro acesso após inatividade demora ~50 s
