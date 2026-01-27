Features Encurtador URL

## Funcionalidades Implementadas

### Encurtamento de URLs
- [x] Receber URL longa e retornar URL encurtada
- [x] Geracao de short_code com 8 caracteres (nanoid)
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

---

## Funcionalidades Planejadas

### Alta Prioridade

#### CRUD Completo de URLs
- [ ] Listar todas as URLs (GET /urls)
- [ ] Atualizar URL original (PUT /urls/{id} ou PATCH /urls/{id})
- [ ] Remover URL (DELETE /urls/{id})
- [ ] Filtros e paginacao na listagem

#### Tratamento de Erros
- [ ] Padrao consistente de respostas de erro
- [ ] Validacoes robustas de entrada
- [ ] Codigos HTTP apropriados
- [ ] Mensagens de erro descritivas

#### Customizacao de Short Code
- [x] Permitir short_code com 6 caracteres (ajustar SHORT_CODE_SIZE)
- [ ] Alias/custom short_code definido pelo usuario
- [x] Validacao de caracteres permitidos

#### Modulo Gerador de ID
- [x] Criar modulo dedicado para geracao de IDs
- [x] Implementar gerador usando Base 62 (A-Z, a-z, 0-9)
- [x] Garantir unicidade e colisao minima
- [x] Suportar configuracao de tamanho do ID gerado (1-6 caracteres)
- [x] Permitir troca facil entre diferentes algoritmos (estrutura escalavel)

---

### Media Prioridade

#### Expiracao e TTL
- [ ] Definir tempo de validade da URL (tempo maximo e minimo)
- [ ] Campo expires_at no modelo
- [ ] Validacao de expiracao no redirecionamento
- [ ] Limpeza automatica de URLs expiradas (job/scheduler)

#### Metricas Avancadas
- [ ] Cliques por periodo (dia/mes/ano/hora/minuto/segundo)
- [ ] Armazenar timestamp de cada clique
- [ ] User-agent dos acessos
- [ ] Referrer (origem do trafego)
- [ ] Geolocalizacao basica (IP)

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
