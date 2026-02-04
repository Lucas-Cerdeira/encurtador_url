Features Encurtador URL

## Funcionalidades Implementadas

### Encurtamento de URLs
- [x] Receber URL longa e retornar URL encurtada
- [x] Geracao de short_code com 6 caracteres (Hash Generator)
- [x] Tratamento de colisao com retry automatico
- [x] Configuracao de URL_BASE via variavel de ambiente

### Redirecionamento
- [x] Redirecionar short_code para URL original
- [x] Incremento automatico de contador de cliques

### Estatisticas Basicas
- [x] Retornar metricas basicas da URL:
  - Numero total de cliques
  - URL original
  - Short code

### Testes
- [x] Testes unitarios para URLService (shorten, redirect, stats)
- [x] Testes de rotas com validacao via Pydantic
- [x] Fixtures e banco de dados em memoria para testes

### CRUD Completo
- [x] Listar todas as URLs (GET /urls)
- [x] Atualizar URL original (PUT /urls/{id})
- [x] Remover URL (DELETE /urls/{id})

### Tratamento de Erros
- [x] Padrao consistente de respostas de erro com codigo e detalhes
- [x] Validacoes robustas de entrada com Pydantic
- [x] Codigos HTTP apropriados
- [x] Mensagens de erro descritivas

### Paginacao e Listagem
- [x] Paginacao na listagem de URLs (GET /urls?page=1&page_size=10)
- [x] Parametros configuraveis: page (min: 1) e page_size (min: 1, max: 100)
- [x] Ordenacao por data de criacao (mais recentes primeiro)
- [x] Retorno padronizado com total, page, page_size e lista de URLs
- [x] Validacao de parametros com tratamento de erros (InvalidPaginationError)
- [x] Testes completos de paginacao (service e rotas)

---

## 🎯 ROADMAP - Features Pendentes

### 🔴 PRIORIDADE CRÍTICA (Bloqueadores para Produção)

> **Objetivo:** Tornar a aplicação segura e pronta para uso em produção

#### 1. Autenticação e Autorização
**Status:** Não implementado | **Complexidade:** Alta | **Impacto:** Crítico

**Descrição:**
Sistema completo de autenticação para controlar acesso às URLs e operações.

**Por quê é crítico:**
- Sem auth, qualquer pessoa pode deletar/editar URLs de outros
- Impossível rastrear quem criou cada URL
- Sem controle de acesso ou quotas por usuário

**Arquitetura:**
```
models/user.py
├── User (id, email, password_hash, created_at, is_active)
└── Relacionamento: User hasMany URLs

middleware/auth.py
├── JWT token generation/validation
├── Password hashing (bcrypt)
└── Protected route decorator

routes/auth.py
├── POST /register (criar conta)
├── POST /login (gerar token)
├── POST /logout (invalidar token)
└── GET /me (dados do usuário logado)
```

**Subtarefas:**
- [ ] Criar modelo User com hash de senha
- [ ] Implementar JWT tokens (access + refresh)
- [ ] Adicionar user_id foreign key em URL model
- [ ] Criar middleware de autenticação
- [ ] Proteger endpoints (apenas dono pode editar/deletar)
- [ ] Endpoints de registro e login
- [ ] Testes de autenticação e autorização

**Dependências:** Nenhuma
**Estimativa:** 3-5 dias

---

#### 2. Rate Limiting e Proteção contra Abuso
**Status:** Não implementado | **Complexidade:** Média | **Impacto:** Crítico

**Descrição:**
Limitar número de requisições por IP/usuário para prevenir spam e ataques.

**Por quê é crítico:**
- Sem rate limit, vulnerável a ataques DDoS
- Spam de criação de URLs pode encher o banco
- Custo de infra pode explodir sem controle

**Arquitetura:**
```
middleware/rate_limit.py
├── Redis para cache de contadores
├── Limites por endpoint:
│   ├── POST /create-url: 10 req/min por IP
│   ├── GET /{short_code}: 100 req/min por IP
│   └── Outros: 50 req/min por IP
└── Resposta 429 (Too Many Requests)

dependencies:
- redis-py ou slowapi (rate limiter para FastAPI)
```

