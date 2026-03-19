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


BUILTIN_PROTHEUS_ADVPL_PATTERNS = [
    {
        'pattern': r'variable does not exist\s+[A-Z0-9_]+',
        'description': 'Rotina ADVPL tentou acessar variavel nao inicializada, removida por customizacao, ou campo inexistente no dicionario/framework carregado.',
        'category': 'Framework/ADVPL',
        'severity': 'Crítico',
        'example': 'variable does not exist B2_MSIDENT',
        'solution': 'Validar compatibilidade entre RPO, dicionario SX3/SX2 e customizacoes; revisar a rotina apontada no stack e confirmar se o campo ou variavel existe no build atual.',
        'tag': 'ADVPL_RUNTIME',
        'reference': 'TOTVS | Application Server - Guia de Suporte',
        'product': 'Protheus/ADVPL'
    },
    {
        'pattern': r'Cannot find method\s+[A-Z0-9_:.]+:[A-Z0-9_]+',
        'description': 'O Framework/TLPP tentou invocar um metodo inexistente para a classe carregada no ambiente.',
        'category': 'Framework/ADVPL',
        'severity': 'Crítico',
        'example': 'Cannot find method QLTQUERYMANAGER:VALIDATAMANHOCAMPOSCHAVENF',
        'solution': 'Conferir compatibilidade entre fontes, LIB, RPO e Framework; validar se a classe e o metodo existem na release instalada e se nao ha mistura de pacotes de datas diferentes.',
        'tag': 'ADVPL_METHOD',
        'reference': 'TOTVS | Application Server / Framework Protheus',
        'product': 'Protheus/ADVPL'
    },
    {
        'pattern': r'Invalid ReadMSInt',
        'description': 'Falha em leitura de stream ou memoria, normalmente associada a incompatibilidade de build, sessao remota corrompida ou erro interno do framework visual.',
        'category': 'Infra/Memória',
        'severity': 'Crítico',
        'example': 'Invalid ReadMSInt in file memstream.hpp at line 657',
        'solution': 'Validar versao do AppServer, SmartClient/HTML e Framework; reiniciar a sessao; revisar componentes graficos e aplicar atualizacao se houver correcao na LIB ou build.',
        'tag': 'MEMSTREAM',
        'reference': 'TOTVS | Application Server - Guia de Suporte',
        'product': 'Protheus/ADVPL'
    },
    {
        'pattern': r'Failed to read status of inifile|fail to open:\s+.+\.(ini|tsk)',
        'description': 'O AppServer nao conseguiu abrir arquivo de configuracao obrigatorio do ambiente ou da rotina executada.',
        'category': 'Configuração/Application Server',
        'severity': 'Alto',
        'example': 'Failed to read status of inifile [/opt/totvs/appserver/language.ini][2][No such file or directory]',
        'solution': 'Conferir montagem de volume, permissoes e existencia do arquivo referenciado; revisar parametrizacao do container ou host e caminhos em appserver.ini.',
        'tag': 'MISSING_CONFIG',
        'reference': 'TOTVS | Application Server - Arquivo de configuração',
        'product': 'Protheus/ADVPL'
    },
    {
        'pattern': r'OPEN EMPTY RPO',
        'description': 'O ambiente abriu um RPO vazio, indicando pacote ausente, montagem incorreta ou artefato invalido.',
        'category': 'Configuração/Application Server',
        'severity': 'Alto',
        'example': 'OPEN EMPTY RPO - Environment ENVIRONMENT - File /mnt/apo/custom.rpo',
        'solution': 'Validar geracao e publicacao do RPO, checar tamanho do arquivo, permissoes e se o volume correto esta montado no ambiente.',
        'tag': 'EMPTY_RPO',
        'reference': 'TOTVS | Application Server - Guia de Suporte',
        'product': 'Protheus/ADVPL'
    },
    {
        'pattern': r'BPC2112.*MULTIPORT - error 5 unrecognized client|MULTIPORT - error 5 unrecognized client',
        'description': 'A porta multiprotocolo recebeu trafego incompatível com o protocolo esperado pelo AppServer.',
        'category': 'Infra/Application Server',
        'severity': 'Médio',
        'code': 'BPC2112',
        'example': 'BPC2112 E x 01 ctx:300002 MULTIPORT - error 5 unrecognized client',
        'solution': 'Revisar roteamento, health checks, ingress ou proxy e configuracao de SSL/MPP para garantir que apenas clientes compativeis acessem a MPPORT.',
        'tag': 'MULTIPORT',
        'reference': 'TOTVS | Application Server / Broker / Multi Protocol Port',
        'product': 'Protheus/ADVPL'
    },
    {
        'pattern': r'Usu[aá]rio do dom[ií]nio n[aã]o encontrado|Usuario do dominio nao encontrado',
        'description': 'Integracao de identidade do ambiente nao encontrou o usuario de dominio esperado para autenticacao ou webagent.',
        'category': 'Segurança/Application Server',
        'severity': 'Médio',
        'example': 'Usuario do dominio nao encontrado. Verifique webagent...',
        'solution': 'Validar parametros JBUSERNAME ou JB_USERNAME, configuracao do webagent e identidade disponivel no ambiente ou container.',
        'tag': 'IDENTITY',
        'reference': 'TOTVS | Application Server / identidade e webagent',
        'product': 'Protheus/ADVPL'
    },
]


