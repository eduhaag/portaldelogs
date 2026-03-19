#!/usr/bin/env python3
"""Regressão do ProfilerAnalyzer alinhada ao fonte legado."""

from profiler_analyzer import ProgressProfilerParser, ProfilerAnalyzer


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


def test_progress_profiler_parser_legacy_layout():
    parser = ProgressProfilerParser(SAMPLE_PROFILER_OUT)
    parser.parse()

    assert parser.session is not None
    assert parser.session.version == 3
    assert parser.session.description == "Sessao Profiler Teste"
    assert parser.session.time == "10:00:00"
    assert parser.session.user == "usuario.teste"
    assert parser.session.total_time == 150.0

    assert len(parser.sources) == 4
    assert parser.sources[2].name == "calc.p"
    assert parser.sources[2].call_count == 5
    assert parser.sources[2].total_time == 65.0
    assert round(parser.sources[2].avg_time, 2) == 13.0
    assert parser.sources[3].call_count == 120
    assert parser.sources[3].first_line == 42
    assert len(parser.trace_info) == 2


def test_profiler_analyzer_frontend_payload():
    analyzer = ProfilerAnalyzer()
    result = analyzer.analyze_file_content(SAMPLE_PROFILER_OUT)

    assert result["success"] is True
    assert result.get("analysis") is not None
    assert result["session"]["description"] == "Sessao Profiler Teste"
    assert result["summary"]["total_modules"] == 4
    assert result["analysis"]["call_tree_stats"]["total_relationships"] == 3
    assert len(result["analysis"]["top_modules_by_time"]) >= 3
    assert len(result["top_bottlenecks"]) >= 3
    assert result["raw_data"]["trace_info_count"] == 2


if __name__ == "__main__":
    test_progress_profiler_parser_legacy_layout()
    test_profiler_analyzer_frontend_payload()
    print("OK - profiler analyzer validated")
