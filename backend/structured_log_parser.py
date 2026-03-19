#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser de logs estruturados integrado ao analisador Datasul existente
Suporta: Apache/Tomcat access, JBoss/Fluig Java logs, Progress/OpenEdge
Baseado na lógica fornecida pelo usuário, integrado com análise de padrões existente
"""

import re
import json
from datetime import datetime
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Dict, List, Any, Optional, Tuple, Generator
import logging

logger = logging.getLogger(__name__)

PROGRESS_TIMESTAMP_TOKEN_RE = re.compile(r'^\d{2}/\d{2}/\d{2}@\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{4}$')
PROGRESS_TABANALYS_HINTS = ("factor", "table scan", "whole-index", "index ", "tabanalys")
PROGRESS_XREF_HINTS = ("xref", "include file", "caller", "callee", "cross-reference", "compile listing")

class StructuredLogParser:
    """Parser de logs estruturados que mantém compatibilidade com análise Datasul existente"""
    
    def __init__(self):
        self.setup_regex_patterns()
        self.reset_statistics()
    
    def setup_regex_patterns(self):
        """Configura padrões regex para detecção de diferentes tipos de log"""
        
        # Apache/Tomcat access: 10.80.73.148 - - [08/Sep/2017:11:24:44 -0300] "GET /path HTTP/1.1" 200 25363
        self.RX_ACCESS = re.compile(
            r'(?P<ip>\S+) \S+ \S+ \[(?P<ts>[^\]]+)\] '
            r'"(?P<method>\S+)\s+(?P<path>\S+)(?:\s+HTTP/\d\.\d)?"\s+'
            r'(?P<status>\d{3})\s+(?P<size>\d+|-)',
            re.ASCII
        )
        
        # JBoss/Tomcat/Fluig (Java log style): 2018-08-24 00:00:01,015 ERROR [logger] message
        self.RX_JAVA_LINE = re.compile(
            r'(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s+'
            r'(?P<level>[A-Z]+)\s+\[(?P<logger>[^\]]+)\]\s*(?P<msg>.*)$'
        )
        
        # Tomcat JUL style: 08-Sep-2017 07:58:03.282 INFO [main] org.apache... Message
        self.RX_TOMCAT_JUL = re.compile(
            r'(?P<ts>\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+'
            r'(?P<level>[A-Z]+)\s+\[(?P<thread>[^\]]+)\]\s+(?P<logger>\S+)\s+(?P<msg>.*)$'
        )
        
        # Fluig com hora apenas: 09:00:00,225 INFO [xxx] msg
        self.RX_HH_ONLY = re.compile(
            r'(?P<ts>\d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>[A-Z]+)\s+\[(?P<logger>[^\]]+)\]\s*(?P<msg>.*)$'
        )
        
        # Progress/OpenEdge: [17/10/21@14:24:44.926-0200] P-018036 T-015544 1 4GL ...
        self.RX_PROGRESS = re.compile(
            r'\[(?P<ts>\d{2}/\d{2}/\d{2}@\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{4})\]\s+'
            r'P-(?P<pid>\d+)\s+T-(?P<tid>\d+)\s+(?P<levelnum>\d+)\s+(?P<comp>[A-Z]+)\s+-?\s*(?P<msg>.*)$'
        )
        
        # Progress simples sem componente: [25/09/25@10:45:34.525-0300] P-033484 T-015236 1 message
        self.RX_PROGRESS_SIMPLE = re.compile(
            r'\[(?P<ts>\d{2}/\d{2}/\d{2}@\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{4})\]\s+'
            r'P-(?P<pid>\d+)\s+T-(?P<tid>\d+)\s+(?P<levelnum>\d+)\s+(?P<msg>.*)$'
        )

        # Progress/AppBroker sem nível explícito: [25/11/24@10:22:09.922-0300] P-002448 T-013056 Broker started
        self.RX_PROGRESS_PROCESS = re.compile(
            r'\[(?P<ts>\d{2}/\d{2}/\d{2}@\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{4})\]\s+'
            r'P-(?P<pid>\d+)\s+T-(?P<tid>\d+)\s+(?P<msg>.*)$'
        )

        # PASOE/Tomcat com timestamp Progress e mensagem livre: [25/11/24@10:22:09.922-0300] SEVERE: Exception...
        self.RX_PROGRESS_TIMESTAMPED = re.compile(
            r'\[(?P<ts>\d{2}/\d{2}/\d{2}@\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{4})\]\s+(?P<msg>.*)$'
        )

        # Progress Tabanalys em linha bruta (resumo de tabela/índice)
        self.RX_TABANALYS_TABLE_RAW = re.compile(
            r'^(?P<table>[A-Za-z_][\w$-]+)\s+(?P<records>\d+)\s+.*?(?P<factor>\d{2,4})\s*$'
        )
        self.RX_TABANALYS_INDEX_RAW = re.compile(
            r'^\s+(?P<index>[A-Za-z_][\w$-]+)\s+.*?(?P<fields>\d+)\s+.*?(?P<factor>\d{2,4})\s*$'
        )

        # LOGIX/TOTVS
        self.RX_LOGIX_THREAD = re.compile(
            r'^\[THREAD\s+(?P<thread>[^\]]+)\]\s*(?:\[(?P<level>[A-Z\s]+)\])?\s*(?:\[(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\])?\s*(?P<msg>.*)$',
            re.IGNORECASE
        )
        self.RX_LOGIX_TIMESTAMP = re.compile(
            r'^\[(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*(?P<msg>.*)$'
        )

        # Protheus / ADVPL error.log
        self.RX_PROTHEUS_THREAD_ERROR = re.compile(
            r'^THREAD ERROR \(\[(?P<thread>\d+)\],\s*(?P<user>[^,]*),\s*(?P<session>[^)]*)\)\s+(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<time>\d{2}:\d{2}:\d{2})$',
            re.IGNORECASE
        )
        self.RX_PROTHEUS_RUNTIME = re.compile(
            r'^(?P<error>(?:Cannot find method|variable does not exist|Invalid ReadMSInt|Failed to read status of inifile|MULTIPORT - error \d+ unrecognized client|OPEN EMPTY RPO|.*fail to open:).*)$',
            re.IGNORECASE
        )
        self.RX_PROTHEUS_SERVER = re.compile(
            r'^\[(?P<level>INFO|WARN|ERROR|FATAL)\s*\]\[(?P<component>[A-Z]+)\]\s*(?P<msg>.*)$',
            re.IGNORECASE
        )
        self.RX_PROTHEUS_CALLED_FROM = re.compile(
            r'^Called from\s+(?P<routine>[^\(]+)\((?P<source>[^)]+)\).*line\s*:\s*(?P<line>\d+)$',
            re.IGNORECASE
        )
    
    def reset_statistics(self):
        """Reinicia estatísticas para nova análise"""
        self.stats = {
            'total_events': 0,
            'by_type': Counter(),
            'by_subtype': Counter(),
            'by_category': Counter(),
            'http_status': Counter(),
            'java_levels': Counter(),
            'progress_levels': Counter(),
            'exceptions': Counter(),
            'error_patterns': Counter(),
            'temporal_distribution': defaultdict(int)
        }

    def _normalize_log_family_hint(self, preferred_log_type: Optional[str]) -> Optional[str]:
        """Normaliza o tipo detectado para selecionar apenas parsers compatíveis."""
        if not preferred_log_type:
            return None

        normalized = preferred_log_type.strip().lower()

        if normalized == "acesso":
            return "access"

        if normalized in {"jboss", "tomcat", "fluig"}:
            return "java"

        if normalized == "logix":
            return "logix_progress"

        if normalized in {"datasul", "appserver", "smartclient", "pasoe", "progress/openedge", "totvs"}:
            return "progress"

        if normalized in {"protheus/advpl", "protheus", "advpl"}:
            return "protheus"

        return None

    def _get_candidate_parsers(self, preferred_log_type: Optional[str] = None):
        """Retorna apenas os parsers relevantes para a família de log detectada."""
        normalized_hint = self._normalize_log_family_hint(preferred_log_type)

        all_parsers = [
            ("access", self.parse_access_log),
            ("logix", self.parse_logix_log),
            ("protheus", self.parse_protheus_log),
            ("progress", self.parse_progress_tabanalys_log),
            ("progress", self.parse_progress_xref_log),
            ("java", self.parse_java_log),
            ("progress", self.parse_progress_log)
        ]

        if normalized_hint == "access":
            return [("access", self.parse_access_log)]

        if normalized_hint == "java":
            return [("java", self.parse_java_log)]

        if normalized_hint == "progress":
            return [
                ("progress", self.parse_progress_tabanalys_log),
                ("progress", self.parse_progress_xref_log),
                ("progress", self.parse_progress_log)
            ]

        if normalized_hint == "protheus":
            return [
                ("protheus", self.parse_protheus_log),
                ("progress", self.parse_progress_tabanalys_log),
                ("progress", self.parse_progress_xref_log),
                ("progress", self.parse_progress_log)
            ]

        if normalized_hint == "logix_progress":
            return [
                ("logix", self.parse_logix_log),
                ("protheus", self.parse_protheus_log),
                ("progress", self.parse_progress_tabanalys_log),
                ("progress", self.parse_progress_xref_log),
                ("progress", self.parse_progress_log)
            ]

        return all_parsers

    def _parse_protheus_timestamp(self, date_part: str, time_part: str) -> Optional[str]:
        try:
            return datetime.strptime(f"{date_part} {time_part}", "%d/%m/%Y %H:%M:%S").isoformat()
        except Exception:
            return None

    def _categorize_protheus_message(self, message: str) -> str:
        lower_message = (message or "").lower()

        if "variable does not exist" in lower_message or "cannot find method" in lower_message:
            return "application"
        if "invalid readmsint" in lower_message:
            return "memory"
        if "fail to open" in lower_message or "failed to read status of inifile" in lower_message or "open empty rpo" in lower_message:
            return "configuration"
        if "unrecognized client" in lower_message or "multiport" in lower_message:
            return "connectivity"
        if "dominio nao encontrado" in lower_message or "domínio não encontrado" in lower_message:
            return "security"
        return "application"

    def _determine_protheus_severity(self, level: str, category: str, message: str) -> str:
        level_upper = (level or "").upper()
        lower_message = (message or "").lower()

        if level_upper == "FATAL" or "thread error" in lower_message or "invalid readmsint" in lower_message:
            return "Crítico"
        if level_upper == "ERROR" or category in {"application", "configuration", "connectivity"}:
            return "Alto"
        if level_upper == "WARN" or category == "security":
            return "Médio"
        return "Baixo"

    def _build_protheus_context(self, message: str, category: str) -> Tuple[Dict[str, Any], List[str], str]:
        lower_message = (message or "").lower()
        domain_fields: Dict[str, Any] = {}
        insight_tags: List[str] = ["protheus", "advpl"]
        recommendation_hint = "review_protheus_runtime"

        variable_match = re.search(r'variable does not exist\s+(?P<variable>[A-Z0-9_]+)', message, re.IGNORECASE)
        if variable_match:
            domain_fields["missing_variable"] = variable_match.group("variable")
            insight_tags.append("missing_variable")
            recommendation_hint = "review_advpl_dictionary_or_customization"

        method_match = re.search(r'Cannot find method\s+(?P<class_name>[A-Z0-9_:.]+):(?P<method_name>[A-Z0-9_]+)', message, re.IGNORECASE)
        if method_match:
            domain_fields["class_name"] = method_match.group("class_name")
            domain_fields["method_name"] = method_match.group("method_name")
            insight_tags.append("missing_method")
            recommendation_hint = "review_rpo_framework_compatibility"

        source_match = re.search(r'on\s+(?P<routine>[^\(]+)\((?P<source>[^)]+)\).*line\s*:\s*(?P<line>\d+)', message, re.IGNORECASE)
        if source_match:
            domain_fields["source_routine"] = source_match.group("routine").strip()
            domain_fields["source_file"] = source_match.group("source")
            domain_fields["source_line"] = int(source_match.group("line"))

        code_match = re.search(r'\b([A-Z]{3}\d{4})\b', message)
        if code_match:
            domain_fields["error_code"] = code_match.group(1)

        if "failed to read status of inifile" in lower_message or "fail to open" in lower_message:
            file_match = re.search(r'(/[^\]\[]+|[A-Za-z]:\\[^\]\[]+\.(?:ini|tsk|rpo))', message)
            if file_match:
                domain_fields["missing_file"] = file_match.group(1)
            insight_tags.append("missing_file")
            recommendation_hint = "review_appserver_files_and_mounts"

        if "open empty rpo" in lower_message:
            insight_tags.append("empty_rpo")
            recommendation_hint = "review_rpo_deployment"

        if "unrecognized client" in lower_message:
            client_match = re.search(r'\b(BPC\d{4})\b', message)
            if client_match:
                domain_fields["error_code"] = client_match.group(1)
            insight_tags.append("invalid_client_protocol")
            recommendation_hint = "review_multi_protocol_port_routing"

        if "invalid readmsint" in lower_message:
            insight_tags.append("memory_stream")
            recommendation_hint = "review_framework_build_and_remote_session"

        if category == "security":
            insight_tags.append("identity")
            recommendation_hint = "review_identity_or_webagent_configuration"

        return domain_fields, self._dedupe_tags(insight_tags), recommendation_hint
    
    def parse_timestamp(self, ts_str: str) -> str:
        """Converte timestamp para formato ISO"""
        return self._parse_timestamp_cached(ts_str)

    @staticmethod
    @lru_cache(maxsize=65536)
    def _parse_timestamp_cached(ts_str: str) -> str:
        if PROGRESS_TIMESTAMP_TOKEN_RE.match(ts_str):
            date_part, time_part = ts_str.split('@', 1)
            year, month, day = date_part.split('/')
            clock_part, timezone = time_part[:-5], time_part[-5:]
            hour, minute, seconds_fraction = clock_part.split(':', 2)
            second, fraction = seconds_fraction.split('.', 1)
            microseconds = fraction.ljust(6, '0')[:6]
            return f"20{year}-{month}-{day}T{hour}:{minute}:{second}.{microseconds}{timezone[:3]}:{timezone[3:]}"

        timestamp_formats = [
            "%d/%b/%Y:%H:%M:%S %z",        # Apache access [08/Sep/2017:11:24:44 -0300]
            "%Y-%m-%d %H:%M:%S,%f",        # Java com data
            "%Y-%m-%d %H:%M:%S",           # Java sem milissegundos
            "%d-%b-%Y %H:%M:%S.%f",        # Tomcat JUL
            "%H:%M:%S,%f",                 # Hora apenas (Fluig)
            "%y/%m/%d@%H:%M:%S.%f%z"       # Progress/OpenEdge
        ]
        
        for fmt in timestamp_formats:
            try:
                return datetime.strptime(ts_str, fmt).isoformat()
            except Exception:
                pass
        return ts_str  # Retorna original se não conseguir parsear
    
    def parse_access_log(self, line: str) -> Optional[Dict]:
        """Parseia logs de acesso Apache/Tomcat"""
        match = self.RX_ACCESS.search(line)
        if not match:
            return None
        
        data = match.groupdict()
        status_code = int(data["status"])
        category = self._categorize_access_status(status_code)
        legacy_mapping = self._map_legacy_progress_source("acesso")
        domain_fields, insight_tags, recommendation_hint = self._build_access_context(data, status_code)
        data.update({
            "log_type": "access",
            "structured_type": "http_access",
            "log_subtype": "acesso",
            "timestamp_parsed": self.parse_timestamp(data.pop("ts")),
            "status_code": status_code,
            "response_size": 0 if data["size"] == "-" else int(data["size"]),
            "is_error": status_code >= 400,
            "severity": self._determine_http_severity(status_code),
            "category": category,
            "clean_message": f"{data['method']} {data['path']} -> HTTP {status_code}",
            "error_signature": f"HTTP_{status_code}",
            "domain_fields": domain_fields,
            "insight_tags": insight_tags,
            "recommendation_hint": recommendation_hint
        })
        data.update(legacy_mapping)
        
        self.stats['http_status'][status_code] += 1
        return data
    
    def parse_java_log(self, line: str) -> Optional[Dict]:
        """Parseia logs Java (JBoss/Fluig/Tomcat)"""
        # Tentar diferentes padrões Java
        for pattern, pattern_name in [
            (self.RX_JAVA_LINE, "java_standard"),
            (self.RX_TOMCAT_JUL, "tomcat_jul"),
            (self.RX_HH_ONLY, "time_only")
        ]:
            match = pattern.match(line)
            if match:
                data = match.groupdict()
                level = data["level"]
                message = data.get("msg", "")
                subtype = self._detect_java_subtype(line, data)
                category = self._categorize_java_message(line, data)
                is_error = level in ["ERROR", "FATAL", "SEVERE"] or self._looks_like_error(message)
                legacy_mapping = self._map_legacy_progress_source(subtype)
                domain_fields, insight_tags, recommendation_hint = self._build_java_domain_context(subtype, data, message, category)
                data.update({
                    "log_type": "java",
                    "structured_type": pattern_name,
                    "log_subtype": subtype,
                    "timestamp_parsed": self.parse_timestamp(data.pop("ts")),
                    "is_error": is_error,
                    "is_warning": level == "WARN",
                    "severity": self._determine_java_severity(level),
                    "category": category,
                    "clean_message": message,
                    "error_signature": self._build_error_signature(subtype, category, message),
                    "domain_fields": domain_fields,
                    "insight_tags": insight_tags,
                    "recommendation_hint": recommendation_hint
                })
                data.update(legacy_mapping)
                
                # Detectar exceções Java
                exception = self._extract_java_exception(message)
                if exception:
                    data["exception_class"] = exception
                    self.stats['exceptions'][exception] += 1
                
                self.stats['java_levels'][level] += 1
                return data
        
        return None

    def parse_progress_tabanalys_log(self, line: str) -> Optional[Dict]:
        """Parse dedicado para Progress Tabanalys."""
        stripped_line = line.strip()
        lower_line = stripped_line.lower()

        if stripped_line.startswith('[') and not any(token in lower_line for token in PROGRESS_TABANALYS_HINTS):
            return None

        progress_match, variant = self._match_progress_variants(line)

        if progress_match:
            data = progress_match.groupdict()
            message = data.get("msg", "")
            extracted = self._extract_tabanalys_fields(message)
            if not extracted:
                return None

            level_raw = data.get("levelnum")
            level_num = int(level_raw) if level_raw and str(level_raw).isdigit() else self._infer_progress_level(message)
            legacy_mapping = self._map_legacy_progress_source("progress_tabanalys")
            factor_value = extracted.get("factor")
            severity = self._determine_tabanalys_severity(level_num, factor_value)
            recommendation_hint = self._recommend_tabanalys_action(extracted)
            insight_tags = self._build_tabanalys_tags(extracted)

            event = {
                **data,
                "log_type": "progress",
                "structured_type": "progress_tabanalys",
                "progress_variant": variant,
                "log_subtype": "progress_tabanalys",
                "timestamp_parsed": self.parse_timestamp(data.pop("ts")),
                "process_id": int(data["pid"]) if data.get("pid") else None,
                "thread_id": data.get("tid"),
                "level_numeric": level_num,
                "is_error": bool(level_num >= 3 or (factor_value is not None and factor_value >= 1.5)),
                "severity": severity,
                "category": "table_analysis",
                "clean_message": message,
                "error_signature": self._build_error_signature("progress_tabanalys", "table_analysis", message),
                "domain_fields": extracted,
                "insight_tags": insight_tags,
                "recommendation_hint": recommendation_hint
            }
            event.update(legacy_mapping)
            self.stats['progress_levels'][level_num] += 1
            return event

        compressed = re.sub(r'\s+', ' ', line.rstrip())
        raw_data = self._extract_tabanalys_raw_fields(line, compressed)
        if not raw_data:
            return None

        event = {
            "log_type": "progress",
            "structured_type": "progress_tabanalys_raw",
            "log_subtype": "progress_tabanalys",
            "timestamp_parsed": None,
            "process_id": None,
            "thread_id": None,
            "level_numeric": 2,
            "is_error": bool((raw_data.get("factor") or 0) >= 1.5),
            "severity": self._determine_tabanalys_severity(2, raw_data.get("factor")),
            "category": "table_analysis",
            "clean_message": compressed,
            "error_signature": self._build_error_signature("progress_tabanalys", "table_analysis", compressed),
            "domain_fields": raw_data,
            "insight_tags": self._build_tabanalys_tags(raw_data),
            "recommendation_hint": self._recommend_tabanalys_action(raw_data)
        }
        event.update(self._map_legacy_progress_source("progress_tabanalys"))
        self.stats['progress_levels'][2] += 1
        return event

    def parse_progress_xref_log(self, line: str) -> Optional[Dict]:
        """Parse dedicado para Progress XREF."""
        stripped_line = line.strip()
        lower_line = stripped_line.lower()

        if stripped_line.startswith('[') and not any(token in lower_line for token in PROGRESS_XREF_HINTS):
            return None

        progress_match, variant = self._match_progress_variants(line)

        if progress_match:
            data = progress_match.groupdict()
            message = data.get("msg", "")
            extracted = self._extract_xref_fields_from_message(message)
            if not extracted:
                return None

            level_raw = data.get("levelnum")
            level_num = int(level_raw) if level_raw and str(level_raw).isdigit() else self._infer_progress_level(message)
            legacy_mapping = self._map_legacy_progress_source("progress_xref")
            severity = self._determine_xref_severity(extracted)

            event = {
                **data,
                "log_type": "progress",
                "structured_type": "progress_xref",
                "progress_variant": variant,
                "log_subtype": "progress_xref",
                "timestamp_parsed": self.parse_timestamp(data.pop("ts")),
                "process_id": int(data["pid"]) if data.get("pid") else None,
                "thread_id": data.get("tid"),
                "level_numeric": level_num,
                "is_error": extracted.get("full_scan") or extracted.get("global_flag") or extracted.get("shared_flag") or False,
                "severity": severity,
                "category": "xref",
                "clean_message": message,
                "error_signature": self._build_error_signature("progress_xref", "xref", message),
                "domain_fields": extracted,
                "insight_tags": self._build_xref_tags(extracted),
                "recommendation_hint": self._recommend_xref_action(extracted)
            }
            event.update(legacy_mapping)
            self.stats['progress_levels'][level_num] += 1
            return event

        extracted = self._extract_xref_fields_from_raw_line(line)
        if not extracted:
            return None

        event = {
            "log_type": "progress",
            "structured_type": "progress_xref_raw",
            "log_subtype": "progress_xref",
            "timestamp_parsed": None,
            "process_id": None,
            "thread_id": None,
            "level_numeric": 2,
            "is_error": extracted.get("full_scan") or extracted.get("global_flag") or extracted.get("shared_flag") or False,
            "severity": self._determine_xref_severity(extracted),
            "category": "xref",
            "clean_message": line.strip(),
            "error_signature": self._build_error_signature("progress_xref", "xref", line.strip()),
            "domain_fields": extracted,
            "insight_tags": self._build_xref_tags(extracted),
            "recommendation_hint": self._recommend_xref_action(extracted)
        }
        event.update(self._map_legacy_progress_source("progress_xref"))
        self.stats['progress_levels'][2] += 1
        return event

    def parse_logix_log(self, line: str) -> Optional[Dict]:
        """Parse dedicado para LOGIX/TOTVS."""
        match = self.RX_LOGIX_THREAD.match(line)
        structured_type = "logix_thread"

        if not match:
            match = self.RX_LOGIX_TIMESTAMP.match(line)
            structured_type = "logix_timestamped"

        if not match:
            return None

        data = match.groupdict()
        message = (data.get("msg") or "").strip()
        combined_text = f"{line} {message}"
        if not self._looks_like_logix(combined_text):
            return None

        subtype = "logix"
        category = self._categorize_logix_message(message)
        domain_fields, insight_tags, recommendation_hint = self._build_logix_domain_context(data, message, category)
        level = (data.get("level") or "").strip().upper() if data.get("level") else ""
        is_error = (
            self._looks_like_error(message)
            or level in ["ERROR", "WARN"]
            or bool(domain_fields.get("status_code") not in [None, 0])
            or bool(domain_fields.get("command_type"))
            or category in ["validation", "integration", "license"]
        )
        severity = self._determine_logix_severity(level, category, domain_fields, message)
        event = {
            **data,
            "log_type": "logix",
            "structured_type": structured_type,
            "log_subtype": subtype,
            "timestamp_parsed": self.parse_timestamp(data["ts"]) if data.get("ts") else None,
            "is_error": is_error,
            "severity": severity,
            "category": category,
            "clean_message": message,
            "error_signature": self._build_error_signature(subtype, category, message),
            "domain_fields": domain_fields,
            "insight_tags": insight_tags,
            "recommendation_hint": recommendation_hint,
            "legacy_parser": "LogAnalysLogix.i",
            "legacy_group": "logix"
        }

        if level:
            event["level"] = level

        return event

    def parse_protheus_log(self, line: str) -> Optional[Dict]:
        """Parse dedicado para error.log do Protheus / ADVPL."""
        match = self.RX_PROTHEUS_THREAD_ERROR.match(line)
        if match:
            data = match.groupdict()
            message = line.strip()
            domain_fields, insight_tags, recommendation_hint = self._build_protheus_context(message, "application")
            domain_fields.update({
                "thread_id": int(data["thread"]),
                "user": data.get("user", "").strip() or None,
                "session": data.get("session", "").strip() or None,
            })
            return {
                **data,
                "log_type": "protheus",
                "structured_type": "protheus_thread_error",
                "log_subtype": "protheus_advpl",
                "timestamp_parsed": self._parse_protheus_timestamp(data["date"], data["time"]),
                "is_error": True,
                "severity": "Crítico",
                "category": "application",
                "clean_message": message,
                "error_signature": "PROTHEUS_THREAD_ERROR",
                "domain_fields": domain_fields,
                "insight_tags": insight_tags,
                "recommendation_hint": recommendation_hint,
                "legacy_parser": "error.log",
                "legacy_group": "protheus"
            }

        match = self.RX_PROTHEUS_SERVER.match(line)
        if match:
            data = match.groupdict()
            message = (data.get("msg") or "").strip()
            if not self.RX_PROTHEUS_RUNTIME.match(message) and not re.search(r'dominio nao encontrado|domínio não encontrado|domain .*not found', message, re.IGNORECASE):
                return None

            category = self._categorize_protheus_message(message)
            domain_fields, insight_tags, recommendation_hint = self._build_protheus_context(message, category)
            return {
                **data,
                "log_type": "protheus",
                "structured_type": "protheus_server_line",
                "log_subtype": "protheus_advpl",
                "timestamp_parsed": None,
                "is_error": data.get("level", "").upper() in {"ERROR", "FATAL", "WARN"},
                "severity": self._determine_protheus_severity(data.get("level", ""), category, message),
                "category": category,
                "clean_message": message,
                "error_signature": self._build_error_signature("protheus_advpl", category, message),
                "domain_fields": domain_fields,
                "insight_tags": insight_tags,
                "recommendation_hint": recommendation_hint,
                "legacy_parser": "error.log",
                "legacy_group": "protheus"
            }

        match = self.RX_PROTHEUS_RUNTIME.match(line)
        if match:
            message = match.group("error").strip()
            category = self._categorize_protheus_message(message)
            domain_fields, insight_tags, recommendation_hint = self._build_protheus_context(message, category)
            return {
                "log_type": "protheus",
                "structured_type": "protheus_runtime_error",
                "log_subtype": "protheus_advpl",
                "timestamp_parsed": None,
                "is_error": True,
                "severity": self._determine_protheus_severity("ERROR", category, message),
                "category": category,
                "clean_message": message,
                "error_signature": self._build_error_signature("protheus_advpl", category, message, domain_fields.get("error_code")),
                "domain_fields": domain_fields,
                "insight_tags": insight_tags,
                "recommendation_hint": recommendation_hint,
                "legacy_parser": "error.log",
                "legacy_group": "protheus"
            }

        match = self.RX_PROTHEUS_CALLED_FROM.match(line)
        if match:
            data = match.groupdict()
            return {
                **data,
                "log_type": "protheus",
                "structured_type": "protheus_stack_frame",
                "log_subtype": "protheus_advpl",
                "timestamp_parsed": None,
                "is_error": False,
                "severity": "Info",
                "category": "application",
                "clean_message": line.strip(),
                "error_signature": self._build_error_signature("protheus_advpl", "application", line.strip()),
                "domain_fields": {
                    "source_routine": data.get("routine", "").strip(),
                    "source_file": data.get("source"),
                    "source_line": int(data.get("line")) if data.get("line") else None,
                },
                "insight_tags": ["stack_frame", "protheus", "advpl"],
                "recommendation_hint": "review_advpl_call_stack",
                "legacy_parser": "error.log",
                "legacy_group": "protheus"
            }

        return None
    
    def parse_progress_log(self, line: str) -> Optional[Dict]:
        """Parseia logs Progress/OpenEdge"""
        match, variant = self._match_progress_variants(line)
        
        if not match:
            return None
        
        data = match.groupdict()
        message = data.get("msg", "")
        level_raw = data.get("levelnum")
        level_num = int(level_raw) if level_raw and str(level_raw).isdigit() else self._infer_progress_level(message)
        subtype = self._detect_progress_subtype(line, data)
        category = self._categorize_progress_message(line, data, subtype)
        error_code = self._extract_error_code(message)
        program_path = self._extract_program_path(message)
        database_name = self._extract_database_name(message)
        is_error = level_num >= 3 or self._looks_like_error(message) or bool(error_code)
        legacy_mapping = self._map_legacy_progress_source(subtype)
        domain_fields, insight_tags, recommendation_hint = self._build_progress_domain_context(
            subtype,
            data,
            message,
            category,
            error_code,
            program_path,
            database_name
        )
        
        data.update({
            "log_type": "progress",
            "structured_type": "openedge",
            "progress_variant": variant,
            "log_subtype": subtype,
            "timestamp_parsed": self.parse_timestamp(data.pop("ts")),
            "process_id": int(data["pid"]) if data.get("pid") else None,
            "thread_id": data.get("tid"),
            "level_numeric": level_num,
            "is_error": is_error,
            "severity": self._determine_progress_severity(level_num, subtype, category, message),
            "category": category,
            "clean_message": message,
            "error_code": error_code,
            "program_path": program_path,
            "database_name": database_name,
            "error_signature": self._build_error_signature(subtype, category, message, error_code),
            "domain_fields": domain_fields,
            "insight_tags": insight_tags,
            "recommendation_hint": recommendation_hint
        })
        data.update(legacy_mapping)
        
        self.stats['progress_levels'][level_num] += 1
        return data
    
    def parse_line(self, line: str, line_number: int = 0, preferred_log_type: Optional[str] = None) -> Dict:
        """Parseia uma linha detectando automaticamente o tipo"""
        line = line.strip()
        if not line:
            return {"log_type": "empty", "original_line": line, "line_number": line_number}
        
        # Quando o tipo do log já é conhecido, evita testar parsers irrelevantes em toda linha.
        parsers = self._get_candidate_parsers(preferred_log_type)
        
        for parser_type, parser_func in parsers:
            result = parser_func(line)
            if result:
                result.update({
                    "original_line": line,
                    "line_number": line_number,
                    "parsed_successfully": True
                })
                self.stats['by_type'][parser_type] += 1
                if result.get("log_subtype"):
                    self.stats['by_subtype'][result["log_subtype"]] += 1
                if result.get("category"):
                    self.stats['by_category'][result["category"]] += 1
                self.stats['total_events'] += 1
                
                # Estatísticas temporais
                if "timestamp_parsed" in result:
                    self._update_temporal_stats(result["timestamp_parsed"])
                
                return result
        
        # Se nenhum parser funcionou, retorna como não estruturado
        return {
            "log_type": "unstructured",
            "original_line": line,
            "line_number": line_number,
            "parsed_successfully": False,
            "clean_message": line  # Para compatibilidade com sistema existente
        }
    
    def group_multiline_events(self, lines: List[str]) -> Generator[str, None, None]:
        """Agrupa linhas de stack trace Java em eventos únicos"""
        buffer = []
        
        for line in lines:
            line = line.rstrip()
            
            # Se linha é continuação (indentada ou stack trace)
            if buffer and (line.startswith('\t') or line.startswith(' ') or 
                          line.strip().startswith('at ') or line.strip().startswith('...')):
                buffer.append(line)
                continue
            
            # Nova linha inicia novo evento
            if buffer:
                yield "\n".join(buffer)
            
            buffer = [line] if line else []
        
        # Último evento no buffer
        if buffer:
            yield "\n".join(buffer)
    
    def parse_log_content(
        self,
        content: str,
        enable_multiline: bool = True,
        preferred_log_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parseia conteúdo completo de log com agrupamento multiline opcional"""
        self.reset_statistics()
        
        lines = content.split('\n')
        events = []
        
        if enable_multiline:
            # Usar agrupamento multiline para logs Java
            grouped_lines = list(self.group_multiline_events(lines))
        else:
            grouped_lines = lines
        
        for idx, line_content in enumerate(grouped_lines, 1):
            header_line = line_content.split("\n", 1)[0]
            event = self.parse_line(header_line, idx, preferred_log_type=preferred_log_type)
            
            # Adicionar stack trace se existir
            if "\n" in line_content and event["log_type"] == "java":
                parts = line_content.split("\n", 1)
                if len(parts) > 1:
                    event["stack_trace"] = parts[1]
                    # Tentar extrair exceção do stack completo
                    exception = self._extract_java_exception(line_content)
                    if exception:
                        event["exception_class"] = exception
                        self.stats['exceptions'][exception] += 1
            
            events.append(event)
        
        return {
            "events": events,
            "statistics": dict(self.stats),
            "total_lines": len(lines),
            "structured_events": len([e for e in events if e.get("parsed_successfully", False)]),
            "success": True
        }
    
    def _determine_http_severity(self, status_code: int) -> str:
        """Determina severidade baseada no código HTTP"""
        if status_code >= 500:
            return "Alto"
        elif status_code >= 400:
            return "Médio"
        elif status_code >= 300:
            return "Baixo"
        else:
            return "Info"
    
    def _determine_java_severity(self, level: str) -> str:
        """Determina severidade baseada no nível Java"""
        severity_map = {
            "FATAL": "Crítico",
            "SEVERE": "Crítico",
            "ERROR": "Alto", 
            "WARN": "Médio",
            "INFO": "Baixo",
            "DEBUG": "Info",
            "TRACE": "Info"
        }
        return severity_map.get(level.upper(), "Médio")
    
    def _determine_progress_severity(self, level_num: int, subtype: str = "progress", category: str = "application", message: str = "") -> str:
        """Determina severidade baseada no nível numérico Progress"""
        message_lower = message.lower()

        if subtype in ["progress_memory", "pasoe", "appserver"] and self._looks_like_error(message):
            return "Crítico"
        if category in ["database", "availability", "security"] and self._looks_like_error(message):
            return "Alto"
        if category == "performance":
            if re.search(r'(\b[5-9]\d{3}\s*ms\b|\b[5-9]\.?\d*\s*seconds?\b)', message_lower):
                return "Alto"
            return "Médio"

        if level_num >= 4:
            return "Crítico"
        elif level_num == 3:
            return "Alto"
        elif level_num == 2:
            return "Médio"
        else:
            return "Info"
    
    def _extract_java_exception(self, message: str) -> Optional[str]:
        """Extrai nome da classe de exceção Java"""
        exception_pattern = r'([a-zA-Z0-9_.]+(?:Exception|Error))(?:[:\s]|$)'
        match = re.search(exception_pattern, message)
        return match.group(1) if match else None

    def _build_access_context(self, data: Dict[str, Any], status_code: int) -> Tuple[Dict[str, Any], List[str], str]:
        path = data.get("path", "")
        route, _, query_string = path.partition("?")
        response_size = 0 if data.get("size") == "-" else int(data.get("size", 0) or 0)

        insight_tags = []
        if status_code >= 500:
            insight_tags.append("http_5xx")
        elif status_code >= 400:
            insight_tags.append("http_4xx")
        elif status_code >= 300:
            insight_tags.append("http_redirect")
        else:
            insight_tags.append("http_success")

        if route.startswith("/api"):
            insight_tags.append("api_endpoint")
        if any(token in route.lower() for token in ["login", "auth", "token"]):
            insight_tags.append("auth_route")
        if re.search(r'\.(css|js|png|jpg|svg|ico|woff2?)$', route, re.IGNORECASE):
            insight_tags.append("static_asset")

        recommendation_hint = "monitor_http_traffic"
        if status_code >= 500:
            recommendation_hint = "investigate_server_error"
        elif status_code >= 400:
            recommendation_hint = "review_client_request"
        elif status_code >= 300:
            recommendation_hint = "review_redirect_chain"

        domain_fields = {
            "client_ip": data.get("ip"),
            "http_method": data.get("method"),
            "path": path,
            "route": route or path,
            "query_string": query_string or None,
            "status_code": status_code,
            "status_family": f"{status_code // 100}xx",
            "response_size_bytes": response_size,
            "route_depth": len([segment for segment in route.split("/") if segment])
        }
        return domain_fields, self._dedupe_tags(insight_tags), recommendation_hint

    def _build_java_domain_context(self, subtype: str, data: Dict[str, Any], message: str, category: str) -> Tuple[Dict[str, Any], List[str], str]:
        logger_name = data.get("logger")
        lifecycle_event = self._extract_lifecycle_event(message)
        web_component = self._extract_web_component(f"{logger_name or ''} {message}")
        servlet_name = self._extract_named_group(message, r'servlet\s+\[([^\]]+)\]')
        deployment_name = self._extract_named_group(message, r'(?:deployment|webapp|context)\s+[\[\"]?([\w.-]+)')

        insight_tags = []
        if category == "exception":
            insight_tags.append("java_exception")
        if category == "performance":
            insight_tags.append("slow_java_flow")
        if lifecycle_event:
            insight_tags.append(f"lifecycle_{lifecycle_event}")
        if web_component:
            insight_tags.append(f"component_{web_component.lower()}")

        recommendation_hint = "inspect_java_application"
        if subtype == "pasoe":
            if category in ["exception", "http"]:
                recommendation_hint = "inspect_pasoe_web_stack"
            elif lifecycle_event in ["start", "stop", "restart", "deploy", "undeploy"]:
                recommendation_hint = "review_pasoe_lifecycle"
            else:
                recommendation_hint = "verify_pasoe_availability"
        elif category == "exception":
            recommendation_hint = "inspect_java_stacktrace"
        elif category == "performance":
            recommendation_hint = "review_java_performance"

        domain_fields = {
            "logger_name": logger_name,
            "thread_name": data.get("thread"),
            "web_component": web_component,
            "servlet_name": servlet_name,
            "deployment_name": deployment_name,
            "lifecycle_event": lifecycle_event
        }
        return domain_fields, self._dedupe_tags(insight_tags), recommendation_hint

    def _build_progress_domain_context(
        self,
        subtype: str,
        data: Dict[str, Any],
        message: str,
        category: str,
        error_code: Optional[str],
        program_path: Optional[str],
        database_name: Optional[str]
    ) -> Tuple[Dict[str, Any], List[str], str]:
        duration_ms = self._extract_duration_ms(message)
        procedure_name = self._extract_procedure_name(message)
        broker_name = self._extract_broker_name(message)
        agent_name = self._extract_agent_name(message)
        lifecycle_event = self._extract_lifecycle_event(message)
        web_component = self._extract_web_component(message)
        program_name = self._extract_program_name(program_path)

        insight_tags = []
        if error_code:
            insight_tags.append("error_code_detected")
        if program_name:
            insight_tags.append("program_reference")
        if database_name:
            insight_tags.append("database_reference")
        if duration_ms is not None and duration_ms >= 2000:
            insight_tags.append("slow_operation")
        if lifecycle_event:
            insight_tags.append(f"lifecycle_{lifecycle_event}")

        recommendation_hint = "inspect_progress_flow"

        message_lower = message.lower()
        if subtype == "pasoe":
            if self._looks_like_error(message) or category in ["exception", "availability", "http"]:
                insight_tags.append("pasoe_incident")
            if web_component:
                insight_tags.append(f"component_{web_component.lower()}")
            recommendation_hint = "verify_pasoe_availability"
            if category == "exception":
                recommendation_hint = "inspect_pasoe_web_stack"
            elif lifecycle_event in ["start", "stop", "restart", "deploy", "undeploy"]:
                recommendation_hint = "review_pasoe_lifecycle"
        elif subtype == "appbroker":
            if "no agents available" in message_lower:
                insight_tags.append("agent_pool_exhausted")
                recommendation_hint = "investigate_agent_pool"
            elif "broker is not available" in message_lower:
                insight_tags.append("broker_unavailable")
                recommendation_hint = "verify_broker_availability"
            elif "dispatch request" in message_lower:
                insight_tags.append("dispatch_queue")
                recommendation_hint = "review_dispatch_queue"
            else:
                recommendation_hint = "verify_broker_availability"
        elif subtype == "appserver":
            if re.search(r'died|terminated|shutdown|stopped', message_lower):
                insight_tags.append("service_interruption")
                recommendation_hint = "investigate_appserver_crash"
            elif duration_ms is not None and duration_ms >= 2000:
                insight_tags.append("slow_program")
                recommendation_hint = "review_slow_program"
            else:
                recommendation_hint = "verify_appserver_availability"
        elif subtype == "progress":
            if database_name:
                recommendation_hint = "review_database_dependency"
            elif program_name:
                recommendation_hint = "inspect_progress_program"
        elif subtype == "app_performance":
            recommendation_hint = "review_slow_program"

        domain_fields = {
            "process_id": int(data["pid"]) if data.get("pid") else None,
            "thread_id": data.get("tid"),
            "component": data.get("comp"),
            "program_path": program_path,
            "program_name": program_name,
            "procedure_name": procedure_name,
            "database_name": database_name,
            "error_code": error_code,
            "duration_ms": duration_ms,
            "broker_name": broker_name,
            "agent_name": agent_name,
            "lifecycle_event": lifecycle_event,
            "web_component": web_component
        }
        return domain_fields, self._dedupe_tags(insight_tags), recommendation_hint

    def _build_logix_domain_context(self, data: Dict[str, Any], message: str, category: str) -> Tuple[Dict[str, Any], List[str], str]:
        thread_name = data.get("thread")
        running_time_ms = self._extract_duration_ms(message)
        source_program = self._extract_named_group(message, r'4GL SOURCE:\s*([\w./\\-]+)')
        source_line = self._extract_int_value(message, r'LINE:\s*(\d+)')
        status_code = self._extract_int_value(message, r'STATUS:\s*(-?\d+)')
        rows_affected = self._extract_int_value(message, r'ROWS\s+AFFECTED:\s*(-?\d+)')
        command = self._extract_named_group(message, r'COMMAND:\s*(.+)$')
        command_type = self._extract_logix_command_type(command or message)

        insight_tags = []
        if command_type:
            insight_tags.append(f"sql_{command_type.lower()}")
        if running_time_ms is not None and running_time_ms >= 2000:
            insight_tags.append("slow_sql")
        if rows_affected is not None:
            insight_tags.append("rows_affected")
        if category == "validation":
            insight_tags.append("xml_validation")
        if category == "integration":
            insight_tags.append("sefaz_integration")
        if category == "license":
            insight_tags.append("license_event")
        if status_code not in [None, 0]:
            insight_tags.append("nonzero_status")

        recommendation_hint = "inspect_logix_application"
        if command_type:
            recommendation_hint = "review_logix_sql"
        elif category == "validation":
            recommendation_hint = "review_logix_xml_validation"
        elif category == "integration":
            recommendation_hint = "verify_logix_integration"
        elif category == "framework":
            recommendation_hint = "inspect_logix_framework"

        domain_fields = {
            "thread_name": thread_name,
            "source_program": source_program,
            "source_line": source_line,
            "status_code": status_code,
            "rows_affected": rows_affected,
            "sql_command": command,
            "command_type": command_type,
            "running_time_ms": running_time_ms,
            "module": self._extract_logix_module(message)
        }
        return domain_fields, self._dedupe_tags(insight_tags), recommendation_hint

    def _match_progress_variants(self, line: str) -> Tuple[Optional[re.Match[str]], str]:
        variant = "full"
        match = self.RX_PROGRESS.match(line)
        if not match:
            match = self.RX_PROGRESS_SIMPLE.match(line)
            variant = "simple"
        if not match:
            match = self.RX_PROGRESS_PROCESS.match(line)
            variant = "process"
        if not match:
            match = self.RX_PROGRESS_TIMESTAMPED.match(line)
            variant = "timestamped"
        return match, variant

    def _infer_progress_level(self, message: str) -> int:
        """Infere nível Progress para linhas sem o campo numérico explícito."""
        message_lower = message.lower()

        if re.search(r'critical|fatal|severe|panic|abend', message_lower):
            return 4
        if re.search(r'error|exception|failed|refused|denied|unavailable|terminated|stopped', message_lower):
            return 3
        if re.search(r'warn|warning|slow|timeout|elapsed|took\s+\d', message_lower):
            return 2
        return 1

    def _categorize_access_status(self, status_code: int) -> str:
        if status_code >= 500:
            return "server_error"
        if status_code >= 400:
            return "client_error"
        if status_code >= 300:
            return "redirect"
        return "success"

    def _detect_java_subtype(self, line: str, data: Dict[str, Any]) -> str:
        text = f"{line} {data.get('logger', '')} {data.get('msg', '')}".lower()

        if any(token in text for token in ["fluig", "ecm", "workflowengine", "dataset", "documentservice"]):
            return "fluig"
        if any(token in text for token in ["catalina", "org.apache.catalina", "tomcat", "http-nio", "localhost-startstop"]):
            return "tomcat"
        if any(token in text for token in ["jboss", "wildfly", "org.jboss", "undertow", "standalone.xml"]):
            return "jboss"
        if any(token in text for token in ["pasoe", "webhandler", "ablwebapp", "oeablsecurity", "msagent", "oepas"]):
            return "pasoe"
        return "java"

    def _categorize_java_message(self, line: str, data: Dict[str, Any]) -> str:
        text = f"{line} {data.get('logger', '')} {data.get('msg', '')}".lower()

        if re.search(r'exception|stacktrace|caused by:', text):
            return "exception"
        if re.search(r'timeout|slow|elapsed|duration|took\s+\d', text):
            return "performance"
        if re.search(r'http\s*5\d\d|bad gateway|service unavailable|websocket', text):
            return "http"
        if re.search(r'login|authentication|authorization|access denied|security', text):
            return "security"
        if re.search(r'database|jdbc|hibernate|sql|connection pool', text):
            return "database"
        if re.search(r'start|stop|deploy|undeploy|initializ', text):
            return "lifecycle"
        return "application"

    def _detect_progress_subtype(self, line: str, data: Dict[str, Any]) -> str:
        text = f"{line} {data.get('comp', '')} {data.get('msg', '')}".lower()

        if any(token in text for token in ["pasoe", "webhandler", "ablwebapp", "oeablsecurity", "msagent", "catalina", "oepas"]):
            return "pasoe"
        if any(token in text for token in ["appbroker", "no agents available", "dispatch request", "broker is not available"]):
            return "appbroker"
        if any(token in text for token in ["appserver", "appsvr", "_mprosrv", "nameserver", "agent process", "broker started"]):
            return "appserver"
        if any(token in text for token in ["memory leak", "outofmemory", "not released", "handle", "object", "heap", "garbage collector"]):
            return "progress_memory"
        if any(token in text for token in ["table scan", "index", "record", "rowid", "factor", "tabanalys", "table "]):
            return "progress_tabanalys"
        if any(token in text for token in ["xref", "cross-reference", "caller", "callee", "include file", "compile listing"]):
            return "progress_xref"
        if any(token in text for token in ["database", "db ", "schema holder", "before-image", "after-image", "biw", "aiw", "latch", "login broker"]):
            return "progress_db"
        if any(token in text for token in ["took ", "elapsed", "duration", "slow", "seconds", "ms"]):
            return "app_performance"
        return "progress"

    def _looks_like_logix(self, text: str) -> bool:
        text_lower = text.lower()
        tokens = [
            "[thread ", "[logix]", "totvs - frw", "logix:", "nfe:", "danfe:", "sefaz:",
            "schema xml", "running time:", "4gl source:", "rows affected:", "command:",
            "license", "wscerr"
        ]
        return any(token in text_lower for token in tokens)

    def _categorize_logix_message(self, message: str) -> str:
        text = message.lower()
        if re.search(r'command:|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|rows affected', text):
            return "sql"
        if re.search(r'schema xml|valida[çc][aã]o|xml', text):
            return "validation"
        if re.search(r'sefaz|webservice|wscerr|nfe|danfe', text):
            return "integration"
        if re.search(r'license|systemkey', text):
            return "license"
        if re.search(r'frw:|framework', text):
            return "framework"
        if re.search(r'server|thread|acceptwt', text):
            return "server"
        return "application"

    def _map_legacy_progress_source(self, subtype: str) -> Dict[str, Any]:
        mapping = {
            "pasoe": {"legacy_parser": "LogAnalysTomcat.i", "legacy_group": "java-web"},
            "appbroker": {"legacy_parser": "LogAnalysAppBroker.i", "legacy_group": "broker"},
            "appserver": {"legacy_parser": "LogAnalysAppBroker.i", "legacy_group": "broker"},
            "progress_db": {"legacy_parser": "LogAnalysProgressDb.i", "legacy_group": "database"},
            "progress_memory": {"legacy_parser": "LogAnalysProgressMemory.i", "legacy_group": "memory"},
            "progress_tabanalys": {"legacy_parser": "LogAnalysProgressTab.i", "legacy_group": "table-analysis"},
            "progress_xref": {"legacy_parser": "LogAnalysProgressXref.i", "legacy_group": "xref"},
            "app_performance": {"legacy_parser": "LogAnalysAppPerf.i", "legacy_group": "performance"},
            "progress": {"legacy_parser": "LogAnalysProgress.i", "legacy_group": "progress"},
            "acesso": {"legacy_parser": "LogAnalysAcesso.i", "legacy_group": "access"},
            "jboss": {"legacy_parser": "LogAnalysJBoss.i", "legacy_group": "java-app"},
            "tomcat": {"legacy_parser": "LogAnalysTomcat.i", "legacy_group": "java-web"},
            "logix": {"legacy_parser": "LogAnalysLogix.i", "legacy_group": "logix"}
        }
        return mapping.get(subtype, {})

    def _categorize_progress_message(self, line: str, data: Dict[str, Any], subtype: str) -> str:
        text = f"{line} {data.get('comp', '')} {data.get('msg', '')}".lower()

        if subtype == "progress_memory":
            return "memory"
        if subtype == "progress_tabanalys":
            return "table_analysis"
        if subtype == "progress_xref":
            return "xref"
        if subtype == "app_performance":
            return "performance"
        if subtype == "logix":
            return self._categorize_logix_message(data.get("msg", ""))
        if subtype in ["appserver", "appbroker"]:
            return "availability"
        if re.search(r'exception|stacktrace|caused by:|severe:', text):
            return "exception"
        if subtype == "progress_db" or re.search(r'database|login broker|schema holder|db\b', text):
            return "database"
        if re.search(r'permission|security|access denied|authorization|authentication', text):
            return "security"
        if re.search(r'broker|agent|not available|not responding|stopped|terminated|shutdown|refused', text):
            return "availability"
        if re.search(r'timeout|elapsed|slow|took\s+\d|ms\b|seconds?\b', text):
            return "performance"
        if re.search(r'http\s*\d\d\d|gateway|service unavailable|websocket', text):
            return "http"
        return "application"

    def _looks_like_error(self, message: str) -> bool:
        return bool(re.search(r'\b(error|exception|failed|fatal|critical|severe|denied|unavailable|timeout|refused|abnormally|stopped|terminated)\b', message, re.IGNORECASE))

    def _extract_error_code(self, message: str) -> Optional[str]:
        patterns = [
            r'\b(FT\d{4})\b',
            r'\b(\d{3,5}/\d{3,5})\b',
            r'\((\d{3,5})\)',
            r'\b(?:error|erro)\s+(\d{3,5})\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_program_path(self, message: str) -> Optional[str]:
        match = re.search(r'([\w./\\-]+\.(?:p|r|w|cls|i))\b', message, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_program_name(self, program_path: Optional[str]) -> Optional[str]:
        if not program_path:
            return None
        return re.split(r'[\\/]', program_path)[-1]

    def _extract_tabanalys_fields(self, message: str) -> Optional[Dict[str, Any]]:
        message_lower = message.lower()
        if not any(token in message_lower for token in ["factor", "table scan", "whole-index", "index ", "tabanalys"]):
            return None

        table_name = self._extract_named_group(message, r'table\s+([\w$-]+)')
        index_name = self._extract_named_group(message, r'index\s+([\w$-]+)')
        factor = self._extract_decimal_value(message, r'factor\s+(\d+(?:[\.,]\d+)?)')
        records = self._extract_int_value(message, r'(?:records?|rows?)\s+(\d+)')
        fields = self._extract_int_value(message, r'fields?\s+(\d+)')

        if not any([table_name, index_name, factor is not None]):
            return None

        if factor is not None and factor > 10:
            factor = round(factor / 10, 2)

        category = "index" if index_name else "table"
        observation = self._build_tabanalys_observation(category, factor)

        return {
            "analysis_type": category,
            "table_name": table_name,
            "index_name": index_name,
            "record_count": records,
            "field_count": fields,
            "factor": factor,
            "observation": observation,
            "full_scan": bool(re.search(r'full\s+table\s+scan|whole-index', message, re.IGNORECASE))
        }

    def _extract_tabanalys_raw_fields(self, original_line: str, compressed_line: str) -> Optional[Dict[str, Any]]:
        match = self.RX_TABANALYS_INDEX_RAW.match(original_line)
        if match:
            factor = self._normalize_tabanalys_factor(match.group("factor"))
            return {
                "analysis_type": "index",
                "table_name": None,
                "index_name": match.group("index"),
                "record_count": None,
                "field_count": int(match.group("fields")),
                "factor": factor,
                "observation": self._build_tabanalys_observation("index", factor),
                "full_scan": False
            }

        match = self.RX_TABANALYS_TABLE_RAW.match(compressed_line)
        if match and not compressed_line.lower().startswith(("table ", "totals:", "subtotals:")):
            factor = self._normalize_tabanalys_factor(match.group("factor"))
            return {
                "analysis_type": "table",
                "table_name": match.group("table"),
                "index_name": None,
                "record_count": int(match.group("records")),
                "field_count": None,
                "factor": factor,
                "observation": self._build_tabanalys_observation("table", factor),
                "full_scan": False
            }

        return None

    def _normalize_tabanalys_factor(self, raw_factor: Any) -> Optional[float]:
        if raw_factor in [None, ""]:
            return None
        value = float(str(raw_factor).replace(",", "."))
        return round(value / 10, 2) if value >= 10 else round(value, 2)

    def _build_tabanalys_observation(self, analysis_type: str, factor: Optional[float]) -> Optional[str]:
        if factor is None or factor < 1.5:
            return None
        if factor < 2.0:
            return "Performance prejudicada. Necessita DUMP/LOAD." if analysis_type == "table" else "Necessita reindexação do índice."
        return "Performance prejudicada. Precisa DUMP/LOAD urgente." if analysis_type == "table" else "Necessita reindexação urgente do índice."

    def _build_tabanalys_tags(self, extracted: Dict[str, Any]) -> List[str]:
        tags = [f"tabanalys_{extracted.get('analysis_type', 'table')}"]
        if extracted.get("full_scan"):
            tags.append("full_scan")
        factor = extracted.get("factor")
        if factor is not None:
            if factor >= 2.0:
                tags.append("critical_fragmentation")
            elif factor >= 1.5:
                tags.append("fragmentation_warning")
        if extracted.get("index_name"):
            tags.append("index_reference")
        if extracted.get("table_name"):
            tags.append("table_reference")
        return self._dedupe_tags(tags)

    def _recommend_tabanalys_action(self, extracted: Dict[str, Any]) -> str:
        factor = extracted.get("factor") or 0
        if extracted.get("analysis_type") == "index":
            return "urgent_reindex" if factor >= 2.0 else "review_index_fragmentation"
        return "urgent_dump_load" if factor >= 2.0 else "review_table_fragmentation"

    def _determine_tabanalys_severity(self, level_num: int, factor: Optional[float]) -> str:
        if factor is not None:
            if factor >= 2.0:
                return "Crítico"
            if factor >= 1.5:
                return "Alto"
        return self._determine_progress_severity(level_num, "progress_tabanalys", "table_analysis", "")

    def _extract_xref_fields_from_message(self, message: str) -> Optional[Dict[str, Any]]:
        lower_message = message.lower()
        if "xref" not in lower_message and not any(token in lower_message for token in ["include file", "caller", "callee"]):
            return None

        xref_type = "INCLUDE" if "include file" in lower_message else "READ"
        key_name = self._extract_named_group(message, r'include\s+file\s+([\w./\\-]+)')
        parameters = self._extract_named_group(message, r'params?[:=]\s*(.+)$')
        return_type = self._extract_named_group(message, r'return[:=]\s*(\S+)')
        caller = self._extract_named_group(message, r'caller\s+([\w./\\-]+)')
        callee = self._extract_named_group(message, r'callee\s+([\w./\\-]+)')
        full_scan = bool(re.search(r'full[-\s]?scan|whole-index', lower_message))
        persistent = bool(re.search(r'persist', lower_message))
        translatable = not bool(re.search(r'untranslatable', lower_message)) if "string" in lower_message else None

        if "procedure" in lower_message:
            xref_type = "PROCEDURE"
        elif "function" in lower_message:
            xref_type = "FUNCTION"
        elif "global" in lower_message:
            xref_type = "VAR.GLOBAL"
        elif "run" in lower_message:
            xref_type = "RUN"
        elif "string" in lower_message:
            xref_type = "STRING"

        return {
            "program_name": caller or callee,
            "source_program": caller,
            "target_program": callee,
            "xref_type": xref_type,
            "key_name": key_name,
            "parameters": parameters,
            "return_type": return_type,
            "full_scan": full_scan,
            "sequence_flag": False,
            "global_flag": bool(re.search(r'global', lower_message)),
            "shared_flag": bool(re.search(r'shared', lower_message)),
            "persistent_flag": persistent,
            "translatable_flag": translatable
        }

    def _extract_xref_fields_from_raw_line(self, line: str) -> Optional[Dict[str, Any]]:
        tokens = re.split(r'\s+', line.strip())
        if len(tokens) < 4 or not tokens[2].isdigit():
            return None

        operation = tokens[3].upper()
        supported_ops = {"CREATE", "DELETE", "REFERENCE", "ACCESS", "UPDATE", "SEARCH", "INCLUDE", "PROCEDURE", "FUNCTION", "EXTERN", "GLOBAL-VARIABLE", "RUN", "STRING"}
        if operation not in supported_ops:
            return None

        source_program = self._compact_program_path(tokens[0])
        target_program = self._compact_program_path(tokens[1])
        remainder = tokens[4:]
        raw_text = " ".join(remainder)
        xref_type = "PROC.EXT" if operation == "EXTERN" else ("VAR.GLOBAL" if operation == "GLOBAL-VARIABLE" else ("READ" if operation == "SEARCH" else operation))

        key_name = remainder[0].replace('"', '') if remainder else None
        return_type = None
        parameters = None

        if operation in ["PROCEDURE", "FUNCTION", "EXTERN"] and remainder:
            key_name = remainder[0].replace('"', '')
            if operation in ["FUNCTION", "EXTERN"] and len(remainder) > 1:
                return_type = remainder[1]
                parameters = " ".join(remainder[2:]) if len(remainder) > 2 else None
            else:
                parameters = " ".join(remainder[1:]) if len(remainder) > 1 else None

        if operation == "INCLUDE" and remainder:
            key_name = remainder[0].replace('"', '')
        if operation == "RUN" and remainder:
            key_name = remainder[0].replace('"', '')

        return {
            "line_number_ref": int(tokens[2]),
            "program_name": target_program,
            "source_program": source_program if source_program != target_program else None,
            "target_program": target_program,
            "xref_type": xref_type,
            "key_name": key_name,
            "parameters": parameters,
            "return_type": return_type,
            "full_scan": "WHOLE-INDEX" in raw_text.upper(),
            "sequence_flag": "SEQUENCE" in raw_text.upper(),
            "global_flag": operation == "GLOBAL-VARIABLE" or "GLOBAL" in raw_text.upper(),
            "shared_flag": "SHARED" in raw_text.upper(),
            "persistent_flag": "PERSISTENT" in raw_text.upper(),
            "translatable_flag": False if "UNTRANSLATABLE" in raw_text.upper() else (True if operation == "STRING" else None)
        }

    def _build_xref_tags(self, extracted: Dict[str, Any]) -> List[str]:
        tags = [f"xref_{str(extracted.get('xref_type', 'unknown')).lower().replace('.', '_')}"]
        if extracted.get("full_scan"):
            tags.append("full_scan")
        if extracted.get("global_flag"):
            tags.append("global_usage")
        if extracted.get("shared_flag"):
            tags.append("shared_usage")
        if extracted.get("persistent_flag"):
            tags.append("persistent_run")
        if extracted.get("translatable_flag") is False:
            tags.append("untranslatable_string")
        return self._dedupe_tags(tags)

    def _recommend_xref_action(self, extracted: Dict[str, Any]) -> str:
        if extracted.get("full_scan"):
            return "review_full_scan_reference"
        if extracted.get("global_flag") or extracted.get("shared_flag"):
            return "review_global_shared_usage"
        if extracted.get("xref_type") in ["RUN", "PROC.EXT"] and extracted.get("persistent_flag"):
            return "review_persistent_run"
        return "review_xref_dependencies"

    def _determine_xref_severity(self, extracted: Dict[str, Any]) -> str:
        if extracted.get("full_scan"):
            return "Alto"
        if extracted.get("global_flag") or extracted.get("shared_flag") or extracted.get("persistent_flag"):
            return "Médio"
        return "Info"

    def _extract_procedure_name(self, message: str) -> Optional[str]:
        patterns = [
            r'Procedure:\s*([\w./\\-]+)',
            r'procedure\s+([\w./\\-]+)',
            r'caller\s+([\w./\\-]+)',
            r'callee\s+([\w./\\-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_duration_ms(self, message: str) -> Optional[float]:
        patterns = [
            (r'(?:took|elapsed|duration)\s+(\d+(?:\.\d+)?)\s*(ms|milliseconds?)', 1.0),
            (r'RUNNING\s+TIME:\s*(\d+(?:\.\d+)?)\s*(ms|milliseconds?)', 1.0),
            (r'RUNNING\s+TIME:\s*(\d+(?:\.\d+)?)\s*(s|sec|secs|second|seconds)', 1000.0),
            (r'(?:took|elapsed|duration)\s+(\d+(?:\.\d+)?)\s*(s|sec|secs|second|seconds)', 1000.0),
            (r'(\d+(?:\.\d+)?)\s*(ms|milliseconds?)\s+to\s+complete', 1.0),
            (r'(\d+(?:\.\d+)?)\s*(s|sec|secs|second|seconds)\s+to\s+complete', 1000.0)
        ]
        for pattern, multiplier in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return round(float(match.group(1)) * multiplier, 2)
        return None

    def _extract_broker_name(self, message: str) -> Optional[str]:
        return self._extract_named_group(message, r'broker\s+(?:is\s+)?(?:named\s+)?([\w.-]+)')

    def _extract_agent_name(self, message: str) -> Optional[str]:
        return self._extract_named_group(message, r'agent(?:\s+process)?\s+([\w.-]+)')

    def _extract_lifecycle_event(self, message: str) -> Optional[str]:
        message_lower = message.lower()
        lifecycle_patterns = [
            (r'failed to start|starting|started|startup', 'start'),
            (r'stopped|stopping|shutdown', 'stop'),
            (r'restart|restarted|restarting', 'restart'),
            (r'undeploy|undeployed|undeploying', 'undeploy'),
            (r'deploy|deployed|deploying', 'deploy')
        ]
        for pattern, event in lifecycle_patterns:
            if re.search(pattern, message_lower):
                return event
        return None

    def _extract_web_component(self, message: str) -> Optional[str]:
        tokens = {
            'WebHandler': r'webhandler',
            'ABLWebApp': r'ablwebapp',
            'MSAgent': r'msagent',
            'OEPAS': r'oepas',
            'Tomcat': r'catalina|tomcat',
            'Security': r'oeablsecurity|security'
        }
        message_lower = message.lower()
        for label, pattern in tokens.items():
            if re.search(pattern, message_lower):
                return label
        return None

    def _extract_named_group(self, message: str, pattern: str) -> Optional[str]:
        match = re.search(pattern, message, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_int_value(self, message: str, pattern: str) -> Optional[int]:
        match = re.search(pattern, message, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _extract_decimal_value(self, message: str, pattern: str) -> Optional[float]:
        match = re.search(pattern, message, re.IGNORECASE)
        if not match:
            return None
        return float(match.group(1).replace(',', '.'))

    def _compact_program_path(self, program_path: str) -> str:
        normalized = program_path.replace('\\', '/')
        parts = [part for part in normalized.split('/') if part]
        if len(parts) >= 2:
            return '/'.join(parts[-2:])
        return normalized

    def _extract_logix_command_type(self, text: str) -> Optional[str]:
        upper_text = (text or "").upper()
        for command in ["SELECT", "INSERT", "UPDATE", "DELETE", "EXECUTE", "DECLARE", "OPEN", "CLOSE", "FREE", "FETCH", "PREPARE"]:
            if re.search(rf'\b{command}\b', upper_text):
                return command
        return None

    def _extract_logix_module(self, message: str) -> Optional[str]:
        upper_message = message.upper()
        for module in ["FRW", "LOGIX", "NFE", "DANFE", "SEFAZ", "LICENSE", "SERVER"]:
            if module in upper_message:
                return module
        return None

    def _determine_logix_severity(self, level: str, category: str, domain_fields: Dict[str, Any], message: str) -> str:
        message_lower = message.lower()
        if level == "ERROR" or self._looks_like_error(message):
            return "Alto"
        if domain_fields.get("status_code") not in [None, 0]:
            return "Alto"
        if category == "sql" and (domain_fields.get("running_time_ms") or 0) >= 5000:
            return "Crítico"
        if category in ["validation", "integration", "license"] and re.search(r'falha|erro|inv[aá]l', message_lower):
            return "Alto"
        if category == "framework":
            return "Médio"
        return "Info"

    def _dedupe_tags(self, tags: List[str]) -> List[str]:
        return list(dict.fromkeys([tag for tag in tags if tag]))

    def _extract_database_name(self, message: str) -> Optional[str]:
        match = re.search(r"database\s+'([^']+)'", message, re.IGNORECASE)
        if match:
            return match.group(1)

        match = re.search(r'\bdb(?:ase)?\s+([\w-]+)', message, re.IGNORECASE)
        return match.group(1) if match else None

    def _build_error_signature(self, subtype: str, category: str, message: str, error_code: Optional[str] = None) -> str:
        if error_code:
            return f"{subtype}:{category}:{error_code}"

        normalized_message = re.sub(r'\s+', ' ', message.strip()).lower()
        normalized_message = re.sub(r'\b\d+\b', '#', normalized_message)
        excerpt = normalized_message[:80] if normalized_message else 'event'
        return f"{subtype}:{category}:{excerpt}"
    
    def _update_temporal_stats(self, timestamp_str: str):
        """Atualiza estatísticas temporais"""
        try:
            if timestamp_str and "T" in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                hour_key = f"{dt.hour:02d}:00"
                self.stats['temporal_distribution'][hour_key] += 1
        except Exception:
            pass  # Ignore parsing errors
    
    def get_error_events(self, events: List[Dict]) -> List[Dict]:
        """Filtra apenas eventos que são erros"""
        error_events = []
        
        for event in events:
            if event.get("is_error", False):
                error_events.append(event)
            elif event.get("log_type") == "access" and event.get("status_code", 0) >= 400:
                error_events.append(event)
            elif event.get("log_type") == "java" and event.get("level") in ["ERROR", "FATAL"]:
                error_events.append(event)
        
        return error_events
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Gera relatório resumido das análises"""
        return {
            "parsing_summary": {
                "total_events": self.stats['total_events'],
                "events_by_type": dict(self.stats['by_type']),
                "events_by_subtype": dict(self.stats['by_subtype']),
                "events_by_category": dict(self.stats['by_category']),
                "parsing_success_rate": (
                    self.stats['total_events'] / max(1, self.stats['total_events']) * 100
                )
            },
            "http_analysis": {
                "status_distribution": dict(self.stats['http_status'].most_common(10)),
                "error_rate": sum(
                    count for status, count in self.stats['http_status'].items() 
                    if status >= 400
                ) / max(1, sum(self.stats['http_status'].values())) * 100
            },
            "java_analysis": {
                "level_distribution": dict(self.stats['java_levels']),
                "top_exceptions": dict(self.stats['exceptions'].most_common(10))
            },
            "progress_analysis": {
                "level_distribution": dict(self.stats['progress_levels'])
            },
            "temporal_analysis": {
                "hourly_distribution": dict(self.stats['temporal_distribution'])
            }
        }


# Função de conveniência para integração rápida
def parse_structured_log(content: str, enable_multiline: bool = True) -> Dict[str, Any]:
    """Função de conveniência para parsing rápido"""
    parser = StructuredLogParser()
    return parser.parse_log_content(content, enable_multiline)