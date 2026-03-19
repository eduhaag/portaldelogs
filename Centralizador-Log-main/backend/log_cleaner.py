# -*- coding: utf-8 -*-
"""
Identifica categorias em logs Progress sem excluir nada.
- Streaming (bom p/ arquivos grandes)
- Suporta .gz, UTF-8 e fallback Latin-1
- Retorna contagens + amostras por categoria
"""

from __future__ import annotations
import re, gzip, json, io
from dataclasses import dataclass, field
from typing import Dict, List, Iterable, Optional

def _rx(p: str) -> re.Pattern:
    return re.compile(p, re.IGNORECASE)

CATEGORIES: Dict[str, List[re.Pattern]] = {
    # ============================================================
    # CATEGORIAS DATASUL/PROGRESS (ORIGINAIS)
    # ============================================================
    
    # Negócio / TOTVS
    "traducao": [
        _rx(r"utp/ut-liter\.p"), _rx(r"utp/ut-trfrrp\.p"), _rx(r"utp/ut-trdfr\.p"),
        _rx(r"utp/ut-fiel2\.p"), _rx(r"btb/btb901zo\.p"),
        _rx(r"\bpi-trad-(?:fill-in|toggle-box|text|radio-set|button|editor|browse|menu|combo-box)\b"),
        _rx(r"utp/ut-field\.p"), _rx(r"utp/ut-trcampos\.p"), _rx(r"\bpi_aplica_facelift\b"),
        _rx(r"\bbtb908za\b.*\bfn_trad\b"),
    ],
    "facelift": [_rx(r"\bpi_aplica_facelift\b")],
    "rpw": [
        _rx(r"\bpi_verificar_ped_exec_a_executar\b"), _rx(r"\bpi_verificar_ped_exec_pendurados\b"),
        _rx(r"\bpi_servid_exec_status\b"), _rx(r"\bpi_sec_to_formatted_time\b"),
        _rx(r"\bpi_formatted_time_to_sec\b"), _rx(r"\bpi_atualiza_tt_ped_exec\b"),
        _rx(r"\bpi_open_servid_exec\b"), _rx(r"\bpi_vld_servid_exec_autom\b"),
        _rx(r"\bpi_disparar_ped_exec_ems2\b"), _rx(r"\bpi_montar_lista_servid_exec_dispon\b"),
        _rx(r"\bpi_vld_fnc_servid_exec\b"),
        _rx(r"\bbtb908za\b.*\b(fn_situacao|fn_motivo|fn_trad|pi-inicializa-variavel)\b"),
    ],
    "di": [
        _rx(r"\bpiSetUserDB\b"), _rx(r"\bpiConectar\b"), _rx(r"\b4GLSession\b"), _rx(r"\bCtrlFrame\.PSTimer\b"),
        _rx(r"\bmen/men702dd\.p\b"), _rx(r"\bmen/men702dc\.w\b"), _rx(r"\bmen/men906zb\.p\b"), _rx(r"\bmen/men906zatimeout\b"),
        _rx(r"\bfwk/utils/diProgress\.p\b"), _rx(r"\bpiEncerrarDI\b"), _rx(r"\bpiEncerrarDISemPSTimer\b"), _rx(r"\bpiTTDialog\b"),
        _rx(r"\bpiEliminarDialog\b"), _rx(r"\bpiAcelerarIntervaloPSTimer\b"), _rx(r"\bpiEncerrarProcesso\b"),
        _rx(r"\benable_UI\b"), _rx(r"\bdisable_UI\b"),
        _rx(r"\bsocketConnected\b"), _rx(r"\bAliveNKickn\b"), _rx(r"\bdoLog\b"), _rx(r"\bTimerRegistrado\b"),
        _rx(r"\bExtendedModeLog\b"), _rx(r"\bloadTimer\b"), _rx(r"\bTimerActive\b"),
        _rx(r"\bReg(OpenKeyA|CloseKey|EnumKeyA|QueryValueExA|SetValueExA)\b"),
        _rx(r"\bpiApply(EndErrorDialog|WindowCloseDialog)\b"), _rx(r"\bpiFecharJanela\b"),
        _rx(r"\bpiEliminar(Objeto|Classes)\b"), _rx(r"\bpiDesconectarBancos\b"), _rx(r"\bpiFecharProgramaGUI\b"),
        _rx(r"\bexecuteProgram\b"), _rx(r"\binstLicManager\b"), _rx(r"\blicManagerLoc\b"), _rx(r"\bverifyLicense\b"),
        _rx(r"\bsendProcedure\b"), _rx(r"\breadProcedure\b"), _rx(r"\breceivedProcedure\b"), _rx(r"\bpiGetIdle\b"),
        _rx(r"\bpiUpdateInfo(LS|Server|Login|AppServer)?\b"), _rx(r"\bpiValidNegocio\b"), _rx(r"\bpiSetInfoUserCompany\b"),
        _rx(r"\bpiUpdateProperties\b"), _rx(r"\bOpenProcess\b"), _rx(r"\bTerminateProcess\b"), _rx(r"\bCloseHandle\b"),
        _rx(r"\bGetLastInputInfo\b"), _rx(r"\bGetTickCount\b"), _rx(r"\bguardaValoresNaSessao\b"),
        _rx(r"\bmen/men906za\.p\b"), _rx(r"\bsendSocketData\b"), _rx(r"\bprotocolBroker\b"), _rx(r"\bpiValidaTimeout\b"),
        _rx(r"\bsendToFlex\b"), _rx(r"\bpiCalculaUtilizacao\b"), _rx(r"\bhasActiveDialogBox\b"), _rx(r"\b4GL FRM\b"),
    ],
    "ls": [
        _rx(r"\bbtb/btb432za\.p\b"), _rx(r"\bbtb/btb432zg\.p\b"), _rx(r"\bbtb/btb970aa\.p\b"),
        _rx(r"\b LS MSG \b"), _rx(r"\binstLicManager\b"), _rx(r"\blicManagerLoc\b"),
    ],
    "ddk": [
        _rx(r"\butp/ut-log\.p\b"), _rx(r"\bRun utp/ut-osver\.p\b"), _rx(r"\butp/ut-cmdln\.p\b"),
        _rx(r"\bmlutp/ut-genxml\.p\b"), _rx(r"\bxmlutp/normalize\.p\b"), _rx(r"\butp/windowstyles\.p\b"),
        _rx(r"\badm/objects/broker\.p\b"), _rx(r"\bpi-trata-state\b"), _rx(r"\butp/showmessage\.w\b"),
        _rx(r"\butp/thinfolder\.w\b"), _rx(r"\butp/ut-win\.p\b"), _rx(r"\butp/ut-style\.p\b"),
        _rx(r"\butp/ut-func\.p\b"), _rx(r"\butp/ut-extra\.p\b"), _rx(r"\bpi-troca-pagina\b"),
        _rx(r"\bpanel/p-navega\.w\b"), _rx(r"\bpanel/p-exihel\.w\b"), _rx(r"\badm/objects/folder\.w\b"),
        _rx(r"\bstate-changed\b"), _rx(r"\bverifySecurity\b"),
    ],
    "bos": [
        _rx(r"\b_selfOthersInfo\b"), _rx(r"\bselfInfo\b"), _rx(r"\b_copyBuffer2TT\b"), _rx(r"\bbeforeCopyBuffer2TT\b"),
        _rx(r"\bemptyRowObject(Aux)?\b"), _rx(r"\bgetBatchRecords\b"), _rx(r"\brepositionRecord\b"), _rx(r"\b_canRunMethod\b"),
    ],
    "fluig": [_rx(r"\bfluig\b")],
    "eai":   [_rx(r"\.eai\."), _rx(r"\bAS EAI2?\b"), _rx(r"\b4GL EAI2?\b"), _rx(r"\bWS EAI2?\b")],

    # Tipos Progress
    "dbconnects": [_rx(r"\b(4GL|AS|WS)\s+CONN(ECTS)?\b"), _rx(r"\bDB\.Connects\b")],
    "proevents":  [_rx(r"\b(4GL|AS|WS)\s+PROEVENTS\b")],
    "dynobjects": [_rx(r"\b(4GL|AS|WS)\s+DYNOBJECTS\b"), _rx(r"\bDynObjects(\.DB|\.XML|\.Other|\.CLASS|\.UI)?\b")],
    "4gltrans":   [_rx(r"\b4GLTRANS\b")],
    "fileid":     [_rx(r"\b(4GL|AS|WS)\s+FILEID\b"), _rx(r"\bFILEID\b")],
    "4glmessages":[_rx(r"\b(4GL|AS|WS)\s+4GLMESSAGE\b"), _rx(r"\b4GL\s+-{6,}\b"), _rx(r"\bLogging level set\b"), _rx(r"\bLog entry types\b")],
    "4gltrace":   [_rx(r"\b4GLTRACE\b")],
    "qryinfo":    [_rx(r"\bQRYINFO\b")],
    
    # ============================================================
    # CATEGORIAS PASOE (Progress Application Server)
    # ============================================================
    "pasoe_catalina": [
        _rx(r"\bINFO:.*org\.apache\.catalina\b"),
        _rx(r"\bINFO:.*org\.apache\.coyote\b"),
        _rx(r"\bINFO:.*org\.apache\.tomcat\b"),
        _rx(r"\bStarting service.*Catalina\b"),
        _rx(r"\bServer startup in \[\d+\] milliseconds\b"),
    ],
    "pasoe_websocket": [
        _rx(r"\bWebSocket\b"),
        _rx(r"\bABL WebSocket\b"),
        _rx(r"\bws-endpoint\b"),
    ],
    "pasoe_webhandler": [
        _rx(r"\bWebHandler\b"),
        _rx(r"\bABLWebApp\b"),
        _rx(r"\bWebRequest\b"),
        _rx(r"\bWebResponse\b"),
    ],
    "pasoe_msagent": [
        _rx(r"\bmsagent\s+\d+\b"),
        _rx(r"\bmsas\b"),
        _rx(r"\btransportIdx\b"),
    ],
    "pasoe_security": [
        _rx(r"\boeablSecurity\b"),
        _rx(r"\bspring\.security\b"),
        _rx(r"\bAuthentication\b.*\bPASOE\b"),
    ],
    
    # ============================================================
    # CATEGORIAS APPSERVER (Classic Progress AppServer)
    # ============================================================
    "appserver_broker": [
        _rx(r"\bBroker\s+(started|stopped|pid)\b"),
        _rx(r"\b_mprosrv\b"),
        _rx(r"\bbroker.*port\s+\d+\b"),
        _rx(r"\bnameserver\b"),
    ],
    "appserver_agent": [
        _rx(r"\bAgent\s+(process|started|stopped)\b"),
        _rx(r"\bagent\s+\d+\b"),
        _rx(r"\bNo agents available\b"),
    ],
    "appserver_connection": [
        _rx(r"\bAppServer.*connected\b"),
        _rx(r"\bAppServer.*disconnected\b"),
        _rx(r"\bConnection to broker\b"),
    ],
    
    # ============================================================
    # CATEGORIAS LOGIX (TOTVS LOGIX)
    # ============================================================
    "logix_framework": [
        _rx(r"\bLOGIX Framework\b"),
        _rx(r"\bTOTVS - FRW\b"),
        _rx(r"\bFRW:\b"),
        _rx(r"\bLOG4J\b"),
    ],
    "logix_nfe": [
        _rx(r"\bNFE:\b"),
        _rx(r"\bDANFE\b"),
        _rx(r"\bSEFAZ\b"),
        _rx(r"\bSchema XML.*NFe\b"),
        _rx(r"\.xml\.nfe\b"),
    ],
    "logix_validacao": [
        _rx(r"\bValidação de schema\b"),
        _rx(r"\bValidação.*XML\b"),
        _rx(r"\bSchema validation\b"),
    ],
    
    # ============================================================
    # CATEGORIAS GENÉRICAS (TODOS OS TIPOS)
    # ============================================================
    "heartbeat": [
        _rx(r"\bSetting attention flag for database\b"),
        _rx(r"\bClient notify thread: time to check\b"),
        _rx(r"\bChecking notification for database\b"),
        _rx(r"\bping\b"),
        _rx(r"\bheartbeat\b"),
        _rx(r"\bkeepalive\b"),
    ],
    "debug_trace": [
        _rx(r"\bDEBUG:\b"),
        _rx(r"\bTRACE:\b"),
        _rx(r"\bVERBOSE:\b"),
    ],
    "info_messages": [
        _rx(r"\bINFO:\b.*\b(started|stopped|initialized|loaded)\b"),
    ],
}

