#!/usr/bin/env python3
"""Teste simples para validar subtipos estruturados por família de log."""

from structured_log_parser import StructuredLogParser
from log_analyzer import LogAnalyzer


def test_structured_subtypes():
    parser = StructuredLogParser()

    cases = [
        (
            "2024-01-20 10:30:45 ERROR [org.apache.catalina.core.StandardWrapperValve] Servlet.service() for servlet [default] threw exception",
            "tomcat",
            "exception"
        ),
        (
            "2024-01-20 10:30:45 ERROR [org.jboss.as.controller.management-operation] WFLYCTL0013: Operation failed",
            "jboss",
            "application"
        ),
        (
            "[25/11/24@10:22:11.200-0300] P-002448 T-013058 2 4GL ERROR PASOE not responding",
            "pasoe",
            "availability"
        ),
        (
            "[25/11/24@10:22:12.300-0300] P-002448 T-013059 4 4GL ERROR Table customer full table scan factor 87%",
            "progress_tabanalys",
            "table_analysis"
        ),
        (
            "[25/11/24@10:22:10.100-0300] P-002448 T-013057 Broker is not available for connections",
            "appbroker",
            "availability"
        ),
        (
            "[25/11/24@10:22:09.922-0300] SEVERE: Exception in WebHandler",
            "pasoe",
            "exception"
        ),
        (
            "10.80.73.148 - - [08/Sep/2017:11:24:44 -0300] \"GET /app HTTP/1.1\" 500 25363",
            "acesso",
            "server_error"
        ),
        (
            "mfg/src/pedido.p mfg/src/pedido.p 120 SEARCH customer idx_customer WHOLE-INDEX",
            "progress_xref",
            "xref"
        ),
        (
            "customer 120000 64 12 8 4 2 870",
            "progress_tabanalys",
            "table_analysis"
        ),
        (
            "[2024-01-10 10:30:45] TOTVS - FRW: Iniciando processamento",
            "logix",
            "framework"
        )
    ]

    for content, expected_subtype, expected_category in cases:
        event = parser.parse_line(content, 1)
        assert event.get("log_subtype") == expected_subtype, f"subtipo inválido: {event}"
        assert event.get("category") == expected_category, f"categoria inválida: {event}"
        assert event.get("legacy_parser"), f"mapeamento legado ausente: {event}"


def test_structured_domain_enrichment():
    parser = StructuredLogParser()

    access_event = parser.parse_line(
        "10.80.73.148 - - [08/Sep/2017:11:24:44 -0300] \"GET /api/login?redirect=/home HTTP/1.1\" 500 25363",
        1
    )
    assert access_event["domain_fields"]["route"] == "/api/login"
    assert "http_5xx" in access_event["insight_tags"]
    assert "api_endpoint" in access_event["insight_tags"]
    assert access_event["recommendation_hint"] == "investigate_server_error"

    pasoe_event = parser.parse_line(
        "[25/11/24@10:22:09.922-0300] SEVERE: Exception in WebHandler while starting PASOE instance",
        2
    )
    assert pasoe_event["domain_fields"]["web_component"] == "WebHandler"
    assert pasoe_event["domain_fields"]["lifecycle_event"] == "start"
    assert "pasoe_incident" in pasoe_event["insight_tags"] or "java_exception" in pasoe_event["insight_tags"]
    assert pasoe_event["recommendation_hint"] in ["inspect_pasoe_web_stack", "review_pasoe_lifecycle"]

    appbroker_event = parser.parse_line(
        "[25/11/24@10:22:10.100-0300] P-002448 T-013057 Broker is not available for connections",
        3
    )
    assert appbroker_event["domain_fields"]["process_id"] == 2448
    assert "broker_unavailable" in appbroker_event["insight_tags"]
    assert appbroker_event["recommendation_hint"] == "verify_broker_availability"

    progress_event = parser.parse_line(
        "[25/11/24@10:22:12.300-0300] P-002448 T-013059 2 4GL Program faturamento.p took 6500 ms to complete",
        4
    )
    assert progress_event["domain_fields"]["program_name"] == "faturamento.p"
    assert progress_event["domain_fields"]["duration_ms"] == 6500.0
    assert "slow_operation" in progress_event["insight_tags"]
    assert progress_event["recommendation_hint"] in ["inspect_progress_program", "review_slow_program"]

    tabanalys_event = parser.parse_line(
        "customer 120000 64 12 8 4 2 870",
        5
    )
    assert tabanalys_event["domain_fields"]["table_name"] == "customer"
    assert tabanalys_event["domain_fields"]["factor"] == 87.0
    assert tabanalys_event["recommendation_hint"] == "urgent_dump_load"

    xref_event = parser.parse_line(
        "mfg/src/pedido.p mfg/src/pedido.p 120 SEARCH customer idx_customer WHOLE-INDEX",
        6
    )
    assert xref_event["domain_fields"]["xref_type"] == "READ"
    assert xref_event["domain_fields"]["full_scan"] is True
    assert "full_scan" in xref_event["insight_tags"]
    assert xref_event["recommendation_hint"] == "review_full_scan_reference"

    logix_event = parser.parse_line(
        "[THREAD 4107975584] [DEBUG] [2024-01-10 10:30:45] COMMAND: SELECT * FROM EMSCAD WHERE COD_ESTAB = 1",
        7
    )
    assert logix_event["log_subtype"] == "logix"
    assert logix_event["domain_fields"]["command_type"] == "SELECT"
    assert logix_event["recommendation_hint"] == "review_logix_sql"
    assert "sql_select" in logix_event["insight_tags"]


