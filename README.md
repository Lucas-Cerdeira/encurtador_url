# Encurtador de URL

API REST para encurtamento de URLs com estatísticas, construída com FastAPI e SQLAlchemy.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Como Rodar](#como-rodar)
- [API Endpoints](#api-endpoints)
- [Modelos de Dados](#modelos-de-dados)
- [Testes](#testes)
- [Padrões de Desenvolvimento](#padrões-de-desenvolvimento)
- [Versionamento](#versionamento)

---

## 🎯 Visão Geral

Este projeto é um encurtador de URLs que permite:
- Criar URLs encurtadas com códigos únicos (hash de 6 caracteres, Base 62)
- Redirecionar para URLs originais
- Rastrear estatísticas de cliques
- Gerenciar URLs (CRUD completo)
- Paginação de resultados

**Versão Atual:** 0.1.1

---

## 🚀 Tecnologias

- **Python 3.12**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **Pydantic** - Validação de dados
- **SQLite** - Banco de dados (desenvolvimento)
- **Pytest** - Framework de testes
- **HashGenerator** - Geração de hash Base 62 (A-Z, a-z, 0-9)
- **python-dotenv** - Gerenciamento de variáveis de ambiente

---

## 📁 Estrutura do Projeto

```
encurtador_url/
├── database/           # Configuração do banco de dados
│   ├── __init__.py
│   └── database.py     # Engine e sessões SQLAlchemy
├── models/             # Modelos SQLAlchemy (ORM)
│   ├── __init__.py
│   └── url.py          # Modelo URL
├── schemas/            # Schemas Pydantic (validação)
│   ├── __init__.py
│   ├── url.py          # Schemas de URL
│   └── health.py       # Schemas de Health Check
├── services/           # Lógica de negócio
│   ├── __init__.py
│   ├── url.py          # Serviço de URLs
│   └── health.py       # Serviço de Health Check
├── utils/              # Utilitários
│   ├── __init__.py
│   ├── hash_generator.py  # Gerador de hash Base 62
│   └── logger.py       # Sistema de logging estruturado
├── routes/             # Rotas da API
│   ├── __init__.py
│   ├── create_url.py   # Endpoints de URLs
│   └── health.py       # Endpoints de Health Check
├── middleware/         # Middlewares da aplicação
│   ├── __init__.py
│   └── request_context.py  # Request ID e métricas
├── exceptions/         # Exceções customizadas
│   ├── __init__.py
│   └── api_exceptions.py   # Classes de exceções da API
├── tests/              # Testes unitários
│   ├── __init__.py
│   ├── conftest.py     # Fixtures do pytest
│   ├── test_routes.py  # Testes de rotas
│   ├── test_service_url.py  # Testes de serviço
│   └── test_hash_generator.py  # Testes do gerador de hash
├── docs/               # Documentação
│   ├── API.md          # Documentação da API
│   ├── ARQUITETURA.md  # Arquitetura do projeto
│   ├── CHANGELOG.md    # Histórico de mudanças
│   ├── PAGINACAO.md    # Documentação de paginação
│   └── VERSIONAMENTO.md
├── .env.example        # Exemplo de variáveis de ambiente
├── main.py             # Ponto de entrada da aplicação
├── requirements.txt    # Dependências Python
└── __version__.py      # Versão da aplicação
```

---

## 💾 Instalação

### Pré-requisitos
- Python 3.12+
- pip

### Passos

1. **Clone o repositório:**
```bash
git clone https://github.com/Lucas-Cerdeira/encurtador_url.git
cd encurtador_url
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Copie o arquivo de exemplo e configure:
```bash
cp .env.example .env
```

**Arquivo `.env`:**
```env
# URL base do encurtador
URL_BASE=http://localhost:8000/

# Logging
LOG_LEVEL=INFO
JSON_LOGS=false

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Configurações Disponíveis

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `URL_BASE` | URL base retornada nas URLs encurtadas | `http://localhost:8000/` |
| `LOG_LEVEL` | Nível de log (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `JSON_LOGS` | Ativar logs em formato JSON (para produção) | `false` |
| `CORS_ORIGINS` | Origens permitidas para CORS (separadas por vírgula) | `http://localhost:5173,...` |

---

## ▶️ Como Rodar

### Desenvolvimento

```bash
uvicorn main:app --reload
```

Acesse a aplicação em: `http://localhost:8000`

### Documentação Interativa

FastAPI gera documentação automática:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Executar Testes

```bash
# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=. --cov-report=html

# Rodar testes específicos
pytest tests/test_routes.py
pytest tests/test_service_url.py
```

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000
```

### Endpoints Disponíveis

#### 1. Criar URL Encurtada
```http
POST /create-url
```

**Request Body:**
```json
{
  "original_url": "https://example.com"
}
```

**Response:** `200 OK`
```json
"http://localhost:8000/aB3xY9"
```

**Nota:** O `short_code` gerado tem **6 caracteres** usando Base 62 (A-Z, a-z, 0-9), totalizando **56.800.235.584 combinações possíveis**.

---

#### 2. Redirecionar para URL Original
```http
GET /{short_code}
```

**Response:** `307 Temporary Redirect`
- Redireciona para a URL original
- Incrementa contador de cliques

---

#### 3. Obter Estatísticas de URL
```http
GET /stats/{short_code}
```

**Response:** `200 OK`
```json
{
  "original_url": "https://example.com",
  "short_url": "abc12345",
  "click_count": 42
}
```

---

#### 4. Listar URLs
```http
GET /urls?page=1&page_size=10
```

**Query Parameters:**
- `page` (opcional): Número da página (padrão: 1, mínimo: 1)
- `page_size` (opcional): Itens por página (padrão: 10, mínimo: 1, máximo: 100)

**Response:** `200 OK`
```json
{
  "total": 50,
  "page": 1,
  "page_size": 10,
  "urls": [
    {
      "id": 1,
      "original_url": "https://example.com",
      "short_code": "aB3xY9",
      "click_count": 42,
      "created_at": "2026-01-22T10:30:00"
    }
  ]
}
```

---

#### 5. Atualizar URL
```http
PATCH /urls/{url_id}
```

**Request Body:**
```json
{
  "original_url": "https://newexample.com"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "original_url": "https://newexample.com/",
  "short_code": "abc12345",
  "click_count": 42,
  "created_at": "2026-01-22T10:30:00"
}
```

---

#### 6. Deletar URL
```http
DELETE /urls/{url_id}
```

**Response:** `200 OK`
```json
{
  "message": "URL 1 deletada com sucesso"
}
```

---

#### 7. Health Check Completo
```http
GET /health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.1",
  "timestamp": "2026-02-04T12:00:00Z",
  "uptime_seconds": 3600.5,
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "response_time_ms": 2.5,
      "message": "Database connection successful"
    }
  ]
}
```

**Status possíveis:** `healthy`, `degraded`, `unhealthy`

---

#### 8. Readiness Probe (Kubernetes)
```http
GET /health/ready
```

**Response:** `200 OK`
```json
{
  "ready": true,
  "message": "Application ready to receive traffic"
}
```

---

#### 9. Liveness Probe (Kubernetes)
```http
GET /health/live
```

**Response:** `200 OK`
```json
{
  "alive": true,
  "timestamp": "2026-02-04T12:00:00Z"
}
```

---

### Códigos de Status HTTP

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 307 | Redirecionamento temporário |
| 400 | Requisição inválida |
| 404 | Recurso não encontrado |
| 422 | Erro de validação |
| 500 | Erro interno do servidor |

---

## 📊 Modelos de Dados

### URL Model

**Tabela:** `urls`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único (chave primária) |
| `short_code` | String | Código curto único (6 caracteres, Base 62) |
| `original_url` | String | URL original completa |
| `click_count` | Integer | Contador de cliques (padrão: 0) |
| `created_at` | DateTime | Data/hora de criação |

**Índices:**
- `id` (primário)
- `short_code` (único)
- `original_url`

---

## 🔐 Geração de Hash (HashGenerator)

O projeto utiliza um gerador de hash customizado baseado em **Base 62** para criar códigos curtos únicos.

### Características

- **Alfabeto Base 62**: A-Z (26 maiúsculas) + a-z (26 minúsculas) + 0-9 (10 números) = 62 caracteres
- **Tamanho**: 6 caracteres (configurável entre 1-6)
- **Combinações possíveis**: 62^6 = **56.800.235.584** combinações
- **Segurança**: Usa `secrets.SystemRandom()` para geração criptograficamente segura
- **Validação**: Método `validate()` para verificar formato de hash

### Uso

```python
from utils.hash_generator import HashGenerator

# Criar gerador com tamanho padrão (6 caracteres)
generator = HashGenerator()

# Gerar hash
hash_code = generator.generate()  # Ex: "aB3xY9"

# Gerar hash com tamanho customizado
hash_code = generator.generate(size=4)  # Ex: "xY9z"

# Validar hash
is_valid = generator.validate("aB3xY9")  # True
is_valid = generator.validate("aB3-xY9")  # False (contém caractere inválido)

# Calcular combinações máximas
max_combinations = HashGenerator.get_max_combinations(6)  # 56800235584
```

### Escalabilidade

O `HashGenerator` foi projetado para ser escalável:
- Fácil troca de tamanho (1-6 caracteres)
- Possibilidade de extensão para outros algoritmos
- Validação robusta de entrada
- Testes completos (16 testes unitários)

---

## 🧪 Testes

### Estrutura de Testes

O projeto possui cobertura completa de testes unitários:

- **`tests/conftest.py`**: Fixtures compartilhadas (banco em memória, cliente de teste)
- **`tests/test_routes.py`**: Testes de endpoints (integração)
- **`tests/test_service_url.py`**: Testes de lógica de negócio
- **`tests/test_hash_generator.py`**: Testes do gerador de hash (16 testes)

### Banco de Dados de Teste

Os testes utilizam **SQLite in-memory** para isolamento total:
- Banco criado do zero para cada teste
- Dados descartados automaticamente após cada teste
- Não interfere com o banco de desenvolvimento

### Cobertura

Testes cobrem:
- ✅ Criação de URLs (sucesso, colisão, retry)
- ✅ Redirecionamento (sucesso, 404)
- ✅ Estatísticas (sucesso, 404)
- ✅ Listagem (vazia, com dados, paginação, validação)
- ✅ Atualização (sucesso, 404, validação)
- ✅ Deleção (sucesso, 404, verificação de remoção)
- ✅ Geração de hash (Base 62, validação, casos extremos)

---

## 📝 Padrões de Desenvolvimento

### Padrão de Commits

Seguimos **Conventional Commits** com prefixos:

- `<feat>`: Nova funcionalidade
- `<fix>`: Correção de bug
- `<refactor>`: Melhoria interna sem mudança de comportamento
- `<test>`: Adição ou modificação de testes
- `<chore>`: Tarefas de manutenção
- `<docs>`: Documentação

**Exemplos:**
```bash
git commit -m "<feat> adicionar endpoint de listagem de URLs"
git commit -m "<fix> corrigir bug no contador de cliques"
git commit -m "<test> adicionar testes para delete endpoint"
```

### Filosofia de Desenvolvimento

1. **Devagar e bem feito**: Commits pequenos e incrementais
2. **Commits curtos**: Não amontoar muitas modificações
3. **Mensagens claras**: Descrição objetiva das mudanças

### Arquitetura

O projeto segue uma **arquitetura em camadas**:

```
Routes (Endpoints) 
    ↓
Services (Lógica de Negócio)
    ↓
Models (ORM/Banco de Dados)
```

**Separação de responsabilidades:**
- **Routes**: Validação de entrada, resposta HTTP
- **Services**: Lógica de negócio, tratamento de erros
- **Models**: Mapeamento objeto-relacional
- **Schemas**: Validação e serialização de dados

---

## 📌 Versionamento

Este projeto segue **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Mudanças que quebram compatibilidade
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs

**Versão Atual:** `0.1.1`

Consulte [VERSIONAMENTO.md](docs/VERSIONAMENTO.md) e [CHANGELOG.md](docs/CHANGELOG.md) para mais detalhes.

---

## 🛠️ Funcionalidades Futuras

Consulte [features_funcionais.md](features_funcionais.md) para o roadmap completo.

**Crítica (Produção):**
- Autenticação e Autorização (JWT)
- Rate Limiting (proteção contra abuso)
- Índices de Banco de Dados

**Alta Prioridade:**
- Migração para PostgreSQL
- Cache Layer (Redis)
- Custom Short Codes (aliases)

**Média Prioridade:**
- Analytics Detalhado (cliques por período, device, referrer)
- Expiração/TTL de links
- Validação de URLs maliciosas

**Baixa Prioridade:**
- QR Code Generator
- Preview de Destino
- Dashboard Web

**✅ Já Implementado:**
- Tratamento de erros padronizado
- Módulo HashGenerator (Base 62)
- Healthcheck e Observabilidade Básica
- Logs estruturados (JSON)

---

## 👥 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feat/nova-feature`)
3. Commit suas mudanças (`git commit -m '<feat> adicionar nova feature'`)
4. Push para a branch (`git push origin feat/nova-feature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob licença MIT.

---

## 📧 Contato

**Lucas Cerdeira**
- GitHub: [@Lucas-Cerdeira](https://github.com/Lucas-Cerdeira)
- Repositório: [encurtador_url](https://github.com/Lucas-Cerdeira/encurtador_url)

---

**Desenvolvido com ❤️ usando FastAPI**
