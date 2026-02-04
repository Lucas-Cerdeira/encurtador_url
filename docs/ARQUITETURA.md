# Arquitetura do Projeto

## Visão Geral

Este documento descreve a arquitetura técnica do sistema de encurtamento de URLs.

---

## Arquitetura em Camadas

O projeto segue uma **arquitetura em camadas** (Layered Architecture) com separação clara de responsabilidades:

```
┌─────────────────────────────────────┐
│         Middleware Layer            │
│         (middleware/)               │
│  - Request ID tracking              │
│  - Métricas de performance          │
│  - Logging de requisições           │
│  - Rate Limiting                    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│         Presentation Layer          │
│           (routes/)                 │
│  - Endpoints REST                   │
│  - Validação de entrada (Pydantic)  │
│  - Serialização de resposta         │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│         Business Logic Layer        │
│          (services/)                │
│  - Lógica de negócio                │
│  - Tratamento de erros              │
│  - Geração de short_code            │
│  - Health checks                    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│         Data Access Layer           │
│        (models/, database/)         │
│  - ORM (SQLAlchemy)                 │
│  - Conexão com banco                │
│  - Queries                          │
└─────────────────────────────────────┘
```

---

## Componentes Principais

### 1. Main Application (`main.py`)

Ponto de entrada da aplicação FastAPI.

**Responsabilidades:**
- Inicialização da aplicação FastAPI
- Carregamento de variáveis de ambiente
- Registro de routers
- Criação das tabelas no banco
- Configuração de logging

```python
app = FastAPI(
    title="Encurtador de URL",
    version=__version__,
    description="API para encurtamento de URLs com estatísticas"
)
```

---

### 2. Database Layer (`database/`)

Gerencia a conexão e sessões do banco de dados.

**Componentes:**
- **Engine**: Motor de conexão SQLAlchemy
- **SessionLocal**: Factory de sessões
- **Base**: Classe base para modelos ORM
- **get_db()**: Dependency Injection para rotas

**Padrão:** Dependency Injection
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 3. Models Layer (`models/`)

Define os modelos ORM (Object-Relational Mapping).

**URL Model:**
```python
class URL(Base):
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)
    original_url = Column(String, index=True)
    click_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Características:**
- Índices para performance (`id`, `short_code`, `original_url`)
- Constraint de unicidade em `short_code`
- Campos com valores padrão

---

### 4. Schemas Layer (`schemas/`)

Define schemas Pydantic para validação e serialização.

**Schemas Disponíveis:**

| Schema | Uso |
|--------|-----|
| `URLCreate` | Criação de URL (input) |
| `URLUpdate` | Atualização de URL (input) |
| `URLResponse` | Resposta individual (output) |
| `URLListResponse` | Resposta de listagem (output) |
| `URL` | Schema base |

**Exemplo:**
```python
class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    click_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

---

### 5. Services Layer (`services/`)

Contém a lógica de negócio da aplicação.

**URLService:**

| Método | Responsabilidade |
|--------|------------------|
| `shorten_url()` | Criar URL encurtada com retry de colisão |
| `get_original_url()` | Buscar URL original e incrementar cliques |
| `get_url_stats()` | Retornar estatísticas de URL |
| `list_urls()` | Listar URLs com paginação |
| `update_url()` | Atualizar URL original |
| `delete_url()` | Deletar URL |

**HealthService:**

| Método | Responsabilidade |
|--------|------------------|
| `check_database()` | Verificar conectividade com banco de dados |
| `check_redis()` | Verificar conectividade com Redis (preparado) |
| `get_health()` | Retornar status completo de saúde |
| `get_readiness()` | Verificar se aplicação está pronta |
| `get_liveness()` | Verificar se aplicação está viva |

**Padrões Implementados:**
- **Retry Pattern**: Retry automático em caso de colisão de `short_code`
- **Error Handling**: Tratamento centralizado de erros
- **Logging**: Registro de operações importantes

---

### 6. Utils Layer (`utils/`)

Contém utilitários e helpers reutilizáveis.

**HashGenerator:**

Gerador de hash customizado usando Base 62 para criação de códigos curtos únicos.

**Características:**
- **Base 62**: Alfabeto com 62 caracteres (A-Z, a-z, 0-9)
- **Tamanho configurável**: 1 a 6 caracteres (padrão: 6)
- **Segurança**: Usa `secrets.SystemRandom()` para geração criptograficamente segura
- **Validação**: Método para validar formato de hash
- **Escalável**: Fácil extensão para outros algoritmos

**Métodos Principais:**

| Método | Descrição |
|--------|-----------|
| `generate(size)` | Gera hash aleatório de tamanho especificado |
| `validate(hash_code)` | Valida se hash está no formato correto |
| `get_max_combinations(size)` | Calcula combinações máximas para um tamanho |
| `get_alphabet()` | Retorna alfabeto Base 62 usado |

