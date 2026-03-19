# -*- coding: utf-8 -*-
"""
Analisador de arquivos Profiler Progress (.out)
Baseado na lógica extraída do profiler-main
"""

import re
import json
from typing import Dict, List, Any
from collections import defaultdict


def _split_sections(text: str) -> List[str]:
    """Divide o texto em seções baseado em quebras de linha duplas"""
    blocks = re.split(r'\n\s*\n+', text.strip(), flags=re.M)
    return [b.strip() for b in blocks if b.strip()]


def _split_row(line: str) -> List[str]:
    """Divide uma linha em colunas usando diferentes delimitadores"""
    if ',' in line: 
        return [c.strip() for c in line.split(',')]
    if '\t' in line: 
        return [c.strip() for c in line.split('\t')]
    return re.split(r'\s{2,}', line.strip())


def parse_progress_profiler_out(text: str) -> Dict[str, Any]:
    """
    Parse completo de arquivo .out do Progress Profiler
    
    Retorna estrutura:
    {
        "info": {"session_id": "...", "database": "...", ...},
        "modules": [{"module": "...", "calls": 0, "time_total_ms": 0.0, ...}],
        "lines": [{"module": "...", "line": 0, "calls": 0, ...}],
        "call_tree": [{"caller": "...", "callee": "...", "calls": 0, ...}]
    }
    """
    modules, lines, call_tree, info = [], [], [], {}
    
    # Dividir o texto em seções
    blocks = _split_sections(text)
    
    for block in blocks:
        rows = [r for r in block.splitlines() if r.strip()]
        if not rows:
            continue
            
        # Primeira linha como header
        header = [h.strip().lower() for h in _split_row(rows[0])]
        data = rows[1:]
        hdr = set(header)
        
        # Detectar seção de módulos
        if ({"module", "calls"} <= hdr and ("total time (ms)" in hdr or "total" in hdr)) or ({"procedure", "calls"} <= hdr):
            for r in data:
                cols = _split_row(r)
                
                def get(n, d=""):
                    try: 
                        return cols[header.index(n)]
                    except Exception: 
                        return d
                
                mod = get("module") or get("procedure") or get("program")
                if not mod:
                    continue
                    
                modules.append({
                    "module": mod,
                    "calls": int((get("calls") or "0") or 0),
                    "time_total_ms": float((get("total time (ms)") or get("total") or "0") or 0),
                    "time_avg_ms": float((get("avg time (ms)") or get("average time (ms)") or "0") or 0),
                })
                
        # Detectar seção de linhas por módulo
        elif {"module", "line", "calls"} <= hdr:
            for r in data:
                cols = _split_row(r)
                
                def get(n, d=""):
                    try: 
                        return cols[header.index(n)]
                    except Exception: 
                        return d
                
                lines.append({
                    "module": get("module"),
                    "line": int((get("line") or "0") or 0),
                    "calls": int((get("calls") or "0") or 0),
                    "time_total_ms": float((get("total time (ms)") or "0") or 0),
                    "time_avg_ms": float((get("avg time (ms)") or get("average time (ms)") or "0") or 0),
                })
                
        # Detectar seção de call tree (caller -> callee)
        elif {"caller"} <= hdr and ("callee" in hdr or "child" in hdr):
            for r in data:
                cols = _split_row(r)
                
                def get(n, d=""):
                    try: 
                        return cols[header.index(n)]
                    except Exception: 
                        return d
                
                call_tree.append({
                    "caller": get("caller") or get("parent"),
                    "callee": get("callee") or get("child"),
                    "calls": int((get("calls") or "0") or 0),
                    "time_total_ms": float((get("total time (ms)") or "0") or 0),
                })
                
        # Detectar seção de informações da sessão
        elif any("session" in h or "avm" in h or "database" in h for h in header):
            for r in data:
                cols = _split_row(r)
                if len(cols) >= 2: 
                    info[cols[0]] = cols[1]
    
    # Calcular tempo exclusivo: module.total - sum(child times onde callee==module)
    child_sum = defaultdict(float)
    for e in call_tree:
        child_sum[e.get("callee")] += float(e.get("time_total_ms") or 0)
    
    for m in modules:
        total = float(m.get("time_total_ms") or 0)
        m["time_exclusive_ms"] = max(0.0, total - child_sum.get(m["module"], 0.0))
    
    return {
        "info": info, 
        "modules": modules, 
        "lines": lines, 
        "call_tree": call_tree
    }


