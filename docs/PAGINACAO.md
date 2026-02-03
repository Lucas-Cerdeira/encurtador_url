# Documentacao - Paginacao de URLs

## Visao Geral

A API do Encurtador de URLs implementa paginacao offset-based para a listagem de URLs, permitindo consultas eficientes mesmo com grandes volumes de dados.

**Status:** Implementado (v0.1.0)

---

## Endpoint

### Listar URLs com Paginacao

**Metodo:** `GET /urls`

**Query Parameters:**

| Parametro | Tipo | Obrigatorio | Padrao | Validacao | Descricao |
|-----------|------|-------------|---------|-----------|-----------|
| `page` | integer | Nao | 1 | >= 1 | Numero da pagina |
| `page_size` | integer | Nao | 10 | 1 <= x <= 100 | Itens por pagina |

**Exemplos de Uso:**

```bash
# Primeira pagina com 10 itens (padrao)
GET /urls

# Segunda pagina com 20 itens
GET /urls?page=2&page_size=20

# Primeira pagina com 50 itens
GET /urls?page=1&page_size=50
```

---

## Formato de Resposta

### Sucesso (200 OK)

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
      "created_at": "2026-01-27T10:30:00"
    }
  ]
}
```

**Campos:**
- `total`: Numero total de URLs no banco de dados
- `page`: Pagina atual retornada
- `page_size`: Quantidade de itens por pagina
- `urls`: Array com os objetos URL

### Erro (400 Bad Request)

**Parametros invalidos:**

```json
{
  "error": {
    "code": "INVALID_PAGINATION",
    "message": "Numero da pagina deve ser maior ou igual a 1"
  }
}
```

ou

```json
{
  "error": {
    "code": "INVALID_PAGINATION",
    "message": "Tamanho da pagina deve estar entre 1 e 100"
  }
}
```

### Erro (422 Unprocessable Entity)

**Tipo de dado invalido:**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Erro de validacao nos dados fornecidos",
    "details": [
      {
        "field": "query.page",
        "message": "Input should be a valid integer",
        "type": "int_parsing"
      }
    ]
  }
}
```

---

## Comportamento

### Ordenacao

As URLs sao **sempre ordenadas por data de criacao descendente** (`created_at DESC`), ou seja, as URLs mais recentes aparecem primeiro.

### Paginas Vazias

Se a pagina solicitada nao tiver URLs (ex: pagina 10 quando so existem 2 paginas), a resposta retorna:

```json
{
  "total": 15,
  "page": 10,
  "page_size": 10,
  "urls": []
}
```

### Calculo de Paginas

Para calcular o numero total de paginas:

```python
import math
total_pages = math.ceil(total / page_size)
```

Exemplo: 25 URLs com `page_size=10` -> 3 paginas

---

## Implementacao Tecnica

### Arquivos Envolvidos

| Arquivo | Responsabilidade |
|---------|------------------|
| `routes/create_url.py` | Endpoint e validacao de parametros |
| `services/url.py` | Logica de negocio e query |
| `schemas/url.py` | Schema de resposta (URLListResponse) |
| `exceptions/__init__.py` | InvalidPaginationError |

### Service Layer

```python
def list_urls(self, db: Session, page: int = 1, page_size: int = 10) -> dict:
    # Validacoes
    if page < 1:
        raise InvalidPaginationError("Numero da pagina deve ser maior ou igual a 1")
    
    if page_size < 1 or page_size > 100:
        raise InvalidPaginationError("Tamanho da pagina deve estar entre 1 e 100")
    
    # Conta total
    total = db.query(URL).count()
    
    # Calcula offset
    offset = (page - 1) * page_size
    
    # Busca com paginacao
    urls = db.query(URL).order_by(URL.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "urls": urls
    }
```

### Tipo de Paginacao

**Offset-based Pagination:**
- Simples de implementar
- Permite navegacao aleatoria entre paginas
- Retorna contagem total
- Performance degrada com offsets muito grandes
- Pode ter inconsistencias se dados mudarem durante navegacao

---

## Testes

A funcionalidade possui cobertura completa de testes:

