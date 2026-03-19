# Matriz de cobertura backend x frontend

## Objetivo

Consolidar quais endpoints do backend estão efetivamente consumidos pelo frontend Angular, o nível de cobertura atual e os principais gaps de contrato, apresentação e testes.

## Resumo executivo

- **Cobertura funcional principal:** alta
- **Cobertura visual dos retornos:** parcial em alguns fluxos
- **Cobertura de contratos tipados:** média/baixa
- **Cobertura automatizada frontend:** baixa

### Principais conclusões

1. O frontend Angular cobre praticamente todos os endpoints de negócio do backend.
2. Os fluxos críticos (`auth`, análise, resultados, profiler, base de conhecimento, busca avançada, padrões, Datasul e comparação de versão) estão presentes.
3. Existem retornos relevantes do backend que ainda não são exibidos ou são exibidos de forma resumida.
4. Há endpoints consumidos com tipagem genérica (`Record<string, unknown>`), o que enfraquece o contrato.
5. A página da base de conhecimento exibe apenas parte do retorno real disponível.
6. Não há hoje uma malha de testes E2E/contrato suficiente para garantir aderência contínua.

---

## Matriz endpoint -> frontend

| Endpoint backend | Método | Serviço Angular | Tela(s) | Cobertura | Observações |
|---|---|---|---|---|---|
| `/api/` | GET | — | — | Não aplicável | Endpoint técnico de teste. |
| `/api/status` | POST | — | — | Não coberto | Endpoint operacional, sem uso no Angular. |
| `/api/status` | GET | — | — | Não coberto | Endpoint operacional, sem uso no Angular. |
| `/api/auth/register` | POST | `registerUser()` | `register-user` | Completa | Fluxo presente e funcional. |
| `/api/auth/login` | POST | `login()` | `login` | Completa | Sessão + token + redirect cobertos. |
| `/api/analyze-info` | POST | `analyzeInfo()` | `analysis`, `analyze-log` | Completa | Pré-análise e recomendações exibidas. |
| `/api/analyze-log` | POST | `analyzeLog()` | `analysis`, `analyze-log`, `analysis-results` | Parcial alta | Fluxo principal coberto, mas parte das métricas retornadas não aparece. |
| `/api/download-csv` | POST | `downloadAnalysisCsv()` | `analysis` | Completa | Download tratado como blob. |
| `/api/search-knowledge-base` | POST | `searchKnowledgeBase()` | `analysis`, `knowledge-base` | Parcial | Frontend consome, mas backend limita `matches` a 3 itens. |
| `/api/analyze-log-categories` | POST | `analyzeLogCategories()` | `analysis` | Completa | Prévia para limpeza de log coberta. |
| `/api/clean-log` | POST | `cleanLog()` | `analysis` | Completa | Download + estatísticas via header. |
| `/api/split-log` | POST | `splitLogFile()` | `analysis` | Completa | Download zip coberto. |
| `/api/analyze-profiler` | POST | `analyzeProfiler()` | `analysis`, `profiler-analysis`, `profiler-version-compare` | Parcial alta | Fluxo coberto; nem todos os blocos retornados são explorados visualmente. |
| `/api/analysis-history` | GET | `getAnalysisHistory()` | `analysis` | Parcial | Histórico aparece, mas parte do payload é resumida. |
| `/api/add-pattern` | POST | `addCustomPattern()` | `analysis` | Completa | Fluxo de criação presente. |
| `/api/test-pattern` | POST | `testPattern()` | `analysis` | Completa | Validação prévia presente. |
| `/api/custom-patterns` | GET | `getCustomPatterns()` | `analysis` | Completa | Lista carregada. |
| `/api/custom-patterns/{pattern_id}` | DELETE | `deleteCustomPattern()` | `analysis` | Completa | Exclusão lógica presente. |
| `/api/search-log` | POST | `searchLog()` | `advanced-search` | Completa | Busca e detalhe de match presentes. |
| `/api/categorize-error` | POST | `categorizeError()` | `analysis` | Completa | Permanente/sessão presente. |
| `/api/error-categorizations` | GET | `getErrorCategorizations()` | `analysis` | Completa | Gestão de categorizações presente. |
| `/api/mark-as-non-error` | POST | `markAsNonError()` | `analysis`, `analyze-log`, `analysis-results` | Completa | Fluxo importante coberto em múltiplas telas. |
| `/api/non-error-patterns` | GET | `getNonErrorPatterns()` | `analysis` | Completa | Lista carregada. |
| `/api/save-analysis-changes` | POST | `saveAnalysisChanges()` | `analysis` | Completa | Persistência de ajustes presente. |
| `/api/analysis-changes` | GET | `getAnalysisChanges()` | `analysis` | Completa | Histórico de alterações visível. |
| `/api/datasul-patterns` | GET | `getDatasulPatterns()` | `analysis` | Completa | Catálogo exibido. |
| `/api/datasul-statistics` | GET | `getDatasulStatistics()` | `analysis` | Completa | Estatísticas exibidas. |
| `/api/refresh-datasul-patterns` | POST | `refreshDatasulPatterns()` | `analysis` | Completa | Atualização manual presente. |
| `/api/version-compare/status` | GET | `getVersionCompareStatus()` | `analysis`, `version-compare`, `profiler-version-compare` | Completa | Status do índice coberto. |
| `/api/version-compare/reload` | POST | `reloadVersionCompare()` | `analysis`, `version-compare`, `profiler-version-compare` | Completa | Rebuild do índice presente. |
| `/api/version-compare` | POST | `compareVersions()` | `analysis`, `version-compare`, `profiler-version-compare` | Completa | Fluxo funcional bem coberto. |

