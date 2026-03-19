#!/usr/bin/env python3
"""
===============================
Optimized Pattern Matcher - O ninja dos padrões!
===============================
Aqui a gente faz análise de padrões em larga escala, rápido e sem perder a pose.
Comentários didáticos e bem humorados para quem gosta de performance e truques de ninja!
"""

import re
import time
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class OptimizedPatternMatcher:
    """
    Matcher otimizado que usa múltiplas estratégias para acelerar análise:
    1. Regex combinada única para todos os padrões (o famoso "tudo em um")
    2. Pre-filtering baseado em palavras-chave (porque regex também gosta de atalho)
    3. Priorização por severidade (erro grave vai pro VIP)
    4. Cache de resultados (para não reinventar a roda)
    """
    
    def __init__(self):
        self.combined_regex = None
        self.pattern_lookup = {}
        self.keyword_filters = defaultdict(list)
        self.priority_patterns = {'high': [], 'medium': [], 'low': []}
        self.compiled_patterns = {}
        self.setup_time = 0
        
    def setup_patterns(self, patterns_data: List[Dict[str, Any]]) -> bool:
        """Configura padrões com otimizações avançadas"""
        start_time = time.time()
        
        try:
            logger.info(f"Setting up optimized matching for {len(patterns_data)} patterns")
            
            # Limpar estado anterior
            self._reset_state()
            
            # Estratégia 1: Criar regex combinada para detecção rápida
            self._create_combined_regex(patterns_data)
            
            # Estratégia 2: Organizar por prioridade/severidade
            self._organize_by_priority(patterns_data)
            
            # Estratégia 3: Criar filtros por palavra-chave
            self._create_keyword_filters(patterns_data)
            
            # Estratégia 4: Pre-compilar padrões individuais
            self._precompile_individual_patterns(patterns_data)
            
            self.setup_time = time.time() - start_time
            logger.info(f"Pattern optimization setup completed in {self.setup_time:.3f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up optimized patterns: {e}")
            return False
    
    def _reset_state(self):
        """Reset interno do estado"""
        self.combined_regex = None
        self.pattern_lookup = {}
        self.keyword_filters = defaultdict(list)
        self.priority_patterns = {'high': [], 'medium': [], 'low': []}
        self.compiled_patterns = {}
    
    def _create_combined_regex(self, patterns_data: List[Dict]) -> bool:
        """Cria uma regex combinada para detecção rápida inicial"""
        try:
            # Extrair padrões válidos e criar grupos nomeados
            valid_patterns = []
            
            for i, pattern_data in enumerate(patterns_data):
                pattern = pattern_data.get('pattern', '').strip()
                if not pattern:
                    continue
                    
                try:
                    # Testar se é regex válida
                    re.compile(pattern)
                    
                    # Criar grupo nomeado para identificar matches
                    group_name = f"p{i}"
                    grouped_pattern = f"(?P<{group_name}>{pattern})"
                    valid_patterns.append(grouped_pattern)
                    
                    # Mapear grupo para dados do padrão
                    self.pattern_lookup[group_name] = pattern_data
                    
                except re.error:
                    # Se não for regex válida, escapar e tratar como literal
                    escaped = re.escape(pattern)
                    group_name = f"p{i}"
                    grouped_pattern = f"(?P<{group_name}>{escaped})"
                    valid_patterns.append(grouped_pattern)
                    self.pattern_lookup[group_name] = pattern_data
            
            # Combinar todos os padrões em uma única regex
            if valid_patterns:
                combined_pattern = "|".join(valid_patterns)
                self.combined_regex = re.compile(combined_pattern, re.IGNORECASE)
                logger.info(f"Combined regex created with {len(valid_patterns)} patterns")
                return True
            
        except Exception as e:
            logger.error(f"Error creating combined regex: {e}")
            
        return False
    
    def _organize_by_priority(self, patterns_data: List[Dict]):
        """Organiza padrões por prioridade/severidade"""
        for pattern_data in patterns_data:
            severity = pattern_data.get('severity', 'Médio').lower()
            pattern_info = {
                'pattern': pattern_data.get('pattern', ''),
                'data': pattern_data
            }
            
            if severity in ['crítico', 'critical', 'alto', 'high']:
                self.priority_patterns['high'].append(pattern_info)
            elif severity in ['baixo', 'low', 'info', 'informativo']:
                self.priority_patterns['low'].append(pattern_info)
            else:
                self.priority_patterns['medium'].append(pattern_info)
    
    def _create_keyword_filters(self, patterns_data: List[Dict]):
        """Cria filtros de palavra-chave para pre-filtering"""
        for pattern_data in patterns_data:
            pattern = pattern_data.get('pattern', '').lower()
            description = pattern_data.get('description', '').lower()
            
            # Extrair palavras-chave do padrão e descrição
            keywords = self._extract_keywords(pattern + ' ' + description)
            
            for keyword in keywords:
                self.keyword_filters[keyword].append(pattern_data)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extrai palavras-chave relevantes para indexação"""
        # Remover caracteres especiais de regex
        clean_text = re.sub(r'[\\.*+?^${}[\]|()\s]+', ' ', text)
        
        # Extrair palavras de 3+ caracteres
        words = [w.strip() for w in clean_text.split() if len(w.strip()) >= 3]
        
        # Filtrar palavras comuns irrelevantes
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'use', 'man', 'new', 'now', 'old', 'see', 'him', 'two', 'how', 'its', 'who', 'oil', 'sit', 'set', 'run', 'eat', 'far', 'sea', 'eye', 'ago', 'off', 'add', 'bag', 'big', 'red', 'hot', 'let', 'put', 'end', 'why', 'try', 'god', 'six', 'dog', 'car', 'got', 'may', 'say', 'she', 'use', 'her', 'way', 'too', 'any', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'own', 'say', 'she', 'too', 'use'}
        
        relevant_words = {w for w in words if w not in stopwords and len(w) >= 3}
        
        return relevant_words
    
    def _precompile_individual_patterns(self, patterns_data: List[Dict]):
        """Pre-compila padrões individuais para uso quando necessário"""
        for i, pattern_data in enumerate(patterns_data):
            pattern = pattern_data.get('pattern', '').strip()
            if pattern:
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    self.compiled_patterns[pattern] = {
                        'compiled': compiled,
                        'data': pattern_data
                    }
                except re.error:
                    # Tratar como literal
                    escaped = re.escape(pattern)
                    compiled = re.compile(escaped, re.IGNORECASE)
                    self.compiled_patterns[pattern] = {
                        'compiled': compiled,
                        'data': pattern_data
                    }
    
    def match_line_optimized(self, line: str) -> List[Dict[str, Any]]:
        """
        Análise otimizada de uma linha usando múltiplas estratégias
        Retorna lista de matches encontrados
        """
        if not line.strip():
            return []
        
        matches = []
        line_lower = line.lower()
        
        # ESTRATÉGIA 1: Usar regex combinada para detecção rápida
        if self.combined_regex:
            match = self.combined_regex.search(line)
            if match:
                # Identificar qual(is) padrão(ões) fizeram match
                for group_name, matched_text in match.groupdict().items():
                    if matched_text:  # Se esse grupo fez match
                        pattern_data = self.pattern_lookup.get(group_name)
                        if pattern_data:
                            matches.append({
                                'pattern_data': pattern_data,
                                'matched_text': matched_text,
                                'match_method': 'combined_regex'
                            })
        
        # ESTRATÉGIA 2: Se não houve matches na regex combinada, 
        # tentar filtros por palavra-chave (para padrões que podem ter falhado na combinação)
        if not matches:
            words_in_line = set(self._extract_keywords(line_lower))
            
            # Encontrar padrões candidatos baseado em palavras-chave
            candidate_patterns = set()
            for word in words_in_line:
                if word in self.keyword_filters:
                    candidate_patterns.update(self.keyword_filters[word])
            
            # Testar apenas padrões candidatos
            for pattern_data in candidate_patterns:
                pattern = pattern_data.get('pattern', '')
                if pattern in self.compiled_patterns:
                    compiled_info = self.compiled_patterns[pattern]
                    if compiled_info['compiled'].search(line):
                        matches.append({
                            'pattern_data': pattern_data,
                            'matched_text': line,
                            'match_method': 'keyword_filtered'
                        })
        
        return matches
    
    def analyze_content_optimized(self, content: str) -> Dict[str, Any]:
        """
        Análise otimizada de conteúdo completo
        """
        start_time = time.time()
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        results = []
        line_processing_times = []
        
        logger.info(f"Starting optimized analysis of {total_lines:,} lines")
        
        for line_num, line in enumerate(lines, 1):
            line_start = time.time()
            
            line = line.strip()
            if not line:
                continue
            
            # Usar método otimizado
            line_matches = self.match_line_optimized(line)
            
            # Processar matches encontrados
            for match_info in line_matches:
                pattern_data = match_info['pattern_data']
                
                result_item = {
                    'line': line_num,
                    'message': line,
                    'pattern_matched': pattern_data.get('pattern', ''),
                    'error_type': 'Datasul',
                    'severity': pattern_data.get('severity', 'Médio'),
                    'description': pattern_data.get('description', ''),
                    'solution': pattern_data.get('solution', ''),
                    'category': pattern_data.get('category', ''),
                    'match_method': match_info['match_method']
                }
                
                results.append(result_item)
            
            line_time = time.time() - line_start
            line_processing_times.append(line_time)
            
            # Log progresso para logs grandes
            if line_num % 10000 == 0:
                avg_time = sum(line_processing_times[-1000:]) / min(1000, len(line_processing_times))
                lines_per_sec = 1 / max(avg_time, 0.001)
                logger.info(f"Processed {line_num:,}/{total_lines:,} lines ({lines_per_sec:,.0f} lines/sec)")
        
        total_time = time.time() - start_time
        
        # Estatísticas finais
        avg_line_time = sum(line_processing_times) / max(len(line_processing_times), 1)
        lines_per_second = 1 / max(avg_line_time, 0.001)
        
        analysis_result = {
            'success': True,
            'total_lines_processed': total_lines,
            'total_results': len(results),
            'results': results,
            'performance_metrics': {
                'total_time_seconds': round(total_time, 3),
                'average_line_time_ms': round(avg_line_time * 1000, 3),
                'lines_per_second': round(lines_per_second, 1),
                'setup_time_seconds': round(self.setup_time, 3),
                'optimization_used': True
            },
            'match_methods_used': {
                'combined_regex': len([r for r in results if r.get('match_method') == 'combined_regex']),
                'keyword_filtered': len([r for r in results if r.get('match_method') == 'keyword_filtered'])
            }
        }
        
        logger.info(f"Optimized analysis completed: {total_lines:,} lines in {total_time:.2f}s ({lines_per_second:,.0f} lines/sec)")
        
        return analysis_result

# Função de conveniência
def create_optimized_matcher(patterns_data: List[Dict]) -> OptimizedPatternMatcher:
    """Cria e configura um matcher otimizado"""
    matcher = OptimizedPatternMatcher()
    matcher.setup_patterns(patterns_data)
    return matcher