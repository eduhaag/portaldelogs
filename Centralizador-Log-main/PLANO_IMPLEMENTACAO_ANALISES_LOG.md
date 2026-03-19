# Plano de implementação das melhorias de análise de logs

## Objetivo

Transformar o estudo funcional em um backlog técnico executável, por fases, com foco em impacto, risco e reaproveitamento da arquitetura atual.

Documento-base relacionado:

- [ESTUDO_MELHORIAS_ANALISES_LOG.md](ESTUDO_MELHORIAS_ANALISES_LOG.md)

---

## Estratégia geral

A melhor sequência é:

1. **enriquecer o parser atual sem quebrar compatibilidade**
2. **adicionar payload especializado por subtipo**
3. **criar parsers dedicados para tipos com maior retorno**
4. **evoluir o frontend para filtros e KPIs específicos**
5. **adicionar correlação temporal e análises avançadas**

### Princípio técnico

Manter o fluxo atual do analisador e acrescentar uma nova camada de especialização:

- detecção do subtipo continua centralizada
- parsing estruturado continua sendo a base
- cada subtipo pode gerar `domain_fields`, `kpis`, `insights` e `recommendations`

Estrutura sugerida de resposta por evento e por análise:

```json
{
  "log_subtype": "progress_tabanalys",
  "category": "table_analysis",
  "domain_fields": {
    "table": "customer",
    "index": "idx_customer_01",
    "factor": 87.0,
    "records": 120000
  },
  "insight_tags": ["full_scan", "high_factor"],
  "recommendation_hint": "review_index"
}
```

---

## Fase 1 — Base de enriquecimento semântico

### Objetivo

Aproveitar o parser atual e enriquecer o payload dos subtipos mais valiosos sem reescrever tudo.

### Escopo

- `progress`
- `appserver`
- `appbroker`
- `acesso`
- `pasoe`

### Backend

#### 1. Criar contrato de especialização por subtipo

Adicionar no backend um padrão comum para resultados especializados.

### Tarefas

- criar estrutura padrão com:
  - `domain_fields`
  - `insight_tags`
  - `recommendation_hint`
- adicionar isso aos eventos retornados pelo parser estruturado
- garantir retrocompatibilidade com o payload atual

### Arquivos prováveis

- [backend/structured_log_parser.py](backend/structured_log_parser.py)
- [backend/log_analyzer.py](backend/log_analyzer.py)

#### 2. Enriquecer `progress`

### Extrair

- processo `P-`
- thread `T-`
- programa `.p/.w/.cls`
- procedure interna
- linha fonte
- código FT

### Tarefas

- ampliar regex e pós-processamento das mensagens Progress
- identificar nomes de programas e códigos de erro
- popular `domain_fields`

#### 3. Enriquecer `appserver` e `appbroker`

### Extrair

- broker
- agente
- processo
- programa
- tempo de execução
- sinais de indisponibilidade

### Tarefas

- criar heurísticas para `no agents available`, `broker is not available`, `dispatch request`, `agent process`
- classificar causa em:
  - indisponibilidade
  - saturação
  - crash
  - fila

#### 4. Enriquecer `acesso`

### Extrair

- IP
- método
- rota
- status
- bytes
- user agent, quando existir

### Tarefas

- ampliar parsing do access log
- gerar agregações iniciais:
  - top rotas
  - top erros 4xx/5xx
  - top IPs

#### 5. Enriquecer `pasoe`

### Extrair

- instância
- contexto web
- servlet/webhandler
- evento de lifecycle

### Tarefas

- separar `pasoe infra` de `pasoe app`
- detectar start/stop/deploy/failure

### Frontend

#### 6. Mostrar painéis por subtipo

### Tarefas

- exibir seção de KPIs quando `structured_analysis` estiver presente
- exibir filtros rápidos por subtipo detectado
- mostrar top subtipos, categorias e severidades

### Critério de pronto da fase 1

- resultados continuam compatíveis com a UI atual
- novos `domain_fields` passam a aparecer em eventos estruturados
- acesso, progress e appserver/appbroker já retornam dados úteis de domínio

---

## Fase 2 — Parsers dedicados de alto retorno

### Objetivo

Criar análise realmente especializada para os formatos onde o legado era muito mais rico.

### Escopo prioritário

- `progress_tabanalys`
- `progress_xref`
- `progress_memory`
- `progress_db`
- `logix`

### Backend

#### 1. Criar módulo para `progress_tabanalys`

### Estrutura sugerida

- novo parser dedicado, por exemplo:
  - `backend/parsers/progress_tabanalys_parser.py`

### Extrair

- tabela
- índice
- registros
- campos
- factor
- observação

### Entregas

- ranking de tabelas com pior fator
- ranking de índices problemáticos
- score de risco
- recomendações como:
  - revisar índice
  - revisar consulta
  - analisar full scan

#### 2. Criar módulo para `progress_xref`

### Extrair

- programa
- tipo de referência
- chave
- parâmetros
- retorno
- flags:
  - full scan
  - sequência
  - global
  - shared
  - persistente
  - traduzível

### Entregas

- breakdown por tipo XREF
- mapa de dependências
- alertas de risco estrutural

#### 3. Criar módulo para `progress_memory`

