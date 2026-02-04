# Documentação da API

## Visão Geral

Esta é a documentação detalhada da API REST do Encurtador de URL.

## Base URL

```
http://localhost:8000
```

Para produção, configure a variável de ambiente `URL_BASE`.

---

## Autenticação

Atualmente, a API não requer autenticação. (Feature futura)

---

## Endpoints

### 1. Criar URL Encurtada

Cria uma nova URL encurtada a partir de uma URL longa.

**Endpoint:**
```http
POST /create-url
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "original_url": "https://example.com/very/long/url/path"
}
```

**Validações:**
- `original_url` deve ser uma URL válida (HTTP/HTTPS)
- `original_url` é obrigatório

**Response Success:** `200 OK`
```json
"http://localhost:8000/aB3xY9"
```

**Nota:** O `short_code` gerado tem **6 caracteres** usando Base 62 (A-Z, a-z, 0-9), totalizando **56.800.235.584 combinações possíveis**.

**Response Error:** `422 Unprocessable Entity`
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Erro de validação nos dados fornecidos",
    "details": [
      {
        "field": "body.original_url",
        "message": "Input should be a valid URL, relative URL without a base",
        "type": "url_parsing"
      }
    ]
  }
}
```

**Comportamento:**
- Gera um `short_code` único de 6 caracteres usando HashGenerator (Base 62)
- Implementa retry automático em caso de colisão (até 5 tentativas)
- Retorna a URL completa encurtada

---

### 2. Redirecionar para URL Original

Redireciona para a URL original e incrementa o contador de cliques.

**Endpoint:**
```http
GET /{short_code}
```

**Path Parameters:**
- `short_code` (string): Código curto da URL

**Response Success:** `307 Temporary Redirect`
```
Location: https://example.com/very/long/url/path
```

**Response Error:** `404 Not Found`
```json
{
  "error": {
    "code": "URL_NOT_FOUND",
    "message": "URL short_code 'abc123' não encontrada"
  }
}
```

**Comportamento:**
- Busca a URL no banco de dados
- Incrementa `click_count` em 1
- Redireciona para `original_url`

---

### 3. Obter Estatísticas de URL

Retorna estatísticas de uma URL encurtada.

**Endpoint:**
```http
GET /stats/{short_code}
```

**Path Parameters:**
- `short_code` (string): Código curto da URL

**Response Success:** `200 OK`
```json
{
  "original_url": "https://example.com",
  "short_url": "abc12345",
  "click_count": 42
}
```

**Response Error:** `404 Not Found`
```json
{
  "error": {
    "code": "URL_NOT_FOUND",
    "message": "URL short_code 'abc123' não encontrada"
  }
}
```

---

### 4. Listar URLs

Lista todas as URLs encurtadas com paginação.

**Endpoint:**
```http
GET /urls
```

**Query Parameters:**
- `page` (integer, opcional): Número da página (padrão: 1, mínimo: 1)
- `page_size` (integer, opcional): Itens por página (padrão: 10, min: 1, max: 100)

**Exemplo:**
```http
GET /urls?page=2&page_size=20
```

**Response Success:** `200 OK`
```json
{
  "total": 150,
  "page": 2,
  "page_size": 20,
  "urls": [
    {
      "id": 21,
      "original_url": "https://example.com",
      "short_code": "aB3xY9",
      "click_count": 42,
      "created_at": "2026-01-22T10:30:00"
    },
    {
      "id": 22,
      "original_url": "https://another.com",
      "short_code": "xY9zA1",
      "click_count": 15,
      "created_at": "2026-01-22T11:45:00"
    }
  ]
}
```

**Response Error:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

**Comportamento:**
- Ordenação: Mais recentes primeiro (`created_at DESC`)
- Retorna array vazio se não houver URLs
- Validação automática de parâmetros pelo FastAPI

---

### 5. Atualizar URL

Atualiza a URL original de uma URL encurtada.

**Endpoint:**
```http
PATCH /urls/{url_id}
```

**Path Parameters:**
- `url_id` (integer): ID da URL

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "original_url": "https://newexample.com"
}
```

**Validações:**
- `original_url` deve ser uma URL válida (HTTP/HTTPS)
- `original_url` não pode ser `null` ou omitido

**Response Success:** `200 OK`
```json
{
  "id": 1,
  "original_url": "https://newexample.com/",
  "short_code": "abc12345",
  "click_count": 42,
  "created_at": "2026-01-22T10:30:00"
}
```

