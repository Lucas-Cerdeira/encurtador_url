# Documentação de Analytics - Sistema de Encurtamento de URLs

## 📊 Visão Geral para Analistas de Dados

Este documento descreve os dados de cliques disponíveis para análise e os insights que podem ser extraídos.

---

## 🗃️ Estrutura dos Dados

### Tabela: `clicks`

Cada registro representa **um clique individual** em uma URL encurtada.

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `id` | Integer | Identificador único do clique | 12345 |
| `url_id` | Integer | ID da URL encurtada (FK) | 42 |
| `clicked_at` | DateTime | Timestamp exato do clique | 2026-02-02 14:35:22 |
| `user_agent` | String | Informações do navegador/dispositivo | "Mozilla/5.0 (iPhone; ..." |
| `referrer` | String | URL de origem do tráfego | "https://instagram.com/..." |
| `ip_address` | String | Endereço IP do visitante | "201.23.45.67" |

### Tabela: `urls`

Informações sobre as URLs encurtadas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | Identificador único |
| `short_code` | String | Código curto (6 caracteres) |
| `original_url` | String | URL de destino |
| `click_count` | Integer | Total de cliques (cache) |
| `created_at` | DateTime | Data de criação da URL |

---

## 📈 Análises Disponíveis

### 1. **Análise Temporal**

**Perguntas de Negócio:**
- Qual horário do dia tem mais cliques?
- Qual dia da semana é mais efetivo?
- Como o tráfego evoluiu ao longo do tempo?
- Existem picos sazonais?

**Dimensões Temporais:**
```sql
-- Hora do dia (0-23)
EXTRACT(HOUR FROM clicked_at) as hour

-- Dia da semana (0=Domingo, 6=Sábado)
EXTRACT(DOW FROM clicked_at) as day_of_week

-- Dia do mês
DATE(clicked_at) as date

-- Semana do ano
EXTRACT(WEEK FROM clicked_at) as week_number
```

**Exemplo de Insight:**
> "O pico de cliques ocorre entre 20h-22h (horário noturno), com 45% dos cliques concentrados nesse período. Considere agendar posts importantes nesse horário."

---

### 2. **Análise de Fontes de Tráfego (Referrer)**

**Perguntas de Negócio:**
- De onde vêm nossos visitantes?
- Qual canal de marketing é mais efetivo?
- Quais posts/páginas geram mais cliques?

**Classificação de Fontes:**

| Padrão do Referrer | Fonte | Tipo |
|-------------------|-------|------|
| `instagram.com`, `facebook.com`, `twitter.com` | Redes Sociais | Social |
| `google.com`, `bing.com` | Buscadores | Organic Search |
| `youtube.com` | Vídeo | Video |
| `NULL` ou vazio | Direto | Direct |
| `t.co` (Twitter), `l.instagram.com` | Link Shortener | Social (encadeado) |

**Query de Exemplo:**
```sql
SELECT 
  CASE 
    WHEN referrer LIKE '%instagram%' THEN 'Instagram'
    WHEN referrer LIKE '%facebook%' THEN 'Facebook'
    WHEN referrer LIKE '%twitter%' OR referrer LIKE '%t.co%' THEN 'Twitter'
    WHEN referrer LIKE '%google%' THEN 'Google Search'
    WHEN referrer IS NULL THEN 'Direct'
    ELSE 'Other'
  END as source,
  COUNT(*) as clicks,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM clicks
GROUP BY source
ORDER BY clicks DESC;
```

**Exemplo de Insight:**
> "Instagram representa 65% do tráfego, seguido por Facebook (20%) e tráfego direto (15%). O ROI da campanha no Instagram está superando outras plataformas."

---

### 3. **Análise de Dispositivos (User-Agent)**

**Perguntas de Negócio:**
- Mobile ou Desktop?
- Quais navegadores nossos usuários usam?
- Qual sistema operacional predomina?

**Extração do User-Agent:**

| Padrão | Tipo de Dispositivo |
|--------|---------------------|
| `Mobile`, `iPhone`, `Android` | Mobile |
| `iPad`, `Tablet` | Tablet |
| `Windows`, `Macintosh`, `Linux` (sem Mobile) | Desktop |

| Padrão | Navegador |
|--------|-----------|
| `Chrome` | Google Chrome |
| `Safari` | Apple Safari |
| `Firefox` | Mozilla Firefox |
| `Edg` | Microsoft Edge |

