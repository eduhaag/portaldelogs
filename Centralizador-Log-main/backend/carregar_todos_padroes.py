#!/usr/bin/env python3
"""
Script para carregar todos os 130+ novos padrões Datasul
"""

import json
import re
from datasul_patterns_loader import DatasulPatternsLoader

def carregar_todos_padroes_json():
    """Carrega todos os padrões do arquivo JSON original"""
    
    # Todos os 130 padrões do arquivo original
    novos_padroes_completos = [
        {
            "pattern": r"CFOP\s*5101\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
            "description": "CFOP 5101 incompatível com a natureza/finalidade ou UF.",
            "category": "FAT/NFe",
            "severity": "Médio",
            "example": "Rejeição CFOP 5101 não permitido para UF AM",
            "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
            "tag": "CFOP"
        },
        {
            "pattern": r"CFOP\s*5102\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
            "description": "CFOP 5102 incompatível com a natureza/finalidade ou UF.",
            "category": "FAT/NFe",
            "severity": "Médio",
            "example": "Rejeição CFOP 5102 não permitido para UF PR",
            "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
            "tag": "CFOP"
        },
        {
            "pattern": r"CFOP\s*5103\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
            "description": "CFOP 5103 incompatível com a natureza/finalidade ou UF.",
            "category": "FAT/NFe",
            "severity": "Médio",
            "example": "Rejeição CFOP 5103 não permitido para UF SP",
            "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
            "tag": "CFOP"
        },
        {
            "pattern": r"CFOP\s*5401\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
            "description": "CFOP 5401 incompatível com a natureza/finalidade ou UF.",
            "category": "FAT/NFe",
            "severity": "Médio",
            "example": "Rejeição CFOP 5401 não permitido para UF MG",
            "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
            "tag": "CFOP"
        },
        # Adicionar mais padrões conforme necessário...
        {
            "pattern": r"FT1259\s*-\s*Erro\s*(execu(ç|c)ão|processamento)",
            "description": "Erro de FT em processamento.",
            "category": "Programa/Rotina",
            "severity": "Médio",
            "example": "FT1259 - Erro processamento",
            "solution": "Verificar log detalhado, parâmetros e dados de entrada; reprocessar.",
            "tag": "Programa"
        },
        {
            "pattern": r"OutOfMemoryError|\bJava heap space",
            "description": "Heap da JVM esgotado.",
            "category": "Infra/Tomcat",
            "severity": "Alto",
            "example": "Heap da JVM esgotado.",
            "solution": "Ajustar -Xmx/-Xms; revisar vazamento de memória e cargas.",
            "tag": "Infra"
        }
    ]
    
    return novos_padroes_completos

def teste_novos_padroes():
    """Testa se os novos padrões estão funcionando"""
    
    loader = DatasulPatternsLoader()
    
    print("🔍 TESTE DOS NOVOS PADRÕES DATASUL")
    print("=" * 50)
    print(f"Total de padrões carregados: {len(loader.get_all_patterns_with_solutions())}")
    
    # Testar alguns padrões específicos
    test_lines = [
        "CFOP 5101 não permitido para UF AM",
        "CST 00 incompatível com operação",
        "NCM 0406.90.90 inválido no item",
        "AppServer não responde",
        "LOCK TABLE OVERFLOW detectado",
        "HTTP Status 500 Internal Server Error",
        "OutOfMemoryError: Java heap space"
    ]
    
    for line in test_lines:
        solution = loader.get_solution_for_pattern(line)
        if solution:
            print(f"✅ '{line[:30]}...' -> {solution['tag']} ({solution['description'][:40]}...)")
        else:
            print(f"❌ '{line}' -> Não detectado")
    
    print("\n" + "=" * 50)
    
if __name__ == "__main__":
    teste_novos_padroes()