# Nomes amigáveis para exibição no frontend
CATEGORY_DISPLAY_NAMES = {
    # ============================================================
    # CATEGORIAS DATASUL/PROGRESS (ORIGINAIS)
    # ============================================================
    "traducao": "Tradução/Literais",
    "facelift": "Facelift UI",
    "rpw": "RPW (Pedidos de Execução)",
    "di": "DI (Desktop Integration)",
    "ls": "License Server",
    "ddk": "DDK (Development Kit)",
    "bos": "BOS (Business Object Services)",
    "fluig": "Fluig",
    "eai": "EAI (Enterprise Application Integration)",
    
    # Tipos Progress
    "dbconnects": "Conexões de Banco",
    "proevents": "Eventos Progress",
    "dynobjects": "Objetos Dinâmicos",
    "4gltrans": "Transações 4GL",
    "fileid": "Identificadores de Arquivo",
    "4glmessages": "Mensagens 4GL",
    "4gltrace": "Trace 4GL",
    "qryinfo": "Informações de Query",
    
    # ============================================================
    # CATEGORIAS PASOE
    # ============================================================
    "pasoe_catalina": "PASOE - Catalina/Tomcat (INFO)",
    "pasoe_websocket": "PASOE - WebSocket",
    "pasoe_webhandler": "PASOE - WebHandler",
    "pasoe_msagent": "PASOE - MS Agent",
    "pasoe_security": "PASOE - Segurança",
    
    # ============================================================
    # CATEGORIAS APPSERVER
    # ============================================================
    "appserver_broker": "AppServer - Broker",
    "appserver_agent": "AppServer - Agent",
    "appserver_connection": "AppServer - Conexões",
    
    # ============================================================
    # CATEGORIAS LOGIX
    # ============================================================
    "logix_framework": "LOGIX - Framework/FRW",
    "logix_nfe": "LOGIX - NFe/DANFE/SEFAZ",
    "logix_validacao": "LOGIX - Validação XML",
    
    # ============================================================
    # CATEGORIAS GENÉRICAS
    # ============================================================
    "heartbeat": "Heartbeat/Ping (Todos os tipos)",
    "debug_trace": "Debug/Trace (Todos os tipos)",
    "info_messages": "Mensagens INFO (Todos os tipos)",
}

