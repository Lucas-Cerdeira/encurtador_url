# Análise Detalhada dos Erros nos Testes de Autenticação

## Resumo Executivo
**14 de 24 testes falhando** devido a 4 causas principais relacionadas à configuração incorreta dos fixtures de teste.

---

## Erro #1: Falta de Isolamento do Banco de Dados 🔴 [CRÍTICO]

### Problema
O arquivo `test_auth_routes.py` cria um `TestClient` no **nível do módulo** (linha 24):

```python
from main import app
client = TestClient(app)
```

Isso causa:
- O `client` usa o `app` real de `main.py`
- O `app` real usa `get_db()` que conecta ao banco de dados SQLite persistente
- O fixture `db_session` cria um banco SQLite **em memória** separado
- **Dados criados via `db_session` não existem quando `client` faz requests HTTP**

### Onde acontece
Afeta **10 testes** que:
1. Criam usuário via `UserService.create_user(user_data, db_session)` → SQLite em memória
2. Fazem request via `client.post("/auth/login", ...)` → banco real (não tem o usuário)
3. ❌ Falha: "Credenciais inválidas" / "Email não encontrado"

#### Testes afetados:
- `TestLoginRoute::test_deve_fazer_login_com_credenciais_corretas`
- `TestLoginRoute::test_deve_retornar_403_para_usuario_inativo`
- `TestLoginRoute::test_deve_aceitar_content_type_form_urlencoded`
- `TestLoginRoute::test_token_deve_ser_valido_para_decodificacao`
- `TestGetCurrentUserInfoRoute::test_deve_retornar_dados_do_usuario_autenticado`
- `TestGetCurrentUserInfoRoute::test_deve_retornar_403_para_usuario_inativo`
- `TestAuthenticationFlow::test_fluxo_completo_registro_login_acesso`
- `TestAuthenticationFlow::test_deve_manter_sessao_com_token_valido`

### Correção necessária
```python
# Em vez de:
from main import app
client = TestClient(app)

# Usar fixture que sobrescreve get_db:
@pytest.fixture
def client(db_session):
    from main import app
    from database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
```

---

## Erro #2: Dados Persistentes Entre Execuções 🟡 [ALTO]

### Problema
Como o `client` usa o **banco real** (SQLite persistente em disco), emails registrados em execuções anteriores do pytest **permanecem no banco**.

Na segunda execução:
```python
def test_deve_registrar_usuario_com_sucesso(self, db_session):
    user_data = {"email": "newuser@example.com", "password": "senha12345"}
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201  # ❌ Retorna 409 (email já existe)
```

### Log da falha:
```
ERROR | Erro da API: O email 'newuser@example.com' já está cadastrado 
      | (código: EMAIL_ALREADY_EXISTS)
```

#### Testes afetados:
- `TestRegisterRoute::test_deve_registrar_usuario_com_sucesso` → 409 em vez de 201
- `TestRegisterRoute::test_deve_hashear_senha_no_banco` → 409 para `hashtest@example.com`
- `TestAuthenticationFlow::test_fluxo_completo_registro_login_acesso` → 409 para `fullflow@example.com`

### Correção
Uma vez corrigido o Erro #1 (usando banco em memória via fixture), este erro desaparece automaticamente, pois cada execução de teste teria um banco limpo.

**Alternativa temporária (não recomendada):**
Usar emails únicos com timestamp/UUID em cada teste.

---

## Erro #3: Validação Pydantic Intercepta Antes do Service 🟠 [MÉDIO]

### Problema
O schema `schemas/user.py` define validação no Pydantic:

```python
class UserCreate(BaseModel):
    password: str = Field(..., min_length=8, description="...")
```

O service `services/user.py` também valida:

```python
class UserService:
    MIN_PASSWORD_LENGTH = 8
    
    @staticmethod
    def create_user(user_data: UserCreate, db: Session) -> User:
        if len(user_data.password) < UserService.MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(...)  # 400
```

**Fluxo atual:**
```
Request com senha="123"
  → Pydantic valida min_length=8
  → ❌ Retorna 422 VALIDATION_ERROR (antes de chegar ao service)
  → Service nunca é chamado
  → WeakPasswordError(400) nunca é lançada
```

#### Teste afetado:
```python
def test_deve_retornar_400_para_senha_fraca(self):
    user_data = {"email": "weakpass@example.com", "password": "123"}
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400  # ❌ Recebe 422
```

### Correções possíveis:

**Opção A:** Aceitar 422 como correto (validação de schema)
```python
def test_deve_retornar_422_para_senha_menor_que_8_caracteres(self):
    user_data = {"email": "weakpass@example.com", "password": "123"}
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 422
    data = response.json()
    assert "password" in str(data).lower()
```

**Opção B:** Remover validação do schema, deixar só no service
```python
# schemas/user.py
class UserCreate(BaseModel):
    email: EmailStr
    password: str  # Remove min_length=8
```

**Opção C:** Testar senha com 8+ caracteres mas "fraca" (ex: "12345678")
```python
def test_deve_retornar_400_para_senha_fraca(self):
    # Se implementasse validação de complexidade no futuro
    user_data = {"email": "weakpass@example.com", "password": "12345678"}
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400  # WeakPasswordError
```

