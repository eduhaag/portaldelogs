"""
===============================
Analisador de Logs - Aqui a diversão começa!
===============================
Este arquivo é o Sherlock Holmes dos logs: detecta, categoriza, faz gráficos e ainda encontra aquele erro escondido no rodapé.
Prepare-se para comentários didáticos, piadinhas e dicas para quem for manter ou aprender!
"""

# =============================
# Configuração de logging global (porque até bug gosta de aparecer no log!)
# =============================
# Compila padrões originais e normalizados para busca turbo!
# Padrões específicos do Datasul (porque todo sistema tem seu jeitinho)
# Deixa os gráficos bonitos, porque até erro merece um visual legal!
# Carregadores de padrões do MongoDB (serão inicializados no servidor, tipo "robôs ajudantes")
# Padrões compilados para busca turbo (original e normalizado)
# Padrões para pontos de atenção (tipo "olha aqui!")
# OTIMIZAÇÕES DE PERFORMANCE: porque ninguém gosta de esperar!
# =============================
import re
import csv
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
from datetime import datetime
import io
import base64
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import os
import logging
import unicodedata
from time import monotonic
from datasul_hybrid_loader import DatasulHybridLoader
from local_pattern_store import list_records
from logix_patterns_loader import LogixPatternsLoader
from totvs_errors_loader import TotvsErrorsLoader
from structured_log_parser import StructuredLogParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROGRESS_TIMESTAMP_RE = re.compile(r'\[(\d{2})/(\d{2})/(\d{2})@(\d{2}):(\d{2}):(\d{2})\.(\d{3})([+-]\d{4})\]')
EXTRACT_TIMESTAMP_PATTERNS = (
    re.compile(r'\[(\d{2}/\d{2}/\d{2}@\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{4})\]'),
    re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'),
    re.compile(r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})'),
    re.compile(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})'),
    re.compile(r'(\w{3} \d{2} \d{2}:\d{2}:\d{2})'),
)
PROGRESS_LOG_MESSAGE_RE = re.compile(r'^\[[\d/]+@[\d:.-]+\]\s+P-\d+\s+T-\d+\s+(\d+)\s+')
OTHER_LOG_METADATA_PATTERNS = (
    re.compile(r'^\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\]\s*\[[^\]]+\]\s*\[[^\]]+\]\s*'),
    re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[.\d]*\s+\w+\s+\[[^\]]+\]\s*'),
    re.compile(r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+\w+\[\d+\]:\s*'),
    re.compile(r'^\d{2}:\d{2}:\d{2}[.\d]*\s+\[[^\]]+\]\s+\w+\s*'),
    re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*'),
    re.compile(r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*'),
)
ATTENTION_TOKENS = (
    ('UPC', 'UPC'),
    ('TW-', 'tw-'),
    ('(PROCEDURE', '(Procedure'),
    ('LOG:MANAGER', 'LOG:MANAGER'),
    ('CRC', 'CRC'),
    ('ESPEC', 'ESPEC'),
    ('TD-', 'td-'),
    ('-00U', '-00u'),
)

def normalize_text(text):
    """Remove acentos e converte para minúscula para comparação insensível a acentos."""
    if not isinstance(text, str):
        text = str(text)
    # Normalizar unicode e remover acentos
    nfkd_form = unicodedata.normalize('NFKD', text)
    without_accents = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    return without_accents.lower()

def create_partial_pattern(pattern):
    """Cria padrão regex para busca parcial, escapando caracteres especiais."""
    if not pattern:
        return pattern
    # Escapar caracteres especiais do regex, mas permitir busca parcial
    escaped = re.escape(str(pattern))
    # Substituir espaços por regex que permite qualquer quantidade de espaços
    escaped = escaped.replace(r'\ ', r'\s+')
    return escaped

def compile_custom_patterns(patterns_list):
    """Compila lista de padrões personalizados para busca parcial e insensível a acentos."""
    if not patterns_list:
        return [], []
    
    original_patterns = []
    normalized_patterns = []
    
    for pattern in patterns_list:
        if not pattern or not str(pattern).strip():
            continue
            
        pattern_str = str(pattern).strip()
        
        # Padrão original com busca parcial
        try:
            partial_pattern = create_partial_pattern(pattern_str)
            compiled = re.compile(partial_pattern, re.IGNORECASE)
            original_patterns.append(compiled)
        except re.error:
            # Fallback: escape completo
            try:
                escaped = re.escape(pattern_str)
                compiled = re.compile(escaped, re.IGNORECASE)
                original_patterns.append(compiled)
            except re.error:
                logger.warning(f"Could not compile pattern: {pattern_str}")
                continue
        
        # Padrão normalizado (sem acentos) com busca parcial
        try:
            normalized_pattern_str = normalize_text(pattern_str)
            partial_normalized = create_partial_pattern(normalized_pattern_str)
            compiled_norm = re.compile(partial_normalized, re.IGNORECASE)
            normalized_patterns.append(compiled_norm)
        except re.error:
            try:
                escaped_norm = re.escape(normalize_text(pattern_str))
                compiled_norm = re.compile(escaped_norm, re.IGNORECASE)
                normalized_patterns.append(compiled_norm)
            except re.error:
                logger.warning(f"Could not compile normalized pattern: {pattern_str}")
    
    return original_patterns, normalized_patterns

class LogAnalyzer:
    """Analisador de logs para OpenEdge/PASOE/AppServer com melhorias.
    
    OTIMIZAÇÕES DE PERFORMANCE APLICADAS:
    - Cache de padrões compilados (elimina recompilação)
    - Cache de resultados de busca (elimina buscas repetidas)
    - Sets para lookup O(1) ao invés de listas O(n)
    - Early exit em loops de busca
    """
    
    def __init__(self):
        # Padrões de erro padrão - expandidos e melhorados
        self.default_patterns = [
            # Genéricos
            r"ERROR", r"Exception", r"FAILED", r"SEVERE", r"CRITICAL", r"FATAL",
            r"WARNING", r"WARN", r"ALERT",
            
            # Progress/OpenEdge - somente padrões de ERRO, não genéricos
            r"STOP condition", r"System Error", r"Database disconnected",
            
            # PASOE
            r"Unable to start PASOE instance", r"Connection refused", r"Session crash",
            r"AppServer request failure", r"Broker is not available", r"No license for PASOE",
            r"PASOE agent", r"Transport failure", r"Session timeout",
            
            # AppServer
            r"AppServer process died", r"Broker disconnected", r"Client unable to connect",
            r"Socket connection reset", r"No servers available", r"Error 1793",
            r"Broker shutdown", r"Connection pool", r"Session limit",
            
            # HTTP/HTML
            r"HTTP 500", r"HTTP 404", r"HTTP 403", r"HTTP 502", r"HTTP 503", r"HTTP 504",
            r"Bad Gateway", r"Service Unavailable", r"Gateway Timeout", r"Internal Server Error",
            
            # Sistema/Rede
            r"OutOfMemoryError", r"StackOverflow", r"Timeout", r"Connection timeout",
            r"Network unreachable", r"Permission denied", r"Access denied",
            
            # Database
            r"Lock timeout", r"Deadlock", r"Transaction rolled back", r"Index corruption",
            r"Table full", r"Disk full", r"Cannot connect to database"
        ]
        
        # Padrões específicos do Datasul
        self.datasul_patterns = [
            # Identificadores gerais do Datasul
            r"Message", r"Log:Manager", r"Procedure:", r"###", r"\*\*\*",
            
            # Erros específicos do Datasul por número - escapados corretamente
            r"4GL STOP condition \(8026/7241\)", r"Erro 1793", r"Erro 30930", r"Erro 31330", 
            r"Erro 31331", r"Erro 500", r"errno 0/1432", r"Erro 402", r"Erro 34\.914",
            r"Erro 32\.318", r"Erro 19\.638", r"Erro 52\.200", r"Erro 36\.370",
            r"Rejeição 232",
            
            # PASOE específico
            r"Unable to start PASOE instance", r"PASOE.*not responding",
            r"WebHandler.*error", r"ABLWebApp.*exception", r"msagent.*died",
            r"SEVERE:.*catalina", r"tomcat.*error", r"WebSocket.*closed",
            r"transportIdx.*failed", r"oeablSecurity.*denied",
            
            # AppServer específico  
            r"AppServer process died", r"Broker is not available", 
            r"Agent.*disconnected", r"nameserver.*unavailable",
            r"_mprosrv.*terminated", r"srv.*stopped",
            r"broker.*shutdown", r"No agents available",
            
            # Erros por descrição - padrões simplificados para evitar problemas
            r"Connection refused", 
            r"HTTP 500 Internal Server Error",
            r"No license for PASOE",
            r"Unidade Negócio não cadastrada", r"Estabelecimento não tem acesso",
            r"Usuário super não tem acesso", r"Could not connect to server for database",
            r"Internal server error", r"NoSuchMethodError",
            r"Mensagens de erro ao programar", r"Insufficient access privilege",
            r"Component-handle.*inválido", r"Documento possui movimento contabilizado",
            r"Serviço não cadastrado", r"Quantidades incorretas", 
            r"Conta de Devolução não informada", r"CST de PIS/COFINS não informado",
            r"Conexão com WebService", r"IE do destinatário não informada",
            r"Erro de login ao inicializar JOB", r"Senhas passaram a ser case-sensitive",
            r"Ocorreu um erro ao localizar o broker"
        ]
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Lista de padrões personalizados adicionados em tempo real
        self.custom_patterns = []
        
        # Lista de padrões personalizados com dados completos (soluções, etc)
        self.custom_patterns_data = []
        
        # Lista de padrões que NÃO são erros (falsos positivos)
        self.non_error_patterns = []
        
        # NOVO: Padrões Progress que são ruído/heartbeat (não são erros)
        self.progress_noise_patterns = [
            r"Setting attention flag for database",
            r"Client notify thread: time to check for notifications",
            r"Checking notification for database",
            r"Cannot check notification inside a transaction for database"
        ]
        
        # Padrões compilados para busca otimizada (original e normalizado)
        self.compiled_custom_patterns_original = []
        self.compiled_custom_patterns_normalized = []
        self.compiled_non_error_patterns_original = []
        self.compiled_non_error_patterns_normalized = []
        self.compiled_progress_noise_patterns = []  # NOVO
        
        # Padrões para pontos de atenção
        self.attention_patterns = [
            r"UPC", r"tw-", r"\(Procedure", r"LOG:MANAGER", r"CRC", r"ESPEC", r"td-", r"-00u"
        ]
        
        # Carregadores de padrões do MongoDB (serão inicializados no servidor)
        self.datasul_loader = None
        self.logix_loader = None
        self.totvs_loader = None  # NOVO: Loader para erros TOTVS/Datasul específicos
        
        # Parser estruturado para múltiplos formatos de log
        self.structured_parser = StructuredLogParser()
        
        # ========================================
        # OTIMIZAÇÕES DE PERFORMANCE
        # ========================================
        
        # Cache de padrões compilados (evita recompilação)
        self._compiled_regex_cache = {}
        
        # Cache de resultados de busca por linha (evita buscas repetidas)
        self._line_match_cache = {}
        
        # Sets para lookup O(1) ao invés de listas O(n)
        self._custom_patterns_set = set()
        self._non_error_patterns_set = set()
        
        # Cache de padrões Datasul e Logix para classificação rápida
        self._datasul_patterns_cache = []
        self._logix_patterns_cache = []
        
        # Inicializar padrões compilados
        self.recompile_patterns()
    
    async def initialize_datasul_loader(self, db):
        """Inicializa o carregador híbrido de padrões Datasul"""
        try:
            self.datasul_loader = DatasulHybridLoader()
            success = await self.datasul_loader.initialize(db)
            if success:
                logger.info("Datasul hybrid loader initialized successfully")
                return True

            logger.warning("Failed to initialize Datasul loader")
            return False
        except Exception as e:
            logger.error(f"Error initializing Datasul loader: {e}")
            return False
    
    async def initialize_logix_loader(self, db):
        """Inicializa o carregador de padrões LOGIX"""
        try:
            self.logix_loader = LogixPatternsLoader(db if db is not None else None)
            if db is not None:
                await self.logix_loader.load_from_mongodb()
            logger.info("LOGIX patterns loader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LOGIX loader: {e}")
            # Continuar com LOGIX patterns do arquivo JSON
            self.logix_loader = LogixPatternsLoader(None)
            return False

        return True
    
    async def initialize_totvs_loader(self, db):
        """Inicializa o carregador de padrões de erro TOTVS/Datasul específicos"""
        try:
            self.totvs_loader = TotvsErrorsLoader(db if db is not None else None)
            if db is not None:
                await self.totvs_loader.load_from_mongodb()
            logger.info(f"TOTVS errors loader initialized with {len(self.totvs_loader.patterns)} patterns")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TOTVS errors loader: {e}")
            # Continuar com patterns do arquivo JSON
            self.totvs_loader = TotvsErrorsLoader(None)
            return False

    def load_external_patterns(self, file_content: str) -> List[str]:
        """Carrega padrões extras de conteúdo de arquivo."""
        try:
            patterns = [line.strip() for line in file_content.split('\n') if line.strip()]
            logger.info(f"Loaded {len(patterns)} external patterns")
            return patterns
        except Exception as e:
            logger.error(f"Error loading external patterns: {e}")
            return []

    def recompile_patterns(self):
        """Recompila os padrões personalizados para busca parcial e insensível a acentos.
        
        OTIMIZAÇÃO: Também cria sets para lookup O(1).
        """
        # Recompilar padrões personalizados
        self.compiled_custom_patterns_original, self.compiled_custom_patterns_normalized = compile_custom_patterns(self.custom_patterns)
        
        # Recompilar padrões de não-erro
        self.compiled_non_error_patterns_original, self.compiled_non_error_patterns_normalized = compile_custom_patterns(self.non_error_patterns)
        
        # NOVO: Compilar padrões de ruído Progress
        self.compiled_progress_noise_patterns = []
        for pattern in self.progress_noise_patterns:
            try:
                self.compiled_progress_noise_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                logger.warning(f"Could not compile Progress noise pattern: {pattern}")
        
        # OTIMIZAÇÃO: Criar sets para lookup rápido O(1)
        self._custom_patterns_set = set(self.custom_patterns)
        self._non_error_patterns_set = set(self.non_error_patterns)
        
        # OTIMIZAÇÃO: Limpar cache quando padrões mudam
        self._line_match_cache.clear()
        self._compiled_regex_cache.clear()
        
        logger.info(f"Recompiled {len(self.compiled_custom_patterns_original)} custom patterns, {len(self.compiled_non_error_patterns_original)} non-error patterns, and {len(self.compiled_progress_noise_patterns)} Progress noise patterns")

    def extract_progress_timestamp(self, line: str) -> Optional[datetime]:
        """Extrai e parseia timestamp Progress específico: [DD/MM/YY@HH:MM:SS.mmm-TZTZ]
        
        Returns:
            datetime object ou None se não encontrado
        """
        # Pattern Progress: [25/11/24@10:22:09.922-0300]
        match = PROGRESS_TIMESTAMP_RE.search(line)
        
        if match:
            day, month, year, hour, minute, second, millisecond, timezone = match.groups()
            
            # Converter ano de 2 dígitos para 4 (assumir 20XX)
            full_year = 2000 + int(year)
            
            try:
                # Criar datetime (ignorando timezone por enquanto para simplicidade)
                dt = datetime(
                    year=full_year,
                    month=int(month),
                    day=int(day),
                    hour=int(hour),
                    minute=int(minute),
                    second=int(second),
                    microsecond=int(millisecond) * 1000  # ms para microsegundos
                )
                return dt
            except ValueError:
                return None
        
        return None
    
    def extract_timestamp(self, line: str) -> str:
        """Extrai timestamp da linha com múltiplos formatos."""
        for pattern in EXTRACT_TIMESTAMP_PATTERNS:
            match = pattern.search(line)
            if match:
                return match.group(1)
        return "N/A"

    def extract_log_message(self, line: str) -> str:
        """Extrai apenas a mensagem relevante do log, mantendo APENAS o nível."""
        if not line or not line.strip():
            return line
        
        # Padrão específico para Progress/OpenEdge que mantém o nível
        # [25/09/25@10:45:34.525-0300] P-033484 T-015236 1 mensagem...
        match = PROGRESS_LOG_MESSAGE_RE.match(line)
        if match:
            level = match.group(1)  # Captura o nível (ex: 3)
            message = line[match.end():].strip()  # Mensagem após metadados
            return f"{level} {message}" if message else line
        
        # Outros padrões de metadados (sem nível para manter)
        for pattern in OTHER_LOG_METADATA_PATTERNS:
            match = pattern.match(line)
            if match:
                # Retorna apenas a parte após os metadados
                message = line[match.end():].strip()
                return message if message else line
        
        # Se não encontrar padrão de metadados, retorna a linha original
        return line.strip()

    def classify_error(self, line: str, external_patterns: List[str]) -> str:
        """Classifica o tipo de erro com base na linha."""
        # Extrair apenas a mensagem relevante do log
        message = self.extract_log_message(line)
        line_lower = message.lower()
        
        # Verificar padrões Datasul primeiro (prioridade alta)
        if self._is_datasul_error(message):
            return "Datasul"
        
        # Verificar padrões personalizados com busca parcial e insensível a acentos
        if self._check_custom_patterns(message):
            return "Personalizado"
        
        # Ordem de prioridade na classificação
        if re.search(r"pasoe", line_lower):
            return "PASOE"
        elif re.search(r"appserver|broker|1793", line_lower):
            return "AppServer"
        elif re.search(r"http|gateway|service|bad request|unauthorized", line_lower):
            return "HTTP/Web"
        elif re.search(r"progress|openedge|4gl|database", line_lower):
            return "Progress/OpenEdge"
        elif re.search(r"outofmemory|stackoverflow|timeout|connection", line_lower):
            return "Sistema/Rede"
        elif re.search(r"lock|deadlock|transaction|index|table|disk", line_lower):
            return "Database"
        elif any(re.search(p.lower(), line_lower) for p in external_patterns):
            return "LOG-DEV"
        elif re.search(r"warning|warn", line_lower):
            return "Warning"
        elif re.search(r"error|exception|failed|severe|critical|fatal", line_lower):
            return "Error Crítico"
        else:
            return "Outros"
    
    def _classify_error_optimized(self, line: str, external_patterns: List[str], is_datasul: bool = False, is_logix: bool = False) -> str:
        """Classifica o tipo de erro com base na linha - VERSÃO OTIMIZADA.
        
        OTIMIZAÇÃO: Recebe is_datasul e is_logix pré-calculados para evitar busca repetida.
        """
        # Extrair apenas a mensagem relevante do log
        message = self.extract_log_message(line)
        line_lower = message.lower()
        
        # Verificar padrões LOGIX primeiro (prioridade alta)
        # OTIMIZAÇÃO: Usa resultado pré-calculado
        if is_logix:
            return "LOGIX"
        
        # Verificar padrões Datasul (prioridade alta)
        # OTIMIZAÇÃO: Usa resultado pré-calculado
        if is_datasul:
            return "Datasul"
        
        # Verificar padrões personalizados com busca parcial e insensível a acentos
        # OTIMIZAÇÃO: Esta função já usa cache interno
        if self._check_custom_patterns(message):
            return "Personalizado"

        if self._looks_like_protheus_advpl(message):
            return "Protheus/ADVPL"
        
        # Ordem de prioridade na classificação
        if re.search(r"pasoe", line_lower):
            return "PASOE"
        elif re.search(r"appserver|broker|1793", line_lower):
            return "AppServer"
        elif re.search(r"http|gateway|service|bad request|unauthorized", line_lower):
            return "HTTP/Web"
        elif re.search(r"progress|openedge|4gl|database", line_lower):
            return "Progress/OpenEdge"
        elif re.search(r"outofmemory|stackoverflow|timeout|connection", line_lower):
            return "Sistema/Rede"
        elif re.search(r"lock|deadlock|transaction|index|table|disk", line_lower):
            return "Database"
        elif any(re.search(p.lower(), line_lower) for p in external_patterns):
            return "LOG-DEV"
        elif re.search(r"warning|warn", line_lower):
            return "Warning"
        elif re.search(r"error|exception|failed|severe|critical|fatal", line_lower):
            return "Error Crítico"
        else:
            return "Outros"

    def _looks_like_protheus_advpl(self, message: str) -> bool:
        """Identifica mensagens típicas de runtime e infraestrutura do Protheus/ADVPL."""
        message_lower = (message or '').lower()
        return any(
            indicator in message_lower
            for indicator in (
                'thread error',
                'called from',
                'totvs environment',
                'starting program siga',
                'starting program mdiexecute',
                'variable does not exist',
                'cannot find method',
                'invalid readmsint',
                'failed to read status of inifile',
                'fail to open:',
                'open empty rpo',
                'multiport - error',
                'totvs application server is running',
                'bpc2112',
                'apsdu',
                'advpl'
            )
        )
    
    def _quick_error_type_detection(self, message: str) -> str:
        """
        OTIMIZAÇÃO DE PERFORMANCE: Detecta rapidamente o tipo de erro antes de buscar padrões específicos.
        Evita buscar em todos os padrões desnecessariamente.
        """
        message_lower = message.lower()
        
        # 1. Verificação rápida por palavras-chave principais (mais comuns primeiro)
        datasul_keywords = ['datasul', 'progress', 'procedure:', 'log:manager', 'cfop', 'icms', 'nfe', 'cte', 'mdfe']
        protheus_keywords = ['thread error', 'called from', 'variable does not exist', 'cannot find method', 'invalid readmsint', 'totvs environment', 'starting program siga', 'failed to read status of inifile', 'open empty rpo', 'multiport - error', 'bpc2112', 'advpl']
        java_keywords = ['java.', 'exception', 'stacktrace', 'tomcat', 'hibernate']
        db_keywords = ['database', 'connection', 'sql', 'oracle', 'postgres', 'mysql']
        network_keywords = ['timeout', 'connection reset', 'broken pipe', 'network']

        if any(keyword in message_lower for keyword in protheus_keywords):
            return 'protheus_candidate'
        
        # Verificar Datasul primeiro (mais específico)
        if any(keyword in message_lower for keyword in datasul_keywords):
            return 'datasul_candidate'
        
        # Java/Tomcat errors
        if any(keyword in message_lower for keyword in java_keywords):
            return 'java_candidate'
            
        # Database errors
        if any(keyword in message_lower for keyword in db_keywords):
            return 'database_candidate'
            
        # Network errors  
        if any(keyword in message_lower for keyword in network_keywords):
            return 'network_candidate'
            
        # 2. Verificação por códigos de erro (padrões numéricos comuns)
        if re.search(r'\(\d{3,4}\)', message):  # Progress error codes
            return 'progress_candidate'
            
        if re.search(r'[A-Z]{2,3}\d{4}\s*-', message):  # Datasul program codes
            return 'datasul_program_candidate'
        
        # 3. Verificação por severidade
        if re.search(r'\b(critical|fatal|severe)\b', message_lower):
            return 'critical_candidate'
        elif re.search(r'\b(error|fail|exception)\b', message_lower):
            return 'error_candidate'
        elif re.search(r'\b(warn|warning)\b', message_lower):
            return 'warning_candidate'
            
        return 'generic_candidate'

    def _is_datasul_error(self, line: str) -> bool:
        """
        Verifica se a linha contém padrões específicos do Datasul.
        OTIMIZADO: Só verifica se foi identificado como candidato Datasul + usa cache.
        Também verifica os padrões TOTVS específicos.
        """
        # OTIMIZAÇÃO: Verificar cache primeiro
        cache_key = ('datasul', line)
        if cache_key in self._line_match_cache:
            return self._line_match_cache[cache_key]
        
        result = False
        
        # NOVO: Verificar padrões TOTVS específicos primeiro (mais precisos)
        if self.totvs_loader:
            totvs_match = self._is_totvs_error(line)
            if totvs_match:
                result = True
        
        # Se não encontrou nos TOTVS, verificar padrões Datasul
        if not result and self.datasul_loader:
            error_type = self._quick_error_type_detection(line)
            
            # Só buscar nos padrões Datasul se for candidato
            if error_type in ['datasul_candidate', 'datasul_program_candidate', 'progress_candidate']:
                # Verificar padrões originais
                for pattern in self.datasul_patterns:
                    try:
                        if re.search(pattern, line, re.IGNORECASE):
                            result = True
                            break  # OTIMIZAÇÃO: Early exit
                    except re.error:
                        # Se regex inválido, fazer busca literal
                        if pattern.lower() in line.lower():
                            result = True
                            break  # OTIMIZAÇÃO: Early exit
                
                # Verificar padrões novos do carregador (se disponível)
                if not result:
                    for pattern in self._get_datasul_patterns_cached():
                        try:
                            if re.search(pattern, line, re.IGNORECASE):
                                result = True
                                break  # OTIMIZAÇÃO: Early exit
                        except re.error:
                            continue
        
        # OTIMIZAÇÃO: Guardar no cache
        self._line_match_cache[cache_key] = result
        
        return result
    
    def _is_logix_error(self, line: str) -> bool:
        """
        Verifica se a linha contém padrões específicos do LOGIX.
        Similar ao _is_datasul_error mas para LOGIX.
        """
        if not self.logix_loader:
            return False
        
        # OTIMIZAÇÃO: Verificar cache primeiro
        cache_key = ('logix', line)
        if cache_key in self._line_match_cache:
            return self._line_match_cache[cache_key]
        
        result = False
        
        # Verificar padrões LOGIX
        for pattern_obj in self.logix_loader.get_all_patterns():
            try:
                pattern = pattern_obj.get('pattern', '')
                if re.search(pattern, line, re.IGNORECASE):
                    result = True
                    break  # OTIMIZAÇÃO: Early exit
            except re.error:
                continue
        
        # OTIMIZAÇÃO: Guardar no cache
        self._line_match_cache[cache_key] = result
        
        return result
    
    def _is_totvs_error(self, line: str) -> Optional[Dict]:
        """
        Verifica se a linha contém padrões de erro TOTVS/Datasul específicos.
        Retorna as informações do erro se encontrado, None caso contrário.
        
        OTIMIZAÇÃO: Usa cache e detecção por código de erro.
        """
        if not self.totvs_loader:
            return None
        
        # OTIMIZAÇÃO: Verificar cache primeiro
        cache_key = ('totvs', line)
        if cache_key in self._line_match_cache:
            return self._line_match_cache[cache_key]
        
        result = self.totvs_loader.check_error_partial(line)
        
        # OTIMIZAÇÃO: Guardar no cache
        self._line_match_cache[cache_key] = result
        
        return result
    
    def _get_datasul_patterns_cached(self) -> list:
        """OTIMIZAÇÃO: Cache de padrões Datasul para evitar chamadas repetidas"""
        if not self._datasul_patterns_cache:
            self._datasul_patterns_cache = self.datasul_loader.get_patterns_for_classification()
        return self._datasul_patterns_cache
    
    def _is_non_error(self, line: str) -> bool:
        """Verifica se a linha é um padrão marcado como não-erro usando busca parcial e insensível a acentos.
        
        OTIMIZAÇÃO: Usa cache para evitar buscas repetidas na mesma linha.
        """
        if not line:
            return False
        
        # OTIMIZAÇÃO: Verificar cache primeiro
        cache_key = ('non_error', line)
        if cache_key in self._line_match_cache:
            return self._line_match_cache[cache_key]
        
        result = False
        
        # Testar padrões originais compilados
        for compiled_pattern in self.compiled_non_error_patterns_original:
            try:
                if compiled_pattern.search(line):
                    result = True
                    break  # OTIMIZAÇÃO: Early exit
            except:
                continue
        
        # Se não encontrou, testar padrões normalizados (sem acentos)
        if not result:
            normalized_line = normalize_text(line)
            for compiled_pattern in self.compiled_non_error_patterns_normalized:
                try:
                    if compiled_pattern.search(normalized_line):
                        result = True
                        break  # OTIMIZAÇÃO: Early exit
                except:
                    continue
        
        # OTIMIZAÇÃO: Guardar no cache
        self._line_match_cache[cache_key] = result
        
        return result
    
    def _is_progress_noise(self, line: str) -> bool:
        """Verifica se a linha é ruído Progress (heartbeat/conexão) que deve ser ignorado.
        
        IMPORTANTE: Só filtra se for APENAS ruído. Se a linha tiver ERROR, CRITICAL, etc,
        não filtra mesmo que contenha padrão de ruído.
        """
        # Se a linha contém indicadores de erro, NÃO é ruído
        error_indicators = [
            'ERROR', 'CRITICAL', 'FATAL', 'EXCEPTION', 'FAIL', 'ERRO',
            'WARNING', 'WARN', 'ALERT', 'Cannot', 'Unable', 'Failed',
            'Timeout', 'Denied', 'Refused', 'Lost connection', 'died'
        ]
        
        line_upper = line.upper()
        for indicator in error_indicators:
            if indicator.upper() in line_upper:
                return False  # Não é ruído, tem erro!
        
        # Agora verifica se é ruído puro
        for compiled_pattern in self.compiled_progress_noise_patterns:
            try:
                if compiled_pattern.search(line):
                    return True
            except:
                continue
        return False
    
    def _is_attention_point(self, line: str) -> bool:
        """Verifica se a linha contém pontos de atenção."""
        if not line:
            return False

        line_upper = line.upper()
        for token, _label in ATTENTION_TOKENS:
            if token in line_upper:
                return True
        return False

    def _get_attention_keywords(self, line: str) -> List[str]:
        if not line:
            return []

        line_upper = line.upper()
        return [label for token, label in ATTENTION_TOKENS if token in line_upper]
    
    def _check_custom_patterns(self, line: str) -> bool:
        """Verifica se a linha corresponde aos padrões personalizados usando busca parcial e insensível a acentos.
        
        OTIMIZAÇÃO: Usa cache para evitar buscas repetidas na mesma linha.
        """
        if not line:
            return False
        
        # OTIMIZAÇÃO: Verificar cache primeiro
        cache_key = ('custom', line)
        if cache_key in self._line_match_cache:
            return self._line_match_cache[cache_key]
        
        result = False
        
        # Testar padrões originais compilados
        for compiled_pattern in self.compiled_custom_patterns_original:
            try:
                if compiled_pattern.search(line):
                    result = True
                    break  # OTIMIZAÇÃO: Early exit
            except:
                continue
        
        # Se não encontrou, testar padrões normalizados (sem acentos)
        if not result:
            normalized_line = normalize_text(line)
            for compiled_pattern in self.compiled_custom_patterns_normalized:
                try:
                    if compiled_pattern.search(normalized_line):
                        result = True
                        break  # OTIMIZAÇÃO: Early exit
                except:
                    continue
        
        # OTIMIZAÇÃO: Guardar no cache
        self._line_match_cache[cache_key] = result
        
        return result
    
    def load_non_error_patterns(self, non_error_patterns: List[str]):
        """Carrega padrões de não-erro da base de dados."""
        self.non_error_patterns = non_error_patterns
        self.recompile_patterns()  # Recompilar padrões para busca parcial
        logger.info(f"Loaded {len(non_error_patterns)} non-error patterns")

    def _extract_analysis_timestamp(self, line: str):
        """Extrai o timestamp mais confiável disponível para análises de performance."""
        timestamp_obj = self.extract_progress_timestamp(line)
        if timestamp_obj:
            return timestamp_obj

        timestamp = self.extract_timestamp(line)
        if timestamp == "N/A":
            return None

        try:
            return self._parse_timestamp(timestamp)
        except Exception:
            return None

    def _split_program_reference(self, raw_reference: str) -> Tuple[str, str]:
        """Separa uma referência textual em programa e método."""
        reference = (raw_reference or '').strip().strip('()[]{}"\'')
        if not reference:
            return ('UNKNOWN', 'MAIN')

        reference = reference.replace('\\', '/')
        lowered = reference.lower()
        file_extensions = ('.p', '.r', '.w', '.cls', '.4gl', '.java', '.py', '.js', '.ts')

        if '::' in reference:
            program, method = reference.split('::', 1)
        elif '/' in reference and not lowered.endswith(file_extensions):
            program, method = reference.rsplit('/', 1)
        elif '.' in reference and not lowered.endswith(file_extensions):
            program, method = reference.rsplit('.', 1)
        else:
            program, method = reference, 'MAIN'

        if '/' in program:
            program = program.split('/')[-1]

        program = program.strip() or 'UNKNOWN'
        method = method.strip() or 'MAIN'
        return (program.upper(), method.upper())

    def _extract_caller_reference(self, line: str) -> Optional[Tuple[str, str]]:
        """Tenta identificar o caller associado a uma linha de log."""
        caller_patterns = [
            r"called from[:\s]+(?P<caller>[A-Za-z0-9_$.:/\\\-]+(?:::[A-Za-z0-9_$\-]+)?)",
            r"caller[:=\s]+(?P<caller>[A-Za-z0-9_$.:/\\\-]+(?:::[A-Za-z0-9_$\-]+)?)",
            r"origin[:=\s]+(?P<caller>[A-Za-z0-9_$.:/\\\-]+(?:::[A-Za-z0-9_$\-]+)?)",
            r"from program[:=\s]+(?P<caller>[A-Za-z0-9_$.:/\\\-]+(?:::[A-Za-z0-9_$\-]+)?)"
        ]

        for pattern in caller_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return self._split_program_reference(match.group('caller'))

        return None

    def _convert_duration_to_ms(self, value: float, unit: str) -> float:
        """Converte segundos/milisegundos para ms."""
        unit_lower = (unit or 'ms').lower()
        if unit_lower in ['s', 'second', 'seconds']:
            return value * 1000
        return value

    def _get_log_type_performance_patterns(self, log_type: str) -> Dict[str, List[str]]:
        """Retorna padrões específicos por tipo de log para reforçar a análise de performance."""
        patterns: Dict[str, List[str]] = {
            'timed_programs': [],
            'calls': []
        }

        if log_type in ('Progress/OpenEdge', 'PASOE', 'AppServer', 'Datasul', 'LOGIX', 'TOTVS'):
            patterns['timed_programs'].extend([
                r"(?:Procedure|Program|Execute|Running|Call|Method|Function)[\s:=]+([A-Za-z0-9_$.:/\\\-]+(?:::[A-Za-z0-9_$\-]+)?)\s+.*?(?:took|duration|time|elapsed|completed in|executed in)[\s:=]*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)",
                r"([A-Za-z0-9_$.:/\\\-]+\.(?:p|r|w|cls|4gl))\s+.*?(?:took|duration|time|elapsed|completed in|executed in)[\s:=]*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)",
                r"([A-Za-z0-9_$.:/\\\-]+(?:::[A-Za-z0-9_$\-]+)?)\s*[-:=]\s*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)"
            ])
            patterns['calls'].extend([
                r"(?:Procedure|Program|Execute|Running|Call|Method|Function)[\s:=]+([A-Za-z0-9_$.:/\\\-]+(?:::[A-Za-z0-9_$\-]+)?)",
                r"LOG:MANAGER.*?([A-Za-z0-9_$.:/\\\-]+\.(?:p|r|w|cls|4gl))",
                r"\(Procedure[\s:]+([^\)]+)\)"
            ])

        if log_type == 'HTTP/Web':
            patterns['timed_programs'].extend([
                r"((?:GET|POST|PUT|DELETE|PATCH)\s+[A-Za-z0-9_./{}\-]+).*?(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)",
                r"([A-Za-z0-9_./{}\-]+)\s+.*?status\s+\d{3}.*?(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)"
            ])
            patterns['calls'].append(r"((?:GET|POST|PUT|DELETE|PATCH)\s+[A-Za-z0-9_./{}\-]+)")

        if log_type in ('Sistema/Rede', 'Database'):
            patterns['timed_programs'].extend([
                r"((?:QUERY|SELECT|INSERT|UPDATE|DELETE|CONNECT|SOCKET|REQUEST)\s+[A-Za-z0-9_./{}\-]+).*?(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)",
                r"([A-Za-z0-9_$.:/\\\-]+)\s+.*?(?:timeout|latency|elapsed|duration)[\s:=]*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)"
            ])
            patterns['calls'].extend([
                r"((?:QUERY|SELECT|INSERT|UPDATE|DELETE)\s+[A-Za-z0-9_./{}\-]+)",
                r"((?:CONNECT|SOCKET|REQUEST)\s+[A-Za-z0-9_./{}\-]+)"
            ])

        return patterns
    
    def _detect_informational_lines(self, lines: List[str]) -> List[dict]:
        """Detecta linhas informativas que podem ser confundidas com erros."""
        informational_patterns = [
            r"INFO", r"DEBUG", r"TRACE", r"SUCCESS", r"SUCCESSFUL", r"COMPLETE", r"COMPLETED",
            r"START", r"STARTING", r"STARTED", r"END", r"ENDING", r"FINISHED", 
            r"CONNECT", r"CONNECTED", r"LOGIN", r"LOGOUT", r"LOAD", r"LOADED", r"LOADING"
        ]
        
        informational_lines = []
        
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue
                
            for pattern in informational_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    timestamp = self.extract_timestamp(line)
                    informational_lines.append({
                        "line": line_num,
                        "message": line,
                        "timestamp": timestamp,
                        "detected_pattern": pattern,
                        "suggestion": "Esta linha parece ser informativa, não um erro"
                    })
                    break
        
        return informational_lines[:50]  # Limitar a 50 sugestões


    def _prefilter_relevant_lines(self, lines: List[str], log_type: str) -> List[str]:
        """Pre-filtra linhas para análises custosas (performance, callers, new errors).
        Remove entry types informativos de logs Progress (4GL, UB, AS)."""
        # Entry types informativos para Progress client logs (4GL)
        _4gl_informational = frozenset({
            '4GLTRACE', 'FILEID', 'Properties', 'DYNOBJECTS',
            'PROEVENTS', 'DBCONNECTS', '----------', '--'
        })
        # Entry types informativos para Broker logs (UB)
        _ub_informational = frozenset({
            'Basic', 'Plumbing', 'Statistics', 'Info'
        })
        # Entry types informativos para AppServer logs (AS)
        _as_informational = frozenset({
            '4GLTrace', 'FILEID', 'ASPlumbing', 'ASDefault', 'AS',
            'DB.Connects', 'Properties', '--', '----------', 'CONN'
        })
        
        relevant = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Skip continuation lines (don't start with [)
            if not stripped.startswith('['):
                continue
            # Quick check for Progress log format: [timestamp] P-xxx T-xxx ...
            # Extract entry type section
            if ' 4GL ' in stripped:
                idx = stripped.find(' 4GL ')
                rest = stripped[idx + 5:].lstrip()
                etype = rest.split()[0] if rest else ''
                if etype in _4gl_informational:
                    continue
            elif ' UB ' in stripped:
                idx = stripped.find(' UB ')
                rest = stripped[idx + 4:].lstrip()
                etype = rest.split()[0] if rest else ''
                if etype in _ub_informational:
                    continue
            elif ' AS ' in stripped:
                idx = stripped.find(' AS ')
                rest = stripped[idx + 4:].lstrip()
                etype = rest.split()[0] if rest else ''
                if etype in _as_informational:
                    continue
            relevant.append(stripped)
        return relevant


    def _analyze_callers_and_programs(self, lines: List[str], log_type: str = 'Other') -> Dict[str, Any]:
        """Analisa o log para extrair programas/métodos mais chamados, seus tempos totais
        calculados a partir dos timestamps e quais programas/métodos chamaram eles.

        Retorna estrutura:
        {
          'top_programs': [
               { 'program': 'PROG1', 'method': 'meth', 'calls': N, 'total_time_ms': T, 'callers': [{'program':p,'method':m,'count':c}, ...] },
               ... up to 3
          ]
        }
        """
        from collections import defaultdict, Counter

        patterns = self._get_log_type_performance_patterns(log_type)
        timed_patterns = patterns['timed_programs']
        call_patterns = patterns['calls']

        calls_counter = Counter()
        callers_map = defaultdict(Counter)
        times_map = defaultdict(lambda: {'first': None, 'last': None, 'explicit_time_ms': 0.0})

        for line in lines:
            if not line:
                continue

            timestamp_obj = self._extract_analysis_timestamp(line)
            caller_reference = self._extract_caller_reference(line)
            references_seen = set()

            for pattern in timed_patterns:
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    try:
                        raw_reference = match.group(1)
                        duration_value = float(match.group(2))
                        duration_ms = self._convert_duration_to_ms(duration_value, match.group(3))
                    except (IndexError, ValueError):
                        continue

                    pm = self._split_program_reference(raw_reference)
                    references_seen.add(pm)
                    calls_counter[pm] += 1
                    times_map[pm]['explicit_time_ms'] += duration_ms

                    if timestamp_obj:
                        if times_map[pm]['first'] is None or timestamp_obj < times_map[pm]['first']:
                            times_map[pm]['first'] = timestamp_obj
                        if times_map[pm]['last'] is None or timestamp_obj > times_map[pm]['last']:
                            times_map[pm]['last'] = timestamp_obj

                    if caller_reference:
                        callers_map[pm][caller_reference] += 1

            for pattern in call_patterns:
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    try:
                        pm = self._split_program_reference(match.group(1))
                    except IndexError:
                        continue

                    if pm in references_seen:
                        continue

                    calls_counter[pm] += 1
                    if timestamp_obj:
                        if times_map[pm]['first'] is None or timestamp_obj < times_map[pm]['first']:
                            times_map[pm]['first'] = timestamp_obj
                        if times_map[pm]['last'] is None or timestamp_obj > times_map[pm]['last']:
                            times_map[pm]['last'] = timestamp_obj

                    if caller_reference:
                        callers_map[pm][caller_reference] += 1

        ranked_programs = []
        total_tracked_time_ms = 0.0

        for pm, cnt in calls_counter.items():
            tinfo = times_map.get(pm, {})
            explicit_time_ms = float(tinfo.get('explicit_time_ms') or 0.0)
            span_time_ms = 0.0
            if tinfo.get('first') and tinfo.get('last'):
                span_time_ms = max((tinfo['last'] - tinfo['first']).total_seconds() * 1000.0, 0.0)

            total_ms = explicit_time_ms if explicit_time_ms > 0 else span_time_ms
            avg_time_ms = round(total_ms / cnt, 2) if cnt > 0 and total_ms > 0 else 0.0
            total_tracked_time_ms += total_ms

            callers_list = []
            for (cp, cm), ccount in callers_map.get(pm, Counter()).most_common(10):
                callers_list.append({'program': cp, 'method': cm, 'count': ccount})

            ranked_programs.append({
                'program': pm[0],
                'method': pm[1],
                'calls': cnt,
                'total_time_ms': round(total_ms, 2),
                'avg_time_ms': avg_time_ms,
                'callers': callers_list,
                'callers_summary': ', '.join([f"{caller['program']}::{caller['method']} ({caller['count']})" for caller in callers_list[:3]]) or '-',
                'log_type': log_type
            })

        ranked_programs.sort(key=lambda item: (item['total_time_ms'], item['calls']), reverse=True)

        top_programs = []
        for item in ranked_programs[:10]:
            total_time_ms = float(item['total_time_ms'])
            item['percent_of_total_time'] = round((total_time_ms / total_tracked_time_ms) * 100, 2) if total_tracked_time_ms > 0 else 0.0
            top_programs.append(item)

        return {
            'top_programs': top_programs,
            'total_tracked_time_ms': round(total_tracked_time_ms, 2),
            'total_ranked_programs': len(ranked_programs),
            'log_type': log_type
        }
    
    def load_custom_patterns(self, custom_patterns: List[str]):
        """Carrega padrões customizados da base de dados.""" 
        self.custom_patterns = custom_patterns
        self.recompile_patterns()  # Recompilar padrões para busca parcial
        logger.info(f"Loaded {len(custom_patterns)} custom patterns")
        
    def load_custom_patterns_with_solutions(self, patterns_data: List[dict]):
        """Carrega padrões customizados com soluções e informações parciais."""
        self.custom_patterns_data = patterns_data
        # Ainda mantém lista simples para compatibilidade
        self.custom_patterns = [p.get("pattern", "") for p in patterns_data]
        self.recompile_patterns()  # Recompilar padrões para busca parcial
        logger.info(f"Loaded {len(patterns_data)} custom patterns with solutions")

    def analyze_performance(self, lines: List[str], log_type: str = 'Other') -> Dict[str, Any]:
        """Analisa métricas de performance do log."""
        
        performance_metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "database_queries": [],
            "slow_operations": [],
            "slow_programs": [],  # Programas/procedures que demoram > 2 segundos
            "connection_stats": {
                "total_connections": 0,
                "failed_connections": 0,
                "timeout_connections": 0
            },
            "throughput": {
                "requests_per_minute": {},
                "peak_periods": []
            },
            # NOVO: Análise detalhada de chamadas
            "call_analysis": {
                "calls_by_hour": {},  # Chamadas por hora
                "calls_by_minute": {},  # Chamadas por minuto
                "method_call_count": {},  # Contagem de chamadas por método/procedure
                "top_methods": [],  # Top métodos mais chamados
                "total_calls": 0
            },
            "program_analysis": {
                "total_tracked_program_time_ms": 0,
                "total_timed_entries": 0,
                "top_programs_by_time": []
            },
            "log_type": log_type,
            "analysis_scope": f"Heurísticas específicas para {log_type} + padrões genéricos",
            # NOVO: Alertas específicos
            "specific_alerts": {
                "upc_detected": False,
                "upc_count": 0,
                "upc_lines": [],
                "espec_detected": False,
                "espec_count": 0,
                "espec_lines": [],
                "procedure_in_errors": False,
                "procedure_error_count": 0,
                "procedure_error_lines": []
            }
        }
        
        # Padrões para detectar métricas de performance
        response_time_patterns = [
            r"response time[:\s]*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)",
            r"duration[:\s]*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)",
            r"took\s+(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)",
            r"elapsed[:\s]*(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)"
        ]
        
        log_type_patterns = self._get_log_type_performance_patterns(log_type)
        program_time_patterns = log_type_patterns['timed_programs']
        procedure_call_patterns = log_type_patterns['calls']
        
        memory_patterns = [
            r"memory[:\s]*(\d+\.?\d*)\s*(mb|gb|kb|bytes?)",
            r"heap[:\s]*(\d+\.?\d*)\s*(mb|gb|kb|bytes?)",
            r"ram[:\s]*(\d+\.?\d*)\s*(mb|gb|kb|bytes?)"
        ]
        
        cpu_patterns = [
            r"cpu[:\s]*(\d+\.?\d*)%?",
            r"processor[:\s]*(\d+\.?\d*)%?"
        ]
        
        slow_operation_keywords = [
            "slow", "timeout", "performance", "lag", "delay", "bottleneck",
            "waiting", "blocked", "deadlock", "queue"
        ]
        
        requests_by_minute = defaultdict(int)
        
        for line_num, line in enumerate(lines, start=1):
            line_lower = line.lower()
            
            # MELHORADO: Priorizar timestamp Progress (mais preciso)
            timestamp_obj = self._extract_analysis_timestamp(line)
            if timestamp_obj:
                # Usar datetime object direto
                minute_key = timestamp_obj.strftime("%H:%M")
                requests_by_minute[minute_key] += 1
                timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Fallback para outros formatos
                timestamp = self.extract_timestamp(line)
                if timestamp != "N/A":
                    try:
                        dt = self._parse_timestamp(timestamp)
                        if dt:
                            minute_key = dt.strftime("%H:%M")
                            requests_by_minute[minute_key] += 1
                    except:
                        pass
            
            # Análise de tempos de resposta
            for pattern in response_time_patterns:
                matches = re.finditer(pattern, line_lower)
                for match in matches:
                    try:
                        value = float(match.group(1))
                        unit = match.group(2).lower()
                        
                        # Converter para millisegundos
                        if unit in ['s', 'seconds', 'second']:
                            value *= 1000
                        elif unit in ['ms', 'milliseconds', 'millisecond']:
                            pass  # já em ms
                        
                        performance_metrics["response_times"].append({
                            "line": line_num,
                            "value": value,
                            "unit": "ms",
                            "timestamp": timestamp,
                            "context": line[:100] + "..." if len(line) > 100 else line
                        })
                    except (ValueError, IndexError):
                        continue
            
            # Análise de uso de memória
            for pattern in memory_patterns:
                matches = re.finditer(pattern, line_lower)
                for match in matches:
                    try:
                        value = float(match.group(1))
                        unit = match.group(2).lower()
                        
                        # Converter para MB
                        if unit in ['gb']:
                            value *= 1024
                        elif unit in ['kb']:
                            value /= 1024
                        elif unit in ['bytes', 'byte']:
                            value /= (1024 * 1024)
                        
                        performance_metrics["memory_usage"].append({
                            "line": line_num,
                            "value": value,
                            "unit": "MB",
                            "timestamp": timestamp,
                            "context": line[:100] + "..." if len(line) > 100 else line
                        })
                    except (ValueError, IndexError):
                        continue
            
            # Análise de CPU
            for pattern in cpu_patterns:
                matches = re.finditer(pattern, line_lower)
                for match in matches:
                    try:
                        value = float(match.group(1))
                        performance_metrics["cpu_usage"].append({
                            "line": line_num,
                            "value": value,
                            "unit": "%",
                            "timestamp": timestamp,
                            "context": line[:100] + "..." if len(line) > 100 else line
                        })
                    except (ValueError, IndexError):
                        continue
            
            # Detectar operações lentas
            for keyword in slow_operation_keywords:
                if keyword in line_lower:
                    performance_metrics["slow_operations"].append({
                        "line": line_num,
                        "keyword": keyword,
                        "timestamp": timestamp,
                        "message": line[:200] + "..." if len(line) > 200 else line
                    })
                    break
            
            # Análise de conexões
            if re.search(r"connect", line_lower):
                performance_metrics["connection_stats"]["total_connections"] += 1
                
                if re.search(r"failed|error|refused|denied", line_lower):
                    performance_metrics["connection_stats"]["failed_connections"] += 1
                
                if re.search(r"timeout", line_lower):
                    performance_metrics["connection_stats"]["timeout_connections"] += 1
            
            # Detectar queries de banco de dados
            if re.search(r"query|select|insert|update|delete|sql", line_lower):
                # Extrair tempo se disponível
                query_time = None
                for pattern in response_time_patterns:
                    match = re.search(pattern, line_lower)
                    if match:
                        try:
                            query_time = float(match.group(1))
                            unit = match.group(2).lower()
                            if unit in ['s', 'seconds']:
                                query_time *= 1000
                        except:
                            pass
                        break
                
                performance_metrics["database_queries"].append({
                    "line": line_num,
                    "timestamp": timestamp,
                    "query_time": query_time,
                    "message": line[:150] + "..." if len(line) > 150 else line
                })
            
            # NOVO: Detectar programas/procedures com tempo de execução
            for pattern in program_time_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    try:
                        # Grupos: (program_name, time_value, time_unit)
                        groups = match.groups()
                        if len(groups) >= 3:
                            program_name = groups[0].strip()
                            time_value = float(groups[1])
                            time_unit = groups[2].lower()
                            
                            # Converter para millisegundos
                            time_ms = time_value
                            if time_unit in ['s', 'seconds', 'second']:
                                time_ms = time_value * 1000
                            
                            performance_metrics["program_analysis"]["total_tracked_program_time_ms"] += round(time_ms, 2)
                            performance_metrics["program_analysis"]["total_timed_entries"] += 1
                            program_ref = self._split_program_reference(program_name)
                            top_program_key = f"{program_ref[0]}::{program_ref[1]}"
                            timed_programs = performance_metrics["program_analysis"].setdefault("_aggregated_programs", {})
                            current_program = timed_programs.get(top_program_key, {
                                "program": program_ref[0],
                                "method": program_ref[1],
                                "calls": 0,
                                "total_time_ms": 0.0,
                                "log_type": log_type
                            })
                            current_program["calls"] += 1
                            current_program["total_time_ms"] += round(time_ms, 2)
                            timed_programs[top_program_key] = current_program

                            # Se demora mais de 2 segundos (2000ms), adicionar à lista
                            if time_ms >= 2000:
                                performance_metrics["slow_programs"].append({
                                    "line": line_num,
                                    "program": program_name,
                                    "duration_ms": round(time_ms, 2),
                                    "duration_seconds": round(time_ms / 1000, 2),
                                    "timestamp": timestamp,
                                    "context": line[:200] + "..." if len(line) > 200 else line,
                                    "severity": "critical" if time_ms >= 5000 else ("high" if time_ms >= 3000 else "medium"),
                                    "log_type": log_type
                                })
                    except (ValueError, IndexError) as e:
                        continue
            
            # NOVO: Detectar chamadas de métodos/procedures (para contagem)
            for pattern in procedure_call_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    try:
                        method_name = match.group(1).strip()
                        # Limpar nome (remover paths, manter só o arquivo)
                        if '/' in method_name:
                            method_name = method_name.split('/')[-1]
                        
                        # Contar chamada
                        performance_metrics["call_analysis"]["method_call_count"][method_name] = \
                            performance_metrics["call_analysis"]["method_call_count"].get(method_name, 0) + 1
                        performance_metrics["call_analysis"]["total_calls"] += 1
                        
                        # Contar por hora se tiver timestamp
                        if timestamp_obj:
                            hour_key = timestamp_obj.strftime("%H:00")
                            performance_metrics["call_analysis"]["calls_by_hour"][hour_key] = \
                                performance_metrics["call_analysis"]["calls_by_hour"].get(hour_key, 0) + 1
                            
                            minute_key = timestamp_obj.strftime("%H:%M")
                            performance_metrics["call_analysis"]["calls_by_minute"][minute_key] = \
                                performance_metrics["call_analysis"]["calls_by_minute"].get(minute_key, 0) + 1
                    except (IndexError, AttributeError):
                        continue
            
            # NOVO: Detectar alertas específicos (UPC, ESPEC, (Procedure)
            line_upper = line.upper()
            
            # Detectar UPC
            if 'UPC' in line_upper:
                performance_metrics["specific_alerts"]["upc_detected"] = True
                performance_metrics["specific_alerts"]["upc_count"] += 1
                if len(performance_metrics["specific_alerts"]["upc_lines"]) < 10:  # Limitar a 10 exemplos
                    performance_metrics["specific_alerts"]["upc_lines"].append({
                        "line": line_num,
                        "timestamp": timestamp,
                        "context": line[:200] + "..." if len(line) > 200 else line
                    })
            
            # Detectar ESPEC
            if 'ESPEC' in line_upper:
                performance_metrics["specific_alerts"]["espec_detected"] = True
                performance_metrics["specific_alerts"]["espec_count"] += 1
                if len(performance_metrics["specific_alerts"]["espec_lines"]) < 10:
                    performance_metrics["specific_alerts"]["espec_lines"].append({
                        "line": line_num,
                        "timestamp": timestamp,
                        "context": line[:200] + "..." if len(line) > 200 else line
                    })
            
            # Detectar (Procedure nos erros
            if '(PROCEDURE' in line_upper and any(err in line_upper for err in ['ERROR', 'CRITICAL', 'FAIL', 'EXCEPTION']):
                performance_metrics["specific_alerts"]["procedure_in_errors"] = True
                performance_metrics["specific_alerts"]["procedure_error_count"] += 1
                if len(performance_metrics["specific_alerts"]["procedure_error_lines"]) < 10:
                    performance_metrics["specific_alerts"]["procedure_error_lines"].append({
                        "line": line_num,
                        "timestamp": timestamp,
                        "context": line[:200] + "..." if len(line) > 200 else line
                    })
        
        # Processar ranking de métodos mais chamados
        if performance_metrics["call_analysis"]["method_call_count"]:
            sorted_methods = sorted(
                performance_metrics["call_analysis"]["method_call_count"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            performance_metrics["call_analysis"]["top_methods"] = [
                {
                    "method": method,
                    "count": count,
                    "percent_of_total_calls": round((count / performance_metrics["call_analysis"]["total_calls"]) * 100, 2)
                    if performance_metrics["call_analysis"]["total_calls"] > 0 else 0.0
                }
                for method, count in sorted_methods[:20]  # Top 20
            ]
        
        # Remover duplicatas (mesmo programa na mesma linha)
        seen = set()
        unique_slow_programs = []
        for sp in performance_metrics["slow_programs"]:
            key = (sp["line"], sp["program"], sp["duration_ms"])
            if key not in seen:
                seen.add(key)
                unique_slow_programs.append(sp)
        
        performance_metrics["slow_programs"] = unique_slow_programs
        
        # Ordenar programas lentos por duração (mais lentos primeiro)
        performance_metrics["slow_programs"].sort(key=lambda x: x["duration_ms"], reverse=True)

        total_tracked_program_time_ms = float(performance_metrics["program_analysis"].get("total_tracked_program_time_ms", 0) or 0)
        if total_tracked_program_time_ms > 0:
            for item in performance_metrics["slow_programs"]:
                item["percent_of_total_tracked_time"] = round((float(item["duration_ms"]) / total_tracked_program_time_ms) * 100, 2)
        else:
            for item in performance_metrics["slow_programs"]:
                item["percent_of_total_tracked_time"] = 0.0

        aggregated_programs = performance_metrics["program_analysis"].pop("_aggregated_programs", {})
        ranked_programs = sorted(
            aggregated_programs.values(),
            key=lambda item: (item.get("total_time_ms", 0), item.get("calls", 0)),
            reverse=True
        )
        performance_metrics["program_analysis"]["top_programs_by_time"] = [
            {
                **item,
                "avg_time_ms": round((item.get("total_time_ms", 0) / item.get("calls", 1)), 2) if item.get("calls", 0) else 0.0,
                "percent_of_total_time": round((item.get("total_time_ms", 0) / total_tracked_program_time_ms) * 100, 2)
                if total_tracked_program_time_ms > 0 else 0.0
            }
            for item in ranked_programs[:15]
        ]
        
        # Calcular estatísticas de throughput
        performance_metrics["throughput"]["requests_per_minute"] = dict(requests_by_minute)
        
        # Identificar períodos de pico
        if requests_by_minute:
            avg_requests = sum(requests_by_minute.values()) / len(requests_by_minute)
            peak_threshold = avg_requests * 1.5
            
            for minute, count in requests_by_minute.items():
                if count > peak_threshold:
                    performance_metrics["throughput"]["peak_periods"].append({
                        "time": minute,
                        "requests": count,
                        "above_average": round(count - avg_requests, 2)
                    })
        
        # Calcular médias e percentis
        if performance_metrics["response_times"]:
            response_values = [rt["value"] for rt in performance_metrics["response_times"]]
            response_values.sort()
            n = len(response_values)
            
            performance_metrics["response_time_stats"] = {
                "average": round(sum(response_values) / n, 2),
                "median": response_values[n // 2],
                "p95": response_values[int(n * 0.95)] if n > 0 else 0,
                "p99": response_values[int(n * 0.99)] if n > 0 else 0,
                "min": min(response_values),
                "max": max(response_values),
                "total_samples": n
            }
        
        if performance_metrics["memory_usage"]:
            memory_values = [mem["value"] for mem in performance_metrics["memory_usage"]]
            performance_metrics["memory_stats"] = {
                "average": round(sum(memory_values) / len(memory_values), 2),
                "max": max(memory_values),
                "min": min(memory_values),
                "total_samples": len(memory_values)
            }
        
        if performance_metrics["cpu_usage"]:
            cpu_values = [cpu["value"] for cpu in performance_metrics["cpu_usage"]]
            performance_metrics["cpu_stats"] = {
                "average": round(sum(cpu_values) / len(cpu_values), 2),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "total_samples": len(cpu_values)
            }
        
        # NOVO: Estatísticas de programas lentos
        if performance_metrics["slow_programs"]:
            durations = [sp["duration_ms"] for sp in performance_metrics["slow_programs"]]
            performance_metrics["slow_programs_stats"] = {
                "total_slow_programs": len(performance_metrics["slow_programs"]),
                "slowest_duration_ms": max(durations),
                "average_duration_ms": round(sum(durations) / len(durations), 2),
                "critical_count": len([sp for sp in performance_metrics["slow_programs"] if sp["severity"] == "critical"]),
                "high_count": len([sp for sp in performance_metrics["slow_programs"] if sp["severity"] == "high"]),
                "medium_count": len([sp for sp in performance_metrics["slow_programs"] if sp["severity"] == "medium"])
            }
        
        return performance_metrics

    def _detect_log_type(self, log_content: str, sample_size: int = 300) -> str:
        """
        Detecta o tipo de log baseado no conteúdo.
        Tipos: "Datasul", "LOGIX", "Protheus/ADVPL", "JBoss", "Tomcat", "Fluig", "Acesso", "SmartClient", "Other"
        """
        lines = log_content.split('\n')[:sample_size]
        sample_text = '\n'.join(lines)
        sample_lower = sample_text.lower()
        
        # 1. Detecção por formato de timestamp Progress [YY/MM/DD@HH:MM:SS]
        has_progress_ts = bool(re.search(r'\[\d{2}/\d{2}/\d{2}@\d{2}:\d{2}:\d{2}', sample_text))
        
        # 2. Detecção Fluig (antes de JBoss pois Fluig roda sobre JBoss)
        fluig_indicators = sum([
            'com.fluig' in sample_lower or 'com.totvs.fluig' in sample_lower,
            'com.totvs.technology.wcm' in sample_lower,
            'fluig' in sample_lower,
            'ecm.service' in sample_lower,
        ])
        if fluig_indicators >= 2:
            logger.info(f"Log type detected: Fluig (indicators: {fluig_indicators})")
            return "Fluig"
        
        # 3. Detecção JBoss/Wildfly (muito específica)
        jboss_indicators = sum([
            'org.jboss' in sample_lower,
            'jbas0' in sample_lower,
            'wflyctl' in sample_lower,
            'org.wildfly' in sample_lower,
            'jboss.as' in sample_lower,
            'jboss.web' in sample_lower,
            bool(re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3}\s+(INFO|ERROR|WARN|DEBUG)\s+\[', sample_text)),
            bool(re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s+(INFO|ERROR|WARN|DEBUG)\s+\[', sample_text)),
        ])
        if jboss_indicators >= 2:
            logger.info(f"Log type detected: JBoss (indicators: {jboss_indicators})")
            return "JBoss"
        
        # 4. Detecção Tomcat (sem ser JBoss)
        tomcat_indicators = sum([
            'org.apache.catalina' in sample_lower,
            'org.apache.coyote' in sample_lower,
            'catalina.startup' in sample_lower,
            bool(re.search(r'SEVERE|INFO.*org\.apache', sample_text)),
        ])
        if tomcat_indicators >= 2:
            logger.info(f"Log type detected: Tomcat (indicators: {tomcat_indicators})")
            return "Tomcat"
        
        # 5. Detecção Apache Access Log
        access_indicators = sum([
            bool(re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s+-\s+-\s+\[', lines[0] if lines else '')),
            bool(re.search(r'(GET|POST|PUT|DELETE|HEAD)\s+/\S+\s+HTTP/', sample_text)),
            'access_log' in sample_lower,
        ])
        if access_indicators >= 2:
            logger.info(f"Log type detected: Acesso (indicators: {access_indicators})")
            return "Acesso"
        
        # 6. Detecção SmartClient
        smart_indicators = sum([
            'smartclient' in sample_lower,
            'clientlogsmc' in sample_lower,
            'buildinfoclient' in sample_lower,
            bool(re.search(r'SmartClient\s+Build', sample_text)),
            bool(re.search(r'AppServer connection.*smartclient', sample_lower)),
        ])
        if smart_indicators >= 1:
            logger.info(f"Log type detected: SmartClient (indicators: {smart_indicators})")
            return "SmartClient"
        
        # 7. Detecção Protheus / ADVPL
        protheus_specific = sum([
            'thread error' in sample_lower,
            'called from ' in sample_lower,
            'totvs environment' in sample_lower,
            'variable does not exist' in sample_lower,
            'cannot find method' in sample_lower,
            'invalid readmsint' in sample_lower,
            'failed to read status of inifile' in sample_lower,
            'open empty rpo' in sample_lower,
            'totvs application server is running' in sample_lower,
            'starting program siga' in sample_lower,
            'starting program mdiexecute' in sample_lower,
            'multiport - error' in sample_lower,
            'bpc2112' in sample_lower,
            bool(re.search(r'\[totvs environment:', sample_lower)),
            bool(re.search(r'\*\*\*\s+totvs s/?a', sample_lower)),
        ])

        if protheus_specific >= 2:
            logger.info(f"Log type detected: Protheus/ADVPL (score: {protheus_specific})")
            return "Protheus/ADVPL"

        # 8. Detecção LOGIX vs Datasul vs AppServer (todos TOTVS mas diferentes)
        logix_specific = sum([
            'totvs - frw' in sample_lower,
            'frw:' in sample_lower,
            'logix' in sample_lower,
            bool(re.search(r'sefaz|danfe|xml\.nfe', sample_lower)),
            bool(re.search(r'validação de schema|entidade.*nfe', sample_lower)),
            'totvsconsole' in sample_lower,
        ])
        
        # PERFORMANCE FIX: Distinguish AppServer logs from Datasul client logs
        # AppServer logs have AS markers but NOT 4GL markers
        has_as_markers = bool(re.search(r' AS ', sample_text))
        has_4gl_markers = bool(re.search(r' 4GL ', sample_text))
        has_ub_markers = bool(re.search(r' UB ', sample_text))
        has_appserver_keywords = sum([
            has_as_markers and not has_4gl_markers,
            bool(re.search(r'ASPlumbing|ASDefault|ASError', sample_text)),
            bool(re.search(r'AppServer|Broker|broker', sample_text)),
        ])
        
        datasul_specific = sum([
            has_progress_ts,
            has_4gl_markers,
            has_ub_markers,
            bool(re.search(r'P-\d{6}\s+T-', sample_text)),
            'propath' in sample_lower,
            bool(re.search(r'\.p\b.*procedure|procedure.*\.p\b', sample_lower)),
        ])
        
        if logix_specific >= 2:
            logger.info(f"Log type detected: LOGIX (score: {logix_specific})")
            return "LOGIX"
        elif has_appserver_keywords >= 2:
            logger.info(f"Log type detected: AppServer (score: {has_appserver_keywords})")
            return "AppServer"
        elif datasul_specific >= 2:
            logger.info(f"Log type detected: Datasul (score: {datasul_specific})")
            return "Datasul"
        elif has_progress_ts:
            # If only timestamp is present, check if it's AppServer
            if has_as_markers and not has_4gl_markers:
                logger.info("Log type detected: AppServer (Progress timestamp + AS markers)")
                return "AppServer"
            logger.info("Log type detected: Datasul (Progress timestamp found)")
            return "Datasul"
        elif logix_specific >= 1:
            logger.info(f"Log type detected: LOGIX (weak: {logix_specific})")
            return "LOGIX"
        else:
            logger.info(f"Log type detected: Other (datasul={datasul_specific}, logix={logix_specific})")
            return "Other"

    def detect_log_type(self, log_content: str, sample_size: int = 300) -> str:
        """API pública para detecção rápida do tipo do log antes da análise pesada."""
        return self._detect_log_type(log_content, sample_size=sample_size)

    def _should_enable_structured_parsing_for_type(self, log_type: str) -> bool:
        """Ativa parsing estruturado apenas para famílias onde ele agrega valor."""
        return log_type in {
            'Acesso',
            'JBoss',
            'Tomcat',
            'Fluig',
            'Datasul',
            'AppServer',
            'SmartClient',
            'LOGIX',
            'PASOE',
            'TOTVS',
            'Progress/OpenEdge',
            'Protheus/ADVPL',
        }

    def _should_enable_structured_parsing_for_content(self, log_type: str, log_content: str, sample_size: int = 20) -> bool:
        if self._should_enable_structured_parsing_for_type(log_type):
            return True

        if log_type != 'Other':
            return False

        sample_lines_checked = 0
        for raw_line in log_content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if (
                self.structured_parser.RX_JAVA_LINE.match(line)
                or self.structured_parser.RX_TOMCAT_JUL.match(line)
                or self.structured_parser.RX_HH_ONLY.match(line)
                or self.structured_parser.RX_ACCESS.match(line)
                or self.structured_parser.RX_PROGRESS.match(line)
                or self.structured_parser.RX_PROGRESS_SIMPLE.match(line)
                or self.structured_parser.RX_PROGRESS_PROCESS.match(line)
                or self.structured_parser.RX_PROGRESS_TIMESTAMPED.match(line)
            ):
                return True

            sample_lines_checked += 1
            if sample_lines_checked >= sample_size:
                break

        return False
    
    def analyze_log_content(
        self, 
        log_content: str, 
        external_patterns_content: Optional[str] = None,
        enable_structured_parsing: bool = False,
        detected_log_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analisa o conteúdo do log com suporte a parsing estruturado e análise de padrões Datasul.
        
        Args:
            log_content: Conteúdo do log a ser analisado
            external_patterns_content: Padrões externos opcionais
            enable_structured_parsing: Se True, usa parsing estruturado para Apache/Java/Progress
        """
        
        try:
            # Detectar o tipo do log antes da análise pesada e reutilizar o resultado.
            log_type = detected_log_type or self._detect_log_type(log_content)
            use_type_hint_for_structured_parsing = detected_log_type is not None
            logger.info(f"Analyzing log as type: {log_type}")
            analysis_started_at = monotonic()
            analysis_timings = {
                "structured_parsing_ms": 0.0,
                "pattern_analysis_ms": 0.0,
                "post_processing_ms": 0.0,
                "total_analysis_ms": 0.0,
            }
            
            # Parse external patterns if provided
            external_patterns = []
            if external_patterns_content:
                external_patterns = self.load_external_patterns(external_patterns_content)

            structured_result = None
            structured_events_by_line = {}
            if enable_structured_parsing and self._should_enable_structured_parsing_for_content(log_type, log_content):
                structured_started_at = monotonic()
                structured_result = self.structured_parser.parse_log_content(
                    log_content,
                    enable_multiline=False,
                    preferred_log_type=log_type if use_type_hint_for_structured_parsing else None
                )
                analysis_timings["structured_parsing_ms"] = round((monotonic() - structured_started_at) * 1000, 2)
                structured_events_by_line = {
                    event.get("line_number"): event
                    for event in structured_result.get("events", [])
                    if event.get("parsed_successfully")
                }
            
            # Estruturas para armazenar resultados
            results = []
            attention_points = []
            error_counts = Counter()
            errors_by_time = defaultdict(int)
            severity_counts = Counter()
            hourly_distribution = defaultdict(int)
            pattern_analysis_started_at = monotonic()
            
            # === ANÁLISE DE PADRÕES (VERSÃO OTIMIZADA ORIGINAL) ===
            # Combine all patterns baseado no tipo de log detectado
            all_patterns = []
            
            # Padrões padrão sempre incluídos
            all_patterns.extend(self.default_patterns)
            
            # Adicionar padrões Datasul APENAS para tipo Datasul
            if log_type == "Datasul":
                all_patterns.extend(self.datasul_patterns)
                logger.info(f"Added {len(self.datasul_patterns)} Datasul patterns")
            
            # CORRIGIDO: Adicionar padrões LOGIX se for tipo LOGIX
            if log_type == "LOGIX" and self.logix_loader:
                try:
                    logix_pattern_objs = self.logix_loader.get_all_patterns()
                    # Extrair apenas os padrões regex
                    logix_patterns = [p.get('pattern', '') for p in logix_pattern_objs if p.get('pattern')]
                    all_patterns.extend(logix_patterns)
                    logger.info(f"Added {len(logix_patterns)} LOGIX patterns from {len(logix_pattern_objs)} objects")
                except Exception as e:
                    logger.warning(f"Could not load LOGIX patterns: {e}")
            
            # Adicionar padrões customizados do usuário
            all_patterns.extend([p for p in self.custom_patterns if p.strip()])
            
            # Validate and compile patterns
            safe_patterns = []
            for pattern in all_patterns:
                try:
                    re.compile(pattern)
                    safe_patterns.append(pattern)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern skipped: {pattern} - Error: {e}")
                    # Tentar escapar o padrão
                    escaped_pattern = re.escape(pattern)
                    try:
                        re.compile(escaped_pattern)
                        safe_patterns.append(escaped_pattern)
                        logger.info(f"Pattern escaped and added: {escaped_pattern}")
                    except re.error:
                        logger.error(f"Pattern completely invalid, skipping: {pattern}")
            
            if not safe_patterns:
                logger.warning("No valid patterns found, using basic error patterns")
                safe_patterns = ["ERROR", "Exception", "FAILED", "CRITICAL"]
            
            # Compile final regex pattern
            regex = re.compile("|".join(safe_patterns), re.IGNORECASE)
            
            # OTIMIZAÇÃO: Limpar cache a cada nova análise
            self._line_match_cache.clear()
            
            # Processar linha por linha
            lines = log_content.split('\n')
            total_lines = len(lines)
            
            # OTIMIZAÇÃO: Pre-filter para Progress logs - pular entry types informativos
            progress_informational_types = frozenset({
                '4GLTRACE', 'FILEID', 'Properties', 'DYNOBJECTS',
                'PROEVENTS', 'DBCONNECTS', '----------'
            })
            ub_informational = frozenset({'Basic', 'Plumbing', 'Statistics', 'Info'})
            as_informational = frozenset({'4GLTrace', 'FILEID', 'ASPlumbing', 'ASDefault', 'AS', 'DB.Connects', 'Properties', '--', '----------', 'CONN'})
            # PERFORMANCE FIX: Only apply Progress pre-filter to Progress-based log types
            _progress_log_types = frozenset({'Datasul', 'LOGIX', 'SmartClient', 'AppServer', 'Other', 'Protheus/ADVPL'})
            _totvs_check_types = frozenset({'Datasul', 'TOTVS', 'SmartClient', 'Protheus/ADVPL'})
            is_progress_log = log_type in _progress_log_types
            
            for line_num, line in enumerate(lines, start=1):
                original_line = line.strip()
                if not original_line:
                    continue

                # OTIMIZAÇÃO: Fast skip de linhas informativas em logs Progress
                if is_progress_log and original_line.startswith('['):
                    if ' 4GL ' in original_line:
                        idx_4gl = original_line.find(' 4GL ')
                        if idx_4gl > 0:
                            rest = original_line[idx_4gl + 5:].lstrip()
                            entry_type = rest.split()[0] if rest else ''
                            if entry_type in progress_informational_types or entry_type == '--':
                                continue
                    elif ' UB ' in original_line:
                        idx_ub = original_line.find(' UB ')
                        if idx_ub > 0:
                            rest = original_line[idx_ub + 4:].lstrip()
                            entry_type = rest.split()[0] if rest else ''
                            if entry_type in ub_informational:
                                continue
                    elif ' AS ' in original_line:
                        idx_as = original_line.find(' AS ')
                        if idx_as > 0:
                            rest = original_line[idx_as + 4:].lstrip()
                            entry_type = rest.split()[0] if rest else ''
                            if entry_type in as_informational:
                                continue
                
                # OTIMIZAÇÃO: Para JBoss/Tomcat - skip linhas INFO/DEBUG/TRACE level
                if log_type in ('JBoss', 'Tomcat', 'Fluig') and (' INFO ' in original_line or ' DEBUG ' in original_line or ' TRACE ' in original_line):
                    if not any(kw in original_line for kw in ('Exception', 'Error', 'FAILED', 'Caused by')):
                        continue

                # PERFORMANCE FIX: Para LOGIX logs - skip linhas INFO rotineiras sem indicadores de erro
                if log_type == 'LOGIX' and not original_line.startswith('['):
                    if original_line.startswith('INFO ') or 'Operação de rotina' in original_line or 'executada com sucesso' in original_line:
                        if not any(kw in original_line for kw in ('ERROR', 'Error', 'FATAL', 'WARN', 'falhou', 'falha', 'Timeout', 'timeout', 'Exception', 'rejected', 'STOP')):
                            continue

                structured_event = structured_events_by_line.get(line_num)
                
                # NOVO: Ignorar ruído Progress (heartbeat/conexão) - only for Progress logs
                if is_progress_log and self._is_progress_noise(original_line):
                    continue
                
                # Extrair apenas a mensagem relevante (removendo metadados)
                clean_message = (
                    structured_event.get("clean_message")
                    if structured_event and structured_event.get("clean_message")
                    else self.extract_log_message(original_line)
                )
                
                # Verificar se é um padrão de não-erro primeiro
                if self._is_non_error(clean_message):
                    continue
                
                # Verificar pontos de atenção (usar mensagem limpa)
                if self._is_attention_point(clean_message):
                    timestamp = self.extract_timestamp(original_line)
                    attention_item = {
                        "line": line_num,
                        "message": clean_message,  # Mostrar mensagem limpa SEM metadados
                        "clean_message": clean_message,  # Armazenar mensagem limpa
                        "timestamp": timestamp,
                        "type": "attention_point",
                        "matched_keywords": self._get_attention_keywords(clean_message)
                    }
                    
                    # Adicionar informações extras para Procedure: e LOG:MANAGER
                    if self.datasul_loader:
                        datasul_info = self.datasul_loader.get_solution_for_pattern(clean_message)
                        if datasul_info:
                            attention_item.update({
                                "description": datasul_info.get("description", ""),
                                "solution": datasul_info.get("solution", ""),
                                "tag": datasul_info.get("tag", ""),
                                "matched_pattern": datasul_info.get("matched_pattern", ""),
                                "priority": datasul_info.get("priority", 3)
                            })
                    
                    attention_points.append(attention_item)
                    
                    # NOVO: Adicionar ponto de atenção também como erro de severidade ALTA
                    error_item = {
                        "line": line_num,
                        "timestamp": timestamp,
                        "error_type": "Ponto de Atenção",
                        "severity": "Alta",
                        "message": clean_message,
                        "clean_message": clean_message,
                        "is_attention_point": True,
                        "matched_keywords": attention_item.get("matched_keywords", [])
                    }
                    results.append(error_item)
                    
                # OTIMIZAÇÃO: Verificar se a mensagem limpa corresponde aos padrões principais ou aos novos padrões Datasul/LOGIX
                # Fazer verificações UMA VEZ e reutilizar resultados
                # PERFORMANCE FIX: Scoped Datasul/LOGIX checks to relevant log types only
                # LOGIX patterns are already in the main regex, so _is_logix_error is only for enrichment later
                is_main_error = regex.search(clean_message)
                is_datasul_error = self._is_datasul_error(clean_message) if log_type in _totvs_check_types else False
                is_logix_error = False  # LOGIX patterns already in main regex; enrichment done post-match
                is_structured_error = bool(structured_event and structured_event.get("is_error"))
                
                if is_main_error or is_datasul_error or is_logix_error or is_structured_error:
                    # OTIMIZAÇÃO: Extrair timestamp e classificar UMA VEZ
                    timestamp = (
                        structured_event.get("timestamp_parsed")
                        if structured_event and structured_event.get("timestamp_parsed")
                        else self.extract_timestamp(original_line)
                    )
                    
                    # OTIMIZAÇÃO: classify_error foi otimizado para não repetir buscas
                    error_type = self._classify_error_optimized(original_line, external_patterns, is_datasul_error, is_logix_error)
                    error_type = self._refine_error_type_with_structure(error_type, structured_event)
                    
                    # Determinar severidade usando mensagem limpa
                    severity = (
                        structured_event.get("severity")
                        if structured_event and structured_event.get("severity")
                        else self._determine_severity(clean_message)
                    )
                    
                    # Não considerar erros de nível "Baixo" como erros reais
                    if severity.lower() == 'baixo':
                        continue
                    
                    result_item = {
                        "line": line_num,
                        "timestamp": timestamp,
                        "error_type": error_type,
                        "severity": severity,
                        "message": clean_message[:500] + "..." if len(clean_message) > 500 else clean_message,  # Mostrar mensagem limpa SEM metadados
                        "clean_message": clean_message[:500] + "..." if len(clean_message) > 500 else clean_message  # Mensagem limpa para processamento
                    }

                    if structured_event:
                        result_item.update({
                            "structured_type": structured_event.get("structured_type"),
                            "log_family": structured_event.get("log_type"),
                            "log_subtype": structured_event.get("log_subtype"),
                            "category": structured_event.get("category"),
                            "error_signature": structured_event.get("error_signature")
                        })

                        for field in ["domain_fields", "insight_tags", "recommendation_hint"]:
                            if field in structured_event and structured_event.get(field) not in [None, "", []]:
                                result_item[field] = structured_event.get(field)

                        for field in [
                            "logger",
                            "thread",
                            "status_code",
                            "method",
                            "path",
                            "comp",
                            "process_id",
                            "thread_id",
                            "level_numeric",
                            "exception_class",
                            "error_code",
                            "program_path",
                            "database_name",
                            "progress_variant",
                            "legacy_parser",
                            "legacy_group"
                        ]:
                            if field in structured_event and structured_event.get(field) not in [None, ""]:
                                normalized_field = "component" if field == "comp" else field
                                result_item[normalized_field] = structured_event.get(field)
                    
                    # === PADRÕES LOGIX (NOVO) ===
                    
                    # Adicionar informações detalhadas de solução para padrões LOGIX
                    if error_type == "LOGIX" and self.logix_loader:
                        logix_info = self.logix_loader.get_solution_for_pattern(clean_message)
                        if logix_info:
                            result_item.update({
                                "description": logix_info.get("description", ""),
                                "solution": logix_info.get("solution", ""),
                                "tag": logix_info.get("tag", ""),
                                "matched_pattern": logix_info.get("matched_pattern", ""),
                                "priority": logix_info.get("priority", 3),
                                "category": logix_info.get("category", ""),
                                "severity": logix_info.get("severity", result_item.get("severity", "Médio")),
                                "example": logix_info.get("example", ""),
                                "source": logix_info.get("source", "LOGIX Knowledge Base")
                            })
                    
                    # === PADRÕES DATASUL (OTIMIZADO) ===
                    
                    # Adicionar informações detalhadas de solução para padrões Datasul (usar mensagem limpa)
                    if error_type == "Datasul" and self.datasul_loader:
                        datasul_info = self.datasul_loader.get_solution_for_pattern(clean_message)
                        if datasul_info:
                            result_item.update({
                                "description": datasul_info.get("description", ""),
                                "solution": datasul_info.get("solution", ""),
                                "tag": datasul_info.get("tag", ""),
                                "matched_pattern": datasul_info.get("matched_pattern", ""),
                                "priority": datasul_info.get("priority", 3),
                                "pattern_id": datasul_info.get("pattern_id", ""),
                                "category": datasul_info.get("category", result_item.get("category", "")),
                                "severity": datasul_info.get("severity", result_item.get("severity", "Médio"))
                            })
                    
                    # === PADRÕES TOTVS ESPECÍFICOS (NOVO) ===
                    
                    # Verificar e adicionar informações detalhadas para erros TOTVS/Datasul específicos
                    # Only for Datasul-related log types
                    if self.totvs_loader and log_type in _totvs_check_types:
                        totvs_info = self._is_totvs_error(clean_message)
                        if totvs_info:
                            result_item.update({
                                "description": totvs_info.get("description", ""),
                                "solution": totvs_info.get("solution", ""),
                                "tag": totvs_info.get("tag", ""),
                                "matched_pattern": totvs_info.get("matched_pattern", ""),
                                "priority": totvs_info.get("priority", 2),
                                "error_code": totvs_info.get("code", ""),
                                "category": totvs_info.get("category", ""),
                                "severity": totvs_info.get("severity", result_item.get("severity", "Médio")),
                                "reference": totvs_info.get("reference", ""),
                                "example": totvs_info.get("example", ""),
                                "product": totvs_info.get("product", "TOTVS")
                            })
                            if log_type == 'Protheus/ADVPL' or totvs_info.get('product') == 'Protheus/ADVPL':
                                result_item["error_type"] = "Protheus/ADVPL"
                            else:
                                result_item["error_type"] = "TOTVS"

                    result_item = self._finalize_result_item_context(result_item, structured_event, clean_message)
                    
                    results.append(result_item)
                    
                    # Contadores
                    error_counts[error_type] += 1
                    severity_counts[severity] += 1
                    
                    # Análise temporal
                    if timestamp != "N/A":
                        try:
                            dt = self._parse_timestamp(timestamp)
                            if dt:
                                errors_by_time[dt.date()] += 1
                                hourly_distribution[dt.hour] += 1
                        except Exception as e:
                            logger.warning(f"Could not parse timestamp {timestamp}: {e}")
            analysis_timings["pattern_analysis_ms"] = round((monotonic() - pattern_analysis_started_at) * 1000, 2)
            
            # Detectar novos erros potenciais
            # OTIMIZAÇÃO: Pre-filtrar linhas para análises custosas
            post_processing_started_at = monotonic()
            relevant_lines = self._prefilter_relevant_lines(lines, log_type)
            
            new_errors_analysis = self._detect_new_errors(relevant_lines, regex)
            
            # Análise de performance
            performance_analysis = self.analyze_performance(relevant_lines, log_type)
            
            # Gerar estatísticas
            statistics = {
                "total_lines_processed": total_lines,
                "total_matches_found": len(results),
                "match_percentage": round((len(results) / total_lines) * 100, 2) if total_lines > 0 else 0,
                "error_types_count": len(error_counts),
                "date_range": self._get_date_range(errors_by_time),
                "most_common_error": error_counts.most_common(1)[0] if error_counts else ("N/A", 0),
                "peak_hour": max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else "N/A",
                "new_errors_found": len(new_errors_analysis["potential_errors"])
            }
            
            # Preparar dados para gráficos
            chart_data = self._prepare_chart_data(error_counts, errors_by_time, severity_counts, hourly_distribution)
            
            # Preparar resultado final com dados estruturados
            result = {
                "success": True,
                "log_type": log_type,  # NOVO: Informar tipo de log detectado
                "statistics": statistics,
                "results": results[:1000],  # Limitar a 1000 resultados para performance
                "total_results": len(results),
                "chart_data": chart_data,
                "error_counts": dict(error_counts),
                "severity_counts": dict(severity_counts),
                "attention_points": attention_points[:500],  # Limitar pontos de atenção
                "total_attention_points": len(attention_points),
                "new_errors": new_errors_analysis,
                "performance_analysis": performance_analysis,
                # Top programs/methods analysis: will be filled by _analyze_callers_and_programs
                "top_programs_methods": self._analyze_callers_and_programs(relevant_lines, log_type),
                "informational_lines": [],
                "structured_analysis": self._build_structured_analysis(structured_result)
            }
            analysis_timings["post_processing_ms"] = round((monotonic() - post_processing_started_at) * 1000, 2)
            analysis_timings["total_analysis_ms"] = round((monotonic() - analysis_started_at) * 1000, 2)
            result["analysis_timings"] = analysis_timings
            
            # === RESULTADO OTIMIZADO (SIMPLICIDADE ORIGINAL) ===
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing log: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total_results": 0,
                "statistics": {
                    "total_lines_processed": 0,
                    "total_matches_found": 0,
                    "match_percentage": 0,
                    "error_types_count": 0,
                    "date_range": {"start": "N/A", "end": "N/A"},
                    "most_common_error": ("N/A", 0),
                    "peak_hour": "N/A",
                    "new_errors_found": 0
                },
                "chart_data": {
                    "error_types": {"labels": [], "values": []},
                    "temporal": {"labels": [], "values": []},
                    "severity": {"labels": [], "values": []},
                    "hourly": {"labels": [], "values": []}
                },
                "error_counts": {},
                "severity_counts": {},
                "analysis_timings": {
                    "structured_parsing_ms": 0.0,
                    "pattern_analysis_ms": 0.0,
                    "post_processing_ms": 0.0,
                    "total_analysis_ms": 0.0,
                },
                "new_errors": {
                    "potential_errors": [],
                    "pattern_suggestions": [],
                    "frequent_suspicious_words": [],
                    "total_potential_errors": 0,
                    "analysis_coverage": {
                        "lines_analyzed": 0,
                        "lines_with_known_patterns": 0,
                        "lines_with_potential_new_errors": 0
                    }
                },
                "performance_analysis": {},
                "structured_analysis": None
            }

    def _refine_error_type_with_structure(self, error_type: str, structured_event: Optional[Dict[str, Any]]) -> str:
        """Ajusta o tipo do erro quando o parser estruturado encontrou um subtipo mais específico."""
        if not structured_event:
            return error_type

        subtype_labels = {
            "acesso": "Acesso",
            "tomcat": "Tomcat",
            "jboss": "JBoss",
            "fluig": "Fluig",
            "pasoe": "PASOE",
            "appserver": "AppServer",
            "appbroker": "AppBroker",
            "progress_db": "Progress DB",
            "progress_memory": "Progress Memory",
            "progress_tabanalys": "Progress TabAnalys",
            "progress_xref": "Progress XRef",
            "app_performance": "App Performance",
            "logix": "LOGIX",
            "protheus_advpl": "Protheus/ADVPL",
            "progress": "Progress/OpenEdge",
            "java": "Java"
        }

        generic_types = {"Outros", "Error Crítico", "Warning", "HTTP/Web", "Progress/OpenEdge"}
        structured_label = subtype_labels.get(structured_event.get("log_subtype"))

        if structured_label and error_type in generic_types:
            return structured_label

        return error_type

    def _build_structured_analysis(self, structured_result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Normaliza a saída do parsing estruturado para a resposta principal."""
        if not structured_result or not structured_result.get("success"):
            return None

        stats = structured_result.get("statistics", {})
        http_status = dict(stats.get("http_status", {}))
        specialized_metrics = self._build_specialized_structured_metrics(structured_result.get("events", []))

        return {
            "enabled": True,
            "total_events": structured_result.get("structured_events", 0),
            "type_breakdown": dict(stats.get("by_type", {})),
            "subtype_breakdown": dict(stats.get("by_subtype", {})),
            "category_breakdown": self._normalize_category_breakdown(dict(stats.get("by_category", {}))),
            "http_metrics": {
                "status_distribution": http_status,
                "total_requests": sum(http_status.values())
            },
            "java_metrics": {
                "level_distribution": dict(stats.get("java_levels", {})),
                "top_exceptions": dict(stats.get("exceptions", {}))
            },
            "progress_metrics": {
                "level_distribution": dict(stats.get("progress_levels", {}))
            },
            "specialized_metrics": specialized_metrics
        }

    def _build_specialized_structured_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolida métricas adicionais baseadas em enriquecimento por subtipo."""
        parsed_events = [event for event in events if event.get("parsed_successfully")]

        insight_tags = Counter()
        recommendation_hints = Counter()
        top_5xx_routes = Counter()
        top_progress_programs = Counter()
        broker_incidents = Counter()
        top_tabanalys_tables = Counter()
        xref_types = Counter()
        logix_commands = Counter()
        logix_programs = Counter()

        for event in parsed_events:
            for tag in event.get("insight_tags", []):
                insight_tags[tag] += 1

            recommendation_hint = event.get("recommendation_hint")
            if recommendation_hint:
                recommendation_hints[recommendation_hint] += 1

            domain_fields = event.get("domain_fields") or {}
            subtype = event.get("log_subtype")

            if subtype == "acesso" and (event.get("status_code") or domain_fields.get("status_code", 0)) >= 500:
                route = domain_fields.get("route") or domain_fields.get("path")
                if route:
                    top_5xx_routes[route] += 1

            if subtype in ["progress", "pasoe", "appserver", "appbroker", "app_performance"]:
                program_name = domain_fields.get("program_name")
                if program_name:
                    top_progress_programs[program_name] += 1

            if subtype in ["appserver", "appbroker"]:
                broker_name = domain_fields.get("broker_name")
                if broker_name:
                    broker_incidents[broker_name] += 1

            if subtype == "progress_tabanalys":
                table_name = domain_fields.get("table_name") or domain_fields.get("index_name")
                if table_name:
                    top_tabanalys_tables[table_name] += 1

            if subtype == "progress_xref":
                xref_type = domain_fields.get("xref_type")
                if xref_type:
                    xref_types[xref_type] += 1

            if subtype == "logix":
                command_type = domain_fields.get("command_type")
                if command_type:
                    logix_commands[command_type] += 1
                source_program = domain_fields.get("source_program")
                if source_program:
                    logix_programs[source_program] += 1

        return {
            "insight_tags": dict(insight_tags.most_common(20)),
            "recommendation_hints": dict(recommendation_hints.most_common(10)),
            "access_kpis": {
                "top_5xx_routes": [
                    {"route": route, "count": count}
                    for route, count in top_5xx_routes.most_common(10)
                ]
            },
            "progress_kpis": {
                "top_programs": [
                    {"program_name": program_name, "count": count}
                    for program_name, count in top_progress_programs.most_common(10)
                ],
                "broker_incidents": [
                    {"broker_name": broker_name, "count": count}
                    for broker_name, count in broker_incidents.most_common(10)
                ]
            },
            "tabanalys_kpis": {
                "top_objects": [
                    {"object_name": object_name, "count": count}
                    for object_name, count in top_tabanalys_tables.most_common(10)
                ]
            },
            "xref_kpis": {
                "type_breakdown": dict(xref_types.most_common(10))
            },
            "logix_kpis": {
                "top_command_types": [
                    {"command_type": command_type, "count": count}
                    for command_type, count in logix_commands.most_common(10)
                ],
                "top_programs": [
                    {"program_name": program_name, "count": count}
                    for program_name, count in logix_programs.most_common(10)
                ]
            }
        }

    def _finalize_result_item_context(self, result_item: Dict[str, Any], structured_event: Optional[Dict[str, Any]], message: str) -> Dict[str, Any]:
        """Prioriza severidade e categoria com base no contexto estruturado e regras legadas."""
        structured_category = structured_event.get("category") if structured_event else None
        current_category = result_item.get("category") or structured_category
        normalized_category = self._normalize_legacy_category(
            structured_event.get("log_subtype") if structured_event else None,
            current_category,
            message
        )

        if normalized_category:
            result_item["category"] = normalized_category
        if structured_category:
            result_item["structured_category"] = structured_category

        current_severity = result_item.get("severity", "Médio")
        normalized_severity = self._normalize_legacy_severity(
            current_severity,
            structured_event,
            result_item.get("category"),
            message
        )
        result_item["severity"] = normalized_severity

        return result_item

    def _normalize_legacy_category(self, subtype: Optional[str], category: Optional[str], message: str) -> str:
        """Traduz categorias técnicas para rótulos mais próximos da tela legada."""
        message_lower = message.lower()
        category = category or ""

        if category and "/" in category:
            return category

        subtype_category_map = {
            "pasoe": {
                "exception": "Infra/PASOE",
                "availability": "Infra/PASOE",
                "http": "Infra/PASOE",
                "performance": "Performance/PASOE",
                "security": "Segurança/PASOE",
                "application": "Infra/PASOE"
            },
            "tomcat": {
                "exception": "Infra/Tomcat",
                "availability": "Infra/Tomcat",
                "http": "Infra/Tomcat",
                "performance": "Performance/Tomcat",
                "security": "Segurança/Tomcat",
                "application": "Infra/Tomcat"
            },
            "jboss": {
                "exception": "Infra/JBoss",
                "availability": "Infra/JBoss",
                "database": "Infra/JBoss",
                "performance": "Performance/JBoss",
                "security": "Segurança/JBoss",
                "application": "Infra/JBoss"
            },
            "fluig": {
                "exception": "Infra/Fluig",
                "database": "Infra/Fluig",
                "performance": "Performance/Fluig",
                "security": "Segurança/Fluig",
                "application": "Infra/Fluig"
            },
            "appserver": {
                "availability": "Infra/AppServer",
                "performance": "Performance/AppServer",
                "security": "Segurança/AppServer",
                "application": "Infra/AppServer",
                "exception": "Infra/AppServer"
            },
            "appbroker": {
                "availability": "Infra/AppServer",
                "performance": "Performance/AppServer",
                "application": "Infra/AppServer",
                "exception": "Infra/AppServer"
            },
            "progress_db": {
                "database": "DataServer/DB",
                "performance": "Performance/DB",
                "availability": "DataServer/DB",
                "security": "Segurança/DB",
                "application": "DataServer/DB"
            },
            "progress_memory": {
                "memory": "Infra/Memória",
                "exception": "Infra/Memória",
                "application": "Infra/Memória"
            },
            "progress_tabanalys": {
                "table_analysis": "Performance/DB",
                "performance": "Performance/DB"
            },
            "progress_xref": {
                "xref": "Framework/XRef",
                "application": "Framework/XRef"
            },
            "logix": {
                "sql": "SQL/LOGIX",
                "validation": "Validação/LOGIX",
                "integration": "Integração/LOGIX",
                "license": "Licença/LOGIX",
                "framework": "Framework/LOGIX",
                "server": "Infra/LOGIX",
                "application": "LOGIX"
            },
            "protheus_advpl": {
                "application": "Framework/ADVPL",
                "configuration": "Configuração/Application Server",
                "connectivity": "Infra/Application Server",
                "memory": "Infra/Memória",
                "security": "Segurança/Application Server"
            },
            "app_performance": {
                "performance": "Performance/AppServer",
                "application": "Performance/AppServer"
            },
            "acesso": {
                "server_error": "Infra/Web",
                "client_error": "Infra/Web",
                "redirect": "Infra/Web",
                "success": "Infra/Web"
            },
            "progress": {
                "database": "DataServer/DB",
                "performance": "Performance/Progress",
                "security": "Segurança",
                "availability": "Infra/Framework",
                "exception": "Infra/Framework",
                "application": "Infra/Framework"
            }
        }

        if subtype in subtype_category_map and category in subtype_category_map[subtype]:
            return subtype_category_map[subtype][category]

        english_category_map = {
            "exception": "Infra/Framework",
            "database": "DataServer/DB",
            "security": "Segurança",
            "availability": "Infra/Framework",
            "performance": "Performance",
            "http": "Infra/Web",
            "memory": "Infra/Memória",
            "table_analysis": "Performance/DB",
            "xref": "Framework/XRef",
            "sql": "SQL/LOGIX",
            "validation": "Validação/LOGIX",
            "integration": "Integração/LOGIX",
            "license": "Licença/LOGIX",
            "framework": "Framework/LOGIX",
            "server": "Infra/LOGIX",
            "application": "Infra/Framework",
            "server_error": "Infra/Web",
            "client_error": "Infra/Web"
        }

        if category in english_category_map:
            return english_category_map[category]

        if re.search(r'webhandler|ablwebapp|pasoe|oepas|msagent', message_lower):
            return "Infra/PASOE"
        if re.search(r'broker|appserver|_mprosrv|nameserver', message_lower):
            return "Infra/AppServer"
        if re.search(r'database|schema holder|before-image|after-image|biw|aiw', message_lower):
            return "DataServer/DB"
        if re.search(r'table scan|index|factor', message_lower):
            return "Performance/DB"
        if re.search(r'totvs|logix|schema xml|sefaz|danfe|\bfrw\b', message_lower):
            return "LOGIX"
        if self._looks_like_protheus_advpl(message):
            return "Framework/ADVPL"

        return category

    def _normalize_legacy_severity(self, current_severity: str, structured_event: Optional[Dict[str, Any]], category: Optional[str], message: str) -> str:
        """Escalona severidade para ficar mais próxima da priorização legada."""
        message_lower = message.lower()
        subtype = structured_event.get("log_subtype") if structured_event else None
        severity = current_severity or "Médio"

        if subtype in ["pasoe", "appserver", "appbroker"] and re.search(r'died|not available|failed to start|refused|terminated|shutdown|unavailable', message_lower):
            return self._pick_higher_severity(severity, "Crítico")

        if subtype in ["pasoe", "tomcat", "jboss", "fluig"] and re.search(r'exception|stacktrace|caused by:|outofmemory|stackoverflow', message_lower):
            return self._pick_higher_severity(severity, "Crítico")

        if subtype == "progress_db" or (category and "DB" in category):
            if re.search(r'disconnect|cannot connect|deadlock|corrupt|latch|full|stopped', message_lower):
                return self._pick_higher_severity(severity, "Crítico")
            if re.search(r'lock|timeout|schema holder|before-image|after-image', message_lower):
                return self._pick_higher_severity(severity, "Alto")

        if subtype == "progress_memory":
            return self._pick_higher_severity(severity, "Crítico")

        if subtype == "logix":
            if re.search(r'erro|error|falha|inv[aá]l|schema xml|wscerr', message_lower):
                return self._pick_higher_severity(severity, "Alto")
            if re.search(r'\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|running time', message_lower):
                return self._pick_higher_severity(severity, "Médio")

        if subtype in ["app_performance", "progress_tabanalys"] or (category and category.startswith("Performance")):
            if re.search(r'([89]\d|100)%', message_lower) or re.search(r'\b([5-9]\d{3}|\d{5,})\s*ms\b', message_lower) or re.search(r'\b([5-9]|[1-9]\d+)\.?\d*\s*seconds?\b', message_lower):
                return self._pick_higher_severity(severity, "Alto")
            return self._pick_higher_severity(severity, "Médio")

        if category and category.startswith("Segurança"):
            return self._pick_higher_severity(severity, "Alto")

        return severity

    def _pick_higher_severity(self, left: str, right: str) -> str:
        order = {
            "Info": 0,
            "Baixo": 1,
            "Médio": 2,
            "Alta": 3,
            "Alto": 3,
            "Crítico": 4
        }
        return left if order.get(left, 2) >= order.get(right, 2) else right

    def _normalize_category_breakdown(self, category_breakdown: Dict[str, int]) -> Dict[str, int]:
        """Agrupa categorias estruturadas em rótulos legados."""
        normalized = defaultdict(int)
        for category, count in category_breakdown.items():
            normalized[self._normalize_legacy_category(None, category, "")] += count
        return dict(normalized)

    def _determine_severity(self, line: str) -> str:
        """Determina a severidade do erro."""
        line_lower = line.lower()
        
        # Padrões Datasul devem ter pelo menos severidade Médio
        if self._is_datasul_error(line):
            if re.search(r"critical|fatal|severe|erro \d+", line_lower):
                return "Crítico"
            elif re.search(r"error|exception|failed", line_lower):
                return "Alto"
            else:
                return "Médio"  # Datasul patterns get at least Medium severity
        
        if re.search(r"critical|fatal|severe", line_lower):
            return "Crítico"
        elif re.search(r"error|exception|failed", line_lower):
            return "Alto"
        elif re.search(r"warning|warn", line_lower):
            return "Médio"
        else:
            return "Baixo"

    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        """Tenta fazer parse do timestamp com múltiplos formatos."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%b %d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                candidate = timestamp
                candidate_format = fmt

                if "%Y" not in fmt:
                    candidate = f"{timestamp} {datetime.now().year}"
                    candidate_format = f"{fmt} %Y"

                return datetime.strptime(candidate, candidate_format)
            except ValueError:
                continue
        return None

    def _get_date_range(self, errors_by_time: Dict) -> Dict[str, str]:
        """Obtém o range de datas do log."""
        if not errors_by_time:
            return {"start": "N/A", "end": "N/A"}
        
        dates = sorted(errors_by_time.keys())
        return {
            "start": str(dates[0]),
            "end": str(dates[-1])
        }

    def _prepare_chart_data(
        self, 
        error_counts: Counter, 
        errors_by_time: Dict,
        severity_counts: Counter,
        hourly_distribution: Dict
    ) -> Dict[str, Any]:
        """Prepara dados para os gráficos."""
        
        # Dados por tipo de erro
        error_types_data = {
            "labels": list(error_counts.keys()),
            "values": list(error_counts.values())
        }
        
        # Dados temporais
        sorted_dates = sorted(errors_by_time.keys())
        temporal_data = {
            "labels": [str(date) for date in sorted_dates],
            "values": [errors_by_time[date] for date in sorted_dates]
        }
        
        # Dados por severidade
        severity_data = {
            "labels": list(severity_counts.keys()),
            "values": list(severity_counts.values())
        }
        
        # Distribuição por hora
        hours = sorted(hourly_distribution.keys())
        hourly_data = {
            "labels": [f"{hour:02d}:00" for hour in hours],
            "values": [hourly_distribution[hour] for hour in hours]
        }
        
        return {
            "error_types": error_types_data,
            "temporal": temporal_data,
            "severity": severity_data,
            "hourly": hourly_data
        }

    def _detect_new_errors(self, lines: List[str], existing_regex) -> Dict[str, Any]:
        """Detecta possíveis novos erros que não foram capturados pelos padrões existentes."""
        
        # Palavras-chave suspeitas que podem indicar erros
        suspicious_keywords = [
            'fail', 'abort', 'crash', 'panic', 'corrupt', 'invalid', 'illegal',
            'refused', 'denied', 'forbidden', 'unavailable', 'unreachable',
            'overflow', 'underflow', 'violation', 'breach', 'leak',
            'hang', 'freeze', 'stuck', 'slow', 'degraded',
            'miss', 'lost', 'drop', 'reject', 'discard',
            'retry', 'backoff', 'circuit', 'breaker',
            'quota', 'limit', 'exceed', 'maximum', 'minimum',
            'bad', 'wrong', 'incorrect', 'mismatch', 'conflict'
        ]
        
        potential_errors = []
        suspicious_patterns = Counter()
        word_frequency = Counter()
        
        for line_num, line in enumerate(lines, start=1):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Skip linhas que já foram capturadas pelos padrões existentes
            if existing_regex.search(line_clean):
                continue
            
            # Verificar se contém palavras-chave suspeitas
            line_lower = line_clean.lower()
            suspicious_words_found = []
            
            for keyword in suspicious_keywords:
                if keyword in line_lower:
                    suspicious_words_found.append(keyword)
                    word_frequency[keyword] += 1
            
            # Se encontrou palavras suspeitas, pode ser um novo tipo de erro
            if suspicious_words_found:
                # Extrair possível padrão (primeiras 3-5 palavras significativas)
                words = line_clean.split()
                pattern_words = []
                for word in words[:7]:  # Pegar até 7 palavras
                    # Filtrar timestamps e números
                    if not re.match(r'^\d{2,4}[-/]\d{1,2}[-/]\d{1,4}', word) and \
                       not re.match(r'^\d{1,2}:\d{2}', word) and \
                       len(word) > 2:
                        pattern_words.append(word)
                    if len(pattern_words) >= 4:
                        break
                
                suggested_pattern = ' '.join(pattern_words[:4])
                if len(suggested_pattern) > 5:  # Padrão deve ter pelo menos 5 caracteres
                    suspicious_patterns[suggested_pattern] += 1
                
                potential_error = {
                    "line": line_num,
                    "message": line_clean[:200] + "..." if len(line_clean) > 200 else line_clean,
                    "suspicious_words": suspicious_words_found,
                    "suggested_pattern": suggested_pattern,
                    "confidence": self._calculate_error_confidence(line_clean, suspicious_words_found)
                }
                potential_errors.append(potential_error)
        
        # Encontrar padrões mais frequentes para sugestões
        pattern_suggestions = []
        for pattern, count in suspicious_patterns.most_common(10):
            if count >= 2:  # Só sugerir padrões que aparecem pelo menos 2 vezes
                pattern_suggestions.append({
                    "pattern": pattern,
                    "frequency": count,
                    "suggested_regex": self._generate_regex_suggestion(pattern)
                })
        
        # Análise de palavras mais frequentes
        frequent_words = [
            {"word": word, "count": count} 
            for word, count in word_frequency.most_common(15)
            if count >= 2
        ]
        
        return {
            "potential_errors": potential_errors[:50],  # Limitar a 50 para performance
            "pattern_suggestions": pattern_suggestions,
            "frequent_suspicious_words": frequent_words,
            "total_potential_errors": len(potential_errors),
            "analysis_coverage": {
                "lines_analyzed": len(lines),
                "lines_with_known_patterns": sum(1 for line in lines if existing_regex.search(line)),
                "lines_with_potential_new_errors": len(potential_errors)
            }
        }
    
    def _calculate_error_confidence(self, line: str, suspicious_words: List[str]) -> str:
        """Calcula o nível de confiança de que a linha representa um erro."""
        score = 0
        
        # Mais pontos para certas palavras críticas
        critical_words = ['error', 'fail', 'crash', 'abort', 'panic', 'corrupt']
        for word in suspicious_words:
            if word in critical_words:
                score += 3
            else:
                score += 1
        
        # Mais pontos se contém códigos de erro ou números
        if re.search(r'\b\d{3,4}\b', line):  # Códigos como 404, 500, 1793
            score += 2
        
        # Mais pontos se está em maiúsculo (indicativo de log level)
        if re.search(r'\b[A-Z]{4,}\b', line):
            score += 1
        
        if score >= 5:
            return "Alto"
        elif score >= 3:
            return "Médio"
        else:
            return "Baixo"
    
    def _generate_regex_suggestion(self, pattern: str) -> str:
        """Gera uma sugestão de regex baseada no padrão encontrado."""
        # Escapar caracteres especiais e criar regex básico
        escaped = re.escape(pattern)
        # Permitir variações em números e algumas palavras
        regex_suggestion = escaped.replace(r'\ ', r'\s+')  # Permitir múltiplos espaços
        regex_suggestion = re.sub(r'\\?\d+', r'\\d+', regex_suggestion)  # Generalizar números
        
        return regex_suggestion

    def generate_csv_content(self, results: List[Dict]) -> str:
        """Gera conteúdo CSV dos resultados com campos expandidos."""
        if not results:
            return "linha,timestamp,tipo_erro,severidade,mensagem,descricao,solucao,tag\n"
        
        output = io.StringIO()
        
        # Campos expandidos incluindo informações Datasul
        fieldnames = ["linha", "timestamp", "tipo_erro", "severidade", "mensagem", "descricao", "solucao", "tag"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        
        # Header em português
        writer.writeheader()
        
        # Processar cada resultado
        for result in results:
            csv_row = {
                "linha": result.get("line", ""),
                "timestamp": result.get("timestamp", ""),
                "tipo_erro": result.get("error_type", ""),
                "severidade": result.get("severity", ""),
                "mensagem": result.get("message", ""),
                "descricao": result.get("description", ""),
                "solucao": result.get("solution", ""),
                "tag": result.get("tag", "")
            }
            writer.writerow(csv_row)
        
        return output.getvalue()
    
    def add_custom_pattern(self, pattern: str):
        """Adiciona um novo padrão personalizado à lista."""
        if pattern and pattern not in self.custom_patterns:
            self.custom_patterns.append(pattern)
            self.recompile_patterns()  # Recompilar padrões para busca parcial
            logger.info(f"Custom pattern added: {pattern}")
    
    def remove_custom_pattern(self, pattern: str):
        """Remove um padrão personalizado da lista."""
        if pattern in self.custom_patterns:
            self.custom_patterns.remove(pattern)
            self.recompile_patterns()  # Recompilar padrões para busca parcial
            logger.info(f"Custom pattern removed: {pattern}")
    
    def get_custom_patterns(self):
        """Retorna a lista de padrões personalizados."""
        return self.custom_patterns.copy()

    def _load_custom_patterns_from_local_store(self):
        fallback_patterns = list_records(
            "custom_patterns",
            {"active": True},
            sort_field="created_at",
            descending=True,
            limit=1000,
        )
        self.custom_patterns = [pattern.get("pattern", "") for pattern in fallback_patterns if pattern.get("pattern")]
        self.recompile_patterns()
        logger.info(f"Loaded {len(self.custom_patterns)} custom patterns from local fallback store")
    
    async def load_custom_patterns_from_db(self, db):
        """Carrega padrões personalizados do banco de dados."""
        if db is None:
            self._load_custom_patterns_from_local_store()
            return

        try:
            patterns = await db.custom_patterns.find({"active": True}).to_list(1000)
            self.custom_patterns = [pattern["pattern"] for pattern in patterns]
            self.recompile_patterns()  # Recompilar padrões para busca parcial
            logger.info(f"Loaded {len(self.custom_patterns)} custom patterns from database")
        except Exception as e:
            logger.error(f"Error loading custom patterns from database: {e}")
            self._load_custom_patterns_from_local_store()