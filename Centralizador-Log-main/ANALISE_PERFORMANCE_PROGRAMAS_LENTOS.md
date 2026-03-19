# 📊 Análise de Performance - Programas Lentos

## 🎯 Nova Funcionalidade Implementada

Foi adicionada uma **análise automática de performance** que detecta programas, procedures e processos que demoram **mais de 2 segundos** para executar nos logs do sistema Datasul/Progress/OpenEdge.

---

## ✨ Características

### 📍 O que é detectado:

✅ **Programas Progress (.p, .r, .w)**
- Procedures
- Programs
- Rotinas 4GL
- Classes (.cls)

✅ **Informações Capturadas:**
- Nome do programa/procedure
- Tempo de execução (em segundos e milissegundos)
- Linha do log onde foi detectado
- Timestamp da execução
- Contexto completo da linha do log
- Severidade automática baseada no tempo

---

## 🎨 Severidade Automática

O sistema classifica automaticamente os programas lentos em 3 níveis:

| Severidade | Tempo | Cor | Emoji |
|------------|-------|-----|-------|
| **CRÍTICO** | ≥ 5 segundos | 🔴 Vermelho | 🔴 |
| **ALTO** | ≥ 3 segundos | 🟠 Laranja | 🟠 |
| **MÉDIO** | ≥ 2 segundos | 🟡 Amarelo | 🟡 |

---

## 📋 Formatos de Log Suportados

A funcionalidade reconhece diversos formatos de log Progress/Datasul:

### ✅ Exemplos Suportados:

```log
✓ Procedure: /usr/datasul/prg/financeiro.p took 2.5 seconds to complete
✓ Program /usr/datasul/prg/nfe_transmissao.p duration: 8.2 seconds
✓ Procedure: /usr/datasul/prg/estoque_consulta.p executed in 4500ms
✓ Executing report_vendas.p (3200 milliseconds)
✓ LOG:MANAGER - backup_dados.p execution time: 2100ms
✓ (importacao_xml.p) completed in 6.5 seconds
✓ Running: relatorio_fiscal.p took 4.1 seconds
✓ Program: validacao_nfe.p elapsed: 3.8 seconds
✓ Procedure controle_estoque.p response time: 7200ms
```

---

## 🖥️ Visualização na Interface

### 📊 Na Aba "Performance" > "Visão Geral":

**Card Destacado de Programas Lentos:**
- 🚨 Alerta visual com borda vermelha/laranja
- 📈 Estatísticas resumidas:
  - Total de programas lentos
  - Programa mais lento
  - Tempo médio de execução
  - Contadores por severidade

**Lista Detalhada:**
- 📄 Nome do programa
- ⏱️ Tempo de execução (segundos e ms)
- 📍 Linha no log
- 🕐 Timestamp
- ⚠️ Badge de severidade
- 📝 Contexto da linha do log

---

## 🔧 Padrões Regex Utilizados

O sistema utiliza múltiplos padrões regex para capturar diferentes formatos:

1. **Progress/OpenEdge patterns:**
   ```regex
   (?:Procedure|Program|Execute|Running)[\s:]+([^\s]+\.(?:p|r|w))\s+.*?(?:took|duration|time|elapsed)[\s:]*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)
   ```

2. **Datasul patterns:**
   ```regex
   (?:LOG:MANAGER|Message).*?([^\s/]+\.p).*?(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)
   ```

3. **Generic patterns:**
   ```regex
   ([a-zA-Z0-9_\-/]+\.(?:p|r|w|4gl|cls)).*?(?:took|duration|time|elapsed)[\s:]*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)
   ```

4. **Pattern com parênteses:**
   ```regex
   \(([^)]+\.(?:p|r|w))\).*?(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)
   ```

---

## 📊 Estatísticas Fornecidas

### Métricas Calculadas:

- ✅ **Total de programas lentos**
- ✅ **Programa mais lento** (em ms)
- ✅ **Tempo médio** de todos os programas lentos
- ✅ **Contadores por severidade**:
  - Críticos (≥5s)
  - Altos (≥3s)
  - Médios (≥2s)

---

## 🎯 Casos de Uso

### 1. **Identificação de Gargalos**
Encontre rapidamente quais programas estão causando lentidão no sistema.

### 2. **Otimização de Performance**
Priorize a otimização dos programas mais lentos e críticos.

### 3. **Análise de Incidentes**
Em caso de problemas de performance, identifique imediatamente quais procedures estavam lentas.

### 4. **Monitoramento Contínuo**
Acompanhe a evolução da performance dos programas ao longo do tempo.

---

## 🚀 Como Usar

