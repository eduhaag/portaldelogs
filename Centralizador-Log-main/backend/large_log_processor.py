#!/usr/bin/env python3
"""
Processador otimizado para logs de grande escala (80k+ linhas)
Processa em chunks para evitar sobrecarga de memória e CPU
"""

import asyncio
import time
import gc
from typing import Dict, List, Any, Generator, Optional
from collections import defaultdict, Counter
from log_analyzer import LogAnalyzer
from structured_log_parser import StructuredLogParser
import logging

logger = logging.getLogger(__name__)

class LargeLogProcessor:
    """Processador otimizado para logs corporativos de grande escala"""
    
    def __init__(self, chunk_size: int = 1000, max_results: int = 10000):
        """
        Args:
            chunk_size: Número de linhas por chunk (padrão: 1000)
            max_results: Máximo de resultados a retornar para o frontend (padrão: 10000)
                       OBS: Isso não para o processamento, apenas limita o que é enviado ao frontend
        """
        self.chunk_size = chunk_size
        self.max_results = max_results
        self.analyzer = LogAnalyzer()
        self.structured_parser = StructuredLogParser()
        
    async def initialize(self, db):
        """Inicializa o analisador com MongoDB"""
        await self.analyzer.initialize_datasul_loader(db)
        logger.info("Large log processor initialized")
    
    def chunk_lines(self, content: str) -> Generator[List[str], None, None]:
        """Divide o conteúdo em chunks otimizados"""
        lines = content.split('\n')
        total_lines = len(lines)
        
        logger.info(f"Processing {total_lines} lines in chunks of {self.chunk_size}")
        
        for i in range(0, total_lines, self.chunk_size):
            chunk = lines[i:i + self.chunk_size]
            # Filtrar linhas vazias para otimização
            chunk = [line.strip() for line in chunk if line.strip()]
            if chunk:  # Só retornar chunks não vazios
                yield chunk
    
    async def process_large_log(
        self, 
        content: str, 
        filename: str = "large_log",
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Processa log grande com otimizações de performance
        """
        start_time = time.time()
        all_lines = content.split('\n')
        log_type = self.analyzer._detect_log_type(content)
        
        # Estatísticas consolidadas
        consolidated_stats = {
            'total_lines_processed': 0,
            'total_chunks': 0,
            'errors_found': [],
            'total_errors_detected': 0,  # NOVO: Contador total de erros (sem limite)
            'attention_points': [],
            'error_counts': Counter(),
            'severity_counts': Counter(),
            'structured_events': 0,
            'processing_time_seconds': 0,
            'performance_metrics': {
                'lines_per_second': 0,
                'chunks_processed': 0,
                'memory_efficient': True,
                'chunk_size_used': self.chunk_size
            }
        }
        
        # Processamento estruturado consolidado
        structured_stats = {
            'by_type': Counter(),
            'http_status': Counter(),
            'java_levels': Counter(),
            'progress_levels': Counter(),
            'exceptions': Counter(),
            'temporal_distribution': defaultdict(int)
        }
        
        total_lines = len(content.split('\n'))
        processed_lines = 0
        
        logger.info(f"Starting large log processing: {total_lines} lines")
        
        try:
            # Processar em chunks
            for chunk_num, chunk_lines in enumerate(self.chunk_lines(content), 1):
                chunk_start_time = time.time()
                
                # Processar chunk atual
                chunk_content = '\n'.join(chunk_lines)
                
                # Análise tradicional de padrões (otimizada)
                chunk_result = self.analyzer.analyze_log_content(
                    chunk_content, 
                    enable_structured_parsing=False  # Fazer separadamente para controle
                )
                
                # Análise estruturada (otimizada)
                structured_result = self.structured_parser.parse_log_content(
                    chunk_content, 
                    enable_multiline=False  # Desabilitar para performance
                )
                
                # Consolidar resultados do chunk
                self._consolidate_chunk_results(
                    chunk_result, 
                    structured_result, 
                    consolidated_stats, 
                    structured_stats
                )
                
                processed_lines += len(chunk_lines)
                consolidated_stats['total_chunks'] = chunk_num
                consolidated_stats['total_lines_processed'] = processed_lines
                
                # Callback de progresso
                if progress_callback:
                    progress = (processed_lines / total_lines) * 100
                    await progress_callback({
                        'progress': progress,
                        'chunk': chunk_num,
                        'lines_processed': processed_lines,
                        'total_lines': total_lines,
                        'current_errors': len(consolidated_stats['errors_found'])
                    })
                
                # Log de progresso
                chunk_time = time.time() - chunk_start_time
                if chunk_num % 10 == 0:  # Log a cada 10 chunks
                    logger.info(f"Processed chunk {chunk_num}: {len(chunk_lines)} lines in {chunk_time:.2f}s")
                
                # Limpeza de memória periódica
                if chunk_num % 50 == 0:  # A cada 50 chunks
                    gc.collect()
                
                # REMOVIDO: Não parar o processamento - continuar processando todo o log
                # O limite max_results é aplicado apenas na consolidação, não para o processamento
        
        except Exception as e:
            logger.error(f"Error processing large log: {e}")
            return {
                'success': False,
                'error': str(e),
                'partial_results': consolidated_stats
            }
        
        # Finalizar estatísticas
        total_time = time.time() - start_time
        consolidated_stats['processing_time_seconds'] = round(total_time, 2)
        consolidated_stats['performance_metrics']['lines_per_second'] = round(
            processed_lines / max(total_time, 1), 2
        )
        
        # Criar resultado final otimizado
        final_result = self._create_optimized_result(
            consolidated_stats, 
            structured_stats, 
            filename,
            all_lines,
            log_type
        )
        
        logger.info(f"Large log processing completed: {processed_lines} lines in {total_time:.2f}s")
        
        return final_result
    
    def _consolidate_chunk_results(
        self, 
        chunk_result: Dict, 
        structured_result: Dict, 
        consolidated_stats: Dict, 
        structured_stats: Dict
    ):
        """Consolida resultados de um chunk nas estatísticas gerais"""
        
        # Consolidar erros
        if 'results' in chunk_result:
            # Contar TODOS os erros encontrados
            consolidated_stats['total_errors_detected'] += len(chunk_result['results'])
            
            # Mas só guardar até o limite (para não sobrecarregar memória/frontend)
            for result in chunk_result['results']:
                if len(consolidated_stats['errors_found']) < self.max_results:
                    # Adicionar informações de chunk para contexto
                    result['chunk_info'] = {
                        'chunk_number': consolidated_stats['total_chunks'],
                        'relative_line': result.get('line', 0)
                    }
                    consolidated_stats['errors_found'].append(result)
        
        # Consolidar pontos de atenção (limitado)
        if 'attention_points' in chunk_result:
            for attention in chunk_result['attention_points']:
                if len(consolidated_stats['attention_points']) < 1000:  # Limite menor
                    attention['chunk_info'] = {
                        'chunk_number': consolidated_stats['total_chunks']
                    }
                    consolidated_stats['attention_points'].append(attention)
        
        # Consolidar contadores
        if 'error_counts' in chunk_result:
            consolidated_stats['error_counts'].update(chunk_result['error_counts'])
        
        if 'severity_counts' in chunk_result:
            consolidated_stats['severity_counts'].update(chunk_result['severity_counts'])
        
        # Consolidar dados estruturados
        if 'statistics' in structured_result:
            stats = structured_result['statistics']
            
            consolidated_stats['structured_events'] += structured_result.get('structured_events', 0)
            
            # Atualizar contadores estruturados
            for key, counter in [
                ('by_type', 'by_type'),
                ('http_status', 'http_status'),
                ('java_levels', 'java_levels'),
                ('progress_levels', 'progress_levels'),
                ('exceptions', 'exceptions')
            ]:
                if key in stats:
                    structured_stats[counter].update(stats[key])
    
    def _create_optimized_result(
        self, 
        consolidated_stats: Dict, 
        structured_stats: Dict, 
        filename: str,
        all_lines: List[str],
        log_type: str
    ) -> Dict[str, Any]:
        """Cria resultado final otimizado para logs grandes"""
        
        total_results = len(consolidated_stats['errors_found'])
        total_attention = len(consolidated_stats['attention_points'])
        
        # Total de erros realmente detectados (pode ser maior que errors_found se atingiu limite)
        total_errors_detected = consolidated_stats.get('total_errors_detected', total_results)
        
        performance_analysis = self.analyzer.analyze_performance(all_lines, log_type)
        top_programs_methods = self.analyzer._analyze_callers_and_programs(all_lines, log_type)

        return {
            'success': True,
            'log_type': log_type,
            'large_log_processing': True,
            'filename': filename,
            'processing_summary': {
                'total_lines_processed': consolidated_stats['total_lines_processed'],
                'chunks_processed': consolidated_stats['total_chunks'],
                'processing_time': consolidated_stats['processing_time_seconds'],
                'lines_per_second': consolidated_stats['performance_metrics']['lines_per_second'],
                'chunk_size_used': self.chunk_size,
                'results_limited': total_results >= self.max_results,
                'total_errors_detected': total_errors_detected,  # NOVO: Total real de erros
                'errors_shown': total_results  # Quantos estão sendo mostrados
            },
            'statistics': {
                'total_lines_processed': consolidated_stats['total_lines_processed'],
                'total_matches_found': total_errors_detected,  # ATUALIZADO: Usar contador total
                'matches_shown': total_results,  # NOVO: Quantos estão visíveis
                'match_percentage': round((total_errors_detected / max(consolidated_stats['total_lines_processed'], 1)) * 100, 2),
                'error_types_count': len(consolidated_stats['error_counts']),
                'most_common_error': consolidated_stats['error_counts'].most_common(1),
                'processing_performance': {
                    'lines_per_second': consolidated_stats['performance_metrics']['lines_per_second'],
                    'total_time_seconds': consolidated_stats['processing_time_seconds'],
                    'memory_efficient': True,
                    'fully_processed': True  # NOVO: Indica que todo o log foi processado
                }
            },
            'results': consolidated_stats['errors_found'][:1000],  # Limitar resposta para frontend
            'total_results': total_errors_detected,  # ATUALIZADO: Total real
            'results_truncated': total_results > 1000,  # Para indicar se os results foram limitados
            'error_counts': dict(consolidated_stats['error_counts'].most_common(20)),
            'severity_counts': dict(consolidated_stats['severity_counts']),
            'attention_points': consolidated_stats['attention_points'][:200],  # Limitar
            'total_attention_points': total_attention,
            'performance_analysis': performance_analysis,
            'top_programs_methods': top_programs_methods,
            'informational_lines': self.analyzer._detect_informational_lines(all_lines),
            'structured_analysis': {
                'enabled': True,
                'total_events': consolidated_stats['structured_events'],
                'type_breakdown': dict(structured_stats['by_type']),
                'http_metrics': {
                    'status_distribution': dict(structured_stats['http_status'].most_common(10)),
                    'total_requests': sum(structured_stats['http_status'].values())
                } if structured_stats['http_status'] else {},
                'java_metrics': {
                    'level_distribution': dict(structured_stats['java_levels']),
                    'top_exceptions': dict(structured_stats['exceptions'].most_common(10))
                } if structured_stats['java_levels'] else {}
            },
            'chart_data': self._create_optimized_charts(consolidated_stats, structured_stats),
            'performance_notes': [
                f"Processed {consolidated_stats['total_lines_processed']:,} lines in {consolidated_stats['total_chunks']} chunks",
                f"Performance: {consolidated_stats['performance_metrics']['lines_per_second']:,.0f} lines/second",
                f"Memory efficient processing used (chunk size: {self.chunk_size})",
                "Results may be truncated for large datasets" if total_results >= self.max_results else "Complete analysis"
            ]
        }
    
    def _create_optimized_charts(self, consolidated_stats: Dict, structured_stats: Dict) -> Dict[str, Any]:
        """Cria dados de gráficos otimizados"""
        
        # Top 10 apenas para performance
        top_errors = consolidated_stats['error_counts'].most_common(10)
        top_severities = consolidated_stats['severity_counts'].most_common(5)
        
        return {
            'error_types': {
                'labels': [item[0] for item in top_errors],
                'values': [item[1] for item in top_errors]
            },
            'severity': {
                'labels': [item[0] for item in top_severities],
                'values': [item[1] for item in top_severities]
            },
            'temporal': {
                'labels': [],  # Desabilitado para performance
                'values': []
            },
            'hourly': {
                'labels': [],  # Desabilitado para performance em logs grandes
                'values': []
            },
            'structured_types': {
                'labels': list(structured_stats['by_type'].keys()),
                'values': list(structured_stats['by_type'].values())
            } if structured_stats['by_type'] else {'labels': [], 'values': []}
        }

# Funções de conveniência
async def process_large_log_file(content: str, db, filename: str = "large_log") -> Dict[str, Any]:
    """Função de conveniência para processar logs grandes"""
    processor = LargeLogProcessor(chunk_size=1000, max_results=5000)
    await processor.initialize(db)
    return await processor.process_large_log(content, filename)

async def get_processing_recommendations(file_size_bytes: int, line_count: int) -> Dict[str, Any]:
    """Retorna recomendações de processamento baseadas no tamanho do arquivo"""
    
    # Calcular chunk size otimizado baseado no tamanho
    if line_count <= 5000:
        chunk_size = 1000
        processing_type = "normal"
    elif line_count <= 20000:
        chunk_size = 2000
        processing_type = "large"
    elif line_count <= 50000:
        chunk_size = 3000
        processing_type = "very_large"
    else:
        chunk_size = 5000
        processing_type = "massive"
    
    # Estimar tempo de processamento
    estimated_time_seconds = max(10, line_count / 2000)  # ~2000 linhas por segundo
    
    return {
        'processing_type': processing_type,
        'recommended_chunk_size': chunk_size,
        'estimated_time_seconds': round(estimated_time_seconds, 1),
        'estimated_time_human': f"{estimated_time_seconds/60:.1f} minutos" if estimated_time_seconds > 60 else f"{estimated_time_seconds:.0f} segundos",
        'memory_usage_estimate': 'Alto' if line_count > 50000 else 'Médio',
        'recommendations': [
            "Processamento em chunks otimizado será usado",
            "Resultados podem ser limitados para performance",
            "Análise estruturada será otimizada",
            f"Arquivo será dividido em ~{line_count//chunk_size} chunks"
        ]
    }