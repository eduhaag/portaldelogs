#!/usr/bin/env python3
"""
Teste para verificar filtragem de ruído Progress e parsing de timestamp
"""

import sys
from textwrap import dedent

from log_analyzer import LogAnalyzer


SAMPLE_PROGRESS_LOG = dedent("""
[25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL CONN Setting attention flag for database 'eai', interval '30'
[25/11/24@10:22:09.950-0300] P-002448 T-013056 4 4GL CONN Client notify thread: time to check for notifications
[25/11/24@10:22:09.980-0300] P-002448 T-013056 4 4GL CONN Checking notification for database mgadt
[25/11/24@10:22:10.100-0300] P-002448 T-001164 2 4GL ERROR Procedure faturamento.p took 3.5 seconds
[25/11/24@10:22:10.200-0300] P-002448 T-001165 2 4GL ERROR Program pedidos.p took 6500 ms to complete
[25/11/24@10:22:10.300-0300] P-002448 T-001166 2 4GL ERROR Cannot connect to database 'emsdb'
[25/11/24@10:22:10.400-0300] P-002448 T-001167 3 4GL WARNING Memory allocation failed
[25/11/24@10:22:10.500-0300] P-002448 T-001168 4 4GL INFO Setting attention flag for database 'emscad', interval '30'
""").strip()

def test_progress_filtering():
    """Testa filtragem de ruído Progress e análise"""
    
    print("=" * 80)
    print("TESTE: Filtragem de Ruído Progress + Timestamp + Programas Lentos")
    print("=" * 80)
    
    # Criar analisador
    analyzer = LogAnalyzer()
    
    log_content = SAMPLE_PROGRESS_LOG
    
    lines = log_content.splitlines()
    print(f"\n📄 Arquivo de teste: {len(lines)} linhas totais\n")
    
    # Contar linhas de ruído
    noise_count = 0
    useful_lines = 0
    
    print("🔍 ANÁLISE DE LINHAS:")
    print("-" * 80)
    
    for i, line in enumerate(lines, 1):
        if analyzer._is_progress_noise(line):
            noise_count += 1
            if noise_count <= 5:  # Mostrar apenas primeiras 5
                print(f"   ❌ RUÍDO (Linha {i}): {line[:80]}...")
        else:
            useful_lines += 1
            if useful_lines <= 5:  # Mostrar apenas primeiras 5
                print(f"   ✅ ÚTIL (Linha {i}): {line[:80]}...")
    
    if noise_count > 5:
        print(f"   ... e mais {noise_count - 5} linhas de ruído")
    if useful_lines > 5:
        print(f"   ... e mais {useful_lines - 5} linhas úteis")
    
    print(f"\n📊 RESUMO DE FILTRAGEM:")
    print(f"   • Total de linhas: {len(lines)}")
    print(f"   • Linhas de ruído (filtradas): {noise_count}")
    print(f"   • Linhas úteis (processadas): {useful_lines}")
    print(f"   • Taxa de filtragem: {(noise_count/len(lines)*100):.1f}%")
    
    # Testar extração de timestamp Progress
    print(f"\n⏰ TESTE DE TIMESTAMP PROGRESS:")
    print("-" * 80)
    
    test_lines = [
        "[25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL CONN Setting attention flag",
        "[25/11/24@10:22:10.100-0300] P-002448 T-001164 2 4GL ERROR Procedure took 3.5 seconds"
    ]
    
    for line in test_lines:
        dt = analyzer.extract_progress_timestamp(line)
        if dt:
            print(f"   ✅ {line[:50]}...")
            print(f"      → Timestamp: {dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        else:
            print(f"   ❌ Falhou: {line[:50]}...")
    
    # Analisar o log completo
    print(f"\n🔍 ANÁLISE COMPLETA DO LOG:")
    print("-" * 80)
    
    result = analyzer.analyze_log_content(log_content, None)
    
    assert result.get('success'), result.get('error')
    
    # Verificar resultados
    total_errors = result.get('total_results', 0)
    print(f"   • Erros detectados: {total_errors}")
    
    # Verificar análise de performance
    perf = result.get('performance_analysis')
    if perf:
        slow_programs = perf.get('slow_programs', [])
        print(f"   • Programas lentos (>2s): {len(slow_programs)}")
        
        if slow_programs:
            print(f"\n📋 PROGRAMAS LENTOS DETECTADOS:")
            for i, prog in enumerate(slow_programs[:5], 1):
                print(f"   {i}. {prog['program']}")
                print(f"      ⏱️  Duração: {prog['duration_seconds']}s ({prog['duration_ms']}ms)")
                print(f"      📍 Linha: {prog['line']}")
                print(f"      ⚠️  Severidade: {prog['severity'].upper()}")
    
    # Verificar se linhas de ruído foram filtradas corretamente
    results_list = result.get('results', [])
    noise_in_results = 0
    
    for r in results_list:
        msg = r.get('message', '')
        if 'Setting attention flag' in msg or 'Client notify thread' in msg:
            noise_in_results += 1
    
    print(f"\n✅ VALIDAÇÃO:")
    print(f"   • Linhas de ruído nos resultados: {noise_in_results}")
    
    if noise_in_results == 0:
        print(f"   ✅ Filtragem funcionando perfeitamente!")
    else:
        print(f"   ⚠️  ATENÇÃO: {noise_in_results} linhas de ruído não foram filtradas")

    assert noise_count >= 3
    assert useful_lines >= 4
    assert total_errors >= 3
    assert noise_in_results == 0
    assert perf is not None
    assert len(perf.get('slow_programs', [])) >= 2
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 80)
    
    return None

if __name__ == '__main__':
    try:
        success = test_progress_filtering()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
