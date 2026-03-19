#!/usr/bin/env python3
"""
Teste para verificar se todos os tipos de logs estão sendo processados
"""

from log_analyzer import LogAnalyzer

def test_all_log_types():
    """Testa se Datasul, LOGIX e outros tipos são detectados e processados"""
    
    print("=" * 80)
    print("TESTE: Verificação de Suporte a Todos os Tipos de Logs")
    print("=" * 80)
    
    analyzer = LogAnalyzer()
    
    test_cases = [
        # (log_content, expected_type, description)
        (
            """
            [25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL ERROR
            FT7394: Cannot find procedure /usr/datasul/prg/nfe_transmissao.p
            LOG:MANAGER - Datasul error occurred
            """,
            "Datasul",
            "Log Progress/Datasul típico"
        ),
        (
            """
            2024-01-20 10:30:45 INFO LOGIX Framework initialized
            TOTVS - FRW: Starting application
            NFE: Validação de schema XML failed
            LOG4J: Database connection error
            Schema XML validation error - DANFE
            """,
            "LOGIX",
            "Log LOGIX/TOTVS típico"
        ),
        (
            """
            2024-01-20 10:30:45 ERROR Database connection failed
            Exception in thread main: NullPointerException
            Connection timeout after 30 seconds
            """,
            "Other",
            "Log genérico (não Progress, não LOGIX)"
        )
    ]
    
    print(f"\n🔍 Testando {len(test_cases)} tipos de log:\n")
    
    passed = 0
    failed = 0
    
    for i, (log_content, expected_type, description) in enumerate(test_cases, 1):
        print(f"\n{i}. Testando: {description}")
        print(f"   Tipo esperado: {expected_type}")
        
        # Detectar tipo
        detected_type = analyzer._detect_log_type(log_content)
        
        print(f"   Tipo detectado: {detected_type}")
        
        if detected_type == expected_type:
            print(f"   ✅ PASS - Tipo detectado corretamente")
            passed += 1
        else:
            print(f"   ❌ FAIL - Esperado: {expected_type}, Obtido: {detected_type}")
            failed += 1
        
        # Verificar se os padrões estão sendo carregados
        print(f"\n   Verificando padrões carregados:")
        
        # Simular análise
        try:
            result = analyzer.analyze_log_content(log_content, None)
            
            if result.get('success'):
                total_errors = result.get('total_results', 0)
                print(f"   ✅ Análise executada com sucesso")
                print(f"   📊 Erros detectados: {total_errors}")
                
                # Verificar se detectou erros (deve detectar pelo menos 1 em cada log)
                if total_errors > 0:
                    print(f"   ✅ Padrões sendo aplicados corretamente")
                else:
                    print(f"   ⚠️  AVISO: Nenhum erro detectado (pode ser problema de padrões)")
            else:
                print(f"   ❌ Erro na análise: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Exceção durante análise: {e}")
    
    print("\n" + "=" * 80)
    print(f"📊 RESULTADOS:")
    print(f"   ✅ Passou: {passed}/{len(test_cases)}")
    print(f"   ❌ Falhou: {failed}/{len(test_cases)}")
    print(f"   Taxa de sucesso: {(passed/len(test_cases)*100):.1f}%")
    print("=" * 80)
    
    # Verificar loaders
    print(f"\n🔧 VERIFICAÇÃO DE LOADERS:")
    print(f"   Datasul Loader: {'✅ Inicializado' if analyzer.datasul_loader else '❌ Não inicializado'}")
    print(f"   LOGIX Loader: {'✅ Inicializado' if analyzer.logix_loader else '❌ Não inicializado'}")
    
    if analyzer.datasul_loader:
        try:
            datasul_patterns = analyzer.datasul_loader.get_all_patterns()
            print(f"   Padrões Datasul carregados: {len(datasul_patterns)}")
        except:
            print(f"   ⚠️  Erro ao carregar padrões Datasul")
    
    if analyzer.logix_loader:
        try:
            logix_patterns = analyzer.logix_loader.get_all_patterns()
            print(f"   Padrões LOGIX carregados: {len(logix_patterns)}")
        except:
            print(f"   ⚠️  Erro ao carregar padrões LOGIX")
    
    print("=" * 80)
    
    if failed == 0:
        print("✅ TODOS OS TIPOS DE LOG ESTÃO SENDO SUPORTADOS!")
    else:
        print(f"❌ {failed} TESTE(S) FALHARAM!")

    assert failed == 0, f"Falharam {failed} validações de tipo de log"
    return None

if __name__ == '__main__':
    import sys
    success = test_all_log_types()
    sys.exit(0 if success else 1)
