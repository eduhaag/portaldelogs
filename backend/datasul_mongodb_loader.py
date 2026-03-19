#!/usr/bin/env python3
"""
Carregador otimizado de padrões Datasul do MongoDB
"""

import logging
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

logger = logging.getLogger(__name__)

class DatasulMongoDBLoader:
    """Carregador de padrões Datasul do MongoDB com cache e otimizações."""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
        self.datasul_patterns_cache = []
        self.patterns_by_priority = {}
        self.patterns_by_category = {}
        self.last_cache_update = None
        self.cache_ttl_seconds = 300  # 5 minutos
        
    async def load_patterns_from_db(self) -> bool:
        """Carrega padrões do MongoDB com otimização por prioridade"""
        
        if self.db is None:
            logger.error("Database connection not provided")
            return False
            
        try:
            # Carregando TODOS os padrões ativos (filtro removido para incluir batch 165)
            patterns = await self.db.datasul_patterns.find({
                "active": True
            }).to_list(None)
            
            if not patterns:
                logger.warning("No active Datasul patterns found in database")
                return False
            
            # Cache principal
            self.datasul_patterns_cache = patterns
            
            # Cache por prioridade (para otimizar detecção)
            self.patterns_by_priority = {
                5: [],  # Crítico
                4: [],  # Alto
                3: [],  # Médio
                2: [],  # Baixo
                1: []   # Informativo
            }
            
            # Cache por categoria
            self.patterns_by_category = {}
            
            for pattern in patterns:
                priority = pattern.get('priority', 3)
                category = pattern.get('category', 'Outros')
                
                self.patterns_by_priority[priority].append(pattern)
                
                if category not in self.patterns_by_category:
                    self.patterns_by_category[category] = []
                self.patterns_by_category[category].append(pattern)
            
            from datetime import datetime
            self.last_cache_update = datetime.now()
            
            logger.info(f"Loaded {len(patterns)} Datasul patterns from MongoDB")
            logger.info(f"Patterns by priority: {[(k, len(v)) for k, v in self.patterns_by_priority.items() if v]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading Datasul patterns from MongoDB: {e}")
            return False
    
    def get_patterns_for_classification(self) -> List[str]:
        """Retorna padrões regex ordenados por prioridade para detecção otimizada"""
        patterns = []
        
        # Retornar por ordem de prioridade (crítico primeiro)
        for priority in [5, 4, 3, 2, 1]:
            for pattern_data in self.patterns_by_priority.get(priority, []):
                pattern = pattern_data.get("pattern", "")
                if pattern and self._validate_regex(pattern):
                    patterns.append(pattern)
        
        return patterns
    
    def get_solution_for_pattern(self, detected_line: str) -> Optional[Dict[str, Any]]:
        """Busca solução otimizada por prioridade e atualiza estatísticas"""
        
        # Buscar por prioridade (crítico primeiro)
        for priority in [5, 4, 3, 2, 1]:
            for pattern_data in self.patterns_by_priority.get(priority, []):
                try:
                    pattern = pattern_data.get("pattern", "")
                    if not pattern:
                        continue
                        
                    if re.search(pattern, detected_line, re.IGNORECASE):
                        # Incrementar contador de uso (async em background)
                        if self.db is not None:
                            import asyncio
                            asyncio.create_task(self._increment_usage_count(pattern_data.get("id")))
                        
                        return {
                            "description": pattern_data.get("description", ""),
                            "category": pattern_data.get("category", ""),
                            "severity": pattern_data.get("severity", "Médio"),
                            "solution": pattern_data.get("solution", ""),
                            "tag": pattern_data.get("tag", "Datasul"),
                            "matched_pattern": pattern,
                            "priority": pattern_data.get("priority", 3),
                            "pattern_id": pattern_data.get("id", "")
                        }
                        
                except re.error as e:
                    logger.warning(f"Invalid regex pattern: {pattern} - Error: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error matching pattern: {e}")
                    continue
        
        return None
    
    async def _increment_usage_count(self, pattern_id: str):
        """Incrementa contador de uso para estatísticas (em background)"""
        try:
            if self.db is not None and pattern_id:
                from datetime import datetime, timezone
                await self.db.datasul_patterns.update_one(
                    {"id": pattern_id},
                    {
                        "$inc": {"usage_count": 1},
                        "$set": {"last_detected": datetime.now(timezone.utc).isoformat()}
                    }
                )
        except Exception as e:
            logger.error(f"Error updating usage count: {e}")
    
    def get_all_patterns_with_solutions(self) -> List[Dict[str, Any]]:
        """Retorna todos os padrões com informações completas"""
        return self.datasul_patterns_cache
    
    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retorna padrões filtrados por categoria"""
        return self.patterns_by_category.get(category, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos padrões carregados"""
        total_patterns = len(self.datasul_patterns_cache)
        
        stats = {
            "total_patterns": total_patterns,
            "patterns_by_priority": {str(k): len(v) for k, v in self.patterns_by_priority.items()},
            "patterns_by_category": {k: len(v) for k, v in self.patterns_by_category.items()},
            "cache_age_seconds": 0,
            "most_used_patterns": []
        }
        
        if self.last_cache_update:
            from datetime import datetime
            delta = datetime.now() - self.last_cache_update
            stats["cache_age_seconds"] = int(delta.total_seconds())
        
        # Top 5 padrões mais usados
        sorted_by_usage = sorted(
            self.datasul_patterns_cache,
            key=lambda x: x.get("usage_count", 0),
            reverse=True
        )
        stats["most_used_patterns"] = [
            {
                "pattern": p.get("pattern", "")[:50] + "..." if len(p.get("pattern", "")) > 50 else p.get("pattern", ""),
                "usage_count": p.get("usage_count", 0),
                "tag": p.get("tag", "")
            }
            for p in sorted_by_usage[:5]
        ]
        
        return stats
    
    def _validate_regex(self, pattern: str) -> bool:
        """Valida se o padrão regex é válido"""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    async def should_refresh_cache(self) -> bool:
        """Verifica se o cache precisa ser atualizado"""
        if not self.last_cache_update:
            return True
            
        from datetime import datetime
        delta = datetime.now() - self.last_cache_update
        return delta.total_seconds() > self.cache_ttl_seconds

# Para compatibilidade com o sistema atual
import asyncio