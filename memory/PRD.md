# Centralizador de Logs - PRD

## Problema Original
Sistema de análise de logs Progress/Datasul com frontend Angular PO-UI 18+ e backend Python FastAPI. Funcionalidades: análise de log, limpeza de log, profiler, comparação de versões, registro de evidência e controle de issues.

## Requisitos Funcionais
1. **Análise de Log** - Upload e análise de arquivos de log Progress client (.log)
2. **Limpeza de Log** - Remoção seletiva de categorias (4gltrace, fileid, traducao, etc.)
3. **Profiler** - Análise de arquivos .out do Progress Profiler (v3 com JSON metadata)
4. **Comparação de Versões** - Compara extrato de versão com base de referência
5. **Registro de Evidência** - Formulário completo para registro de tickets com geração de PDF/DOCX/ZIP
6. **Controle de Issues** - CRUD de issues com import/export CSV, filtros e status
7. **Base de Conhecimento** - Busca de padrões de erro conhecidos

## Arquitetura
- **Backend**: FastAPI (Python) na porta 8001
- **Frontend**: Angular PO-UI 21.5 (build servido via Express na porta 3000)
- **Database**: MongoDB (Motor async)
- **Auth**: JWT (jose)

## O que foi implementado

### 2026-03-17
- **Performance da análise de log**: De >120s (timeout) para <1s (150x mais rápido)
  - Removido padrão `4GL` dos default_patterns (casava 98.8% das linhas)
  - Adicionado pre-filter de entry types informativos (4GLTRACE, FILEID, etc.)
  - Pre-filter aplicado a `analyze_performance` e `_analyze_callers_and_programs`
  - Eliminado LargeLogProcessor desnecessário
- **Performance do cleaner**: De 14.7s para 0.115s (127x mais rápido)
  - Mapa rápido de entry types Progress -> categorias
  - Regex usado apenas para linhas FRMWRK e não-mapeadas
- **Parser do Profiler**: Corrigido para formato v3
  - Corrigido parsing do cabeçalho de sessão com JSON metadata
  - Corrigido tratamento de separadores `.` entre seções
  - Corrigido tokenização para strings com backslash-quote
  - 35 módulos parseados corretamente vs 0 antes
- **Registro de Evidência**: Página Angular criada
  - Formulário completo com informações do ticket, configuração técnica, análise técnica
  - Upload de arquivos de evidência
  - Geração de PDF + DOCX + ZIP
  - Salva issue automaticamente no MongoDB
- **Controle de Issues**: Página Angular criada
  - Tabela com CRUD completo
  - Filtros por texto e status
  - Import/Export CSV
  - Modais para criar/editar
  - Contadores de totais/abertos/resolvidos
- **Frontend Angular servido**: Express server em `/app/frontend/` publica o build gerado em `/app/frontend-angular/`

## Backlog (P0/P1/P2)

### P0 - Crítico
- (nenhum)

### P1 - Importante  
- Detecção de tipo de log: Detecta como "LOGIX" quando deveria ser "Datasul" para Progress client logs
- Comparação de versões: Precisa de base de referência configurada (C:\LIBS) para funcionar

### P2 - Melhorias
- Busca avançada com filtros na base de conhecimento
- Dashboard/histórico de análises anteriores
- Melhoria no front da página de controle de issues (dados vindos da API podem demorar por conta de Cloudflare)

## Credenciais de Teste
- Username: testuser
- Password: Test@1234

## Arquivos de Referência
- Backend: `/app/backend/server.py`, `/app/backend/log_analyzer.py`, `/app/backend/log_cleaner.py`, `/app/backend/profiler_analyzer.py`
- Frontend Angular: `/app/frontend-angular/src/app/`
- Servidor HTTP do frontend: `/app/frontend/server.js`
- Referência Progress 4GL: `/app/react_reference/LogAnalys_src (Unzipped Files)/`
- Amostras de teste: `/tmp/clientlog-lapereira.log`, `/tmp/profiler.out`, `/tmp/ext_ver.log`
