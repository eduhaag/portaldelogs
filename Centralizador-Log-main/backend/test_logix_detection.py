#!/usr/bin/env python3
"""
Teste de detecção de tipo de log - LOGIX vs Outros
"""

import sys
sys.path.insert(0, '/app/backend')

from log_analyzer import LogAnalyzer

# Criar instância do analisador
analyzer = LogAnalyzer()

print("="*80)
print("TESTE DE DETECÇÃO DE TIPO DE LOG")
print("="*80)

# Teste 1: Log LOGIX
logix_log = """
[2024-01-10 10:30:45] TOTVS - FRW: Iniciando processamento
[2024-01-10 10:30:46] LOGIX: Validação de schema XML iniciada
[2024-01-10 10:30:47] NFE: Processando nota fiscal eletrônica
[2024-01-10 10:30:48] DANFE: Gerando PDF da nota fiscal
[2024-01-10 10:30:49] SEFAZ: Enviando para SEFAZ
[2024-01-10 10:30:50] ERROR: Falha na validação do schema XML
"""

print("\n1. TESTE LOG LOGIX:")
print("-" * 80)
log_type = analyzer._detect_log_type(logix_log)
print(f"Tipo detectado: {log_type}")
print(f"✅ Deve detectar como 'LOGIX'")

# Teste 2: Log Datasul
datasul_log = """
[2024-01-10 10:30:45] Datasul MG-001: Iniciando processamento
[2024-01-10 10:30:46] PROCEDURE: api/orders.p executando
[2024-01-10 10:30:47] LOG:MANAGER: Registrando transação
[2024-01-10 10:30:48] cd-estabel: 1001
[2024-01-10 10:30:49] ERROR: Falha no processamento
[2024-01-10 10:30:50] emsfnd: Sistema iniciado
"""

print("\n2. TESTE LOG DATASUL:")
print("-" * 80)
log_type = analyzer._detect_log_type(datasul_log)
print(f"Tipo detectado: {log_type}")
print(f"✅ Deve detectar como 'Other'")

# Teste 3: Log PASOE
pasoe_log = """
[2024-01-10 10:30:45] PASOE: Instance started
[2024-01-10 10:30:46] Tomcat server running on port 8080
[2024-01-10 10:30:47] OEABL: Agent initialized
[2024-01-10 10:30:48] AppServer broker: Connection established
[2024-01-10 10:30:49] ERROR: Failed to start instance
[2024-01-10 10:30:50] Progress OpenEdge running
"""

print("\n3. TESTE LOG PASOE:")
print("-" * 80)
log_type = analyzer._detect_log_type(pasoe_log)
print(f"Tipo detectado: {log_type}")
print(f"✅ Deve detectar como 'Other'")

print("\n" + "="*80)
print("RESUMO:")
print("="*80)
print("✅ Logs LOGIX → Busca APENAS em padrões LOGIX + Custom + Pontos de Atenção")
print("✅ Logs Outros → Busca em Datasul + PASOE + Progress + Custom (NÃO busca LOGIX)")
print("="*80)
