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

### Filtros e Ordenacao Avancada
- [x] Ordenacao configuravel (sort_by: created_at, click_count, original_url)
- [x] Direcao de ordenacao (order: asc, desc)
- [x] Busca textual na URL original (search, case-insensitive)
- [x] Filtro por numero de cliques (min_clicks, max_clicks)
- [x] Filtro por data de criacao (created_after, created_before)
- [x] Metadados avancados de paginacao (total_pages, has_next, has_previous)
- [x] Metadados de filtros aplicados na resposta
- [x] Validacao robusta de parametros (InvalidFilterError)
- [x] Testes completos de filtros e ordenacao (35 novos testes)

---

## 🎯 ROADMAP - Features Pendentes

### 🔴 PRIORIDADE CRÍTICA (Bloqueadores para Produção)

> **Objetivo:** Tornar a aplicação segura e pronta para uso em produção

#### 1. Autenticação e Autorização
**Status:** Em desenvolvimento | **Complexidade:** Alta | **Impacto:** Crítico
**Branch:** `feature/autenticacao`

**Descrição:**
Sistema completo de autenticação para controlar acesso às URLs e operações.

**Por quê é crítico:**
- Sem auth, qualquer pessoa pode deletar/editar URLs de outros
- Impossível rastrear quem criou cada URL
- Sem controle de acesso ou quotas por usuário

---

### 📋 Plano de Implementação (Subtarefas)

#### **Fase 1: Modelo de Dados e Dependências** (Dia 1) ✅ **CONCLUÍDO**
**Objetivo:** Preparar a base de dados e instalar dependências

- [x] **1.1** - Instalar dependências ✅ **[Commit: fcb41c8]**
  - `python-jose[cryptography]` (JWT) - v3.5.0
  - `passlib[bcrypt]` (hash de senha) - v1.7.4
  - `python-multipart` (form data)
  - Atualizar `requirements.txt`
  
- [x] **1.2** - Criar modelo User (`models/user.py`) ✅ **[Commit: c81696c]**
  - Campos: id, email, password_hash, created_at, is_active, is_verified
  - Unique constraint em email
  - Índice em email
  - Métodos: `verify_password()`, `set_password()`
  
- [x] **1.3** - Adicionar relacionamento User-URL ✅ **[Commit: 7b907c9]**
  - Adicionar `user_id` (FK) no modelo URL
  - Relacionamento: `user = relationship("User", back_populates="urls")`
  - Migration para adicionar coluna (nullable=True inicialmente)
  
- [x] **1.4** - Criar schemas Pydantic (`schemas/user.py`) ✅ **[Commit: 06b06bb]**
  - `UserCreate` (email, password com min 8 chars)
  - `UserLogin` (email, password)
  - `UserResponse` (id, email, created_at, is_active, is_verified)
  - `Token` (access_token, token_type)
  - `TokenData` (email: Optional[str])
  - Adiciona `email-validator` para validação de EmailStr

**Estimativa:** 4-6 horas | **Tempo Real:** ~4 horas

---

#### **Fase 2: Autenticação JWT** (Dia 2)
**Objetivo:** Implementar geração e validação de tokens JWT

- [ ] **2.1** - Criar utilitário de senha (`utils/security.py`)
  - `hash_password(password: str) -> str`
  - `verify_password(plain_password: str, hashed_password: str) -> bool`
  - Configurar bcrypt rounds (default: 12)
  
- [ ] **2.2** - Criar utilitário JWT (`utils/jwt.py`)
  - `create_access_token(data: dict, expires_delta: Optional[timedelta]) -> str`
  - `decode_access_token(token: str) -> TokenData`
  - Configurar SECRET_KEY via env (gerar com secrets.token_urlsafe)
  - Configurar ALGORITHM (HS256)
  - Configurar ACCESS_TOKEN_EXPIRE_MINUTES (30 padrão)
  
- [ ] **2.3** - Criar dependency para autenticação (`dependencies/auth.py`)
  - `get_current_user(token: str = Depends(oauth2_scheme)) -> User`
  - `get_current_active_user(user: User = Depends(get_current_user)) -> User`
  - OAuth2PasswordBearer(tokenUrl="/auth/login")
  
