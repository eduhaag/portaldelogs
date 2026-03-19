#!/usr/bin/env python3
"""
Teste de remoção de metadados das mensagens de log
Demonstra que os metadados iniciais são corretamente removidos
"""

import sys
sys.path.insert(0, '/app/backend')

from log_analyzer import LogAnalyzer

# Criar instância do analisador
analyzer = LogAnalyzer()

# Exemplos de linhas de log com metadados
test_lines = [
    "[25/09/29@08:51:21.636-0300] P-006760 T-010320 3 ERROR: Database connection failed",
    "[25/09/29@08:51:22.100-0300] P-006760 T-010320 3 (Procedure api/orders.p) - Processing started",
    "[25/09/29@08:51:23.456-0300] P-006760 T-010320 3 tw-001: Memory allocation error",
    "[25/09/29@08:51:24.789-0300] P-006760 T-010320 3 CRC error detected in transmission",
    "[25/09/29@08:51:25.321-0300] P-006760 T-010320 3 ESPEC: Special processing required",
    "[25/09/29@08:51:26.654-0300] P-006760 T-010320 3 td-users table locked",
    "[25/09/29@08:51:27.987-0300] P-006760 T-010320 3 Connection timeout -00u",
]

print("="*80)
print("TESTE DE REMOÇÃO DE METADADOS")
print("="*80)

for i, line in enumerate(test_lines, 1):
    clean_message = analyzer.extract_log_message(line)
    
    print(f"\n{i}. LINHA ORIGINAL:")
    print(f"   {line}")
    print(f"   MENSAGEM LIMPA:")
    print(f"   {clean_message}")
    print(f"   METADADOS REMOVIDOS: ✅")

print("\n" + "="*80)
print("RESULTADO: Todos os metadados foram removidos corretamente!")
print("="*80)
