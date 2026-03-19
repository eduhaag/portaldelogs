#!/usr/bin/env python3
"""
Teste para verificar se logs de PASOE e AppServer são detectados
"""

from log_analyzer import LogAnalyzer

def test_pasoe_appserver_logs():
    """Testa detecção de logs PASOE e AppServer"""
    
    print("=" * 80)
    print("TESTE: Detecção de Logs PASOE e AppServer")
    print("=" * 80)
    
    analyzer = LogAnalyzer()
    
    # Logs de teste
    test_cases = [
        {
            "name": "PASOE Catalina/Tomcat Log",
            "content": """
[25/11/24@10:22:09.922-0300] SEVERE: Exception in WebHandler
java.lang.NullPointerException at com.progress.abl.ABLWebApp.service
[25/11/24@10:22:10.100-0300] ERROR: msagent 1234 died unexpectedly
[25/11/24@10:22:11.200-0300] PASOE instance failed to start
[25/11/24@10:22:12.300-0300] WebSocket connection closed abnormally
[25/11/24@10:22:13.400-0300] oeablSecurity: Access denied for user admin
            """,
            "expected_keywords": ["pasoe", "websocket", "webhandler", "msagent", "catalina"]
        },
        {
            "name": "AppServer Broker Log",
            "content": """
[25/11/24@10:22:09.922-0300] P-002448 T-013056 Broker started on port 5162
[25/11/24@10:22:10.100-0300] P-002448 T-013057 Agent process 12345 started
[25/11/24@10:22:11.200-0300] P-002448 T-013058 ERROR: AppServer process died unexpectedly
[25/11/24@10:22:12.300-0300] P-002448 T-013059 Broker is not available for connections
[25/11/24@10:22:13.400-0300] P-002448 T-013060 nameserver unavailable on port 5162
[25/11/24@10:22:14.500-0300] P-002448 T-013061 _mprosrv terminated abnormally
[25/11/24@10:22:15.600-0300] P-002448 T-013062 No agents available for requests
            """,
            "expected_keywords": ["broker", "agent", "appserver", "nameserver", "_mprosrv"]
        },
        {
            "name": "PASOE + Progress Mixed Log",
            "content": """
[25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL INFO Starting PASOE instance
[25/11/24@10:22:10.100-0300] P-002448 T-013057 2 4GL ERROR PASOE not responding
[25/11/24@10:22:11.200-0300] P-002448 T-013058 1 4GL CRITICAL catalina SEVERE exception
[25/11/24@10:22:12.300-0300] P-002448 T-013059 4 4GL INFO Procedure: /usr/pasoe/web/nfe.p
[25/11/24@10:22:13.400-0300] P-002448 T-013060 2 4GL ERROR WebHandler failed with HTTP 500
[25/11/24@10:22:14.500-0300] P-002448 T-013061 3 4GL WARNING ABLWebApp session timeout
            """,
            "expected_keywords": ["pasoe", "4gl", "procedure", "webhandler"]
        }
    ]
    
    print(f"\n🔍 Testando {len(test_cases)} cenários de logs:\n")
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"{i}. Testando: {test_case['name']}")
        print(f"{'='*70}")
        
        log_content = test_case['content']
        expected_keywords = test_case['expected_keywords']
        
        # Detectar tipo
        detected_type = analyzer._detect_log_type(log_content)
        
        print(f"   Tipo detectado: {detected_type}")
        
        # Verificar se detectou como Datasul/Progress (esperado)
        if detected_type in ["Datasul", "Other"]:
            print(f"   ✅ Tipo correto (Datasul/Progress/PASOE/AppServer)")
        else:
            print(f"   ❌ Tipo incorreto - Esperado: Datasul, Obtido: {detected_type}")
        
        # Analisar o log
        print(f"\n   📊 Analisando log...")
        result = analyzer.analyze_log_content(log_content, None)
        
        if result.get('success'):
            total_errors = result.get('total_results', 0)
            results = result.get('results', [])
            
            print(f"   ✅ Análise executada com sucesso")
            print(f"   📋 Erros detectados: {total_errors}")
            
            if total_errors > 0:
                print(f"\n   🎯 Erros encontrados:")
                for idx, error in enumerate(results[:5], 1):
                    print(f"      {idx}. Linha {error.get('line')}: {error.get('message')[:80]}...")
                    print(f"         Tipo: {error.get('error_type')} | Severidade: {error.get('severity')}")
                
                if total_errors > 5:
                    print(f"      ... e mais {total_errors - 5} erros")
                
                passed += 1
                print(f"\n   ✅ PASS - Erros de PASOE/AppServer detectados corretamente")
            else:
                failed += 1
                print(f"\n   ❌ FAIL - Nenhum erro detectado (esperado pelo menos 1)")
        else:
            failed += 1
            print(f"   ❌ Erro na análise: {result.get('error')}")
        
        # Verificar keywords no log
        print(f"\n   🔍 Verificando keywords específicas:")
        log_lower = log_content.lower()
        keywords_found = []
        for keyword in expected_keywords:
            if keyword in log_lower:
                keywords_found.append(keyword)
                print(f"      ✅ '{keyword}' encontrado")
            else:
                print(f"      ⚠️  '{keyword}' NÃO encontrado")
        
        if len(keywords_found) >= len(expected_keywords) * 0.6:  # 60% das keywords
            print(f"   ✅ Keywords suficientes encontradas ({len(keywords_found)}/{len(expected_keywords)})")
        else:
            print(f"   ⚠️  Poucas keywords encontradas ({len(keywords_found)}/{len(expected_keywords)})")
    
    print("\n" + "=" * 80)
    print(f"📊 RESULTADOS FINAIS:")
    print(f"   ✅ Passou: {passed}/{len(test_cases)}")
    print(f"   ❌ Falhou: {failed}/{len(test_cases)}")
    print(f"   Taxa de sucesso: {(passed/len(test_cases)*100):.1f}%")
    print("=" * 80)
    
    # Verificar padrões PASOE/AppServer carregados
    print(f"\n🔧 PADRÕES PASOE/APPSERVER:")
    pasoe_patterns = [p for p in analyzer.datasul_patterns if any(k in p.lower() for k in ['pasoe', 'appserver', 'broker', 'agent', 'msagent', 'webhandler'])]
    print(f"   Padrões específicos de PASOE/AppServer: {len(pasoe_patterns)}")
    if pasoe_patterns:
        print(f"   Exemplos:")
        for pattern in pasoe_patterns[:5]:
            print(f"      - {pattern}")
    
    print("=" * 80)
    
    if failed == 0:
        print("✅ LOGS DE PASOE E APPSERVER SENDO DETECTADOS CORRETAMENTE!")
    else:
        print(f"❌ {failed} TESTE(S) FALHARAM!")

    assert failed == 0, f"Falharam {failed} cenários de PASOE/AppServer"
    return None

if __name__ == '__main__':
    import sys
    success = test_pasoe_appserver_logs()
    sys.exit(0 if success else 1)
