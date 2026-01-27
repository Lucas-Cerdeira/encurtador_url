# Padrões de Versionamento

Este documento descreve os padrões de versionamento utilizados no projeto Encurtador de URL, baseado no [Semantic Versioning (SemVer)](https://semver.org/lang/pt-BR/).

## O que é Semantic Versioning?

Semantic Versioning é um esquema de versionamento que usa um conjunto de três números separados por pontos: **MAJOR.MINOR.PATCH** (ex: `1.2.3`).

### Formato da Versão

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Incrementado quando há mudanças incompatíveis na API
- **MINOR**: Incrementado quando funcionalidades são adicionadas de forma compatível
- **PATCH**: Incrementado quando há correções de bugs compatíveis

## Regras de Versionamento

### 1. Versão Inicial: 0.0.1

A primeira versão do projeto começa em `0.0.1`, indicando que o software está em desenvolvimento inicial.

### 2. Versões 0.x.x (Desenvolvimento Inicial)

Durante o desenvolvimento inicial (versões 0.x.x):
- Qualquer mudança pode quebrar compatibilidade
- Versões MINOR podem incluir mudanças incompatíveis
- Use para indicar que a API ainda não está estável

**Exemplos:**
- `0.0.1` → `0.0.2`: Correção de bug
- `0.0.2` → `0.1.0`: Nova funcionalidade (pode quebrar compatibilidade)
- `0.1.0` → `0.2.0`: Nova funcionalidade (pode quebrar compatibilidade)

### 3. Versão 1.0.0 (Primeira Versão Estável)

Quando o projeto atinge `1.0.0`:
- A API é considerada estável
- Mudanças incompatíveis devem incrementar MAJOR
- Mudanças compatíveis incrementam MINOR ou PATCH

### 4. Incremento de PATCH (x.x.PATCH)

Incremente o número PATCH quando você fizer:
- ✅ Correções de bugs
- ✅ Correções de segurança
- ✅ Melhorias de performance (sem mudar API)
- ✅ Correções de documentação
- ✅ Refatorações internas (sem mudar comportamento externo)

**Exemplos:**
- `1.0.0` → `1.0.1`: Correção de bug
- `1.2.3` → `1.2.4`: Correção de segurança
- `0.1.0` → `0.1.1`: Correção de bug em desenvolvimento

### 5. Incremento de MINOR (x.MINOR.x)

Incremente o número MINOR quando você adicionar:
- ✅ Novas funcionalidades (compatíveis com versões anteriores)
- ✅ Novos endpoints na API
- ✅ Novos campos opcionais em schemas
- ✅ Novas dependências (sem remover antigas)
- ✅ Melhorias que não quebram compatibilidade

**Exemplos:**
- `1.0.0` → `1.1.0`: Nova funcionalidade compatível
- `0.2.0` → `0.3.0`: Nova feature em desenvolvimento
- `1.5.2` → `1.6.0`: Novo endpoint adicionado

### 6. Incremento de MAJOR (MAJOR.x.x)

Incremente o número MAJOR quando você fizer:
- ⚠️ Mudanças incompatíveis na API
- ⚠️ Remoção de funcionalidades
- ⚠️ Mudanças em endpoints existentes
- ⚠️ Remoção de campos obrigatórios
- ⚠️ Mudanças que quebram compatibilidade com versões anteriores

**Exemplos:**
- `0.9.0` → `1.0.0`: Primeira versão estável
- `1.5.0` → `2.0.0`: Mudança incompatível na API
- `2.3.1` → `3.0.0`: Remoção de funcionalidade

## Versões de Pré-lançamento (Pre-release)

Para versões que ainda estão em desenvolvimento ou teste, use identificadores de pré-lançamento:

### Formato
```
MAJOR.MINOR.PATCH-IDENTIFIER
```

### Identificadores Comuns

- **alpha** (`1.0.0-alpha.1`): Versão em desenvolvimento inicial
- **beta** (`1.0.0-beta.1`): Versão para testes
- **rc** (`1.0.0-rc.1`): Release candidate (candidato a lançamento)

**Exemplos:**
- `1.0.0-alpha.1` → `1.0.0-alpha.2`: Nova build alpha
- `1.0.0-beta.1` → `1.0.0-beta.2`: Nova build beta
- `1.0.0-rc.1` → `1.0.0`: Versão final

## Metadados de Build (Build Metadata)

Para adicionar informações adicionais sobre a build:

### Formato
```
MAJOR.MINOR.PATCH+METADATA
```

**Exemplos:**
- `1.0.0+20240115`: Build com data
- `1.0.0+sha.abc123`: Build com hash do commit
- `1.0.0+exp.sha.abc123`: Build experimental

## Processo de Versionamento no Projeto

### 1. Atualizar Versão

Quando for fazer uma nova versão:

1. **Atualizar `__version__.py`**:
   ```python
   __version__ = "0.0.2"  # Nova versão
   ```

2. **Atualizar `CHANGELOG.md`**:
   ```markdown
   ## [0.0.2] - 2024-01-16
   
   ### Adicionado
   - Nova funcionalidade X
   
   ### Corrigido
   - Bug Y resolvido
   ```

3. **Criar tag git**:
   ```bash
   git tag -a v0.0.2 -m "Versão 0.0.2"
   git push origin v0.0.2
   ```

### 2. Commits e Versionamento

Use mensagens de commit que facilitem o versionamento:

- `feat:` → Incrementa MINOR (nova funcionalidade)
- `fix:` → Incrementa PATCH (correção de bug)
- `BREAKING CHANGE:` → Incrementa MAJOR (mudança incompatível)

### 3. Checklist de Release

Antes de criar uma nova versão:

- [ ] Todos os testes passando
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] `__version__.py` atualizado
- [ ] Tag git criada
- [ ] Versão testada em ambiente de desenvolvimento

## Exemplos Práticos

### Cenário 1: Correção de Bug
```
Versão atual: 0.0.1
Ação: Corrigir bug no tratamento de colisões
Nova versão: 0.0.2
```

### Cenário 2: Nova Funcionalidade
```
Versão atual: 0.0.2
Ação: Adicionar endpoint de listagem de URLs
Nova versão: 0.1.0
```

### Cenário 3: Mudança Incompatível
```
Versão atual: 0.5.0
Ação: Remover endpoint antigo /api/url
Nova versão: 1.0.0 (primeira versão estável)
```

### Cenário 4: Múltiplas Mudanças
```
Versão atual: 1.2.3
Ações:
  - Adicionar nova feature (MINOR)
  - Corrigir 2 bugs (PATCH)
Nova versão: 1.3.0 (MINOR tem prioridade)
```

## Referências

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Semantic Versioning em Português](https://semver.org/lang/pt-BR/)
- [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)

## Histórico de Versões do Projeto

| Versão | Data | Descrição |
|--------|------|-----------|
| 0.0.1 | 2024-01-15 | Versão inicial com funcionalidades básicas |
| 0.1.0 | 2026-01-27 | CRUD completo, tratamento de erros padronizado, HashGenerator Base 62 |

---

**Última atualização:** 2026-01-27