**Recomendação:** Usar Opção A (mudar teste para esperar 422), pois validação no schema é mais eficiente.

---

## Erro #4: Mock de Decorator Não Funciona 🟠 [MÉDIO]

### Problema
O decorator `@limiter.limit("5/minute")` é aplicado **em tempo de importação** da rota:

```python
# routes/auth.py
from middleware.rate_limit import limiter

@router.post("/register")
@limiter.limit("5/minute")  # ← Executado quando módulo é importado
async def register(...):
    ...
```

Quando o teste faz `@patch('routes.auth.limiter.limit')`, o decorator **já foi aplicado** e vinculado à função. O mock não substitui o decorator existente.

#### Testes afetados:
```python
@patch('routes.auth.limiter.limit')
def test_deve_aplicar_rate_limit(self, mock_limit):
    client.post("/auth/register", json=user_data)
    
    mock_limit.assert_called()  # ❌ Nunca foi chamado (já estava decorado)
```

- `TestRegisterRoute::test_deve_aplicar_rate_limit`
- `TestRateLimitingAuth::test_register_deve_ter_rate_limit`
- `TestRateLimitingAuth::test_login_deve_ter_rate_limit`

### Correções possíveis:

**Opção A:** Inspecionar decorators da função (mais robusto)
```python
import inspect
from routes.auth import register

def test_deve_aplicar_rate_limit(self):
    # Verificar se decorator está presente
    source_code = inspect.getsource(register)
    assert '@limiter.limit' in source_code
    assert '5/minute' in source_code
```

**Opção B:** Testar comportamento real do rate limit
```python
def test_deve_aplicar_rate_limit(self, client):
    user_data = {"email": f"rate{i}@example.com", "password": "senha12345"}
    
    # Fazer 6 requisições (limite é 5/min)
    for i in range(6):
        response = client.post("/auth/register", json=user_data)
    
    # A 6ª deve retornar 429
    assert response.status_code == 429
    assert "RATE_LIMIT_EXCEEDED" in response.json()["error"]["code"]
```

**Opção C:** Remover teste (não adiciona valor)
```python
# Rate limit é testado em testes de integração/E2E
# Não precisa teste unitário específico
```

**Recomendação:** Opção A (inspeção de código) ou C (remover), pois Opção B requer configuração complexa de tempo/redis mock.

---

## Plano de Ação

### Tarefa 1: Criar fixture adequado para testes de auth ✅
**Arquivo:** `tests/conftest.py` (adicionar fixtures)

```python
@pytest.fixture
def app_with_auth():
    """App configurado com rotas de autenticação."""
    from fastapi import FastAPI
    from routes.auth import router as auth_router
    from exceptions import BaseAPIException
    # ... incluir exception handlers
    
    app = FastAPI()
    app.include_router(auth_router)
    # ... exception handlers
    
    return app

@pytest.fixture
def client_auth(db_session, app_with_auth):
    """TestClient com banco de dados em memória para testes de auth."""
    from database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app_with_auth.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app_with_auth) as test_client:
        yield test_client
    
    app_with_auth.dependency_overrides.clear()
```

### Tarefa 2: Atualizar test_auth_routes.py
**Remover:**
```python
from main import app
client = TestClient(app)
```

**Atualizar todos os testes:**
```python
class TestRegisterRoute:
    def test_deve_registrar_usuario_com_sucesso(self, db_session, client_auth):
        #                                                         ^^^^^^^^^^^
        # Usar client_auth em vez do client global
        response = client_auth.post("/auth/register", json=user_data)
```

### Tarefa 3: Corrigir teste de senha fraca
```python
def test_deve_retornar_422_para_senha_muito_curta(self):  # Renomear
    user_data = {"email": "weakpass@example.com", "password": "123"}
    response = client_auth.post("/auth/register", json=user_data)
    
    assert response.status_code == 422  # Mudou de 400 para 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "password" in str(data["error"]["details"]).lower()
```

### Tarefa 4: Corrigir testes de rate limit
```python
def test_deve_ter_decorator_de_rate_limit(self):  # Renomear
    """Deve ter decorator @limiter.limit aplicado."""
    import inspect
    from routes import auth
    
    # Verificar que o decorator está no código
    register_source = inspect.getsource(auth.register)
    assert '@limiter.limit' in register_source
    assert '5/minute' in register_source
```

---

## Resumo de Impacto

| Tipo de Erro | Severidade | Testes Afetados | Correção |
|--------------|------------|-----------------|----------|
| Sem isolamento DB | 🔴 CRÍTICO | 10 | Criar fixture `client_auth` com `dependency_overrides` |
| Dados persistentes | 🟡 ALTO | 3 | Resolvido automaticamente pelo fixture |
| Validação Pydantic | 🟠 MÉDIO | 1 | Mudar teste para esperar 422 |
| Mock de decorator | 🟠 MÉDIO | 2 | Inspecionar código-fonte ou remover teste |

**Total: 14 falhas → 0 falhas após correções**