- [ ] **2.4** - Adicionar variáveis de ambiente
  - `SECRET_KEY` (obrigatório, sem default)
  - `ALGORITHM` (default: HS256)
  - `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30)
  - Documentar no `.env.example`

**Estimativa:** 4-5 horas

---

#### **Fase 3: Rotas de Autenticação** (Dia 2-3)
**Objetivo:** Criar endpoints de registro e login

- [ ] **3.1** - Criar service de usuário (`services/user.py`)
  - `create_user(user_data: UserCreate, db: Session) -> User`
  - `get_user_by_email(email: str, db: Session) -> Optional[User]`
  - `authenticate_user(email: str, password: str, db: Session) -> Optional[User]`
  - Validações: email único, senha forte (min 8 chars)
  
- [ ] **3.2** - Criar rotas de autenticação (`routes/auth.py`)
  - `POST /auth/register` - Criar conta
  - `POST /auth/login` - Login (retorna token)
  - `GET /auth/me` - Dados do usuário logado (protegida)
  - Rate limit especial: 5 req/min para login/register
  
- [ ] **3.3** - Adicionar exception customizada
  - `CredentialsError` (401 Unauthorized)
  - `EmailAlreadyExistsError` (409 Conflict)
  - `WeakPasswordError` (400 Bad Request)
  
- [ ] **3.4** - Registrar router no main.py
  - `app.include_router(auth_router)`
  - Tag: "Authentication"

**Estimativa:** 5-6 horas

---

#### **Fase 4: Proteção de Rotas Existentes** (Dia 3-4)
**Objetivo:** Adicionar autenticação opcional aos endpoints

- [ ] **4.1** - Atualizar URLService
  - Adicionar `user_id` opcional ao `shorten_url()`
  - Validar propriedade em `update_url()` e `delete_url()`
  - Método `is_owner(url_id: int, user_id: int, db: Session) -> bool`
  
- [ ] **4.2** - Proteger rotas de modificação (PATCH/DELETE /urls/{id})
  - Adicionar `current_user = Depends(get_current_user)` 
  - Verificar se user é dono antes de modificar
  - Retornar 403 Forbidden se não for dono
  
- [ ] **4.3** - Tornar autenticação opcional para criação
  - POST /create-url pode ser anônimo OU autenticado
  - Se autenticado, salvar user_id
  - `current_user: Optional[User] = Depends(get_current_user_optional)`
  
- [ ] **4.4** - Atualizar listagem para filtrar por usuário
  - GET /urls?my_urls=true (apenas URLs do usuário logado)
  - Requer autenticação para usar filtro

**Estimativa:** 4-5 horas

---

#### **Fase 5: Testes Automatizados** (Dia 4-5)
**Objetivo:** Garantir qualidade e cobertura de testes

- [ ] **5.1** - Criar fixtures de teste (`tests/conftest.py`)
  - `test_user` (usuário de teste)
  - `test_user_token` (token válido)
  - `authenticated_client` (cliente com auth)
  
- [ ] **5.2** - Testes do modelo User (`tests/test_user_model.py`)
  - Criar usuário com senha hasheada
  - Verificar senha correta/incorreta
  - Validar unique constraint de email
  
- [ ] **5.3** - Testes de autenticação (`tests/test_auth.py`)
  - Registro com sucesso
  - Registro com email duplicado
  - Login com credenciais válidas
  - Login com credenciais inválidas
  - Acesso a /auth/me com token válido
  - Acesso a /auth/me sem token (401)
  - Token expirado (401)
  
- [ ] **5.4** - Testes de autorização (`tests/test_authorization.py`)
  - Deletar URL própria (sucesso)
  - Deletar URL de outro usuário (403)
  - Atualizar URL própria (sucesso)
  - Atualizar URL de outro usuário (403)
  - Listar apenas URLs próprias

**Estimativa:** 6-8 horas

---

#### **Fase 6: Documentação e Ajustes Finais** (Dia 5)
**Objetivo:** Documentar e refinar a implementação

- [ ] **6.1** - Atualizar documentação da API (`docs/API.md`)
  - Seção de autenticação
  - Exemplos de uso com Bearer token
  - Códigos de erro (401, 403, 409)
  
- [ ] **6.2** - Atualizar arquivo ARQUITETURA.md
  - Adicionar seção de autenticação
  - Diagrama de fluxo de login
  - Explicar JWT e segurança
  
- [ ] **6.3** - Criar migration para produção
  - Script para popular user_id em URLs existentes (NULL ou user padrão)
  - Documentar como rodar migration
  
- [ ] **6.4** - Validar todos os testes
  - Rodar suite completa
  - Verificar cobertura (mínimo 80%)
  - Corrigir warnings e deprecations

**Estimativa:** 3-4 horas

---

### 📊 Resumo de Esforço

| Fase | Descrição | Tempo Estimado | Complexidade |
|------|-----------|----------------|--------------|
| 1 | Modelo de Dados | 4-6h | Média |
| 2 | JWT e Segurança | 4-5h | Média |
| 3 | Rotas de Auth | 5-6h | Média |
| 4 | Proteção de Rotas | 4-5h | Alta |
| 5 | Testes | 6-8h | Média |
| 6 | Documentação | 3-4h | Baixa |
| **TOTAL** | **26-34 horas** | **3-5 dias** | **Alta** |

---

### 🔧 Variáveis de Ambiente Necessárias

```bash
# .env
SECRET_KEY=<gerar_com_secrets.token_urlsafe(32)>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