**Subtarefas:**
- [ ] Instalar e configurar Redis
- [ ] Implementar middleware de rate limiting
- [ ] Configurar limites por endpoint
- [ ] Tratamento de erro 429 padronizado
- [ ] Testes de rate limiting
- [ ] Documentar limites na API

**Dependências:** Redis (cache)
**Estimativa:** 2-3 dias

---

#### 3. Índices de Banco de Dados
**Status:** Não implementado | **Complexidade:** Baixa | **Impacto:** Alto

**Descrição:**
Adicionar índices nos campos mais consultados para otimizar performance.

**Por quê é crítico:**
- Queries em `short_code` são O(n) sem índice
- Redirecionamentos ficam lentos com muitas URLs
- Performance degrada rapidamente em escala

**Arquitetura:**
```sql
-- Índices necessários:
CREATE UNIQUE INDEX idx_urls_short_code ON urls(short_code);
CREATE INDEX idx_urls_user_id ON urls(user_id);
CREATE INDEX idx_urls_created_at ON urls(created_at DESC);
CREATE INDEX idx_clicks_url_id ON clicks(url_id);
CREATE INDEX idx_clicks_clicked_at ON clicks(clicked_at);
```

**Implementação:**
```python
# models/url.py
class URL(Base):
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True)
    short_code = Column(String, unique=True, index=True)  # Índice único
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    created_at = Column(DateTime, index=True)
```

**Subtarefas:**
- [ ] Criar migration para adicionar índices
- [ ] Índice único em short_code
- [ ] Índice em user_id (para filtro por usuário)
- [ ] Índice em created_at (para ordenação)
- [ ] Benchmark antes/depois
- [ ] Documentar ganhos de performance

**Dependências:** Nenhuma
**Estimativa:** 1 dia

---

#### 4. Healthcheck e Observabilidade Básica
**Status:** Não implementado | **Complexidade:** Baixa | **Impacto:** Alto

**Descrição:**
Endpoint de saúde da aplicação e logs estruturados para monitoramento.

**Por quê é crítico:**
- Load balancers precisam saber se app está saudável
- Sem logs estruturados, debug em prod é impossível
- Monitoramento (Datadog, New Relic) precisa de métricas

**Arquitetura:**
```
routes/health.py
├── GET /health
│   ├── Status: "healthy" | "degraded" | "unhealthy"
│   ├── Checks: database, redis, disk space
│   └── Response time: < 100ms
│
└── GET /health/ready (Kubernetes readiness)

utils/logging.py
├── JSON structured logging
├── Request ID tracking
├── Performance metrics
└── Error tracking
```

**Subtarefas:**
- [ ] Criar endpoint GET /health
- [ ] Verificar conexão com banco de dados
- [ ] Verificar conexão com Redis (se implementado)
- [ ] Configurar logs estruturados (JSON)
- [ ] Adicionar request_id a todas as requisições
- [ ] Métricas de performance por endpoint
- [ ] Testes do healthcheck

**Dependências:** Nenhuma
**Estimativa:** 1-2 dias

---

### 🟡 PRIORIDADE ALTA (Escala e Profissionalismo)

> **Objetivo:** Preparar para crescimento e uso profissional

#### 5. Migração para PostgreSQL
**Status:** Usando SQLite | **Complexidade:** Média | **Impacto:** Alto

**Descrição:**
Migrar de SQLite para PostgreSQL para suportar concorrência e escala.

**Por quê é importante:**
- SQLite não suporta alta concorrência
- PostgreSQL tem features avançadas (full-text search, JSON)
- Requisito para maioria dos ambientes de produção

**Arquitetura:**
```
database/
├── config.py (detectar DB_URL do ambiente)
├── migrations/ (Alembic)
└── connection_pool (configuração de pool)

Suporte multi-database:
- SQLite: desenvolvimento/testes
- PostgreSQL: produção
```

**Subtarefas:**
- [ ] Instalar e configurar Alembic (migrations)
- [ ] Criar migration inicial do schema
- [ ] Configurar PostgreSQL via variável de ambiente
- [ ] Connection pool com SQLAlchemy
- [ ] Script de migração de dados
- [ ] Testes com PostgreSQL
- [ ] Documentar setup de database

**Dependências:** Nenhuma
**Estimativa:** 2-3 dias

