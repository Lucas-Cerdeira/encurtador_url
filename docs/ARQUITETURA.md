# Arquitetura do Projeto

## Visão Geral

Este documento descreve a arquitetura técnica do sistema de encurtamento de URLs.

---

## Arquitetura em Camadas

O projeto segue uma **arquitetura em camadas** (Layered Architecture) com separação clara de responsabilidades:

```
┌─────────────────────────────────────┐
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

**Padrões Implementados:**
- **Retry Pattern**: Retry automático em caso de colisão de `short_code`
- **Error Handling**: Tratamento centralizado de erros
- **Logging**: Registro de operações importantes

---

### 6. Routes Layer (`routes/`)

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
4. Gera short_code (NanoID)
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

### Algoritmo: NanoID

**Características:**
- Tamanho: 8 caracteres
- Alfabeto: URL-safe (A-Za-z0-9_-)
- Colisão: ~2.3 milhões de IDs necessários para 1% de chance de colisão

**Implementação:**
```python
from nanoid import generate

short_code = generate(size=8)  # Ex: "V1StGXR8"
```

**Tratamento de Colisão:**
- Retry automático até 5 tentativas
- Rollback de transação em caso de `IntegrityError`
- Log de warnings para monitoramento

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

### Carregamento

```python
from dotenv import load_dotenv
load_dotenv()  # Carrega .env

URL_BASE = os.getenv("URL_BASE", "http://localhost:8000/")
```

---

## Logging

### Estratégia

- **Biblioteca:** `logging` (padrão Python)
- **Níveis:** INFO, WARNING, ERROR
- **Formato:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Eventos Logados

| Evento | Nível |
|--------|-------|
| Aplicação iniciada | INFO |
| URL criada | INFO |
| Listagem de URLs | INFO |
| URL atualizada | INFO |
| URL deletada | INFO |
| Colisão de short_code | WARNING |
| Erro ao incrementar cliques | ERROR |
| Erro ao atualizar/deletar | ERROR |

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

- [ ] Cache de URLs mais acessadas (Redis)
- [ ] Índice composto para queries complexas
- [ ] Batch operations para bulk insert
- [ ] Read replicas para escalabilidade

---

## Segurança

### Implementado

✅ Validação de entrada (Pydantic)
✅ SQL Injection (proteção via ORM)
✅ Variáveis de ambiente para configuração

### Futuro

- [ ] Rate limiting (proteção contra DDoS)
- [ ] Autenticação e autorização
- [ ] HTTPS obrigatório
- [ ] Blacklist de domínios maliciosos
- [ ] CORS configurado

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

**Última Atualização:** 2026-01-22  
**Versão:** 0.0.1
