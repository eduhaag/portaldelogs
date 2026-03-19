#!/usr/bin/env python3
"""
Carregador de padrões de erro LOGIX do MongoDB
Similar ao datasul_patterns_loader.py mas para erros LOGIX/TOTVS
"""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LogixPatternsLoader:
    """Carrega e gerencia padrões de erro LOGIX"""
    
    def __init__(self, db=None):
        self.db = db
        self.patterns = []
        self._load_patterns()
    
    def _load_patterns(self):
        """Carrega padrões LOGIX do arquivo JSON"""
        try:
            json_file = Path(__file__).parent / 'logix_erros.json'
            
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
                    logger.info(f"Loaded {len(self.patterns)} LOGIX patterns from JSON file")
            else:
                logger.warning("LOGIX patterns JSON file not found")
                self.patterns = []
                
        except Exception as e:
            logger.error(f"Error loading LOGIX patterns: {e}")
            self.patterns = []
    
    async def load_from_mongodb(self):
        """Carrega padrões LOGIX do MongoDB (se existir coleção)"""
        if self.db is None:
            return []
        
        try:
            # Tentar carregar da coleção logix_patterns
            cursor = self.db.logix_patterns.find({"active": True})
            db_patterns = await cursor.to_list(length=None)
            
            if db_patterns:
                logger.info(f"Loaded {len(db_patterns)} LOGIX patterns from MongoDB")
                merged_patterns = {
                    pattern.get('pattern'): pattern
                    for pattern in self.patterns
                    if pattern.get('pattern')
                }
                for pattern in db_patterns:
                    key = pattern.get('pattern')
                    if key:
                        merged_patterns[key] = pattern
                self.patterns = list(merged_patterns.values())
            
            return db_patterns
            
        except Exception as e:
            logger.warning(f"Could not load LOGIX patterns from MongoDB: {e}")
            return []
    
    def get_patterns_for_classification(self) -> List[str]:
        """Retorna lista de padrões regex para classificação"""
        return [p['pattern'] for p in self.patterns if 'pattern' in p]
    
    def get_all_patterns(self) -> List[Dict]:
        """Retorna todos os padrões LOGIX"""
        return self.patterns
    
    def get_solution_for_pattern(self, error_message: str) -> Optional[Dict]:
        """
        Busca solução para um erro específico
        
        Args:
            error_message: Mensagem de erro
            
        Returns:
            Dict com description, solution, tag, etc. ou None
        """
        import re
        
        for pattern_obj in self.patterns:
            try:
                pattern = pattern_obj.get('pattern', '')
                if re.search(pattern, error_message, re.IGNORECASE):
                    return {
                        'pattern': pattern,
                        'matched_pattern': pattern,
                        'description': pattern_obj.get('description', ''),
                        'solution': pattern_obj.get('solution', ''),
                        'category': pattern_obj.get('category', ''),
                        'severity': pattern_obj.get('severity', 'Médio'),
                        'tag': pattern_obj.get('tag', ''),
                        'example': pattern_obj.get('example', ''),
                        'source': pattern_obj.get('source', 'LOGIX Knowledge Base'),
                        'priority': self._get_priority_from_severity(pattern_obj.get('severity', 'Médio'))
                    }
            except Exception as e:
                logger.warning(f"Error matching LOGIX pattern: {e}")
                continue
        
        return None
    
    def _get_priority_from_severity(self, severity: str) -> int:
        """Converte severidade em prioridade numérica"""
        severity_map = {
            'Crítico': 1,
            'Alto': 2,
            'Médio': 3,
            'Baixo': 4
        }
        return severity_map.get(severity, 3)
    
    def search_patterns(self, search_term: str, limit: int = 20) -> List[Dict]:
        """
        Busca padrões por termo
        
        Args:
            search_term: Termo de busca
            limit: Limite de resultados
            
        Returns:
            Lista de padrões encontrados
        """
        import re
        
        results = []
        search_lower = search_term.lower()
        
        for pattern in self.patterns:
            # Buscar em múltiplos campos
            searchable_text = ' '.join([
                pattern.get('pattern', ''),
                pattern.get('description', ''),
                pattern.get('category', ''),
                pattern.get('tag', ''),
                pattern.get('example', ''),
                pattern.get('solution', '')
            ]).lower()
            
            if search_lower in searchable_text:
                results.append(pattern)
                
                if len(results) >= limit:
                    break
        
        return results


# Instância global para reutilização
_logix_loader = None

def get_logix_loader(db=None):
    """Retorna instância singleton do loader"""
    global _logix_loader
    if _logix_loader is None:
        _logix_loader = LogixPatternsLoader(db)
    return _logix_loader