### Passo 1: Upload do Log
- Faça upload do arquivo de log (.log, .txt) na interface

### Passo 2: Análise Automática
- O sistema analisa automaticamente e detecta programas lentos

### Passo 3: Visualizar Resultados
- Navegue até a aba **"Performance"**
- Clique em **"Visão Geral"**
- Veja o card destacado de **"Programas Lentos Detectados"**

### Passo 4: Análise Detalhada
- Revise cada programa listado
- Note a severidade (cor e badge)
- Verifique o contexto completo no log

---

## 📝 Exemplo de Resultado

```
⚠️ Programas Lentos Detectados
Encontrados 10 programa(s) que demoraram mais de 2 segundos

📊 ESTATÍSTICAS:
• Total de Programas: 10
• Mais Lento: 9.50s
• Tempo Médio: 5.43s

📋 DETALHES:
1. 🔴 sincronizacao_datasul.p - 9.5s - CRÍTICO
2. 🔴 nfe_transmissao.p - 8.2s - CRÍTICO
3. 🔴 controle_estoque.p - 7.2s - CRÍTICO
4. 🔴 importacao_xml.p - 6.5s - CRÍTICO
5. 🔴 calculo_impostos.p - 5.9s - CRÍTICO
6. 🟠 estoque_consulta.p - 4.5s - ALTO
7. 🟠 relatorio_fiscal.p - 4.1s - ALTO
8. 🟠 validacao_nfe.p - 3.8s - ALTO
9. 🟡 financeiro.p - 2.5s - MÉDIO
10. 🟡 backup_dados.p - 2.1s - MÉDIO
```

---

## ⚙️ Configuração

### Limiar de Detecção
Por padrão, programas com **tempo ≥ 2000ms (2 segundos)** são detectados.

### Classificação de Severidade:
- **CRÍTICO**: ≥ 5000ms (5 segundos)
- **ALTO**: ≥ 3000ms (3 segundos)
- **MÉDIO**: ≥ 2000ms (2 segundos)

*Estes valores podem ser ajustados no código se necessário.*

---

## 🔍 Detecção Inteligente

O sistema:
- ✅ Remove duplicatas automáticas
- ✅ Converte automaticamente unidades (s → ms)
- ✅ Preserva contexto completo da linha
- ✅ Extrai timestamp quando disponível
- ✅ Ordena por duração (mais lentos primeiro)

---

## 💡 Dicas

1. **Priorize Críticos**: Comece otimizando programas classificados como CRÍTICO (≥5s)

2. **Verifique Recorrência**: Se o mesmo programa aparece múltiplas vezes, indica problema persistente

3. **Analise o Contexto**: Use o contexto da linha para entender o que o programa estava fazendo

4. **Compare Logs**: Compare logs de diferentes períodos para ver evolução da performance

---

## 🐛 Troubleshooting

### ❓ "Não detectou meus programas lentos"

Verifique se o formato do log inclui:
- Nome do programa (.p, .r, .w)
- Tempo de execução (ms, s, seconds, milliseconds)
- Palavras-chave: "took", "duration", "time", "elapsed", "executed"

### ❓ "Muitos falsos positivos"

O sistema filtra apenas programas ≥2s. Se ainda há muitos, considere:
- Ajustar o limiar para 3s ou 5s
- Focar apenas em programas CRÍTICO ou ALTO

---

## 📚 Arquivos Modificados

### Backend:
- `/app/backend/log_analyzer.py`
  - Função: `analyze_performance()`
  - Novos campos: `slow_programs`, `slow_programs_stats`
  - Padrões regex para detecção

### Frontend:
- `/app/frontend-angular/src/app/pages/analysis-results/analysis-results.page.ts`
  - Fluxo de análise consolidado na tela principal de resultados
  - Visualização de severidade e indicadores no frontend oficial
  - Estatísticas resumidas no dashboard Angular

---

## ✅ Status da Implementação

- ✅ **Backend**: Detecção de programas lentos implementada
- ✅ **Frontend**: Visualização com card destacado
- ✅ **Testes**: Testado com logs de exemplo
- ✅ **Documentação**: Completa e em português
- ✅ **Remoção de duplicatas**: Implementada
- ✅ **Classificação por severidade**: Implementada

---

## 📞 Suporte

Para dúvidas ou melhorias nesta funcionalidade:
1. Verifique se o formato do log está correto
2. Teste com o arquivo de exemplo: `/app/backend/test_slow_programs.log`
3. Execute o teste: `python test_slow_detection.py`

---

**Desenvolvido para otimizar a análise de performance em sistemas Datasul/Progress/OpenEdge** 🚀