def _iter_lines_from_content(content: str) -> Iterable[str]:
    """Itera sobre as linhas do conteúdo do arquivo"""
    for line in content.splitlines():
        yield line

def identify_content(
    content: str,
    *,
    limit_samples_per_cat: int = 10,
    must_start_with_bracket: bool = True,
    min_line_len: int = 60,
) -> dict:
    """
    Percorre o conteúdo e devolve:
    {
      "totals": {"_considered": N, "_unmatched": M, "<categoria>": count, ...},
      "samples": {"<categoria>": ["linha1", ...] }
    }
    """
    totals = {"_considered": 0, "_unmatched": 0}
    for k in CATEGORIES: totals[k] = 0
    samples: Dict[str, List[str]] = {k: [] for k in CATEGORIES}

    for line in _iter_lines_from_content(content):
        s = line.strip()
        if not s:
            continue
        if must_start_with_bracket and not s.startswith("["):
            continue
        if len(s) < min_line_len:
            continue

        totals["_considered"] += 1
        matched_any = False
        for name, patterns in CATEGORIES.items():
            if any(p.search(s) for p in patterns):
                totals[name] += 1
                matched_any = True
                if len(samples[name]) < limit_samples_per_cat:
                    samples[name].append(s[:2000])  # evita estourar JSON
        if not matched_any:
            totals["_unmatched"] += 1

    return {"totals": totals, "samples": samples}