### Testes de Service (`test_service_url.py`)
- `test_list_urls_empty`: Lista vazia
- `test_list_urls_with_data`: Lista com dados
- `test_list_urls_pagination`: Multiplas paginas
- `test_list_urls_invalid_page`: Pagina invalida (< 1)
- `test_list_urls_invalid_page_size`: Tamanho invalido (< 1 ou > 100)

### Testes de Rota (`test_routes.py`)
- `test_list_urls_route_empty`: Endpoint com lista vazia
- `test_list_urls_route_with_data`: Endpoint com dados
- `test_list_urls_route_pagination`: Paginacao via HTTP
- `test_list_urls_route_invalid_params`: Parametros invalidos via HTTP

---

## Exemplos de Uso

### Python com requests

```python
import requests

# Primeira pagina
response = requests.get('http://localhost:8000/urls', params={
    'page': 1,
    'page_size': 10
})
data = response.json()

print(f"Total de URLs: {data['total']}")
print(f"Mostrando {len(data['urls'])} URLs")

# Iterar por todas as paginas
page = 1
while True:
    response = requests.get('http://localhost:8000/urls', params={
        'page': page,
        'page_size': 20
    })
    data = response.json()
    
    if not data['urls']:
        break
    
    for url in data['urls']:
        print(f"{url['short_code']}: {url['original_url']}")
    
    page += 1
```

### JavaScript com fetch

```javascript
async function getAllURLs() {
  let page = 1;
  let allUrls = [];
  
  while (true) {
    const response = await fetch(
      `http://localhost:8000/urls?page=${page}&page_size=50`
    );
    const data = await response.json();
    
    if (data.urls.length === 0) break;
    
    allUrls.push(...data.urls);
    page++;
  }
  
  return allUrls;
}
```

### cURL

```bash
# Primeira pagina com padroes
curl http://localhost:8000/urls

# Segunda pagina com 25 itens
curl "http://localhost:8000/urls?page=2&page_size=25"

# Com formatacao JSON
curl -s "http://localhost:8000/urls?page=1&page_size=5" | jq .
```

---

## Melhorias Futuras Planejadas

### 1. Cursor-based Pagination

Para melhor performance em grandes volumes:

```
GET /urls?cursor=eyJpZCI6MTIzNH0&limit=10
```

**Vantagens:**
- Performance consistente independente da posicao
- Sem problemas com dados em mudanca
- Mais eficiente para infinite scroll

### 2. Filtros Avancados

```
GET /urls?page=1&page_size=10&created_after=2026-01-01&min_clicks=10
```

Filtros planejados:
- `created_after` / `created_before`: Filtro por data
- `min_clicks` / `max_clicks`: Filtro por popularidade
- `search`: Busca na URL original
- `short_code`: Busca por codigo especifico

### 3. Ordenacao Configuravel

```
GET /urls?page=1&sort_by=click_count&order=desc
```

Ordenacoes planejadas:
- `created_at`: Data de criacao (padrao)
- `click_count`: Numero de cliques
- `original_url`: URL original (alfabetica)
- `short_code`: Codigo curto

### 4. Metadados de Paginacao

Adicionar ao response:
```json
{
  "total": 50,
  "page": 2,
  "page_size": 10,
  "total_pages": 5,
  "has_next": true,
  "has_previous": true,
  "next_page": 3,
  "previous_page": 1
}
```

---

## Performance

### Otimizacoes Implementadas
- Uso de `offset()` e `limit()` no SQLAlchemy
- Ordenacao no banco de dados (nao em memoria)
- Single query para contagem total

### Otimizacoes Pendentes
- Indice em `created_at` para ordenacao rapida
- Cache de contagem total (atualizado via trigger)
- Lazy loading de relacionamentos futuros

### Benchmarks Esperados

Com indices adequados:
- Primeira pagina (0-10): < 10ms
- Paginas intermediarias (100-110): < 50ms
- Paginas finais (com offset grande): < 200ms

---

## Changelog

- **v0.1.0** (2026-01-27): Implementacao inicial da paginacao offset-based

---

**Documentacao criada em:** 2026-02-03
**Ultima atualizacao:** 2026-02-03
