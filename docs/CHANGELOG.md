# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.0.1] - 2024-01-15

### Adicionado
- Sistema de tratamento de colisões de short_code com retry automático
- Logging básico para rastreamento de operações
- Tratamento robusto de erros com rollback em operações de banco de dados
- Documentação de métodos no serviço de URLs
- Sistema de versionamento do projeto
- Estrutura de documentação (changelogs e features)
- Endpoint para criação de URLs encurtadas (`POST /create-url`)
- Endpoint para redirecionamento de URLs (`GET /{short_code}`)
- Endpoint para estatísticas de URLs (`GET /stats/{short_code}`)

### Modificado
- Método `shorten_url` agora implementa retry em caso de colisão
- Método `get_original_url` agora tem tratamento de erros no incremento de cliques
- Configuração de logging adicionada na aplicação principal

### Corrigido
- Problema de colisão de short_code não tratado
- Falta de rollback em caso de erros de banco de dados
