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
"http://localhost:8000/abc12345"
```

**Response Error:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["body", "original_url"],
      "msg": "invalid or missing URL scheme",
      "type": "url_scheme"
    }
  ]
}
```

**Comportamento:**
- Gera um `short_code` único de 8 caracteres usando NanoID
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
  "detail": "URL not found"
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
  "detail": "URL not found"
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
      "short_code": "abc12345",
      "click_count": 42,
      "created_at": "2026-01-22T10:30:00"
    },
    {
      "id": 22,
      "original_url": "https://another.com",
      "short_code": "def67890",
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
  "detail": "URL com ID 999 não encontrada"
}
```

**Response Error:** `400 Bad Request`
```json
{
  "detail": "É necessário fornecer a nova URL original"
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
  "detail": "URL com ID 999 não encontrada"
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

Todos os erros seguem a estrutura do FastAPI:

```json
{
  "detail": "Mensagem de erro descritiva"
}
```

ou para erros de validação:

```json
{
  "detail": [
    {
      "loc": ["body", "campo"],
      "msg": "descrição do erro",
      "type": "tipo_do_erro"
    }
  ]
}
```

### Tipos Comuns de Erro

**URL Inválida:**
```json
{
  "detail": [
    {
      "loc": ["body", "original_url"],
      "msg": "invalid or missing URL scheme",
      "type": "url_scheme"
    }
  ]
}
```

**Recurso Não Encontrado:**
```json
{
  "detail": "URL not found"
}
```

**Validação de Parâmetros:**
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
| Tamanho do short_code | 8 caracteres |
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
curl "http://localhost:8000/stats/abc12345"

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

## Changelog da API

Consulte [CHANGELOG.md](CHANGELOG.md) para histórico de alterações.

---

**Última Atualização:** 2026-01-22  
**Versão da API:** 0.0.1