**Response Error:** `404 Not Found`
```json
{
  "error": {
    "code": "URL_NOT_FOUND",
    "message": "URL ID 999 não encontrada"
  }
}
```

**Response Error:** `400 Bad Request`
```json
{
  "error": {
    "code": "MISSING_FIELD",
    "message": "Campo obrigatório 'original_url' não fornecido"
  }
}
```

**Comportamento:**
- O `short_code` **não** é alterado
- O `click_count` **não** é resetado
- Apenas `original_url` é atualizado

---

### 6. Deletar URL

Remove uma URL encurtada do sistema.

**Endpoint:**
```http
DELETE /urls/{url_id}
```

**Path Parameters:**
- `url_id` (integer): ID da URL

**Response Success:** `200 OK`
```json
{
  "message": "URL 1 deletada com sucesso"
}
```

**Response Error:** `404 Not Found`
```json
{
  "error": {
    "code": "URL_NOT_FOUND",
    "message": "URL ID 999 não encontrada"
  }
}
```

**Comportamento:**
- Remoção permanente do banco de dados
- Não é possível desfazer a operação

---

## Códigos de Status HTTP

| Código | Nome | Descrição |
|--------|------|-----------|
| 200 | OK | Requisição bem-sucedida |
| 307 | Temporary Redirect | Redirecionamento para URL original |
| 400 | Bad Request | Requisição malformada ou inválida |
| 404 | Not Found | Recurso não encontrado |
| 422 | Unprocessable Entity | Erro de validação de dados |
| 500 | Internal Server Error | Erro interno do servidor |

---

## Tratamento de Erros

### Estrutura de Erro Padrão

Todos os erros seguem um formato padronizado com código e mensagem:

**Erros de API (400, 404, 500):**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Mensagem de erro descritiva"
  }
}
```

**Erros de Validação (422):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Erro de validação nos dados fornecidos",
    "details": [
      {
        "field": "body.original_url",
        "message": "Input should be a valid URL",
        "type": "url_parsing"
      }
    ]
  }
}
```

### Códigos de Erro

| Código | Descrição | Status HTTP |
|--------|-----------|-------------|
| `URL_NOT_FOUND` | URL não encontrada | 404 |
| `INVALID_PAGINATION` | Parâmetros de paginação inválidos | 400 |
| `MISSING_FIELD` | Campo obrigatório ausente | 400 |
| `SHORT_CODE_GENERATION_FAILED` | Falha ao gerar código único | 500 |
| `DATABASE_ERROR` | Erro no banco de dados | 500 |
| `VALIDATION_ERROR` | Erro de validação de dados | 422 |
| `INTERNAL_SERVER_ERROR` | Erro interno não tratado | 500 |

### Tipos Comuns de Erro

**URL Não Encontrada:**
```json
{
  "error": {
    "code": "URL_NOT_FOUND",
    "message": "URL short_code 'abc123' não encontrada"
  }
}
```

**Campo Obrigatório Ausente:**
```json
{
  "error": {
    "code": "MISSING_FIELD",
    "message": "Campo obrigatório 'original_url' não fornecido"
  }
}
```

**Erro de Validação:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Erro de validação nos dados fornecidos",
    "details": [
      {
        "field": "body.original_url",
        "message": "Input should be a valid URL",
        "type": "url_parsing"
      }
    ]
  }
}
```

---

### 7. Health Check Completo

Verifica o estado de saúde de todos os componentes da aplicação.

**Endpoint:**
```http
GET /health
```

**Response Success:** `200 OK`
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
      "message": "Database connection successful",
      "last_check": "2026-02-04T12:00:00Z"
    }
  ]
}
```

**Response Error:** `503 Service Unavailable`
```json
{
  "status": "unhealthy",
  "version": "0.1.1",
  "timestamp": "2026-02-04T12:00:00Z",
  "uptime_seconds": 3600.5,
  "checks": [
    {
      "name": "database",
      "status": "unhealthy",
      "response_time_ms": 5000.0,
      "message": "Database connection failed: timeout"
    }
  ]
}
```

**Status possíveis:**
- `healthy`: Todos os componentes funcionando normalmente
- `degraded`: Aplicação funcionando com funcionalidade reduzida
- `unhealthy`: Aplicação não pode processar requisições

---

### 8. Readiness Probe (Kubernetes)

Verifica se a aplicação está pronta para receber tráfego.

**Endpoint:**
```http
GET /health/ready
```

**Response Success:** `200 OK`
```json
{
  "ready": true,
  "message": "Application ready to receive traffic"
}
```