def test_analyzer_structured_output():
    analyzer = LogAnalyzer()
    content = """
2024-01-20 10:30:45 ERROR [org.apache.catalina.core.StandardWrapperValve] Servlet.service() for servlet [default] threw exception
[25/11/24@10:22:11.200-0300] P-002448 T-013058 2 4GL ERROR PASOE not responding
[25/11/24@10:22:10.100-0300] P-002448 T-013057 Broker is not available for connections
[25/11/24@10:22:12.300-0300] P-002448 T-013059 4 4GL ERROR Table customer full table scan factor 87%
[THREAD 4107975584] [DEBUG] [2024-01-10 10:30:45] COMMAND: SELECT * FROM EMSCAD WHERE COD_ESTAB = 1
mfg/src/pedido.p mfg/src/pedido.p 120 SEARCH customer idx_customer WHOLE-INDEX
""".strip()

    result = analyzer.analyze_log_content(content, enable_structured_parsing=True)
    assert result["success"] is True
    assert result.get("structured_analysis") is not None
    assert result["structured_analysis"]["subtype_breakdown"].get("tomcat") == 1
    assert result["structured_analysis"]["subtype_breakdown"].get("pasoe") == 1
    assert result["structured_analysis"]["subtype_breakdown"].get("appbroker") == 1
    assert result["structured_analysis"]["subtype_breakdown"].get("logix") == 1
    assert result["structured_analysis"]["subtype_breakdown"].get("progress_xref") == 1

    by_subtype = {item.get("log_subtype"): item for item in result["results"] if item.get("log_subtype")}

    assert by_subtype["tomcat"]["category"] == "Infra/Tomcat"
    assert by_subtype["tomcat"]["severity"] == "Crítico"
    assert by_subtype["pasoe"]["category"] == "Infra/PASOE"
    assert by_subtype["pasoe"]["severity"] == "Crítico"
    assert by_subtype["appbroker"]["category"] == "Infra/AppServer"
    assert by_subtype["appbroker"]["severity"] == "Crítico"
    assert by_subtype["progress_tabanalys"]["category"] == "Performance/DB"
    assert by_subtype["progress_tabanalys"]["severity"] in ["Alto", "Crítico"]
    assert by_subtype["pasoe"]["domain_fields"]["web_component"] in [None, "WebHandler"]
    assert by_subtype["appbroker"]["recommendation_hint"] == "verify_broker_availability"
    assert by_subtype["logix"]["category"] == "SQL/LOGIX"
    assert by_subtype["progress_xref"]["category"] == "Framework/XRef"
    assert "specialized_metrics" in result["structured_analysis"]
    assert "recommendation_hints" in result["structured_analysis"]["specialized_metrics"]
    assert result["structured_analysis"]["specialized_metrics"]["logix_kpis"]["top_command_types"][0]["command_type"] == "SELECT"


if __name__ == "__main__":
    test_structured_subtypes()
    test_structured_domain_enrichment()
    test_analyzer_structured_output()
    print("OK - structured subtype tests passed")