---

#### 6. Cache Layer (Redis)
**Status:** Não implementado | **Complexidade:** Média | **Impacto:** Alto

**Descrição:**
Cache de URLs frequentemente acessadas para reduzir load no banco.

**Por quê é importante:**
- Redirecionamentos são 90% das requisições
- Cache pode reduzir latência de 50ms para 5ms
- Reduz custos de database reads

**Arquitetura:**
```
services/cache.py
├── get_url_from_cache(short_code) -> URL | None
├── set_url_in_cache(short_code, url_data, ttl=3600)
├── invalidate_url_cache(short_code)
└── Cache Strategy: Cache-Aside Pattern

Fluxo de Redirecionamento:
1. GET /{short_code}
2. Verificar Redis
3. Se hit: retornar + incrementar click_count async
4. Se miss: buscar DB + salvar em cache
```

**Subtarefas:**
- [ ] Configurar Redis connection
- [ ] Implementar cache service layer
- [ ] Cache de redirecionamentos (TTL: 1h)
- [ ] Invalidação ao atualizar/deletar URL
- [ ] Incremento de click_count assíncrono
- [ ] Métricas de cache hit/miss
- [ ] Testes com Redis

**Dependências:** Redis
**Estimativa:** 3-4 dias

---

#### 7. Custom Short Codes (Aliases)
**Status:** Não implementado | **Complexidade:** Média | **Impacto:** Médio

**Descrição:**
Permitir usuários definirem short_code personalizado (ex: `/meublog`).

**Por quê é importante:**
- URLs personalizadas são mais memoráveis
- Feature esperada em serviços profissionais
- Valor agregado para usuários pagantes

**Arquitetura:**
```
POST /create-url
{
  "original_url": "https://example.com",
  "custom_code": "meublog"  // opcional
}

Validações:
- 3-20 caracteres
- Alfanumérico + hífen/underscore
- Não conflitar com rotas da API (/health, /stats, etc)
- Único no banco de dados
```

**Subtarefas:**
- [ ] Adicionar campo custom_code ao schema URLCreate
- [ ] Validação de formato (regex: ^[a-zA-Z0-9_-]{3,20}$)
- [ ] Blacklist de palavras reservadas (api, health, stats, etc)
- [ ] Verificar unicidade antes de salvar
- [ ] Fallback para geração automática se custom ocupado
- [ ] Testes de validação
- [ ] Documentar na API

**Dependências:** Nenhuma
**Estimativa:** 2-3 dias

---

#### 8. Filtros e Ordenação Avançada
**Status:** Parcialmente implementado | **Complexidade:** Média | **Impacto:** Médio

**Descrição:**
Adicionar filtros e ordenação configurável na listagem de URLs.

**Por quê é importante:**
- Usuários precisam encontrar URLs antigas
- Descobrir URLs mais populares
- Análise de uso por período

**Arquitetura:**
```
GET /urls?
  page=1&
  page_size=10&
  sort_by=click_count&        // created_at, click_count, original_url
  order=desc&                  // asc, desc
  created_after=2026-01-01&    // filtro de data
  created_before=2026-12-31&
  min_clicks=10&               // filtro de popularidade
  search=example.com           // busca na URL original
```

**Subtarefas:**
- [ ] Adicionar parâmetros de ordenação (sort_by, order)
- [ ] Filtros por data (created_after, created_before)
- [ ] Filtro por cliques (min_clicks, max_clicks)
- [ ] Busca textual em original_url (LIKE ou full-text)
- [ ] Metadados de paginação (total_pages, has_next, has_previous)
- [ ] Validação de parâmetros
- [ ] Testes de filtros e ordenação

**Dependências:** Índices de banco de dados
**Estimativa:** 2-3 dias

---

### 🟢 PRIORIDADE MÉDIA (Melhorias Significativas)

> **Objetivo:** Analytics avançado e funcionalidades premium

#### 9. Analytics Detalhado - Sistema de Cliques
**Status:** Não implementado | **Complexidade:** Alta | **Impacto:** Alto

**Descrição:**
Histórico detalhado de cada clique com metadata (device, location, referrer).

**Por quê é importante:**
- Usuários querem saber QUANDO e DE ONDE vieram os cliques
- Feature diferenciadora vs. concorrentes
- Base para features premium