**Query de Exemplo:**
```sql
SELECT 
  CASE 
    WHEN user_agent LIKE '%Mobile%' OR user_agent LIKE '%Android%' 
         OR user_agent LIKE '%iPhone%' THEN 'Mobile'
    WHEN user_agent LIKE '%iPad%' OR user_agent LIKE '%Tablet%' THEN 'Tablet'
    ELSE 'Desktop'
  END as device_type,
  COUNT(*) as clicks,
  ROUND(AVG(CASE WHEN /* conversão aconteceu */ THEN 1 ELSE 0 END) * 100, 2) as conversion_rate
FROM clicks
GROUP BY device_type;
```

**Exemplo de Insight:**
> "78% dos cliques vêm de dispositivos móveis, mas a taxa de conversão no desktop é 2x maior (40% vs 20%). Considere otimizar a experiência mobile para aumentar conversões."

---

### 4. **Análise Geográfica (IP Address)**

**Perguntas de Negócio:**
- De quais países/regiões vêm os visitantes?
- Existem diferenças de comportamento por localização?
- Onde focar campanhas regionais?

**Processo:**
1. IP → Geolocalização (usar serviço como MaxMind GeoIP2, IP2Location)
2. Obter: País, Estado/Região, Cidade

**Dimensões Geográficas:**
- País (ISO code: BR, US, PT, etc.)
- Estado/Província
- Cidade
- Continente
- Fuso horário

**Exemplo de Insight:**
> "Brasil representa 60% do tráfego (SP: 35%, RJ: 15%, MG: 10%). Portugal contribui com 25% e EUA com 15%. Considere criar conteúdo específico para mercado português."

---

### 5. **Análise de Performance de URLs**

**Perguntas de Negócio:**
- Quais URLs têm melhor performance?
- Quais campanhas geraram mais engajamento?
- Existe correlação entre fonte e URL?

**Métricas por URL:**
```sql
SELECT 
  u.short_code,
  u.original_url,
  COUNT(c.id) as total_clicks,
  COUNT(DISTINCT DATE(c.clicked_at)) as days_active,
  ROUND(COUNT(c.id)::NUMERIC / COUNT(DISTINCT DATE(c.clicked_at)), 2) as avg_clicks_per_day,
  MAX(c.clicked_at) as last_click
FROM urls u
LEFT JOIN clicks c ON u.id = c.url_id
GROUP BY u.id, u.short_code, u.original_url
ORDER BY total_clicks DESC
LIMIT 20;
```

**Exemplo de Insight:**
> "A URL 'promocao-black-friday' teve 2.500 cliques em 3 dias (833 cliques/dia), 5x acima da média. O padrão de sucesso: divulgação no Instagram às 20h + stories."

---

### 6. **Detecção de Anomalias e Fraudes**

**Perguntas de Negócio:**
- Existem bots ou tráfego falso?
- Há tentativas de manipulação de métricas?

**Indicadores de Suspeita:**
- Múltiplos cliques do mesmo IP em curto período
- User-agent suspeito (bots conhecidos)
- Padrão de cliques muito regular (não humano)

**Query de Detecção:**
```sql
-- IPs com cliques suspeitos
SELECT 
  ip_address,
  COUNT(*) as clicks,
  COUNT(DISTINCT url_id) as different_urls,
  MIN(clicked_at) as first_click,
  MAX(clicked_at) as last_click,
  EXTRACT(EPOCH FROM (MAX(clicked_at) - MIN(clicked_at))) as duration_seconds,
  ROUND(COUNT(*)::NUMERIC / NULLIF(EXTRACT(EPOCH FROM (MAX(clicked_at) - MIN(clicked_at))), 0) * 3600, 2) as clicks_per_hour
FROM clicks
WHERE clicked_at > NOW() - INTERVAL '1 day'
GROUP BY ip_address
HAVING COUNT(*) > 100
ORDER BY clicks DESC;
```

**Exemplo de Insight:**
> "IP 203.45.67.89 gerou 1.200 cliques em 2 horas (600 cliques/hora) - padrão de bot. Recomenda-se filtrar esses cliques das métricas de campanha."

---

## 🎯 Dashboards Recomendados

### Dashboard 1: Visão Geral
- **KPIs:** Total de cliques, URLs ativas, cliques hoje vs ontem
- **Gráfico:** Cliques ao longo do tempo (linha)
- **Breakdown:** Top 5 URLs por cliques

### Dashboard 2: Fontes de Tráfego
- **Gráfico de pizza:** Distribuição por fonte (Instagram, Facebook, etc.)
- **Tabela:** Fonte → Cliques → Taxa de crescimento semana a semana
- **Tendência:** Evolução de cada fonte ao longo do tempo