---

## Retornos do backend com cobertura parcial na UI

## 1) Análise de log

O backend retorna um payload rico com:

- `statistics`
- `error_counts`
- `severity_counts`
- `chart_data`
- `attention_points`
- `informational_lines`
- `new_errors`
- `performance_analysis`
- `structured_analysis`
- `top_programs_methods`
- `error`

### O que o frontend já mostra bem

- resumo geral
- tabela principal de ocorrências
- gráficos básicos
- pontos de atenção
- linhas informativas
- novos erros (parte)
- blocos estruturados (parte)
- blocos de performance (parte)
- ranking de programas/métodos

### O que ainda está subaproveitado

- `http_metrics`
- `java_metrics`
- `progress_metrics`
- `memory_stats`
- `cpu_stats`
- `connection_stats`
- `throughput`
- `response_times`
- detalhes completos de `database_queries`

### Impacto

O backend devolve inteligência analítica que o usuário final ainda não enxerga integralmente.

---

## 2) Base de conhecimento

### Situação atual

O backend calcula o total completo de resultados, mas limita os itens devolvidos em `matches`.

### Impacto

A UI mostra que encontrou mais registros do que realmente disponibiliza para navegação.

### Recomendação

Ou devolver paginação real no backend, ou alinhar o frontend para comunicar explicitamente que a lista foi truncada.

---

## 3) Histórico de análises

### Situação atual

O backend retorna mais informação do que o dashboard usa.

### Impacto

A interface mostra o essencial, mas perde contexto útil como estatísticas adicionais do processamento.

---

## Contratos fracos no frontend

Hoje alguns endpoints de mutação usam tipos genéricos:

- `addCustomPattern()`
- `deleteCustomPattern()`
- `categorizeError()`
- `markAsNonError()`
- `saveAnalysisChanges()`
- `refreshDatasulPatterns()`

### Risco

Qualquer mudança de chave no backend pode quebrar comportamento sem erro de compilação.

### Recomendação

Criar interfaces específicas para cada resposta, por exemplo:

- `ApiMessageResponse`
- `PatternMutationResponse`
- `AnalysisChangeSaveResponse`
- `DatasulRefreshResponse`

---

## Inconsistências de regra

## Senha de cadastro

### Backend
- aceita senha com **6+** caracteres

### Frontend
- exige **8+**, maiúscula, número e caractere especial

### Impacto

A regra de negócio está duplicada e divergente.

### Recomendação

Centralizar a política no backend e espelhar no frontend apenas como validação de UX.

---

## Prioridades de melhoria

## Prioridade alta

1. **Fechar contrato tipado entre backend e frontend**
   - remover `Record<string, unknown>`
   - criar interfaces explícitas para todas as mutações

2. **Corrigir base de conhecimento**
   - paginação real, ou retorno completo, ou truncamento explícito

3. **Alinhar regra de senha**
   - uma regra única entre backend e frontend

## Prioridade média

4. **Expor mais métricas de análise já disponíveis**
   - blocos HTTP, Java, Progress, throughput, memória, CPU, queries

5. **Enriquecer histórico de análises**
   - aproveitar mais campos já retornados pelo backend

## Prioridade estrutural

6. **Criar testes de contrato e E2E**
   - login
   - análise de log
   - marcação como não-erro
   - busca avançada
   - comparação de versão

---

## Estratégia recomendada de execução

### Fase 1 — Contrato

- mapear todos os DTOs de resposta
- tipar `backend-api.service.ts`
- revisar telas dependentes

### Fase 2 — Cobertura visual

- revisar `analysis-results`
- revisar `knowledge-base`
- revisar `analysis` dashboard

### Fase 3 — Garantia

- adicionar testes de contrato do serviço Angular
- adicionar testes E2E dos fluxos críticos

---

## Checklist objetivo

- [ ] Tipar todas as respostas do `BackendApiService`
- [ ] Corrigir truncamento/UX da base de conhecimento
- [ ] Alinhar política de senha
- [ ] Revisar exibição dos blocos completos de `structured_analysis`
- [ ] Revisar exibição dos blocos completos de `performance_analysis`
- [ ] Enriquecer histórico de análises
- [ ] Criar testes E2E dos fluxos críticos
- [ ] Criar testes de contrato para o consumo do backend

---

## Conclusão

O frontend **atende a maior parte das funcionalidades do backend**, mas ainda não garante, com robustez, que **todos os retornos estão representados de forma completa e estável**.

O ponto mais importante agora não é criar novas telas, e sim:

1. fortalecer contrato,
2. fechar gaps de exibição,
3. automatizar validação de ponta a ponta.