**Exemplo:**
```python
from utils.hash_generator import HashGenerator

generator = HashGenerator(default_size=6)
hash_code = generator.generate()  # Ex: "aB3xY9"
is_valid = generator.validate("aB3xY9")  # True
```

**Estatísticas:**
- **6 caracteres**: 62^6 = 56.800.235.584 combinações
- **Probabilidade de colisão**: Extremamente baixa
- **Retry automático**: Implementado no `URLService` em caso de colisão

---

**Logger (Sistema de Logging Estruturado):**

Sistema de logging que suporta formato JSON para produção e formato colorido para desenvolvimento.

**Características:**
- **JSON Format**: Logs estruturados para ELK, Datadog, CloudWatch
- **Console Format**: Logs coloridos para desenvolvimento
- **Request ID**: Tracking de requisições com UUID
- **Context Variables**: Contexto adicional por requisição

**Componentes:**

| Componente | Descrição |
|------------|-----------|
| `JSONFormatter` | Formata logs em JSON estruturado |
| `ConsoleFormatter` | Formata logs coloridos para console |
| `setup_logging()` | Configura o sistema de logging |
| `get_logger()` | Obtém logger para um módulo |
| `LogContext` | Context manager para adicionar contexto aos logs |

**Exemplo:**
```python
from utils.logger import get_logger, LogContext

logger = get_logger(__name__)

# Log simples
logger.info("Operação realizada")

# Log com contexto
with LogContext(user_id="123", action="create"):
    logger.info("Criando recurso")  # Inclui user_id e action
```

**Formato JSON (produção):**
```json
{
  "timestamp": "2026-02-04T12:00:00Z",
  "level": "INFO",
  "logger": "encurtador_url.services.url",
  "message": "URL criada com sucesso",
  "request_id": "a1b2c3d4-e5f6-...",
  "context": {"method": "POST", "path": "/create-url"}
}
```

---

### 7. Middleware Layer (`middleware/`)

Middlewares que processam requisições antes de chegarem às rotas.

**RequestContextMiddleware:**

Middleware responsável por observabilidade e rastreamento de requisições.

**Funcionalidades:**
- **Request ID**: Gera UUID único para cada requisição
- **Performance Metrics**: Mede tempo de processamento
- **Headers de Resposta**: Adiciona `X-Request-ID` e `X-Response-Time`
- **Logging Automático**: Loga início e fim de cada requisição
- **IP Real**: Suporta `X-Forwarded-For` e `X-Real-IP`

**Headers Adicionados:**

| Header | Descrição | Exemplo |
|--------|-----------|---------|
| `X-Request-ID` | ID único da requisição | `a1b2c3d4-e5f6-...` |
| `X-Response-Time` | Tempo de processamento | `15.32ms` |

**Exemplo de Uso:**
```python
from middleware import RequestContextMiddleware

app.add_middleware(RequestContextMiddleware)
```

**Fluxo:**
```
1. Requisição chega
2. Gera/obtém X-Request-ID
3. Configura contexto de logging
4. Log de início (exceto health checks)
5. Processa requisição
6. Calcula tempo de resposta
7. Adiciona headers de rastreabilidade
8. Log de fim (exceto health checks)
9. Retorna resposta
```

---

**RateLimitMiddleware:**

Middleware responsável por limitar requisições por IP para proteção contra abusos.

**Funcionalidades:**
- **Limites por Endpoint**: Diferentes limites para diferentes rotas
- **Armazenamento**: Redis (produção) ou memória (desenvolvimento)
- **IP Detection**: Suporta proxies reversos (`X-Forwarded-For`, `X-Real-IP`)
- **Resposta 429**: Retorna erro padronizado quando limite é excedido

**Limites Configurados:**

| Endpoint | Limite | Descrição |
|----------|--------|-----------|
| `POST /create-url` | 10 req/min | Criação de URLs |
| `GET /{short_code}` | 100 req/min | Redirecionamentos |
| Outros | 50 req/min | Endpoints gerais |
| Health checks | Sem limite | `/health/*` |

**Backend de Armazenamento:**

- **Desenvolvimento (padrão):** Armazenamento em memória (`memory://`)
- **Produção (opcional):** Redis (`redis://...`) - configure via `REDIS_URL`

**Configuração:**

```python
# middleware/rate_limit.py
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[RateLimitConfig.DEFAULT],
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    strategy="fixed-window"
)
```

**Variáveis de Ambiente:**

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `REDIS_URL` | URL do Redis (opcional) | `memory://` |
| `RATE_LIMIT_CREATE_URL` | Limite para criação | `10/minute` |
| `RATE_LIMIT_REDIRECT` | Limite para redirecionamento | `100/minute` |
| `RATE_LIMIT_DEFAULT` | Limite padrão | `50/minute` |