**Arquitetura:**
```
models/click.py
├── Click Model
│   ├── id (PK)
│   ├── url_id (FK to urls)
│   ├── clicked_at (timestamp, indexed)
│   ├── ip_address (varchar)
│   ├── user_agent (text)
│   ├── referrer (varchar, nullable)
│   ├── country_code (char(2), nullable)
│   └── device_type (enum: mobile, desktop, tablet, bot)
│
└── Relacionamento: URL hasMany Clicks

Fluxo de Redirecionamento:
1. GET /{short_code}
2. Capturar: IP, User-Agent, Referrer
3. Inserir registro async em clicks table
4. Incrementar click_count (cache)
5. Redirecionar
```

**Endpoints:**
```
GET /stats/{short_code}/clicks?page=1&limit=50
- Lista histórico de cliques com paginação

GET /stats/{short_code}/analytics
- Agregações:
  ├── Cliques por dia/semana/mês
  ├── Top países
  ├── Top referrers
  ├── Distribuição por device
  └── Cliques por hora do dia
```

**Subtarefas:**
- [ ] Criar modelo Click com relacionamento
- [ ] Modificar redirecionamento para salvar clique (async)
- [ ] Parser de User-Agent (biblioteca: user-agents)
- [ ] Geolocalização básica por IP (biblioteca: geoip2)
- [ ] Endpoint GET /stats/{short_code}/clicks
- [ ] Endpoint GET /stats/{short_code}/analytics
- [ ] Agregações e queries otimizadas
- [ ] Índices em clicks (url_id, clicked_at)
- [ ] Testes completos

**Dependências:** Índices de BD, PostgreSQL (recomendado)
**Estimativa:** 5-7 dias

---

#### 10. Expiração de URLs (TTL)
**Status:** Não implementado | **Complexidade:** Média | **Impacto:** Médio

**Descrição:**
URLs com tempo de vida definido, expirando automaticamente.

**Por quê é importante:**
- Links temporários (promoções, eventos)
- Conformidade com GDPR (retenção de dados)
- Limpeza automática de URLs antigas

**Arquitetura:**
```
models/url.py
├── expires_at (datetime, nullable, indexed)
└── is_expired property (computed)

Validação no Redirecionamento:
if url.expires_at and url.expires_at < datetime.now():
    raise URLExpiredError()

Job de Limpeza:
- Cronjob diário: DELETE urls WHERE expires_at < NOW()
- Ou: Soft delete (is_deleted flag)
```

**Subtarefas:**
- [ ] Adicionar campo expires_at ao modelo URL
- [ ] Aceitar TTL em POST /create-url (opcional)
- [ ] Validar expiração no redirecionamento
- [ ] Endpoint GET /urls com filtro de expirados
- [ ] Script/job de limpeza automática
- [ ] Testes de expiração
- [ ] Documentar TTL na API

**Dependências:** Nenhuma
**Estimativa:** 2-3 dias

---

#### 11. Validação de URLs Maliciosas
**Status:** Não implementado | **Complexidade:** Média | **Impacto:** Médio

**Descrição:**
Verificar URLs contra blacklist de sites maliciosos/phishing.

**Por quê é importante:**
- Proteger usuários finais
- Evitar que serviço seja usado para phishing
- Requisito legal em alguns países

**Arquitetura:**
```
services/url_validator.py
├── check_against_blacklist(url) -> bool
├── check_google_safe_browsing(url) -> bool
└── validate_domain_reputation(url) -> bool

Integrações:
- Google Safe Browsing API
- PhishTank API
- Lista local de domínios bloqueados

Fluxo:
1. POST /create-url
2. Validar sintaxe (já existe)
3. Validar contra blacklist
4. Se malicioso: retornar 400 + mensagem
```

**Subtarefas:**
- [ ] Criar blacklist local de domínios
- [ ] Integração com Google Safe Browsing API
- [ ] Validação assíncrona em background
- [ ] Flag is_validated no modelo
- [ ] Endpoint admin para gerenciar blacklist
- [ ] Logs de URLs bloqueadas
- [ ] Testes de validação

**Dependências:** Google API Key
**Estimativa:** 3-4 dias

---