def analyze_profiler_performance(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Análise de performance dos dados do profiler
    Gera estatísticas, tops e insights
    """
    modules = data.get("modules", [])
    lines = data.get("lines", [])
    call_tree = data.get("call_tree", [])
    info = data.get("info", {})
    
    if not modules:
        return {"error": "Nenhum módulo encontrado no arquivo"}
    
    # Estatísticas gerais
    total_calls = sum(m.get("calls", 0) for m in modules)
    total_time = sum(m.get("time_total_ms", 0) for m in modules)
    
    # Top módulos por tempo total
    top_modules_time = sorted(modules, key=lambda x: x.get("time_total_ms", 0), reverse=True)[:10]
    
    # Top módulos por chamadas
    top_modules_calls = sorted(modules, key=lambda x: x.get("calls", 0), reverse=True)[:10]
    
    # Top módulos por tempo médio
    top_modules_avg = sorted(
        [m for m in modules if m.get("time_avg_ms", 0) > 0], 
        key=lambda x: x.get("time_avg_ms", 0), reverse=True
    )[:10]
    
    # Top linhas mais custosas
    top_lines = sorted(lines, key=lambda x: x.get("time_total_ms", 0), reverse=True)[:10]
    
    # Módulos problemáticos (alto tempo médio ou muitas chamadas)
    problematic_modules = []
    for m in modules:
        calls = m.get("calls", 0)
        avg_time = m.get("time_avg_ms", 0)
        total_time_module = m.get("time_total_ms", 0)
        
        issues = []
        if avg_time > 1.0:  # Mais de 1ms por chamada
            issues.append(f"Alto tempo médio: {avg_time:.2f}ms")
        if calls > 1000:  # Muitas chamadas
            issues.append(f"Muitas chamadas: {calls:,}")
        if total_time_module > 500:  # Mais de 500ms total
            issues.append(f"Alto tempo total: {total_time_module:.1f}ms")
            
        if issues:
            problematic_modules.append({
                "module": m.get("module"),
                "issues": issues,
                "calls": calls,
                "time_total_ms": total_time_module,
                "time_avg_ms": avg_time
            })
    
    # Estatísticas de call tree
    call_tree_stats = {
        "total_relationships": len(call_tree),
        "unique_callers": len(set(c.get("caller") for c in call_tree)),
        "unique_callees": len(set(c.get("callee") for c in call_tree))
    }
    
    return {
        "summary": {
            "total_modules": len(modules),
            "total_lines": len(lines),
            "total_calls": total_calls,
            "total_time_ms": total_time,
            "avg_time_per_call": (total_time / total_calls) if total_calls > 0 else 0,
            "session_info": info
        },
        "top_modules_by_time": top_modules_time,
        "top_modules_by_calls": top_modules_calls,
        "top_modules_by_avg_time": top_modules_avg,
        "top_lines": top_lines,
        "problematic_modules": problematic_modules[:5],  # Top 5 módulos problemáticos
        "call_tree_stats": call_tree_stats,
        "recommendations": generate_recommendations(modules, problematic_modules)
    }


def generate_recommendations(modules: List[Dict], problematic_modules: List[Dict]) -> List[str]:
    """Gera recomendações baseadas na análise"""
    recommendations = []
    
    if problematic_modules:
        recommendations.append(
            f"📊 {len(problematic_modules)} módulo(s) identificado(s) com possíveis gargalos de performance"
        )
    
    high_avg_modules = [m for m in modules if m.get("time_avg_ms", 0) > 2.0]
    if high_avg_modules:
        recommendations.append(
            f"⚠️ {len(high_avg_modules)} módulo(s) com tempo médio > 2ms - considere otimização"
        )
    
    high_call_modules = [m for m in modules if m.get("calls", 0) > 2000]
    if high_call_modules:
        recommendations.append(
            f"🔄 {len(high_call_modules)} módulo(s) com > 2000 chamadas - verifique se são necessárias"
        )
    
    total_time = sum(m.get("time_total_ms", 0) for m in modules)
    if total_time > 5000:  # Mais de 5 segundos
        recommendations.append(
            f"🕒 Tempo total de execução alto ({total_time/1000:.1f}s) - analise os módulos principais"
        )
    
    if not recommendations:
        recommendations.append("✅ Performance aparenta estar dentro dos parâmetros normais")
    
    return recommendations


class ProfilerAnalyzer:
    """Classe principal para análise de arquivos .out do Progress Profiler"""
    
    def analyze_file_content(self, content: str) -> Dict[str, Any]:
        """Analisa o conteúdo de um arquivo .out"""
        try:
            # Parse do arquivo
            parsed_data = parse_progress_profiler_out(content)
            
            # Análise de performance
            analysis = analyze_profiler_performance(parsed_data)
            
            return {
                "success": True,
                "raw_data": parsed_data,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao analisar arquivo: {str(e)}"
            }