**Formato da URL do Redis:**

```
redis://localhost:6379                    # Local sem senha
redis://:senha@localhost:6379            # Local com senha
redis://user:senha@host:6379/0          # Com usuário, senha e database
redis://default:abc123@redis.railway.app:6379  # Exemplo de cloud
```

**Exemplo de Uso:**

```python
from middleware.rate_limit import limiter, RateLimitConfig

@router.post("/create-url")
@limiter.limit(RateLimitConfig.CREATE_URL)
def create_url(request: Request, ...):
    ...
```

**Resposta de Erro 429:**

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Limite de requisições excedido. Tente novamente mais tarde.",
    "retry_after_seconds": 60
  }
}
```

---

### 8. Routes Layer (`routes/`)

Define os endpoints da API REST.

**Características:**
- Validação automática via Pydantic
- Dependency Injection de sessão DB
- Documentação automática (docstrings)
- Type hints completos

**Exemplo:**
```python
@router.get("/urls", response_model=URLListResponse)
def list_urls(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    result = URLService().list_urls(db, page, page_size)
    return result
```

---

## Fluxo de Dados

### Criação de URL Encurtada

```
1. Cliente → POST /create-url
             ↓
2. Route valida payload (Pydantic)
             ↓
3. URLService.shorten_url()
             ↓
4. Gera short_code (HashGenerator - Base 62)
             ↓
5. Tenta salvar no banco
   ├─ Sucesso → Retorna URL encurtada
   └─ IntegrityError → Retry (até 5x)
```

### Redirecionamento

```
1. Cliente → GET /{short_code}
             ↓
2. URLService.get_original_url()
             ↓
3. Busca URL no banco
   ├─ Encontrado → Incrementa click_count
   └─ Não encontrado → 404
             ↓
4. RedirectResponse(url=original_url)
```

---

## Banco de Dados

### Estratégia

- **Desenvolvimento:** SQLite (arquivo `app.db`)
- **Testes:** SQLite in-memory
- **Produção:** PostgreSQL (futuro)

### Schema

```sql
CREATE TABLE urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code VARCHAR UNIQUE NOT NULL,
    original_url VARCHAR NOT NULL,
    click_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_short_code ON urls(short_code);
CREATE INDEX idx_original_url ON urls(original_url);
```

---

## Geração de Short Code

### Algoritmo: HashGenerator (Base 62)

**Características:**
- Tamanho: 6 caracteres (configurável entre 1-6)
- Alfabeto: Base 62 (A-Z, a-z, 0-9) = 62 caracteres
- Combinações: 62^6 = **56.800.235.584** combinações possíveis
- Colisão: Probabilidade extremamente baixa (1 em 56 bilhões)
- Segurança: Geração criptograficamente segura usando `secrets.SystemRandom()`

**Implementação:**
```python
from utils.hash_generator import HashGenerator

generator = HashGenerator(default_size=6)
short_code = generator.generate()  # Ex: "aB3xY9"
```

**Tratamento de Colisão:**
- Retry automático até 5 tentativas
- Rollback de transação em caso de `IntegrityError`
- Log de warnings para monitoramento
- Exception `ShortCodeGenerationError` após esgotar tentativas

**Vantagens:**
- ✅ Mais curto (6 vs 8 caracteres)
- ✅ Alfabeto mais simples (sem caracteres especiais)
- ✅ Escalável e extensível
- ✅ Validação integrada

---

## Tratamento de Erros

### Estratégia

1. **Validação de Entrada:** Pydantic (automático)
2. **Erros de Negócio:** HTTPException no service
3. **Erros de Banco:** Try/catch com rollback
4. **Logging:** Registro de erros para debug

### Exemplo

```python
try:
    url.original_url = str(original_url)
    db.commit()
except Exception as e:
    db.rollback()
    logger.error(f"Erro ao atualizar URL {url_id}: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Erro interno ao atualizar a URL"
    )
```

---

## Testes

### Arquitetura de Testes

```
tests/
├── conftest.py          # Fixtures compartilhadas
├── test_routes.py       # Testes de integração (API)
└── test_service_url.py  # Testes unitários (lógica)
```

### Fixtures Principais

**`db_session`:** Banco SQLite in-memory
```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
```

**`client`:** Cliente de teste FastAPI
```python
@pytest.fixture
def client(app):
    return TestClient(app)
```

### Isolamento

- Cada teste usa banco novo em memória
- Nenhum estado compartilhado entre testes
- Uso de `monkeypatch` para mocks

---

## Configuração e Variáveis de Ambiente

### Gerenciamento

- **Biblioteca:** `python-dotenv`
- **Arquivo:** `.env` (não versionado)
- **Exemplo:** `.env.example` (versionado)

### Variáveis

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `URL_BASE` | URL base para URLs encurtadas | `http://localhost:8000/` |
| `LOG_LEVEL` | Nível de log (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `JSON_LOGS` | Ativar logs em formato JSON | `false` |
| `CORS_ORIGINS` | Origens permitidas para CORS | `http://localhost:5173,...` |
| `REDIS_URL` | URL do Redis para rate limiting (opcional) | `memory://` |
| `RATE_LIMIT_CREATE_URL` | Limite para criação de URLs | `10/minute` |
| `RATE_LIMIT_REDIRECT` | Limite para redirecionamentos | `100/minute` |
| `RATE_LIMIT_DEFAULT` | Limite padrão | `50/minute` |

### Carregamento

```python
from dotenv import load_dotenv
load_dotenv()  # Carrega .env

URL_BASE = os.getenv("URL_BASE", "http://localhost:8000/")
```

---

## Logging

### Estratégia

- **Biblioteca:** `logging` (padrão Python) com formatters customizados
- **Níveis:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Formatos:** JSON (produção) ou Console colorido (desenvolvimento)
- **Request ID:** Tracking de requisições com UUID

### Configuração via Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `LOG_LEVEL` | Nível de log | `INFO` |
| `JSON_LOGS` | Formato JSON | `false` |

### Eventos Logados

| Evento | Nível |
|--------|-------|
| Aplicação iniciada | INFO |
| Request started | INFO |
| Request completed | INFO |
| URL criada | INFO |
| Listagem de URLs | INFO |
| URL atualizada | INFO |
| URL deletada | INFO |
| Colisão de short_code | WARNING |
| Request com erro 4xx | WARNING |
| Erro ao incrementar cliques | ERROR |
| Erro ao atualizar/deletar | ERROR |
| Request failed | ERROR |

### Formato JSON (Produção)

```json
{
  "timestamp": "2026-02-04T12:00:00Z",
  "level": "INFO",
  "logger": "encurtador_url.routes.create_url",
  "message": "Request completed: POST /create-url - 200 (15.32ms)",
  "request_id": "a1b2c3d4-e5f6-...",
  "context": {
    "method": "POST",
    "path": "/create-url",
    "client_ip": "192.168.1.1"
  },
  "extra": {
    "event": "request_complete",
    "status_code": 200,
    "response_time_ms": 15.32
  }
}
```

### Formato Console (Desenvolvimento)

```
2026-02-04 12:00:00 | INFO     [a1b2c3d4] | encurtador_url.middleware | Request completed: POST /create-url - 200 (15.32ms)
```

---

## Performance

### Otimizações Implementadas

1. **Índices de Banco:**
   - `short_code` (único): Busca rápida no redirecionamento
   - `original_url`: Queries de busca
   - `id`: Chave primária

2. **Paginação:**
   - Limite de 100 itens por página
   - Offset para navegação eficiente

3. **Connection Pooling:**
   - SQLAlchemy gerencia pool de conexões
   - Reutilização de conexões

### Melhorias Futuras

- [ ] Cache de URLs mais acessadas (Redis) - Redis já disponível para rate limiting
- [ ] Índice composto para queries complexas
- [ ] Batch operations para bulk insert
- [ ] Read replicas para escalabilidade

---

## Segurança

### Implementado

✅ Validação de entrada (Pydantic)
✅ SQL Injection (proteção via ORM)
✅ Variáveis de ambiente para configuração
✅ Rate limiting (proteção contra DDoS)
✅ CORS configurado

### Futuro

- [ ] Autenticação e autorização
- [ ] HTTPS obrigatório
- [ ] Blacklist de domínios maliciosos

---

## Escalabilidade

### Arquitetura Atual

- **Stateless:** Sem estado na aplicação
- **Horizontal Scale:** Possível adicionar mais instâncias
- **Database:** Bottleneck potencial

### Estratégias Futuras

1. **Load Balancer:** Distribuir carga entre instâncias
2. **Database Replication:** Master-slave para leitura
3. **Caching Layer:** Redis para URLs populares
4. **CDN:** Distribuição geográfica

---

## Deployment

### Desenvolvimento

```bash
uvicorn main:app --reload
```

### Produção (Sugestão)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

ou usar Gunicorn:

```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Containerização (Futuro)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Monitoramento (Futuro)

Sugestões de ferramentas:

- **APM:** New Relic, Datadog
- **Logs:** ELK Stack, CloudWatch
- **Métricas:** Prometheus + Grafana
- **Uptime:** UptimeRobot, Pingdom

---

**Última Atualização:** 2026-02-04  
**Versão:** 0.1.1
