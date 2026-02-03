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

## Proximos Passos Imediatos (Versao 0.1.0)

### Listagem Avancada (Filtros e Ordenacao)
- [ ] Adicionar filtros (por data de criacao, status, etc)
- [ ] Ordenacao configuravel (por cliques, data, etc)
- [ ] Metadados de paginacao (total_pages, has_next, has_previous)

### Otimizacoes de Performance
- [ ] Adicionar indices no banco de dados (short_code, original_url)
- [ ] Implementar cache layer para reads frequentes
- [ ] Query optimization com eager loading

### Customizacao de Short Code
- [ ] Permitir alias/custom short_code definido pelo usuario
- [ ] Validar custom codes para evitar conflitos com API routes
- [ ] Endpoint para gerenciar aliases

### Melhorias de Observabilidade
- [ ] Healthcheck endpoint (GET /health)
- [ ] Logs estruturados (JSON format)
- [ ] Tratamento de erros no conftest para testes mais robustos

---

## Funcionalidades Planejadas

### Alta Prioridade (Versao 0.2.0)

#### Customizacao de Short Code
- [x] Permitir short_code com 6 caracteres (ajustar SHORT_CODE_SIZE)
- [x] Validacao de caracteres permitidos
- [ ] Alias/custom short_code definido pelo usuario
- [ ] Endpoint para atualizar custom codes

#### Indices e Performance
- [ ] Adicionar indices no banco para campos frequentes (short_code, original_url)
- [ ] Query optimization
- [ ] Benchmark de performance

---

### Media Prioridade

#### Expiracao e TTL
- [ ] Definir tempo de validade da URL (tempo maximo e minimo)
- [ ] Campo expires_at no modelo
- [ ] Validacao de expiracao no redirecionamento
- [ ] Limpeza automatica de URLs expiradas (job/scheduler)

#### Metricas Avancadas

##### Historico de Cliques com Timestamps
- [ ] Criar tabela `clicks` para armazenar cada clique individualmente
  - [ ] Campos: id, url_id, clicked_at (timestamp), user_agent, referrer, ip_address
  - [ ] Relacionamento: Click belongsTo URL (foreign key)
  - [ ] Índice em url_id e clicked_at para queries rápidas
- [ ] Modificar método `get_original_url()` para salvar registro de clique
  - [ ] Manter incremento de click_count na tabela urls (cache)
  - [ ] Inserir novo registro na tabela clicks com timestamp
- [ ] Criar endpoint `GET /stats/{short_code}/clicks` para histórico
  - [ ] Paginação de cliques
  - [ ] Filtros por período (data início/fim)
  - [ ] Retornar: timestamp, user_agent, referrer, ip
- [ ] Endpoint `GET /stats/{short_code}/analytics`
  - [ ] Cliques por período (dia/semana/mês)
  - [ ] Gráfico de cliques ao longo do tempo
  - [ ] Agregações: cliques por hora do dia, dia da semana

##### Informações Adicionais de Cliques
- [ ] User-agent dos acessos (browser, SO, dispositivo)
- [ ] Referrer (origem do tráfego)
- [ ] Geolocalização básica (IP)

#### Seguranca e Controle
- [ ] Rate limiting para protecao contra abuso
- [ ] Blacklist/allowlist de dominios
- [ ] Validacao de URLs maliciosas

#### Observabilidade
- [ ] Healthcheck endpoint (GET /health)
- [ ] Logs estruturados (JSON)
- [ ] Metricas de performance

---

### Baixa Prioridade

#### Dashboard e Visualizacao
- [ ] Dashboard simples para estatisticas agregadas
- [ ] Graficos de cliques ao longo do tempo
- [ ] Top URLs mais acessadas

#### Melhorias de UX
- [ ] QR Code para URLs encurtadas
- [ ] Previa de destino (sem redirecionar)
- [ ] Modo de teste (preview mode)

---

## Requisitos Tecnicos

### Ajustes Necessarios
- [x] Reduzir SHORT_CODE_SIZE de 8 para 6 caracteres (conforme especificacao original)
- [ ] Adicionar indices no banco para performance
- [ ] Migracao para PostgreSQL (opcional, para producao)

### Infraestrutura
- [ ] Docker e docker-compose para dev
- [ ] CI/CD pipeline
- [ ] Deploy em producao (Railway, Render, AWS, etc)
