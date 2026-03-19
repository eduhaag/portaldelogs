# Estudo detalhado de melhorias nas análises de logs

## Objetivo

Avaliar o que o analisador atual já cobre, o que existia no legado e o que ainda pode ser melhorado para cada família de log.

A análise foi baseada em:

- fonte legado ABL do `LogAnalys`
- exemplos de logs anexados ao pacote legado
- implementação atual do backend
- testes atuais de cobertura de famílias e subtipos

---

## 1. Cobertura atual já existente

Hoje o backend já reconhece e testa explicitamente estas famílias/subtipos:

- `acesso`
- `tomcat`
- `jboss`
- `fluig`
- `pasoe`
- `appserver`
- `appbroker`
- `progress_db`
- `progress_memory`
- `progress_tabanalys`
- `progress_xref`
- `app_performance`
- `progress`

Evidências principais:

- [backend/test_supported_log_families.py](backend/test_supported_log_families.py#L1-L124)
- [backend/structured_log_parser.py](backend/structured_log_parser.py#L412-L518)
- [backend/profiler_analyzer.py](backend/profiler_analyzer.py#L383-L500)

### Conclusão rápida

O projeto atual **já superou o legado em cobertura estrutural bruta** para vários tipos, porque existe parser estruturado, categorização, severidade, breakdown por subtipo e testes automatizados.

O principal espaço de evolução não é apenas "detectar mais logs", mas sim:

1. **extrair campos especializados por família**
2. **mostrar KPIs e filtros próprios de cada tipo**
3. **dar diagnósticos mais orientados ao domínio**
4. **tratar formatos especiais ainda não modelados**

---

## 2. Diferença central entre legado e sistema atual

### Legado

O legado era muito forte em:

- separação por família de log
- tabelas específicas por tipo
- filtros específicos por domínio
- exportação do recorte analisado
- visualização operacional detalhada

### Atual

O sistema atual é forte em:

- parser unificado
- classificação automática por subtipo
- categorização por severidade/categoria
- base de padrões Datasul/LOGIX/TOTVS
- API moderna
- possibilidade de UI mais rica

### Gap real

O maior gap hoje é **modelagem especializada por subtipo**.

Exemplo:

- o parser atual identifica `progress_tabanalys`
- mas ainda não transforma isso em uma visão rica com `tabela`, `índice`, `fator`, `registros`, `observação`, ranking de pior caso e recomendações específicas

---

## 3. Estudo por família de log

## 3.1 JBoss

### O que existia no legado

O legado tratava JBoss como família própria, com foco em:

- tipo
- categoria
- data/hora
- detalhes
- conteúdo integral

### O que já existe hoje

- detecção de subtipo `jboss`
- categorização de mensagens Java em `exception`, `performance`, `http`, `security`, `database`, `lifecycle`, `application`
- parser estruturado para logs Java

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L412-L441)
- [backend/test_supported_log_families.py](backend/test_supported_log_families.py#L15-L27)

### Melhorias recomendadas

1. Extrair `logger`, `classe`, `thread`, `deployment`, `operation code` e `stack root cause`
2. Agrupar exceções por assinatura
3. Destacar falhas de deploy, datasource, Undertow e WildFly management
4. Criar ranking de erros recorrentes por minuto/período
5. Separar erro real de cascata de stacktrace

### Prioridade

**Média**. A base já existe, mas falta enriquecer o payload.

---

## 3.2 Tomcat / PASOE web container

### O que existia no legado

Tomcat era tratado em visão própria, semelhante a JBoss, mas com uso operacional voltado a web/app server.

### O que já existe hoje

- detecção `tomcat`
- detecção `pasoe`
- categorização Java e Progress mistos
- reconhecimento de tokens como `catalina`, `webhandler`, `msagent`, `oepas`

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L423-L473)
- [backend/test_pasoe_appserver.py](backend/test_pasoe_appserver.py#L1-L154)

### Melhorias recomendadas

1. Separar claramente:
   - Tomcat puro
   - PASOE infra
   - PASOE ABL app
2. Extrair nome da instância, webapp, endpoint, servlet e contexto
3. Marcar eventos de ciclo de vida:
   - start
   - stop
   - deploy
   - undeploy
   - restart
4. Detectar indisponibilidade por janela de tempo
5. Mapear erros HTTP 500/503 ao stacktrace ou causa raiz seguinte
6. Identificar saturação de pool, timeout de sessão, WebHandler e OEABL security

### Prioridade

**Alta**. É uma das áreas com maior valor operacional.

---

## 3.3 Logs de acesso

### O que existia no legado

Havia tipo específico de acesso JBoss/Tomcat.

### O que já existe hoje

- parser de access log
- categorização por status HTTP
- subtipo `acesso`

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L110-L143)
- [backend/test_supported_log_families.py](backend/test_supported_log_families.py#L10-L18)

### Melhorias recomendadas

1. Extrair e expor:
   - método
   - rota
   - status
   - bytes
   - IP
   - user agent
   - latência, quando disponível
2. KPIs automáticos:
   - taxa de erro 4xx/5xx
   - top rotas lentas
   - top IPs com erro
   - top endpoints por volume
3. Detectar picos por janela temporal
4. Separar falha de aplicação de falha de cliente
5. Correlacionar acesso 500 com evento Tomcat/PASOE/JBoss próximo no tempo

### Prioridade

**Alta**. Hoje já detecta, mas ainda não entrega análise operacional completa.

---

## 3.4 Fluig

### O que existia no legado

Fluig aparecia como família própria no menu do legado.

### O que já existe hoje

- detecção de subtipo `fluig`
- categorização Java
- identificação por tokens de engine/dataset/document service

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L412-L441)
- [backend/test_supported_log_families.py](backend/test_supported_log_families.py#L24-L27)

### Melhorias recomendadas

1. Extrair dataset, serviço, tenant, usuário e processo quando existirem no log
2. Criar regras específicas para:
   - timeout de dataset
   - erro de workflow
   - documento/ECM
   - autenticação
3. Agrupar por serviço Fluig afetado
4. Sugerir causa funcional além da técnica

### Prioridade

**Média**.

---

## 3.5 Progress Client / Progress genérico

### O que existia no legado

Era uma visão rica com campos como:

- processo
- programa
- PI
- linha do programa
- categoria
- conteúdo
- filtros por data/hora/processo/categoria/programa/PI/conteúdo

### O que já existe hoje

- subtipo `progress`
- parsing estruturado de linhas OpenEdge/Progress
- categorias gerais como `application`, `database`, `performance`, `security`, `availability`

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L444-L501)

### Melhorias recomendadas

1. Extrair de forma estruturada:
   - processo `P-`
   - thread `T-`
   - programa `.p/.w/.cls`
   - procedure interna
   - linha fonte
   - código FT
2. Agrupar por programa e procedimento
3. Mostrar ranking de programas com mais erro
4. Separar erro funcional de erro infra
5. Criar filtros equivalentes ao legado
6. Detectar chamadas recorrentes ao mesmo programa em curto intervalo

### Prioridade

**Muito alta**. O parser já reconhece, mas a exploração analítica ainda está aquém do legado.

---

## 3.6 Progress Profiler

### O que existia no legado

O legado tinha análise bastante rica de profiler:

- sessão
- estatísticas por fonte
- estatísticas por linha
- árvore de chamadas
- buscas
- totais

### O que já existe hoje

O módulo atual já está bem alinhado ao legado:

- parser dedicado
- resumo da sessão
- top módulos por tempo/chamadas/média
- top linhas
- call tree
- gargalos
- suspeitas de N+1
- recomendações

Referências:

- [backend/profiler_analyzer.py](backend/profiler_analyzer.py#L383-L500)
- [backend/test_profiler_analyzer.py](backend/test_profiler_analyzer.py#L1-L65)

### Melhorias recomendadas

1. Comparação entre duas execuções de profiler
2. Heatmap por programa/linha
3. Agrupamento por pacote ou módulo funcional
4. Score de regressão de performance
5. Indicação automática de "alto custo total" vs "alto custo médio" vs "alta cardinalidade"

### Prioridade

**Baixa a média**. Já está maduro; aqui o ganho é refinamento.

---

## 3.7 Progress Memory Leak

### O que existia no legado

O legado tratava explicitamente:

- processo
- tipo/objeto
- handle
- categoria
- detalhe completo
- filtros por processo e conteúdo

### O que já existe hoje

- subtipo `progress_memory`
- detecção por palavras como `memory leak`, `handle`, `object`, `heap`
- categoria `memory`

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L449-L489)
- [backend/test_supported_log_families.py](backend/test_supported_log_families.py#L47-L57)

### Melhorias recomendadas

1. Extrair objeto, handle, tipo e processo
2. Agrupar vazamentos por handle e por tipo de objeto
3. Detectar crescimento temporal do mesmo objeto
4. Sugerir configuração faltante de `LogEntryTypes` quando o log não tem granularidade suficiente
5. Gerar ranking de objetos mais reincidentes

### Prioridade

**Alta**. Há espaço para entregar valor bem específico.

---

## 3.8 Progress Database

### O que existia no legado

O legado organizava por categoria e linha, com filtros por período e exportação por categoria.

### O que já existe hoje

- subtipo `progress_db`
- categoria `database`
- detecção por tokens como `database`, `schema holder`, `biw`, `aiw`, `latch`, `login broker`

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L456-L501)
- [backend/test_supported_log_families.py](backend/test_supported_log_families.py#L42-L52)

### Melhorias recomendadas

1. Subcategorizar:
   - conectividade
   - schema holder
   - latch/lock
   - BI/AI
   - login broker
   - corrupção/estrutura
2. Extrair nome do banco afetado
3. Timeline de indisponibilidade
4. Ranking por categoria DB
5. Recomendação automática por tipo de falha

### Prioridade

**Alta**.

---

## 3.9 Progress Tabanalys

### O que existia no legado

Muito rico em estrutura:

- categoria
- tabela
- índice
- registros
- campos
- fator
- observação
- alternância entre visão de tabela e visão de índice

### O que já existe hoje

- subtipo `progress_tabanalys`
- categoria `table_analysis`
- detecção por termos como `table scan`, `index`, `factor`

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L454-L489)
- [backend/test_supported_log_families.py](backend/test_supported_log_families.py#L52-L62)

### Melhorias recomendadas

1. Criar parser dedicado para extrair:
   - tabela
   - índice
   - registros
   - campos
   - factor
   - observação
2. Exibir ranking das piores tabelas e índices
3. Sugerir necessidade de índice ou revisão de consulta
4. Separar problema por tabela vs problema por índice
5. Gerar score de risco por fator

### Prioridade

**Muito alta**. É um dos maiores gaps entre reconhecimento e análise especializada.

---

## 3.10 Progress XREF

### O que existia no legado

Era uma das visões mais especializadas do legado, com categorias como:

- tabelas
- criação
- leitura
- atualização
- eliminação
- acesso
- includes
- funções
- procedures
- procedures externas
- variáveis globais
- execução
- strings

Além disso, o legado mostrava flags como:

- full scan
- sequência
- global
- shared
- persistente
- traduzível

### O que já existe hoje

- subtipo `progress_xref`
- categoria `xref`
- detecção por `xref`, `include file`, `caller`, `callee`

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L456-L489)
- [backend/test_supported_log_families.py](backend/test_supported_log_families.py#L57-L65)

### Melhorias recomendadas

1. Criar parser específico de XREF
2. Extrair:
   - programa
   - tipo de entrada
   - chave/tabela/procedure/include
   - parâmetros
   - retorno
   - flags booleanas
3. Permitir filtros por categoria XREF, como no legado
4. Detectar riscos:
   - full scan
   - uso excessivo de globais/shared
   - RUN persistente
5. Produzir análise de dependência entre programas

### Prioridade

**Muito alta**. O subtipo já existe, mas a análise rica ainda não existe.

---

## 3.11 AppServer / AppBroker / App Performance

### O que existia no legado

O legado separava:

- AppServer Progress
- AppServer limpa log
- AppServer performance
- AppServer broker
- WebSpeed Progress
- WebSpeed limpa log

Isso mostra que havia uma visão mais operacional e segmentada da camada de aplicação.

### O que já existe hoje

- subtipo `appserver`
- subtipo `appbroker`
- subtipo `app_performance`
- categorização por disponibilidade/performance
- detecção de mensagens de broker e servidor

Referências:

- [backend/structured_log_parser.py](backend/structured_log_parser.py#L447-L501)
- [backend/test_structured_log_subtypes.py](backend/test_structured_log_subtypes.py#L1-L81)
- [backend/test_pasoe_appserver.py](backend/test_pasoe_appserver.py#L1-L154)

### Melhorias recomendadas

1. Separar melhor os domínios:
   - broker indisponível
   - agent indisponível
   - fila/dispatch
   - appserver crash/stop
   - lentidão de programa
2. Extrair processo, agente, broker, serviço, programa e duração
3. KPIs:
   - frequência de queda
   - tempo entre quedas
   - programas mais lentos
   - erros por agente
4. Criar análise específica para `no agents available`
5. Identificar indícios de saturação ou esgotamento de pool

### Prioridade

**Muito alta**.

---

## 3.12 WebSpeed

### O que existia no legado

O legado tinha entradas dedicadas para WebSpeed.

### O que já existe hoje

Não foi encontrada modelagem explícita de subtipo `webspeed` no parser atual. Em muitos casos, ele deve cair em `progress`, `pasoe` ou `appserver`, dependendo do conteúdo.

### Gap

Falta suporte explícito de classificação e visão dedicada.

### Melhorias recomendadas

1. Criar subtipo `webspeed`
2. Detectar assinaturas típicas de agente/broker/CGI/web object
3. Extrair procedimento web, broker, agente e tempos
4. Criar correlação com logs de acesso
5. Dar recomendações específicas para fila, sessão e conectividade

### Prioridade

**Alta**.

---

## 3.13 LOGIX

### O que existia no legado

O legado tinha duas variações:

- LOGIX com SQL
- LOGIX sem SQL

E uma visão rica com campos como:

- thread
- status
- rows affected
- programa
- linhas de programa
- tempo de execução
- comando
- somente erros

### O que já existe hoje

- detecção de tipo LOGIX
- base de padrões LOGIX carregável
- busca dedicada de padrões LOGIX

Referências:

- [backend/test_logix_detection.py](backend/test_logix_detection.py#L1-L70)
- [backend/server.py](backend/server.py#L815-L834)

### Gap

O sistema atual está forte em **base de conhecimento de erro LOGIX**, mas ainda fraco em **parser operacional especializado de log LOGIX**.

### Melhorias recomendadas

1. Criar parser estruturado para LOGIX
2. Separar LOGIX com SQL vs sem SQL
3. Extrair:
   - thread
   - status
   - rows affected
   - programa
   - linha do programa
   - tempo de execução
   - comando SQL
4. KPI de SQL lento e volume por programa
5. Ranking de comandos com maior impacto
6. Modo "somente erros", como no legado

### Prioridade

**Muito alta**.

---

## 3.14 Thread dump Java

### Evidência

O pacote legado inclui exemplo de `thread dump`, com estados e stack traces detalhados.

### O que já existe hoje

Não foi encontrada análise dedicada para thread dump.

### Gap

Hoje um thread dump tende a ser tratado como texto genérico ou como fragmentos Java, sem leitura semântica real.

### Melhorias recomendadas

1. Criar analisador específico de thread dump
2. Extrair por thread:
   - nome
   - estado
   - daemon ou não
   - stack principal
   - lock/monitor
   - recurso aguardado
3. KPIs:
   - total por estado
   - bloqueadas
   - waiting/timed_waiting
   - threads RUNNABLE repetitivas
4. Detectar padrões de risco:
   - deadlock potencial
   - pool preso
   - RMI congestionado
   - repetição de stack semelhante
5. Agrupar threads por assinatura de stack
6. Destacar classes/métodos dominantes

### Prioridade

**Muito alta**. É um ganho novo e de alto valor investigativo.

---

## 4. Melhorias transversais recomendadas

## 4.1 Payload tipado por subtipo

Hoje o sistema classifica bem, mas ainda precisa devolver um bloco mais rico por família, por exemplo:

```json
{
  "log_subtype": "progress_tabanalys",
  "domain_fields": {
    "table": "customer",
    "index": "idx_customer_01",
    "factor": 87.0,
    "records": 120000,
    "observation": "full table scan"
  }
}
```

Isso destrava frontend realmente especializado.

## 4.2 Filtros por família

Replicar a ideia mais valiosa do legado:

- filtros dinâmicos conforme o tipo
- não apenas busca textual genérica

## 4.3 Correlação temporal

Cruzar eventos próximos no tempo entre:

- acesso + tomcat/pasoe
- broker + appserver
- appserver + progress DB
- thread dump + lentidão web

## 4.4 Agrupamento por assinatura

Para reduzir ruído:

- agrupar stacktraces iguais
- agrupar erros repetidos com mesmos códigos
- agrupar linhas equivalentes com normalização

## 4.5 Recomendações especializadas

Hoje já existe recomendação em parte do sistema. O ideal é evoluir para recomendações por subtipo:

- DB
- memory
- xref
- tabanalys
- logix SQL
- PASOE/Tomcat
- thread dump

---

## 5. Roadmap sugerido

## Fase 1 - ganhos rápidos

1. Enriquecer `progress`, `appserver`, `appbroker` e `acesso` com extração de campos
2. Criar breakdowns e KPIs por subtipo
3. Exibir filtros específicos por família no frontend
4. Agrupar exceções por assinatura

## Fase 2 - maior retorno técnico

1. Parser dedicado para `progress_tabanalys`
2. Parser dedicado para `progress_xref`
3. Parser dedicado para `progress_memory`
4. Parser dedicado para LOGIX estruturado

## Fase 3 - diferenciais

1. Analisador de `thread dump`
2. Subtipo explícito `webspeed`
3. Correlação temporal entre famílias
4. comparação entre execuções de profiler

---

## 6. Priorização final

## Prioridade máxima

1. `progress` com extração rica de programa/processo/PI/linha
2. `appserver` e `appbroker` com KPIs operacionais
3. `progress_tabanalys` com parser dedicado
4. `progress_xref` com parser dedicado
5. `LOGIX` com parser estruturado
6. `thread dump` com analisador próprio

## Prioridade alta

1. `progress_db`
2. `progress_memory`
3. `acesso` com métricas e correlação
4. `webspeed` como novo subtipo
5. `pasoe/tomcat` com melhor separação infra x aplicação

## Prioridade média

1. `jboss`
2. `fluig`
3. refinamentos adicionais no profiler

---

## 7. Conclusão

O sistema atual já está em um bom nível de detecção e cobertura estrutural. O legado, porém, mostra com clareza onde ainda existe espaço de evolução:

- **menos foco só em reconhecer**
- **mais foco em extrair semântica de domínio**
- **mais filtros e visões específicas por família**
- **mais KPIs e diagnósticos operacionais**

### Melhor oportunidade prática

Se a evolução for feita por impacto, a melhor sequência é:

1. enriquecer `progress/appserver/appbroker`
2. criar parsers dedicados para `tabanalys`, `xref`, `memory` e `LOGIX`
3. adicionar suporte real para `thread dump` e `webspeed`

Isso aproxima bastante o comportamento analítico do legado, mas em uma arquitetura muito mais moderna e expansível.
