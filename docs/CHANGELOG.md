# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.1.1] - 2026-02-04

### Adicionado
- **Healthcheck e Observabilidade Básica**:
  - Endpoint `GET /health` para verificação completa de saúde
  - Endpoint `GET /health/ready` para Kubernetes readiness probe
  - Endpoint `GET /health/live` para Kubernetes liveness probe
  - Verificação de conectividade com banco de dados
  - Preparado para verificação de Redis (futura implementação)
- **Sistema de Logging Estruturado**:
  - Logs em formato JSON para produção (`JSON_LOGS=true`)
  - Logs coloridos para desenvolvimento
  - Request ID único por requisição (UUID)
  - Contexto de requisição em todos os logs
- **Middleware de Request Context**:
  - Geração automática de `X-Request-ID`
  - Header `X-Response-Time` com tempo de resposta
  - Métricas de performance por endpoint
  - Suporte a `X-Forwarded-For` para IP real em proxies
- **Novas Variáveis de Ambiente**:
  - `JSON_LOGS` - Ativar logs em formato JSON
  - `LOG_LEVEL` - Nível de log configurável

### Modificado
- `main.py` agora usa logging estruturado ao invés de logging básico
- Middleware de CORS agora usa variável de ambiente `CORS_ORIGINS`

---

## [0.0.1] - 2024-01-15

### Adicionado
- Sistema de tratamento de colisões de short_code com retry automático (até 5 tentativas)
- Logging básico para rastreamento de operações
- Tratamento robusto de erros com rollback em operações de banco de dados
- Documentação de métodos no serviço de URLs
- Sistema de versionamento do projeto (arquivo `__version__.py`)
- Documento de padrões de versionamento (`docs/VERSIONAMENTO.md`)
- Estrutura de documentação (changelogs e features)
- Metadata da API FastAPI (title, version, description)
- Constantes configuráveis (`MAX_RETRIES=5`, `SHORT_CODE_SIZE=6`)
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

---

## [0.1.0] - 2026-01-22

### Adicionado
- **CRUD Completo de URLs**:
  - Endpoint `GET /urls` para listar URLs com paginação
  - Endpoint `PATCH /urls/{id}` para atualizar URL original
  - Endpoint `DELETE /urls/{id}` para deletar URLs
- **Configuração via Ambiente**:
  - Variável `URL_BASE` configurável via arquivo `.env`
  - Arquivo `.env.example` para referência
- **Sistema de Exceptions Customizadas**:
  - `BaseAPIException` como classe base
  - `URLNotFoundError` (404)
  - `InvalidPaginationError` (400)
  - `MissingFieldError` (400)
  - `ShortCodeGenerationError` (500)
  - `DatabaseError` (500)
- **Exception Handlers Centralizados**:
  - Handler para exceptions customizadas
  - Handler para erros de validação (Pydantic)
  - Handler genérico para erros não tratados
  - Respostas de erro padronizadas em JSON
- **HashGenerator (Base 62)**:
  - Módulo `utils/hash_generator.py` para geração de hash
  - Base 62 (A-Z, a-z, 0-9) = 62 caracteres
  - Tamanho configurável (1-6 caracteres, padrão: 6)
  - 56.800.235.584 combinações possíveis com 6 caracteres
  - Geração criptograficamente segura
  - Métodos de validação e cálculo de combinações
- **Testes Unitários Completos**:
  - 16 testes para HashGenerator
  - Testes de formato de resposta de erro
  - Cobertura completa de todos os endpoints

### Modificado
- **SHORT_CODE_SIZE**: Reduzido de 8 para 6 caracteres
- **Geração de Hash**: Substituído NanoID por HashGenerator (Base 62)
- **Tratamento de Erros**: Migrado de HTTPException para exceptions customizadas
- **Respostas de Erro**: Formato padronizado com `{"error": {"code": ..., "message": ...}}`
- **URLService**: Agora usa HashGenerator ao invés de nanoid

### Corrigido
- Exception handlers não registrados nos testes (conftest.py)
- Documentação desatualizada sobre tamanho do short_code
