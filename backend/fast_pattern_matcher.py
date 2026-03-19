#!/usr/bin/env python3
"""
===============================
FastPatternMatcher - O Flash das regex!
===============================
Aqui a busca por padrões é tão rápida que até o Sonic ficaria com inveja.
Comentários didáticos e piadinhas para quem gosta de performance e regex gigante.
"""

import re
import time
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FastPatternMatcher:
    """
    Matcher extremamente otimizado usando regex única combinada
    (Reduz complexidade de O(n*m) para O(n) - ou seja, mais rápido que café forte!)
    """
    
    def __init__(self):
        self.combined_regex = None
        self.pattern_map = {}
        self.setup_completed = False
    
    def setup_from_datasul_patterns(self, patterns_data: List[Dict]) -> bool:
        """
        Configura matcher com padrões Datasul
        Cria UMA ÚNICA regex que combina todos os 331 padrões
        (Sim, é muita coisa, mas a vida é curta para loops lentos)
        """
        start_time = time.time()
        
        try:
            logger.info(f"Creating ultra-fast matcher for {len(patterns_data)} patterns")
            
            # Construir regex combinada
            regex_parts = []
            pattern_index = 0
            
            for data in patterns_data:
                pattern = data.get('pattern', '').strip()
                if not pattern:
                    continue
                
                try:
                    # Testar se é regex válida
                    re.compile(pattern)
                    # Adicionar como grupo nomeado
                    group_name = f"g{pattern_index}"
                    regex_parts.append(f"(?P<{group_name}>{pattern})")
                    self.pattern_map[group_name] = data
                    pattern_index += 1
                    
                except re.error:
                    # Se não é regex válida, escapar e usar como literal
                    escaped = re.escape(pattern)
                    group_name = f"g{pattern_index}"
                    regex_parts.append(f"(?P<{group_name}>{escaped})")
                    self.pattern_map[group_name] = data
                    pattern_index += 1
            
            # Combinar tudo em UMA ÚNICA regex
            if regex_parts:
                combined_pattern = "|".join(regex_parts)
                self.combined_regex = re.compile(combined_pattern, re.IGNORECASE)
                
                setup_time = time.time() - start_time
                self.setup_completed = True
                
                logger.info(f"Ultra-fast matcher ready: {len(regex_parts)} patterns in {setup_time:.3f}s")
                return True
            
        except Exception as e:
            logger.error(f"Error creating fast matcher: {e}")
            
        return False
    
    def analyze_fast(self, content: str) -> Dict[str, Any]:
        """
        Análise ultra-rápida usando regex única
        """
        if not self.setup_completed or not self.combined_regex:
            return {'success': False, 'error': 'Matcher not setup'}
        
        start_time = time.time()
        
        lines = content.split('\n')
        total_lines = len(lines)
        results = []
        
        logger.info(f"Starting ultra-fast analysis of {total_lines:,} lines")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # UMA ÚNICA busca por linha para TODOS os padrões
            match = self.combined_regex.search(line)
            
            if match:
                # Identificar QUAL padrão fez match
                for group_name, matched_text in match.groupdict().items():
                    if matched_text:  # Este grupo fez match
                        pattern_data = self.pattern_map.get(group_name)
                        if pattern_data:
                            result = {
                                'line': line_num,
                                'message': line,
                                'error_type': 'Datasul',
                                'severity': pattern_data.get('severity', 'Médio'),
                                'description': pattern_data.get('description', ''),
                                'solution': pattern_data.get('solution', ''),
                                'category': pattern_data.get('category', ''),
                                'pattern': pattern_data.get('pattern', ''),
                                'tag': pattern_data.get('tag', '')
                            }
                            results.append(result)
                            break  # Só primeiro match por linha
            
            # Log progresso
            if line_num % 25000 == 0:
                elapsed = time.time() - start_time
                rate = line_num / elapsed
                logger.info(f"Processed {line_num:,}/{total_lines:,} lines ({rate:,.0f} lines/sec)")
        
        total_time = time.time() - start_time
        lines_per_second = total_lines / max(total_time, 0.001)
        
        return {
            'success': True,
            'ultra_fast_processing': True,
            'total_lines_processed': total_lines,
            'total_results': len(results),
            'results': results,
            'performance': {
                'total_time_seconds': round(total_time, 3),
                'lines_per_second': round(lines_per_second, 0),
                'patterns_used': len(self.pattern_map),
                'optimization': 'single_combined_regex'
            }
        }

# Função de conveniência
async def analyze_with_fast_matcher(content: str, datasul_patterns: List[Dict]) -> Dict[str, Any]:
    """Análise ultra-rápida usando o matcher otimizado"""
    
    matcher = FastPatternMatcher()
    
    if not matcher.setup_from_datasul_patterns(datasul_patterns):
        return {'success': False, 'error': 'Failed to setup fast matcher'}
    
    return matcher.analyze_fast(content)