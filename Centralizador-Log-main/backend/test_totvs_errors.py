#!/usr/bin/env python3
"""
Teste de detecção de erros TOTVS/Datasul específicos
"""

import asyncio
import sys
sys.path.insert(0, '/app/backend')

from totvs_errors_loader import TotvsErrorsLoader
from log_analyzer import LogAnalyzer

def test_totvs_loader():
    """Testa o carregamento dos padrões TOTVS"""
    print("=" * 60)
    print("TESTE 1: Carregamento dos padrões TOTVS")
    print("=" * 60)
    
    loader = TotvsErrorsLoader()
    patterns = loader.get_all_patterns()
    
    print(f"✓ Total de padrões carregados: {len(patterns)}")
    print(f"✓ Códigos de erro disponíveis: {loader.get_all_codes()}")
    
    expected_core_codes = {"18215", "52001", "17055", "17275", "35442", "22550", "19102", "18445", "1455", "5891", "19890", "26045"}
    loaded_codes = set(loader.get_all_codes())

    assert len(patterns) >= len(expected_core_codes), f"Esperado pelo menos {len(expected_core_codes)} padrões, encontrado {len(patterns)}"
    assert expected_core_codes.issubset(loaded_codes), f"Códigos obrigatórios ausentes: {expected_core_codes - loaded_codes}"
    print("✓ Quantidade de padrões correta!")
    return None

def test_partial_detection():
    """Testa a detecção parcial de erros por código"""
    print("\n" + "=" * 60)
    print("TESTE 2: Detecção parcial por código de erro")
    print("=" * 60)
    
    loader = TotvsErrorsLoader()
    
    # Testar detecção por código
    test_cases = [
        ("Erro ao processar: Lote ABC não possui saldo para a série 001. (18215)", "18215", "Rastreabilidade"),
        ("** (18215) - Falha na rastreabilidade", "18215", "Rastreabilidade"),
        ("Não existe alocação física para o item PROD001 no endereço A01. (52001)", "52001", "WMS"),
        ("Centro de Custo CC001 não aceita lançamentos diretos. (17055)", "17055", "Custos"),
        ("A transação de estoque resultará em custo médio negativo. (17275)", "17275", "Custos"),
        ("Configurador de Produtos: Estrutura inválida para a variável V001. (35442)", "35442", "Configurador"),
        ("Documento de Frete (CTE) já vinculado à Nota Fiscal NF001. (22550)", "22550", "Recebimento"),
        ("O somatório das alíquotas de ICMS Retido e ICMS Próprio diverge do ST. (19102)", "19102", "ICMS/ST"),
        ("Operação de reporte de produção bloqueada: Item sem inspeção de qualidade. (18445)", "18445", "Qualidade"),
        ("Estabelecimento destino 002 não possui relação com o Estabelecimento origem. (1455)", "1455", "Transferência"),
        ("Erro ao tentar enviar e-mail de notificação: Servidor SMTP não responde. (5891)", "5891", "Email/SMTP"),
        ("Código de Benefício Fiscal (cBenef) não informado para a UF. (19890)", "19890", "NFe/cBenef"),
        ("Número de parcelas excede o limite permitido para o Portador. (26045)", "26045", "Financeiro"),
    ]
    
    passed = 0
    failed = 0
    
    for test_line, expected_code, expected_tag in test_cases:
        result = loader.check_error_partial(test_line)
        if result and result.get('code') == expected_code:
            print(f"✓ Detectado código {expected_code} ({expected_tag})")
            passed += 1
        else:
            print(f"✗ FALHA: Esperado código {expected_code}, obtido {result}")
            failed += 1
    
    print(f"\n>>> Resultado: {passed}/{len(test_cases)} testes passaram")
    assert failed == 0, f"Falharam {failed} detecções parciais"
    return None

def test_prefix_detection():
    """Testa a detecção de erros com prefixos ** e (Procedure:"""
    print("\n" + "=" * 60)
    print("TESTE 3: Detecção com prefixos especiais")
    print("=" * 60)
    
    loader = TotvsErrorsLoader()
    
    test_cases = [
        ("** (18215) Lote sem saldo", "18215"),
        ("(Procedure: test.p) (17275) custo médio negativo", "17275"),
        ("[19102] ICMS diverge", "19102"),
        ("LOG:MANAGER ** Centro de Custo não aceita (17055)", "17055"),
    ]
    
    passed = 0
    for test_line, expected_code in test_cases:
        result = loader.check_error_partial(test_line)
        if result and result.get('code') == expected_code:
            print(f"✓ Detectado: '{test_line[:50]}...' -> código {expected_code}")
            passed += 1
        else:
            print(f"✗ FALHA: '{test_line[:50]}...' -> esperado {expected_code}")
    
    print(f"\n>>> Resultado: {passed}/{len(test_cases)} testes passaram")
    assert passed == len(test_cases), f"Falharam {len(test_cases) - passed} detecções por prefixo"
    return None

