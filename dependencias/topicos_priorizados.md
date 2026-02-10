Topicos do Projeto por Prioridade

Alta prioridade
- Configurar base URL via ambiente (URL_BASE) para evitar hardcode.
- CRUD de URLs (listar/remover/atualizar) para gestao completa.
- Testes unitarios para URLService (shorten, redirect, stats) e validacoes.
- Tratamento de erros e respostas consistentes (padrao de erro da API).

Media prioridade
- Alias/custom short_code para usuarios.
- Expiracao/TTL de links e limpeza automatica.
- Rate limiting e protecao contra abuso.
- Healthcheck e observabilidade basica (logs estruturados).
- Adicionar camada de cache ao criar o hash

Baixa prioridade
- Metricas avancadas (user-agent, referrer, horario de cliques).
- Blacklist/allowlist de dominos.
- Dashboard simples para estatisticas agregadas.
