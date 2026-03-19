# Plano técnico de execução por sprint

## Objetivo

Executar a evolução da integração backend/frontend em ondas curtas, priorizando:

1. contrato tipado entre frontend Angular e backend,
2. correção do gap da base de conhecimento,
3. automação E2E dos fluxos críticos,
4. ampliação gradual da cobertura visual e de testes.

---

## Sprint 1 — Contrato forte + gap crítico da base de conhecimento

### Meta

Eliminar os pontos mais frágeis do consumo HTTP e corrigir a inconsistência mais visível ao usuário.

### Escopo

- tipagem forte no `BackendApiService`
- criação de interfaces explícitas para mutações e retornos auxiliares
- correção do endpoint de base de conhecimento para retornar metadados de truncamento
- ajuste das telas que consomem a base de conhecimento
- validação de build do frontend e compilação do backend

### Entregáveis

- `BackendApiService` sem dependência de `Record<string, unknown>` nos endpoints principais de mutação
- modelos TypeScript explícitos para:
  - teste de padrão
  - adição de padrão
  - categorização de erro
  - marcação como não-erro
  - persistência de alterações
  - refresh Datasul
- backend retornando:
  - `total_found`
  - `returned_count`
  - `truncated`
  - `max_results`
- UI da base de conhecimento exibindo claramente quando o retorno foi truncado

### Critérios de aceite

- build Angular sem erro
- backend compilando sem erro de sintaxe
- fluxo de base de conhecimento sem discrepância silenciosa entre total encontrado e total exibido

### Risco principal

- ajustes de tipagem podem revelar dependências implícitas em telas antigas

---

## Sprint 2 — Testes E2E dos fluxos críticos

### Meta

Criar uma malha inicial de testes ponta a ponta focada no comportamento do frontend frente aos contratos esperados do backend.

### Escopo

- configurar Playwright
- criar suíte E2E inicial com mocks de API
- validar navegação protegida com sessão autenticada
- cobrir fluxos críticos:
  - login
  - análise de log
  - busca avançada
  - base de conhecimento
  - comparação de versão (adiada para ambiente validável)

### Entregáveis

- configuração E2E no frontend Angular
- script de execução dedicado
- testes versionados no repositório
- fixtures reutilizáveis para sessão autenticada e respostas do backend

### Observação de ambiente

Enquanto o ambiente atual não permitir validação segura da comparação de versão, o fluxo fica fora da suíte crítica ativa e segue preservado sem mudanças funcionais.

### Critérios de aceite

- suíte E2E executando localmente
- testes críticos passando com estabilidade
- nenhum fluxo principal quebrado por regressão óbvia

### Risco principal

- necessidade de estabilizar seletores e estados visuais de componentes PO UI

---

## Sprint 3 — Cobertura visual dos retornos avançados

### Meta

Aumentar a aderência entre o payload retornado pelo backend e a apresentação ao usuário.

### Escopo

- expandir `analysis-results`
- expor blocos ainda subaproveitados de:
  - `structured_analysis`
  - `performance_analysis`
  - métricas HTTP/Java/Progress
  - throughput, memória, CPU, conexões e queries
- enriquecer histórico de análises

### Entregáveis

- painéis adicionais na tela de resultados
- histórico com mais contexto do processamento
- revisão de copy/UX para explicar cada métrica

### Critérios de aceite

- principais blocos retornados pelo backend visíveis na UI
- redução dos campos “não apresentados” na matriz de cobertura

### Risco principal

- excesso de informação na tela sem hierarquia visual adequada

---

## Sprint 4 — Governança de contrato e endurecimento de qualidade

### Meta

Evitar regressão de integração a cada evolução do backend ou frontend.

### Escopo

- testes de contrato por serviço Angular
- padronização de respostas de mutação do backend
- alinhamento definitivo da política de senha
- revisão de erros 400/401/409/500 nas telas principais

### Entregáveis

- suíte de contrato para serviços HTTP
- padrão único de resposta para mutações
- regra de senha única entre backend e frontend
- matriz de cobertura atualizada

### Critérios de aceite

- mudanças de contrato detectadas automaticamente
- mensagens de erro consistentes nas telas críticas

---

## Ordem técnica recomendada

1. **Sprint 1** — contrato forte + base de conhecimento
2. **Sprint 2** — E2E dos fluxos críticos
3. **Sprint 3** — cobertura visual ampliada
4. **Sprint 4** — contrato + governança + endurecimento

---

## Definição de pronto por sprint

### Pronto técnico
- código compilando
- testes relevantes passando
- sem regressão visível nos fluxos principais

### Pronto funcional
- retorno do backend claramente representado ou explicitamente sinalizado como resumido/truncado

### Pronto documental
- matriz de cobertura e plano técnico atualizados