### 📦 Dependências a Instalar

```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

---

### ⚠️ Observações Importantes

1. **SECRET_KEY**: Nunca commitar a chave secreta. Deve ser gerada em produção.
2. **Backward Compatibility**: URLs existentes ficam sem user_id (NULL), funcionam normalmente.
3. **Autenticação Opcional**: POST /create-url não requer auth para não quebrar uso atual.
4. **Rate Limiting**: Login/register tem limite mais restrito (5 req/min).
5. **Token Expiration**: Considerar refresh token em versão futura.

---

**Dependências:** Nenhuma
**Estimativa Total:** 3-5 dias (26-34 horas)
**Branch:** `feature/autenticacao`

---

#### 2. Rate Limiting e Proteção contra Abuso
**Status:** ✅ Implementado | **Complexidade:** Média | **Impacto:** Crítico

**Descrição:**
Limitar número de requisições por IP/usuário para prevenir spam e ataques.

**Por quê é crítico:**
- Sem rate limit, vulnerável a ataques DDoS
- Spam de criação de URLs pode encher o banco
- Custo de infra pode explodir sem controle

**Arquitetura:**
```
middleware/rate_limit.py
├── Suporte a Redis (produção) ou memória (desenvolvimento)
├── Limites por endpoint:
│   ├── POST /create-url: 10 req/min por IP
│   ├── GET /{short_code}: 100 req/min por IP
│   └── Outros: 50 req/min por IP
└── Resposta 429 (Too Many Requests)

dependencies:
- slowapi==0.1.9 (rate limiter para FastAPI)
- limits==3.12.0 (backend de limites)
```

**Subtarefas:**
- [x] Instalar slowapi e limits
- [x] Implementar middleware de rate limiting
- [x] Configurar limites por endpoint
- [x] Tratamento de erro 429 padronizado
- [x] Suporte a Redis (via variável REDIS_URL) - Preparado para produção
- [x] Limites configuráveis via variáveis de ambiente
- [ ] Testes de rate limiting

**Variáveis de ambiente:**
- `REDIS_URL`: URL do Redis (opcional, usa memória se não configurado)
  - **Desenvolvimento:** Não precisa configurar - usa memória automaticamente
  - **Produção:** Configure com URL do seu servidor Redis
  - **Formato:** `redis://localhost:6379` ou `redis://user:senha@host:6379/0`
- `RATE_LIMIT_CREATE_URL`: Limite para criação (padrão: "10/minute")
- `RATE_LIMIT_REDIRECT`: Limite para redirecionamento (padrão: "100/minute")
- `RATE_LIMIT_DEFAULT`: Limite padrão (padrão: "50/minute")

**Dependências:** Redis (opcional para produção)
**Estimativa:** 2-3 dias

---

#### 3. Índices de Banco de Dados
**Status:** ✅ Implementado | **Complexidade:** Baixa | **Impacto:** Alto

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
- [x] Criar migration para adicionar índices
- [x] Índice único em short_code
- [x] Índice em click_count (para ordenação por popularidade)
- [x] Índice em created_at (para ordenação)
- [x] Índices compostos para ordenação DESC
- [ ] Índice em user_id (aguardando implementação de autenticação)
- [ ] Benchmark antes/depois
- [ ] Documentar ganhos de performance

**Dependências:** Nenhuma
**Estimativa:** 1 dia

---

#### 4. Healthcheck e Observabilidade Básica
**Status:** ✅ Implementado | **Complexidade:** Baixa | **Impacto:** Alto

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
- [x] Criar endpoint GET /health
- [x] Verificar conexão com banco de dados
- [x] Verificar conexão com Redis (se implementado) - Preparado para futura implementação
- [x] Configurar logs estruturados (JSON)
- [x] Adicionar request_id a todas as requisições
- [x] Métricas de performance por endpoint
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
**Versão atual:** 0.1.1
**Próxima versão planejada:** 0.2.0 (com features críticas)