### Extrair

- processo
- objeto
- handle
- tipo
- categoria

### Entregas

- agrupamento por objeto/handle
- ranking de reincidência
- alertas de vazamento persistente

#### 4. Criar módulo para `progress_db`

### Subcategorias

- conectividade
- login broker
- schema holder
- latch/lock
- BI/AI
- corrupção/estrutura

### Entregas

- breakdown por subcategoria DB
- timeline de falhas
- recomendações por cenário

#### 5. Criar parser estruturado para `LOGIX`

### Separar

- LOGIX com SQL
- LOGIX sem SQL

### Extrair

- thread
- status
- rows affected
- programa
- linha
- execução
- comando SQL

### Entregas

- top comandos lentos
- top programas críticos
- modo somente erros
- score de impacto SQL

### Arquivos prováveis

- [backend/log_analyzer.py](backend/log_analyzer.py)
- [backend/server.py](backend/server.py)
- novos módulos em `backend/`

### Frontend

#### 6. Criar visões específicas por família

### Tarefas

- tabela específica para `tabanalys`
- tabela específica para `xref`
- visão operacional para `logix`
- cartões de resumo por subtipo

### Critério de pronto da fase 2

- parsers dedicados retornam payload especializado
- o frontend consegue renderizar visões orientadas ao tipo
- tipos de maior valor deixam de ser apenas “classificados” e passam a ser “analisados”

---

## Fase 3 — Tipos novos e diferenciais analíticos

### Objetivo

Adicionar capacidades ainda não modeladas claramente no sistema atual.

### Escopo

- `thread dump`
- `webspeed`
- correlação temporal entre famílias
- comparação entre execuções

### Backend

#### 1. Criar analisador de `thread dump`

### Módulo sugerido

- `backend/thread_dump_analyzer.py`

### Extrair

- nome da thread
- estado
- daemon
- stack principal
- locks/monitores
- recurso aguardado

### Entregas

- total por estado
- agrupamento por assinatura de stack
- suspeita de deadlock
- threads repetitivas
- top classes/métodos dominantes

#### 2. Criar subtipo explícito `webspeed`

### Tarefas

- detectar assinaturas típicas
- separar de `appserver` e `pasoe` quando aplicável
- extrair broker/agente/programa web

#### 3. Correlação temporal

### Casos prioritários

- `acesso` + `tomcat/pasoe`
- `appbroker` + `appserver`
- `progress_db` + `appserver`
- `thread dump` + lentidão web

### Entregas

- linha do tempo correlacionada
- insights de causa provável

#### 4. Comparação entre execuções

### Casos

- profiler A vs profiler B
- log de hoje vs log de ontem
- comportamento por janela temporal

### Critério de pronto da fase 3

- thread dump passa a ser analisado semanticamente
- webspeed vira subtipo explícito
- o sistema começa a explicar relações entre eventos, não apenas listá-los

---

## Fase 4 — Evolução de UX analítica

### Objetivo

Levar a riqueza do backend para a interface.

### Tarefas frontend

1. Filtros dinâmicos por família
2. KPIs por subtipo
3. ranking e agrupamentos por assinatura
4. timeline com correlação
5. exportação do recorte filtrado
6. modo “somente erros” onde fizer sentido

### Componentes prováveis

- cards de KPI
- grids dinâmicos por tipo
- filtros contextuais
- modal de detalhe por evento
- timeline agrupada

---

## Backlog técnico objetivo

## Sprint 1

- criar contrato `domain_fields/insight_tags/recommendation_hint`
- enriquecer `progress`
- enriquecer `appserver`
- enriquecer `appbroker`
- enriquecer `acesso`
- criar testes unitários dessas extrações

## Sprint 2

- parser dedicado `progress_tabanalys`
- parser dedicado `progress_memory`
- parser dedicado `progress_db`
- testes com amostras reais/sintéticas

## Sprint 3

- parser dedicado `progress_xref`
- parser `logix` estruturado
- breakdowns e KPIs específicos
- primeiras telas especializadas no frontend

## Sprint 4

- analisador de `thread dump`
- subtipo `webspeed`
- correlação temporal inicial
- cards e timeline avançada

---

## Testes recomendados

### Backend

- testes por subtipo com amostras curtas e amostras reais
- testes de regressão para não quebrar payload antigo
- testes de performance em logs grandes
- testes de agrupamento por assinatura

### Frontend

- renderização condicional por subtipo
- filtros específicos
- comportamento com payload parcial
- comportamento com logs mistos

---

## Ordem ideal de implementação

### Mais retorno imediato

1. enriquecer `progress`
2. enriquecer `appserver/appbroker`
3. enriquecer `acesso`
4. parser `progress_tabanalys`
5. parser `progress_xref`
6. parser `logix`

### Diferenciais depois

7. parser `thread dump`
8. subtipo `webspeed`
9. correlação temporal
10. comparação entre execuções

---

## Recomendação final

Se for para começar agora com o melhor custo-benefício, a primeira entrega ideal é:

- **Fase 1 completa**
- seguida de **`progress_tabanalys` + `progress_xref` + `LOGIX`**

Isso produz o maior salto percebido na qualidade da análise sem exigir reestruturação total da aplicação.