def clean_log_content(
    content: str,
    categories_to_remove: List[str],
    *,
    must_start_with_bracket: bool = True,
    min_line_len: int = 60,
) -> str:
    """
    Remove as linhas que correspondem às categorias especificadas.
    Retorna o conteúdo limpo.
    """
    cleaned_lines = []
    patterns_to_remove = []
    
    # Coletarodos os padrões das categorias a serem removidas
    for category in categories_to_remove:
        if category in CATEGORIES:
            patterns_to_remove.extend(CATEGORIES[category])
    
    for line in _iter_lines_from_content(content):
        s = line.strip()
        
        # Se a linha está vazia, manter
        if not s:
            cleaned_lines.append(line)
            continue
            
        # Aplicar os mesmos filtros da análise
        if must_start_with_bracket and not s.startswith("["):
            cleaned_lines.append(line)
            continue
        if len(s) < min_line_len:
            cleaned_lines.append(line)
            continue
        
        # Verificar se a linha corresponde a algum padrão das categorias a serem removidas
        should_remove = False
        for pattern in patterns_to_remove:
            if pattern.search(s):
                should_remove = True
                break
        
        # Se não deve ser removida, manter a linha
        if not should_remove:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

class LogCleaner:
    """Classe principal para limpeza de logs Progress"""
    
    def __init__(self):
        self.categories = CATEGORIES
        self.category_names = CATEGORY_DISPLAY_NAMES
    
    def analyze_log(self, content: str) -> dict:
        """Analisa o log e retorna estatísticas por categoria"""
        return identify_content(content)
    
    def get_category_info(self) -> dict:
        """Retorna informações sobre todas as categorias disponíveis"""
        return {
            "categories": list(CATEGORIES.keys()),
            "display_names": CATEGORY_DISPLAY_NAMES,
            "groups": {
                "negocio": {
                    "name": "Negócio / TOTVS",
                    "categories": ["traducao", "facelift", "rpw", "di", "ls", "ddk", "bos", "fluig", "eai"]
                },
                "progress": {
                    "name": "Tipos Progress",
                    "categories": ["dbconnects", "proevents", "dynobjects", "4gltrans", "fileid", "4glmessages", "4gltrace", "qryinfo"]
                }
            }
        }
    
    def clean_log(self, content: str, categories_to_remove: List[str]) -> dict:
        """
        Limpa o log removendo as categorias especificadas.
        Retorna estatísticas do antes/depois e o conteúdo limpo.
        """
        # Analisar o log original
        original_analysis = self.analyze_log(content)
        
        # Limpar o log
        cleaned_content = clean_log_content(content, categories_to_remove)
        
        # Analisar o log limpo
        cleaned_analysis = self.analyze_log(cleaned_content)
        
        # Calcular estatísticas de limpeza
        original_lines = len(content.splitlines())
        cleaned_lines = len(cleaned_content.splitlines())
        removed_lines = original_lines - cleaned_lines
        
        return {
            "success": True,
            "original_analysis": original_analysis,
            "cleaned_analysis": cleaned_analysis,
            "statistics": {
                "original_lines": original_lines,
                "cleaned_lines": cleaned_lines,
                "removed_lines": removed_lines,
                "removal_percentage": round((removed_lines / original_lines * 100), 2) if original_lines > 0 else 0,
                "categories_removed": categories_to_remove
            },
            "cleaned_content": cleaned_content
        }