#### 12. Logs Estruturados e Métricas
**Status:** Logs básicos | **Complexidade:** Média | **Impacto:** Alto

**Descrição:**
Sistema completo de logging e métricas para observabilidade.

**Por quê é importante:**
- Debug de problemas em produção
- Monitoramento de performance
- Alertas proativos de problemas

**Arquitetura:**
```
utils/logger.py
├── Structured JSON logging
├── Contexto por requisição (request_id)
├── Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL
└── Integração com ELK, Datadog, CloudWatch

Métricas (Prometheus):
├── request_duration_seconds (histogram)
├── request_count_total (counter)
├── active_urls_total (gauge)
├── cache_hit_rate (gauge)
└── database_connection_pool (gauge)
```

**Subtarefas:**
- [ ] Configurar logging estruturado (structlog)
- [ ] Middleware para request_id
- [ ] Log de todas as operações importantes
- [ ] Configurar Prometheus metrics
- [ ] Endpoint GET /metrics (Prometheus format)
- [ ] Dashboard Grafana básico
- [ ] Documentar observabilidade

**Dependências:** Prometheus (opcional)
**Estimativa:** 3-4 dias

---

### 🔵 PRIORIDADE BAIXA (Nice to Have)

> **Objetivo:** Funcionalidades premium e diferenciação

#### 13. QR Code Generator
**Status:** Não implementado | **Complexidade:** Baixa | **Impacto:** Baixo

**Descrição:**
Gerar QR Code para cada URL encurtada.

**Endpoints:**
```
GET /qr/{short_code}?size=200&format=png
- Retorna imagem do QR Code
```

**Subtarefas:**
- [ ] Biblioteca: qrcode ou segno
- [ ] Endpoint para gerar QR
- [ ] Parâmetros: size, format (png, svg)
- [ ] Cache de QR codes gerados
- [ ] Testes

**Estimativa:** 1 dia

---

#### 14. Preview de Destino
**Status:** Não implementado | **Complexidade:** Baixa | **Impacto:** Baixo

**Descrição:**
Visualizar destino antes de redirecionar (segurança).

**Endpoints:**
```
GET /{short_code}+        // + no final = preview
- Retorna página HTML com destino e botão "Continuar"
```

**Estimativa:** 1-2 dias

---

#### 15. Dashboard Web
**Status:** Não implementado | **Complexidade:** Alta | **Impacto:** Médio

**Descrição:**
Interface web para gerenciar URLs e ver analytics.

**Stack sugerido:**
- React/Next.js
- TailwindCSS
- Charts: Recharts ou Chart.js

**Estimativa:** 10-15 dias

---

## 🏗️ INFRAESTRUTURA E DEVOPS

### Docker e Docker Compose
**Status:** Não implementado | **Complexidade:** Baixa

```yaml
docker-compose.yml:
  - app (FastAPI)
  - database (PostgreSQL)
  - cache (Redis)
  - nginx (reverse proxy)
```

**Estimativa:** 1-2 dias

---

### CI/CD Pipeline
**Status:** Não implementado | **Complexidade:** Média

```yaml
.github/workflows/ci.yml:
  - Lint (flake8, black)
  - Tests (pytest + coverage)
  - Build Docker image
  - Deploy to staging
  - Deploy to production (manual approval)
```

**Estimativa:** 2-3 dias

---

### Deploy em Produção
**Status:** Não implementado | **Complexidade:** Média

**Opções:**
- Railway (mais fácil)
- Render
- AWS ECS/Fargate
- DigitalOcean App Platform

**Estimativa:** 1-2 dias

---

## 📊 ESTIMATIVA TOTAL

| Prioridade | Features | Dias Estimados |
|------------|----------|----------------|
| 🔴 Crítica | 4 features | 8-12 dias |
| 🟡 Alta | 4 features | 11-16 dias |
| 🟢 Média | 4 features | 13-18 dias |
| 🔵 Baixa | 3 features | 12-18 dias |
| 🏗️ Infra | 3 itens | 4-7 dias |
| **TOTAL** | **18 features** | **48-71 dias** |

---

**Última atualização:** 2026-02-04
**Versão atual:** 0.1.0
**Próxima versão planejada:** 0.2.0 (com features críticas)
