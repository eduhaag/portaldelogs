#!/usr/bin/env python3
"""
Teste para verificar se erros estão sendo filtrados incorretamente
"""

from log_analyzer import LogAnalyzer

def test_error_detection():
    """Testa se erros não estão sendo filtrados como ruído"""
    
    print("=" * 80)
    print("TESTE: Verificação de Filtragem de Erros")
    print("=" * 80)
    
    analyzer = LogAnalyzer()
    
    # Casos de teste
    test_cases = [
        # (linha, deve_ser_ruido, descrição)
        ("[25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL CONN Setting attention flag for database 'eai', interval '30'", 
         True, "Ruído puro - heartbeat normal"),
        
        ("[25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL CONN Client notify thread: time to check for notifications", 
         True, "Ruído puro - thread notification"),
        
        ("[25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL CONN Checking notification for database mgadt", 
         True, "Ruído puro - checking notification"),
        
        ("[25/11/24@10:22:10.100-0300] P-002448 T-001164 2 4GL ERROR Setting attention flag for database failed - connection lost", 
         False, "ERRO com texto de heartbeat - NÃO deve filtrar!"),
        
        ("[25/11/24@10:22:10.200-0300] P-002448 T-001165 1 4GL CRITICAL Cannot check notification - database crashed", 
         False, "CRÍTICO com texto de notification - NÃO deve filtrar!"),
        
        ("[25/11/24@10:22:10.300-0300] P-002448 T-001166 2 4GL ERROR Database connection timeout", 
         False, "Erro real sem texto de ruído"),
        
        ("[25/11/24@10:22:10.400-0300] P-002448 T-001167 3 4GL WARNING Memory allocation failed", 
         False, "Warning - não deve filtrar"),
        
        ("[25/11/24@10:22:10.500-0300] P-002448 T-001168 4 4GL INFO Setting attention flag for database 'emscad', interval '30'", 
         True, "INFO com heartbeat - pode filtrar"),
    ]
    
    print(f"\n🔍 Testando {len(test_cases)} casos:\n")
    
    passed = 0
    failed = 0
    
    for i, (line, should_be_noise, description) in enumerate(test_cases, 1):
        is_noise = analyzer._is_progress_noise(line)
        
        if is_noise == should_be_noise:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{i}. {status}")
        print(f"   Descrição: {description}")
        print(f"   Linha: {line[:100]}...")
        print(f"   Esperado: {'RUÍDO' if should_be_noise else 'NÃO RUÍDO'}")
        print(f"   Resultado: {'RUÍDO' if is_noise else 'NÃO RUÍDO'}")
        
        if is_noise != should_be_noise:
            print(f"   ⚠️  PROBLEMA: Linha {'filtrada' if is_noise else 'não filtrada'} incorretamente!")
        print()
    
    print("=" * 80)
    print(f"📊 RESULTADOS:")
    print(f"   ✅ Passou: {passed}/{len(test_cases)}")
    print(f"   ❌ Falhou: {failed}/{len(test_cases)}")
    print(f"   Taxa de sucesso: {(passed/len(test_cases)*100):.1f}%")
    print("=" * 80)
    
    if failed == 0:
        print("✅ TODOS OS TESTES PASSARAM! Filtragem está correta.")
    else:
        print(f"❌ {failed} TESTE(S) FALHARAM! Revisar filtragem.")

    assert failed == 0, f"Falharam {failed} casos de filtragem"
    return None

if __name__ == '__main__':
    import sys
    success = test_error_detection()
    sys.exit(0 if success else 1)
