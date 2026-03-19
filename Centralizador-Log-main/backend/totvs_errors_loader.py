#!/usr/bin/env python3
"""
Carregador de padrões de erro TOTVS/Datasul específicos
Suporta detecção parcial de erros com códigos numéricos
"""

import json
import logging
import re
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TotvsErrorsLoader:
    """Carrega e gerencia padrões de erro TOTVS/Datasul específicos"""
    
    def __init__(self, db=None):
        self.db = db
        self.patterns = []
        self.code_patterns = {}  # Mapa de código -> padrão para busca rápida
        self._load_patterns()
    
    def _load_patterns(self):
        """Carrega padrões TOTVS/Datasul do arquivo JSON"""
        try:
            json_file = Path(__file__).parent / 'totvs_errors.json'
            
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
                    logger.info(f"Loaded {len(self.patterns)} TOTVS error patterns from JSON file")
                    
                    # Criar mapa de códigos para busca rápida
                    for pattern in self.patterns:
                        code = pattern.get('code')
                        if code:
                            self.code_patterns[code] = pattern
                            # Criar regex simples para detecção por código
                            pattern['code_regex'] = re.compile(rf'\({code}\)|\[{code}\]|{code}', re.IGNORECASE)
            else:
                logger.warning("TOTVS errors JSON file not found")
                self.patterns = []
                
        except Exception as e:
            logger.error(f"Error loading TOTVS error patterns: {e}")
            self.patterns = []
    
    async def load_from_mongodb(self):
        """Carrega padrões TOTVS do MongoDB (se existir coleção)"""
        if self.db is None:
            return []
        
        try:
            # Tentar carregar da coleção totvs_errors
            cursor = self.db.totvs_errors.find({"active": {"$ne": False}})
            db_patterns = await cursor.to_list(length=None)
            
            if db_patterns:
                logger.info(f"Loaded {len(db_patterns)} TOTVS error patterns from MongoDB")
                merged_patterns = {}
                for pattern in self.patterns:
                    key = pattern.get('code') or pattern.get('pattern')
                    if key:
                        merged_patterns[key] = pattern
                for pattern in db_patterns:
                    key = pattern.get('code') or pattern.get('pattern')
                    if key:
                        merged_patterns[key] = pattern
                self.patterns = list(merged_patterns.values())
                self.code_patterns = {}
                for pattern in self.patterns:
                    code = pattern.get('code')
                    if code:
                        self.code_patterns[code] = pattern
            
            return db_patterns
            
        except Exception as e:
            logger.warning(f"Could not load TOTVS error patterns from MongoDB: {e}")
            return []
    
    def get_patterns_for_classification(self) -> List[str]:
        """Retorna lista de padrões regex para classificação"""
        return [p['pattern'] for p in self.patterns if 'pattern' in p]
    
    def get_all_patterns(self) -> List[Dict]:
        """Retorna todos os padrões TOTVS"""
        return self.patterns
    
    def get_all_codes(self) -> List[str]:
        """Retorna todos os códigos de erro disponíveis"""
        return list(self.code_patterns.keys())
    
    def check_error_by_code(self, line: str) -> Optional[Dict]:
        """
        Verifica se a linha contém algum código de erro TOTVS
        
        Args:
            line: Linha do log
            
        Returns:
            Dict com informações do erro ou None
        """
        for code, pattern_obj in self.code_patterns.items():
            # Verificar se o código aparece na linha
            code_regex = pattern_obj.get('code_regex')
            if code_regex and code_regex.search(line):
                return self._format_match_result(pattern_obj, code)
        
        return None
    
    def check_error_partial(self, line: str) -> Optional[Dict]:
        """
        Verifica se a linha contém partes de um erro TOTVS (detecção parcial)
        Útil quando o erro aparece truncado ou com prefixos como ** ou (Procedure:
        
        Args:
            line: Linha do log
            
        Returns:
            Dict com informações do erro ou None
        """
        # Primeiro verificar por código (mais rápido)
        code_match = self.check_error_by_code(line)
        if code_match:
            return code_match
        
        # Depois verificar padrões completos
        for pattern_obj in self.patterns:
            try:
                pattern = pattern_obj.get('pattern', '')
                if pattern and re.search(pattern, line, re.IGNORECASE):
                    return self._format_match_result(pattern_obj)
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {pattern} - {e}")
                continue
        
        return None
    
    def _format_match_result(self, pattern_obj: Dict, matched_code: str = None) -> Dict:
        """Formata resultado do match"""
        return {
            'pattern': pattern_obj.get('pattern', ''),
            'matched_pattern': pattern_obj.get('pattern', ''),
            'code': pattern_obj.get('code', matched_code),
            'description': pattern_obj.get('description', ''),
            'solution': pattern_obj.get('solution', ''),
            'category': pattern_obj.get('category', ''),
            'severity': pattern_obj.get('severity', 'Médio'),
            'tag': pattern_obj.get('tag', ''),
            'example': pattern_obj.get('example', ''),
            'reference': pattern_obj.get('reference', 'TOTVS Datasul Knowledge Base'),
            'priority': self._get_priority_from_severity(pattern_obj.get('severity', 'Médio'))
        }
    
    def get_solution_for_pattern(self, error_message: str) -> Optional[Dict]:
        """
        Busca solução para um erro específico
        
        Args:
            error_message: Mensagem de erro
            
        Returns:
            Dict com description, solution, tag, etc. ou None
        """
        return self.check_error_partial(error_message)
    
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
                pattern.get('solution', ''),
                pattern.get('reference', ''),
                pattern.get('code', '')
            ]).lower()
            
            if search_lower in searchable_text:
                results.append(pattern)
                
                if len(results) >= limit:
                    break
        
        return results


# Instância global para reutilização
_totvs_loader = None

def get_totvs_loader(db=None):
    """Retorna instância singleton do loader"""
    global _totvs_loader
    if _totvs_loader is None:
        _totvs_loader = TotvsErrorsLoader(db)
    return _totvs_loader