class TotvsErrorsLoader:
    """Carrega e gerencia padrões de erro TOTVS/Datasul específicos"""
    
    def __init__(self, db=None):
        self.db = db
        self.patterns = []
        self.code_patterns = {}  # Mapa de código -> padrão para busca rápida
        self._load_patterns()

    def _prepare_pattern(self, pattern: Dict) -> Dict:
        """Normaliza e pré-compila regexes para evitar recompilação por linha."""
        prepared = dict(pattern)

        regex_pattern = prepared.get('pattern')
        if regex_pattern:
            try:
                prepared['compiled_regex'] = re.compile(regex_pattern, re.IGNORECASE)
            except re.error as exc:
                logger.warning(f"Invalid TOTVS regex pattern ignored during precompile: {regex_pattern} - {exc}")
                prepared['compiled_regex'] = None

        code = prepared.get('code')
        if code:
            prepared['code_regex'] = re.compile(rf'\({re.escape(code)}\)|\[{re.escape(code)}\]|{re.escape(code)}', re.IGNORECASE)

        return prepared

    def _rebuild_code_patterns(self):
        """Reconstrói o índice por código após carga de arquivo ou MongoDB."""
        self.code_patterns = {}
        for pattern in self.patterns:
            code = pattern.get('code')
            if code:
                self.code_patterns[code] = pattern
    
    def _load_patterns(self):
        """Carrega padrões TOTVS/Datasul do arquivo JSON"""
        try:
            json_file = Path(__file__).parent / 'totvs_errors.json'
            
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    raw_patterns = json.load(f)
                    merged_patterns = raw_patterns + BUILTIN_PROTHEUS_ADVPL_PATTERNS
                    self.patterns = [self._prepare_pattern(pattern) for pattern in merged_patterns]
                    logger.info(f"Loaded {len(self.patterns)} TOTVS error patterns from JSON file")
                    self._rebuild_code_patterns()
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
                        merged_patterns[key] = self._prepare_pattern(pattern)
                self.patterns = [self._prepare_pattern(pattern) for pattern in merged_patterns.values()]
                self._rebuild_code_patterns()
            
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
                compiled_regex = pattern_obj.get('compiled_regex')
                pattern = pattern_obj.get('pattern', '')
                if compiled_regex and compiled_regex.search(line):
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
            'product': pattern_obj.get('product', 'TOTVS'),
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