### Dashboard 3: Dispositivos e Tecnologia
- **Gráfico de barras:** Mobile vs Desktop vs Tablet
- **Tabela:** Top navegadores e sistemas operacionais
- **Segmentação:** Device type + Source (Mobile do Instagram, etc.)

### Dashboard 4: Geografia
- **Mapa de calor:** Cliques por país
- **Tabela:** Top cidades/regiões
- **Comparativo:** Performance por região

---

## 🔍 Queries SQL Úteis

### Top URLs da Semana
```sql
SELECT 
  u.short_code,
  u.original_url,
  COUNT(c.id) as clicks_this_week
FROM urls u
JOIN clicks c ON u.id = c.url_id
WHERE c.clicked_at >= DATE_TRUNC('week', NOW())
GROUP BY u.id, u.short_code, u.original_url
ORDER BY clicks_this_week DESC
LIMIT 10;
```

### Análise Hora × Dia da Semana (Heatmap)
```sql
SELECT 
  EXTRACT(DOW FROM clicked_at) as day_of_week,
  EXTRACT(HOUR FROM clicked_at) as hour,
  COUNT(*) as clicks
FROM clicks
WHERE clicked_at >= NOW() - INTERVAL '30 days'
GROUP BY day_of_week, hour
ORDER BY day_of_week, hour;
```

### Taxa de Retenção de Audiência
```sql
-- URLs que mantêm cliques consistentes
SELECT 
  u.short_code,
  COUNT(DISTINCT DATE(c.clicked_at)) as active_days,
  STDDEV(daily_clicks) as consistency
FROM urls u
JOIN clicks c ON u.id = c.url_id
JOIN (
  SELECT url_id, DATE(clicked_at) as date, COUNT(*) as daily_clicks
  FROM clicks
  GROUP BY url_id, DATE(clicked_at)
) daily ON daily.url_id = u.id
GROUP BY u.id, u.short_code
HAVING COUNT(DISTINCT DATE(c.clicked_at)) >= 7
ORDER BY consistency ASC;  -- Menor desvio = mais consistente
```

---

## 📋 Checklist de Análise Semanal

- [ ] Comparar cliques semana atual vs anterior (crescimento %)
- [ ] Identificar top 5 URLs e fontes de tráfego
- [ ] Verificar anomalias (picos, quedas, bots)
- [ ] Analisar horários de maior engajamento
- [ ] Avaliar performance mobile vs desktop
- [ ] Revisar distribuição geográfica
- [ ] Identificar oportunidades (fontes sub-exploradas, horários ociosos)

---

## 💡 Dicas para Análise

1. **Compare períodos:** Sempre compare com semana/mês anterior para identificar tendências
2. **Segmente:** Não analise apenas totais, segmente por fonte, dispositivo, geografia
3. **Contextualize:** Relacione picos/quedas com eventos (postagens, campanhas, feriados)
4. **Filtre ruído:** Remova bots e tráfego suspeito antes de análises de comportamento
5. **Cruze dados:** Combine dimensões (Ex: Mobile + Instagram + Noite)

---

## 🔐 Considerações de Privacidade

- **IPs são dados pessoais**: Seguir LGPD/GDPR
- **Anonimização**: Considere agregar dados antes de compartilhar
- **Retenção**: Política de expiração de dados (ex: 90 dias)
- **Acesso**: Dados sensíveis devem ter acesso controlado

---

## 📚 Casos de Uso por Campo

### User-Agent
**Utilidade:**
- Identificar dispositivos (mobile vs desktop)
- Navegadores mais usados
- Sistemas operacionais
- Detecção de bots

**Exemplo:**
```
"Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)"
→ iPhone, Safari, iOS 14.6
```

### Referrer
**Utilidade:**
- Identificar canais de marketing efetivos
- Rastrear origem do tráfego
- Avaliar ROI de campanhas
- Identificar posts virais

**Exemplo:**
```
"https://instagram.com/p/ABC123"
→ Tráfego vindo de post específico no Instagram
```

### IP Address
**Utilidade:**
- Geolocalização (país, estado, cidade)
- Detecção de fraude/bots
- Análise de distribuição geográfica
- Segmentação regional

**Exemplo:**
```
"201.23.45.67" + GeoIP → São Paulo, Brasil
```

---

**Última atualização:** 2026-02-02  
**Versão:** 1.0  
**Autor:** Time de Engenharia  
**Contato:** Consulte o time de dados para dúvidas sobre análises
