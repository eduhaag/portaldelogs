#!/usr/bin/env python3
"""
Carregador híbrido que usa MongoDB quando disponível, senão usa padrões hardcoded + JSON
"""

import logging
from typing import Dict, List, Any, Optional
import re
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class DatasulHybridLoader:
    """Carregador híbrido: MongoDB + JSON files + fallback hardcoded."""
    
    def __init__(self):
        self.mongodb_loader = None
        self.hardcoded_patterns = self._get_hardcoded_patterns()
        self.json_patterns = []  # NOVO: Padrões dos arquivos JSON
        self.use_mongodb = False
        
        # NOVO: Carregar padrões dos arquivos JSON automaticamente
        self._load_json_patterns()
        
    def _load_json_patterns(self):
        """Carrega padrões dos arquivos JSON (255 padrões totais)"""
        try:
            json_files = [
                Path(__file__).parent / 'data' / 'datasul_mais_100_erros_tagged.json',
                Path(__file__).parent / 'data' / 'datasul_fat_mais_100_erros_tagged.json',
                Path(__file__).parent / 'data' / 'datasul_mais_150_erros.json',
                Path(__file__).parent / 'data' / 'datasul_progress_165_erros.json',
                Path(__file__).parent / 'data' / 'novos_erros_datasul.json'
            ]
            
            total_loaded = 0
            for json_file in json_files:
                if json_file.exists():
                    with open(json_file, 'r', encoding='utf-8') as f:
                        patterns = json.load(f)
                        self.json_patterns.extend(patterns)
                        total_loaded += len(patterns)
                        logger.info(f"Loaded {len(patterns)} Datasul patterns from {json_file.name}")
                else:
                    logger.debug(f"Optional JSON file not found: {json_file}")
            
            if total_loaded > 0:
                logger.info(f"Total Datasul JSON patterns loaded: {total_loaded}")
            else:
                logger.warning("No Datasul JSON patterns loaded")
                
        except Exception as e:
            logger.error(f"Error loading Datasul JSON patterns: {e}")
            self.json_patterns = []
        
    async def initialize(self, db=None):
        """Inicializa tentando MongoDB primeiro, depois fallback para JSON + hardcoded"""
        
        # Tentar MongoDB primeiro
        if db is not None:
            try:
                from datasul_mongodb_loader import DatasulMongoDBLoader
                self.mongodb_loader = DatasulMongoDBLoader(db)
                success = await self.mongodb_loader.load_patterns_from_db()
                
                if success:
                    self.use_mongodb = True
                    logger.info("Using MongoDB for Datasul patterns")
                    return True
            except Exception as e:
                logger.warning(f"MongoDB loader failed, using JSON + hardcoded fallback: {e}")
        
        # Fallback para JSON + hardcoded
        self.use_mongodb = False
        total_patterns = len(self.json_patterns) + len(self.hardcoded_patterns)
        logger.info(f"Using JSON + hardcoded Datasul patterns ({total_patterns} patterns total)")
        logger.info(f"  - JSON files: {len(self.json_patterns)} patterns")
        logger.info(f"  - Hardcoded: {len(self.hardcoded_patterns)} patterns")
        return True
    
    def get_patterns_for_classification(self) -> List[str]:
        """Retorna padrões para classificação (MongoDB ou JSON + hardcoded)"""
        if self.use_mongodb and self.mongodb_loader:
            return self.mongodb_loader.get_patterns_for_classification()
        else:
            # Combinar JSON + hardcoded
            patterns = []
            patterns.extend([p["pattern"] for p in self.json_patterns if p.get("pattern")])
            patterns.extend([p["pattern"] for p in self.hardcoded_patterns if p.get("pattern")])
            return patterns
    
    def get_all_patterns(self) -> List[Dict]:
        """Retorna todos os padrões disponíveis"""
        if self.use_mongodb and self.mongodb_loader:
            if hasattr(self.mongodb_loader, "get_all_patterns"):
                return self.mongodb_loader.get_all_patterns()
            return self.mongodb_loader.get_all_patterns_with_solutions()
        else:
            # Combinar JSON + hardcoded
            return self.json_patterns + self.hardcoded_patterns
    
    def get_solution_for_pattern(self, detected_line: str) -> Optional[Dict[str, Any]]:
        """Busca solução com fallback automático (MongoDB -> JSON -> hardcoded)"""
        
        # Tentar MongoDB primeiro
        if self.use_mongodb and self.mongodb_loader:
            result = self.mongodb_loader.get_solution_for_pattern(detected_line)
            if result:
                return result
        
        # Buscar em JSON patterns (255 padrões)
        for pattern_data in self.json_patterns:
            try:
                pattern = pattern_data.get("pattern", "")
                if not pattern:
                    continue
                    
                if re.search(pattern, detected_line, re.IGNORECASE):
                    return {
                        "description": pattern_data.get("description", ""),
                        "category": pattern_data.get("category", ""),
                        "severity": pattern_data.get("severity", "Médio"),
                        "solution": pattern_data.get("solution", ""),
                        "tag": pattern_data.get("tag", "Datasul"),
                        "example": pattern_data.get("example", ""),
                        "matched_pattern": pattern,
                        "priority": self._get_priority(pattern_data.get("severity", "Médio")),
                        "source": pattern_data.get("source", "Datasul JSON")
                    }
                    
            except re.error:
                continue
        
        # Fallback para hardcoded (11 padrões)
        for pattern_data in self.hardcoded_patterns:
            try:
                pattern = pattern_data.get("pattern", "")
                if not pattern:
                    continue
                    
                if re.search(pattern, detected_line, re.IGNORECASE):
                    return {
                        "description": pattern_data.get("description", ""),
                        "category": pattern_data.get("category", ""),
                        "severity": pattern_data.get("severity", "Médio"),
                        "solution": pattern_data.get("solution", ""),
                        "tag": pattern_data.get("tag", "Datasul"),
                        "matched_pattern": pattern,
                        "priority": self._get_priority(pattern_data.get("severity", "Médio")),
                        "source": "hardcoded"
                    }
                    
            except re.error:
                continue
                
        return None
    
    def get_all_patterns_with_solutions(self) -> List[Dict[str, Any]]:
        """Retorna todos os padrões disponíveis"""
        if self.use_mongodb and self.mongodb_loader:
            return self.mongodb_loader.get_all_patterns_with_solutions()
        else:
            return self.hardcoded_patterns
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos padrões"""
        if self.use_mongodb and self.mongodb_loader:
            return self.mongodb_loader.get_statistics()
        else:
            categories = {}
            for pattern in self.hardcoded_patterns:
                cat = pattern.get("category", "Outros")
                categories[cat] = categories.get(cat, 0) + 1
            
            return {
                "total_patterns": len(self.hardcoded_patterns),
                "source": "hardcoded",
                "patterns_by_category": categories,
                "cache_age_seconds": 0,
                "most_used_patterns": []
            }
    
    def _get_priority(self, severity: str) -> int:
        """Converte severidade em prioridade"""
        priority_map = {
            "Crítico": 5,
            "Alto": 4,
            "Médio": 3,
            "Baixo": 2,
            "Informativo": 1
        }
        return priority_map.get(severity, 3)
    
    def _get_hardcoded_patterns(self) -> List[Dict[str, Any]]:
        """Padrões hardcoded como backup"""
        return [
            {
                "pattern": r"\*\*\s*Parametro\s+NFe\s+already\s+exists\s+with\s+Empresa",
                "description": "Erro de duplicação de parâmetro NFe para a empresa. Indica que já existe uma configuração NFe para a empresa especificada.",
                "category": "FAT/NFe",
                "severity": "Alto",
                "example": "** Parametro NFe already exists with Empresa \"000007\". (132)",
                "solution": "1) Verificar se já existe configuração NFe para a empresa no sistema. 2) Se necessário, excluir a configuração duplicada via menu Fiscal > NFe > Configurações. 3) Reprocessar a configuração da empresa. 4) Verificar se o TSS está corretamente configurado.",
                "tag": "NFe/Configuração"
            },
            {
                "pattern": r"Rejei(c|ç)ão\s*204",
                "description": "SEFAZ rejeição 204: Solicitação de concessão de autorização de uso de documento fiscal eletrônico pendente de retorno.",
                "category": "FAT/NFe",
                "severity": "Alto",
                "example": "Rejeição 204 durante transmissão da NFe",
                "solution": "Verificar o status da nota fiscal no portal da SEFAZ. Se estiver pendente, aguardar o processamento e tentar o envio novamente. Se persistir, verificar a conexão com o SEFAZ e contatar o suporte.",
                "tag": "NFe"
            },
            {
                "pattern": r"CFOP\s*5101\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
                "description": "CFOP 5101 incompatível com a natureza/finalidade ou UF.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Rejeição CFOP 5101 não permitido para UF AM",
                "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
                "tag": "CFOP"
            },
            {
                "pattern": r"CFOP\s*5102\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
                "description": "CFOP 5102 incompatível com a natureza/finalidade ou UF.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Rejeição CFOP 5102 não permitido para UF PR",
                "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
                "tag": "CFOP"
            },
            {
                "pattern": r"(CST|CSOSN)\s*00\s*(inv(á|a)lido|incompa)",
                "description": "CST/CSOSN 00 incompatível com CFOP/regime tributário.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Incompatibilidade CST 00 x CFOP",
                "solution": "Alinhar CST/CSOSN ao regime (SN/Normal) e natureza. Revisar regra fiscal do item.",
                "tag": "ICMS"
            },
            {
                "pattern": r"OutOfMemoryError|\bJava heap space",
                "description": "Heap da JVM esgotado.",
                "category": "Infra/Tomcat",
                "severity": "Alto",
                "example": "OutOfMemoryError: Java heap space",
                "solution": "Ajustar -Xmx/-Xms; revisar vazamento de memória e cargas.",
                "tag": "Infra"
            },
            {
                "pattern": r"LOCK TABLE OVERFLOW",
                "description": "Tabela de locks excedida.",
                "category": "DataServer/DB",
                "severity": "Alto",
                "example": "LOCK TABLE OVERFLOW",
                "solution": "Aumentar -L nos parâmetros de banco (OpenEdge) e revisar transações prolongadas.",
                "tag": "Banco de Dados"
            },
            {
                "pattern": r"Appserver.*(nao|não)\s*responde|log\s*4gb",
                "description": "AppServer não responde / log do broker gigante.",
                "category": "Infra/Framework",
                "severity": "Médio",
                "example": "AppServer não responde / log do broker gigante",
                "solution": "Rotacionar/deletar logs >4GB e reiniciar broker; revisar política de logs.",
                "tag": "Infra"
            },
            {
                "pattern": r"Duplicata\s*n(ã|a)o\s*gerada",
                "description": "Erro na geração de duplicatas a partir da nota fiscal.",
                "category": "Financeiro/Integração",
                "severity": "Médio",
                "example": "Duplicata não gerada",
                "solution": "Verificar a integração entre o módulo de faturamento (FAT) e o módulo financeiro (AP/AR). Garantir que as condições de pagamento, vencimentos e dados da nota fiscal estejam corretos para a geração automática das duplicatas.",
                "tag": "Financeiro"
            },
            {
                "pattern": r"Procedure:",
                "description": "Linha de log indicando o início da execução de uma procedure (rotina/programa). Serve como um gatilho para investigar o fluxo do programa.",
                "category": "Framework/Log",
                "severity": "Alto",
                "example": "Procedure: prg/rotina.p Linha: 123 Usuário: ABC",
                "solution": "Utilizar esta informação para rastrear o fluxo de execução do sistema. Analisar a procedure mencionada, a linha de código e o contexto (usuário, dados envolvidos) para entender a origem de um possível problema.",
                "tag": "Pontos de Atenção"
            },
            {
                "pattern": r"LOG:MANAGER",
                "description": "Linha de log gerada pelo módulo de gerenciamento de logs do sistema.",
                "category": "Infra/Log",
                "severity": "Alto",
                "example": "LOG:MANAGER - rotation scheduled, file limit reached",
                "solution": "Analisar as mensagens do LOG:MANAGER para entender eventos relacionados à gestão de logs (rotação, limite de tamanho, etc.). Esses eventos podem indicar problemas de disco ou configurações incorretas que precisam ser corrigidas.",
                "tag": "Pontos de Atenção"
            }
        ]