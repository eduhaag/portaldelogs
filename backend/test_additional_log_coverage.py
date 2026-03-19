#!/usr/bin/env python3
"""Cobertura adicional para tipos de log e rotas ainda sem regressão dedicada."""

import asyncio
import importlib
import io
import sys

from fastapi import UploadFile

from log_analyzer import LogAnalyzer
from structured_log_parser import StructuredLogParser


SAMPLE_PROFILER_OUT = """
3 02/28/2026 "Sessao Profiler Teste" 10:00:00 usuario.teste
0 "Session" "" 0
1 "main.p" "" 123
2 "calc.p" "" 124
3 "dbfind.p" "" 125
0 0 1 1
1 10 2 5
2 20 3 120
0 0 1 150.0 150.0
1 0 1 60.0 80.0
2 0 5 50.0 60.0
2 20 5 15.0 18.0
3 0 120 30.0 35.0
3 42 120 30.0 35.0
1 10 0.100000 0.000000
2 20 0.200000 0.100000
""".strip()


def test_generic_java_subtype_parser_and_analyzer():
    parser = StructuredLogParser()
    event = parser.parse_line(
        "2024-01-20 10:30:45 ERROR [com.example.billing.InvoiceService] java.lang.IllegalStateException: invoice batch aborted",
        1,
    )

    assert event["parsed_successfully"] is True
    assert event["log_type"] == "java"
    assert event["log_subtype"] == "java"
    assert event["category"] == "exception"
    assert event["recommendation_hint"] == "inspect_java_stacktrace"
    assert event["exception_class"] == "java.lang.IllegalStateException"

    analyzer = LogAnalyzer()
    result = analyzer.analyze_log_content(
        "2024-01-20 10:30:45 ERROR [com.example.billing.InvoiceService] java.lang.IllegalStateException: invoice batch aborted",
        enable_structured_parsing=True,
    )

    assert result["success"] is True
    assert result["structured_analysis"]["subtype_breakdown"].get("java") == 1


def test_java_multiline_stacktrace_grouping():
    parser = StructuredLogParser()
    content = """
2024-01-20 10:30:45 ERROR [com.example.billing.InvoiceService] java.lang.NullPointerException: invoice payload missing
    at com.example.billing.InvoiceService.process(InvoiceService.java:42)
    at com.example.billing.JobRunner.run(JobRunner.java:15)
Caused by: java.lang.IllegalArgumentException: customer id missing
""".strip()

    result = parser.parse_log_content(content, enable_multiline=True)

    assert result["success"] is True
    assert result["structured_events"] == 1

    event = result["events"][0]
    assert event["parsed_successfully"] is True
    assert event["log_type"] == "java"
    assert event["log_subtype"] == "java"
    assert "stack_trace" in event
    assert "InvoiceService.process" in event["stack_trace"]
    assert event["exception_class"] == "java.lang.NullPointerException"


async def _call_profiler_route():
    server = importlib.import_module("server")
    upload = UploadFile(
        filename="profile.out",
        file=io.BytesIO(SAMPLE_PROFILER_OUT.encode("utf-8")),
    )
    return await server.analyze_profiler_file(upload)


def test_analyze_profiler_route_payload(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb://127.0.0.1:27017")
    monkeypatch.setenv("DB_NAME", "centralizador_test")

    if "server" in sys.modules:
        del sys.modules["server"]

    result = asyncio.run(_call_profiler_route())

    assert result["success"] is True
    assert result["filename"] == "profile.out"
    assert result["session"]["description"] == "Sessao Profiler Teste"
    assert result["summary"]["total_modules"] == 4
    assert len(result["top_bottlenecks"]) >= 3
    assert result["analysis"]["call_tree_stats"]["total_relationships"] == 3