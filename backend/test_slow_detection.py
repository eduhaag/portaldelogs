#!/usr/bin/env python3
"""
Script de teste para verificar a detecção de programas lentos
"""

import sys
import json
from textwrap import dedent

from log_analyzer import LogAnalyzer


SAMPLE_SLOW_PROGRAMS_LOG = dedent("""
[25/11/24@10:22:10.100-0300] P-002448 T-001164 2 4GL ERROR Procedure faturamento.p took 3.5 seconds
[25/11/24@10:22:10.200-0300] P-002448 T-001165 2 4GL ERROR Program pedidos.p took 6500 ms to complete
[25/11/24@10:22:10.300-0300] P-002448 T-001166 2 4GL ERROR Execute relatorio_cliente.p duration 2.2 seconds
[25/11/24@10:22:10.400-0300] P-002448 T-001167 2 4GL ERROR Program rapido.p took 900 ms to complete
""").strip()

def test_slow_program_detection():
    """Testa a detecção de programas que demoram mais de 2 segundos"""
    
    print("=" * 80)
    print("TESTE: Detecção de Programas Lentos (>2 segundos)")
    print("=" * 80)
    
    # Criar analisador
    analyzer = LogAnalyzer()
    
    log_content = SAMPLE_SLOW_PROGRAMS_LOG
    
    print(f"\n📄 Analisando arquivo de log com {len(log_content.splitlines())} linhas...\n")
    
    # Analisar o log
    result = analyzer.analyze_log_content(log_content, None)
    
    assert result.get('success'), result.get('error')
    
    # Verificar se há análise de performance
    perf_analysis = result.get('performance_analysis')
    
    assert perf_analysis, "Análise de performance não disponível"
    
    # Verificar programas lentos
    slow_programs = perf_analysis.get('slow_programs', [])
    slow_programs_stats = perf_analysis.get('slow_programs_stats')
    
    print(f"✅ Análise de performance realizada com sucesso!\n")
    
    if slow_programs:
        print(f"🎯 PROGRAMAS LENTOS DETECTADOS: {len(slow_programs)}")
        print("-" * 80)
        
        if slow_programs_stats:
            print(f"\n📊 ESTATÍSTICAS:")
            print(f"   • Total de programas lentos: {slow_programs_stats['total_slow_programs']}")
            print(f"   • Mais lento: {slow_programs_stats['slowest_duration_ms']:.2f}ms ({slow_programs_stats['slowest_duration_ms']/1000:.2f}s)")
            print(f"   • Tempo médio: {slow_programs_stats['average_duration_ms']:.2f}ms ({slow_programs_stats['average_duration_ms']/1000:.2f}s)")
            print(f"   • Críticos (≥5s): {slow_programs_stats['critical_count']}")
            print(f"   • Altos (≥3s): {slow_programs_stats['high_count']}")
            print(f"   • Médios (≥2s): {slow_programs_stats['medium_count']}")
        
        print(f"\n📋 DETALHES DOS PROGRAMAS:\n")
        
        for i, program in enumerate(slow_programs, 1):
            severity_emoji = "🔴" if program['severity'] == 'critical' else ("🟠" if program['severity'] == 'high' else "🟡")
            
            print(f"{i}. {severity_emoji} {program['program']}")
            print(f"   ⏱️  Duração: {program['duration_seconds']}s ({program['duration_ms']}ms)")
            print(f"   📍 Linha: {program['line']}")
            print(f"   🕐 Timestamp: {program['timestamp']}")
            print(f"   ⚠️  Severidade: {program['severity'].upper()}")
            print(f"   📝 Contexto: {program['context'][:100]}...")
            print()
        
        print("=" * 80)
        print(f"✅ TESTE BEM-SUCEDIDO! {len(slow_programs)} programas lentos detectados corretamente.")
        print("=" * 80)
        assert len(slow_programs) >= 3
        assert slow_programs_stats is not None
        assert slow_programs_stats['total_slow_programs'] >= 3
        assert slow_programs_stats['critical_count'] >= 1
        return None
    else:
        print("❌ AVISO: Nenhum programa lento foi detectado no log de teste")
        print("   Isso pode indicar que os padrões regex não estão capturando corretamente.")
        
        # Debug: mostrar o que foi encontrado
        print("\n🔍 DEBUG - Response times encontrados:")
        for rt in perf_analysis.get('response_times', [])[:5]:
            print(f"   Linha {rt['line']}: {rt['value']}ms")
        
        raise AssertionError("Nenhum programa lento foi detectado no log de teste")

if __name__ == '__main__':
    try:
        success = test_slow_program_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