def test_solution_info():
    """Testa se as informações de solução são retornadas corretamente"""
    print("\n" + "=" * 60)
    print("TESTE 4: Informações de solução")
    print("=" * 60)
    
    loader = TotvsErrorsLoader()
    
    test_line = "Erro (18215): Lote X não possui saldo para a série Y"
    result = loader.check_error_partial(test_line)
    
    assert result is not None, "Deveria ter detectado o erro"
    assert 'solution' in result, "Deveria ter solução"
    assert 'description' in result, "Deveria ter descrição"
    assert 'reference' in result, "Deveria ter referência"
    
    print(f"✓ Código: {result.get('code')}")
    print(f"✓ Descrição: {result.get('description')[:80]}...")
    print(f"✓ Solução: {result.get('solution')[:80]}...")
    print(f"✓ Referência: {result.get('reference')}")
    print(f"✓ Severidade: {result.get('severity')}")
    print(f"✓ Tag: {result.get('tag')}")
    
    return None

async def _run_log_analyzer_integration():
    """Testa a integração com o LogAnalyzer"""
    print("\n" + "=" * 60)
    print("TESTE 5: Integração com LogAnalyzer")
    print("=" * 60)
    
    analyzer = LogAnalyzer()
    await analyzer.initialize_totvs_loader(None)
    
    # Criar um log de teste com vários erros TOTVS
    test_log = """[25/11/24@10:22:09.922-0300] P-033484 T-015236 1 Iniciando processamento
[25/11/24@10:22:10.123-0300] P-033484 T-015236 2 ERROR: Lote LT001 não possui saldo para a série SR001. (18215)
[25/11/24@10:22:11.456-0300] P-033484 T-015236 2 ERROR: Centro de Custo CC123 não aceita lançamentos diretos. (17055)
[25/11/24@10:22:12.789-0300] P-033484 T-015236 3 WARNING: Verificando estoque
[25/11/24@10:22:13.012-0300] P-033484 T-015236 2 ERROR: A transação de estoque resultará em custo médio negativo. (17275)
[25/11/24@10:22:14.345-0300] P-033484 T-015236 2 CRITICAL: Código de Benefício Fiscal (cBenef) não informado para a UF SP. (19890)
[25/11/24@10:22:15.678-0300] P-033484 T-015236 1 Processamento finalizado"""
    
    result = analyzer.analyze_log_content(test_log)
    
    # Verificar resultados
    errors = result.get('results', [])
    totvs_errors = [e for e in errors if e.get('error_type') == 'TOTVS']
    
    print(f"✓ Total de erros detectados: {len(errors)}")
    print(f"✓ Erros TOTVS específicos: {len(totvs_errors)}")
    
    for err in totvs_errors:
        code = err.get('error_code', 'N/A')
        msg = err.get('clean_message', '')[:60]
        solution = err.get('solution', 'N/A')[:60]
        print(f"  - Código {code}: {msg}...")
        if solution and solution != 'N/A':
            print(f"    Solução: {solution}...")
    
    # Deve ter detectado pelo menos 4 erros TOTVS
    assert len(totvs_errors) >= 4, f"Esperado pelo menos 4 erros TOTVS, encontrado {len(totvs_errors)}"
    
    print("\n✓ Integração com LogAnalyzer funcionando!")
    return None


def test_log_analyzer_integration():
    """Testa a integração com o LogAnalyzer em ambiente pytest síncrono."""
    asyncio.run(_run_log_analyzer_integration())

def main():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("TESTES DE DETECÇÃO DE ERROS TOTVS/DATASUL")
    print("=" * 60)
    
    all_passed = True
    
    try:
        test_totvs_loader()
        test_partial_detection()
        test_prefix_detection()
        test_solution_info()
        asyncio.run(_run_log_analyzer_integration())
    except Exception as e:
        print(f"\n✗ ERRO DURANTE TESTES: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print(">>> TODOS OS TESTES PASSARAM! ✓")
    else:
        print(">>> ALGUNS TESTES FALHARAM! ✗")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