**Response Error:** `503 Service Unavailable`
```json
{
  "ready": false,
  "message": "Database not available"
}
```

**Uso:** Kubernetes usa este endpoint para decidir se deve enviar tráfego para o pod.

---

### 9. Liveness Probe (Kubernetes)

Verifica se a aplicação está viva e respondendo.

**Endpoint:**
```http
GET /health/live
```

**Response Success:** `200 OK`
```json
{
  "alive": true,
  "timestamp": "2026-02-04T12:00:00Z"
}
```

**Uso:** Kubernetes usa este endpoint para decidir se deve reiniciar o pod. Se não responder, o pod é reiniciado.

---

## Headers de Rastreabilidade

Todas as respostas incluem headers de observabilidade:

| Header | Descrição | Exemplo |
|--------|-----------|---------|
| `X-Request-ID` | ID único da requisição | `a1b2c3d4-e5f6-...` |
| `X-Response-Time` | Tempo de processamento | `15.32ms` |

**Nota:** O `X-Request-ID` pode ser enviado pelo cliente. Se não fornecido, é gerado automaticamente.

---

## Rate Limiting

**Status:** Não implementado

Feature futura para proteção contra abuso.

---

## Paginação

A listagem de URLs utiliza **paginação baseada em offset**.

**Parâmetros:**
- `page`: Número da página (começa em 1)
- `page_size`: Quantidade de itens por página

**Exemplo de Navegação:**
```http
GET /urls?page=1&page_size=10  # Primeiros 10 itens
GET /urls?page=2&page_size=10  # Itens 11-20
GET /urls?page=3&page_size=10  # Itens 21-30
```

**Cálculo de Páginas:**
```python
total_pages = ceil(total / page_size)
```

---

## Limites e Constraints

| Recurso | Limite |
|---------|--------|
| Tamanho do short_code | 6 caracteres (Base 62) |
| page_size máximo | 100 itens |
| page mínimo | 1 |
| Retries de colisão | 5 tentativas |

---

## Exemplos de Uso

### Python (requests)

```python
import requests

# Criar URL encurtada
response = requests.post(
    "http://localhost:8000/create-url",
    json={"original_url": "https://example.com"}
)
short_url = response.json()
print(f"URL encurtada: {short_url}")

# Listar URLs
response = requests.get("http://localhost:8000/urls?page=1&page_size=10")
data = response.json()
print(f"Total de URLs: {data['total']}")

# Atualizar URL
response = requests.patch(
    "http://localhost:8000/urls/1",
    json={"original_url": "https://newexample.com"}
)
updated = response.json()
print(f"URL atualizada: {updated['original_url']}")

# Deletar URL
response = requests.delete("http://localhost:8000/urls/1")
result = response.json()
print(result['message'])
```

### cURL

```bash
# Criar URL encurtada
curl -X POST "http://localhost:8000/create-url" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com"}'

# Listar URLs
curl "http://localhost:8000/urls?page=1&page_size=10"

# Obter estatísticas
curl "http://localhost:8000/stats/aB3xY9"

# Atualizar URL
curl -X PATCH "http://localhost:8000/urls/1" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://newexample.com"}'

# Deletar URL
curl -X DELETE "http://localhost:8000/urls/1"
```

---

## Documentação Interativa

FastAPI gera documentação automática:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Geração de Short Code

### HashGenerator (Base 62)

O sistema utiliza um gerador de hash customizado baseado em **Base 62** para criar códigos curtos únicos.

**Características:**
- **Alfabeto**: A-Z (26 maiúsculas) + a-z (26 minúsculas) + 0-9 (10 números) = 62 caracteres
- **Tamanho**: 6 caracteres (configurável entre 1-6)
- **Combinações**: 62^6 = **56.800.235.584** combinações possíveis
- **Segurança**: Geração criptograficamente segura usando `secrets.SystemRandom()`
- **Colisão**: Probabilidade extremamente baixa (1 em 56 bilhões)

**Exemplo de Hash Gerado:**
```
aB3xY9  (6 caracteres, Base 62)
```

**Tratamento de Colisão:**
- Retry automático até 5 tentativas em caso de colisão
- Exception `ShortCodeGenerationError` após esgotar tentativas
- Log de warnings para monitoramento

---

## Changelog da API

Consulte [CHANGELOG.md](CHANGELOG.md) para histórico de alterações.

---

**Última Atualização:** 2026-02-04  
**Versão da API:** 0.1.1
