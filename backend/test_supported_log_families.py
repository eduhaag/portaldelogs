#!/usr/bin/env python3
"""Validação ampla dos tipos de logs suportados pelo parser e pelo analisador."""

from structured_log_parser import StructuredLogParser
from log_analyzer import LogAnalyzer


def test_structured_supported_families():
    parser = StructuredLogParser()

    cases = [
        (
            "10.80.73.148 - - [08/Sep/2017:11:24:44 -0300] \"GET /app HTTP/1.1\" 500 25363",
            "acesso",
            "server_error"
        ),
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
            "09:00:00,225 ERROR [com.fluig.foundation] Dataset timeout while processing request",
            "fluig",
            "performance"
        ),
        (
            "[25/11/24@10:22:09.922-0300] SEVERE: Exception in WebHandler",
            "pasoe",
            "exception"
        ),
        (
            "[25/11/24@10:22:11.200-0300] P-002448 T-013058 ERROR: AppServer process died unexpectedly",
            "appserver",
            "availability"
        ),
        (
            "[25/11/24@10:22:10.100-0300] P-002448 T-013057 Broker is not available for connections",
            "appbroker",
            "availability"
        ),
        (
            "[25/11/24@10:22:10.100-0300] P-002448 T-001164 2 4GL ERROR Cannot connect to database 'emsdb'",
            "progress_db",
            "database"
        ),
        (
            "[25/11/24@10:22:10.100-0300] P-002448 T-001164 4 4GL ERROR Memory leak detected for object CustomerTempTable handle 999",
            "progress_memory",
            "memory"
        ),
        (
            "[25/11/24@10:22:12.300-0300] P-002448 T-013059 4 4GL ERROR Table customer full table scan factor 87%",
            "progress_tabanalys",
            "table_analysis"
        ),
        (
            "[25/11/24@10:22:12.300-0300] P-002448 T-013059 2 4GL XREF include file customer.i caller mfg/prog/teste.p",
            "progress_xref",
            "xref"
        ),
        (
            "[25/11/24@10:22:12.300-0300] P-002448 T-013059 2 4GL Program faturamento.p took 6500 ms to complete",
            "app_performance",
            "performance"
        ),
        (
            "[25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL ERROR FT7394: Cannot find procedure /usr/datasul/prg/nfe_transmissao.p",
            "progress",
            "application"
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
            "[2024-01-10 10:30:45] TOTVS - FRW: Starting application",
            "logix",
            "framework"
        )
    ]

    for content, expected_subtype, expected_category in cases:
        event = parser.parse_line(content, 1)
        assert event.get("parsed_successfully") is True, f"linha não parseada: {content}"
        assert event.get("log_subtype") == expected_subtype, f"subtipo inválido: {event}"
        assert event.get("category") == expected_category, f"categoria inválida: {event}"


def test_analyzer_supported_log_families():
    analyzer = LogAnalyzer()

    log_content = """
10.80.73.148 - - [08/Sep/2017:11:24:44 -0300] "GET /app HTTP/1.1" 500 25363
2024-01-20 10:30:45 ERROR [org.apache.catalina.core.StandardWrapperValve] Servlet.service() for servlet [default] threw exception
2024-01-20 10:30:45 ERROR [org.jboss.as.controller.management-operation] WFLYCTL0013: Operation failed
09:00:00,225 ERROR [com.fluig.foundation] Dataset timeout while processing request
[25/11/24@10:22:09.922-0300] SEVERE: Exception in WebHandler
[25/11/24@10:22:11.200-0300] P-002448 T-013058 ERROR: AppServer process died unexpectedly
[25/11/24@10:22:10.100-0300] P-002448 T-013057 Broker is not available for connections
[25/11/24@10:22:10.100-0300] P-002448 T-001164 2 4GL ERROR Cannot connect to database 'emsdb'
[25/11/24@10:22:10.100-0300] P-002448 T-001164 4 4GL ERROR Memory leak detected for object CustomerTempTable handle 999
[25/11/24@10:22:12.300-0300] P-002448 T-013059 4 4GL ERROR Table customer full table scan factor 87%
[25/11/24@10:22:12.300-0300] P-002448 T-013059 2 4GL XREF include file customer.i caller mfg/prog/teste.p
[25/11/24@10:22:12.300-0300] P-002448 T-013059 2 4GL Program faturamento.p took 6500 ms to complete
[25/11/24@10:22:09.922-0300] P-002448 T-013056 4 4GL ERROR FT7394: Cannot find procedure /usr/datasul/prg/nfe_transmissao.p
TOTVS - FRW: Starting application
[THREAD 4107975584] [DEBUG] [2024-01-10 10:30:45] COMMAND: SELECT * FROM EMSCAD WHERE COD_ESTAB = 1
mfg/src/pedido.p mfg/src/pedido.p 120 SEARCH customer idx_customer WHOLE-INDEX
customer 120000 64 12 8 4 2 870
NFE: Validação de schema XML failed
2024-01-20 10:30:45 ERROR Database connection failed
Exception in thread main: NullPointerException
""".strip()

    result = analyzer.analyze_log_content(log_content, enable_structured_parsing=True)

    assert result["success"] is True
    assert result.get("structured_analysis") is not None

    subtype_breakdown = result["structured_analysis"]["subtype_breakdown"]
    expected_subtypes = [
        "acesso", "tomcat", "jboss", "fluig", "pasoe", "appserver",
        "appbroker", "progress_db", "progress_memory", "progress_tabanalys",
        "progress_xref", "app_performance", "progress", "logix"
    ]

    for subtype in expected_subtypes:
        assert subtype_breakdown.get(subtype, 0) >= 1, f"subtipo ausente: {subtype}"

    assert result["total_results"] >= 10


if __name__ == "__main__":
    test_structured_supported_families()
    test_analyzer_supported_log_families()
    print("OK - supported log families validated")