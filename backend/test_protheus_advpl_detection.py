from log_analyzer import LogAnalyzer
from structured_log_parser import StructuredLogParser
from totvs_errors_loader import TotvsErrorsLoader


PROTHEUS_SAMPLE_LOG = """
2025-12-01T19:51:44.654543+00:00 123|
[FATAL][SERVER] [01/12/2025 19:51:44] Failed to read status of inifile [/opt/totvs/appserver/language.ini][2][No such file or directory]
2025-12-01T19:57:14.320740+00:00 275|
THREAD ERROR ([275], TP|SD|HTTP@T1|TRUE_, 7C971194EB7C4AD3A009846577DE8711)   01/12/2025   19:57:14
variable does not exist B2_MSIDENT
 on AC.ACCALC.REPOSITORY.ACCALCREP:LOGERRORPROC(ACCALCREPOSITORY.TLPP) 17/04/2023 17:40:39 line : 78
Called from GRAVALOG(APLIB060.PRW) 31/10/2025 17:03:17 line : 1401
[VDRPORT] 251201_194616 7FBD43D4 BPC2112 E x 01 ctx:300002 MULTIPORT - error 5 unrecognized client [GET /81f45506-e92d-435e-8fdc-d4b] 10.233.95.131:44341
Cannot find method QLTQUERYMANAGER:VALIDATAMANHOCAMPOSCHAVENF on Q215ATURES(QIEA215.PRW) 02/12/2025 17:29:16 line : 470
Invalid ReadMSInt in file /usr/local/bamboo/xml-data/build-dir/TP11-OF2431X-APPSRVLIN64/lib_base/memstream.hpp at line 657
""".strip()


def test_detects_protheus_advpl_log_type():
    analyzer = LogAnalyzer()

    detected_type = analyzer.detect_log_type(PROTHEUS_SAMPLE_LOG)

    assert detected_type == "Protheus/ADVPL"


def test_totvs_loader_matches_protheus_patterns():
    loader = TotvsErrorsLoader()

    cases = [
        ("variable does not exist B2_MSIDENT", "Protheus/ADVPL"),
        ("Cannot find method QLTQUERYMANAGER:VALIDATAMANHOCAMPOSCHAVENF", "Protheus/ADVPL"),
        ("Invalid ReadMSInt in file memstream.hpp at line 657", "Protheus/ADVPL"),
        ("[FATAL][SERVER] Failed to read status of inifile [/opt/totvs/appserver/language.ini][2][No such file or directory]", "Protheus/ADVPL"),
        ("[VDRPORT] BPC2112 MULTIPORT - error 5 unrecognized client", "Protheus/ADVPL"),
    ]

    for line, expected_product in cases:
        result = loader.check_error_partial(line)
        assert result is not None, f"pattern not detected: {line}"
        assert result.get("product") == expected_product


def test_structured_parser_parses_protheus_thread_error():
    parser = StructuredLogParser()

    event = parser.parse_line(
        "THREAD ERROR ([275], TP|SD|HTTP@T1|TRUE_, 7C971194EB7C4AD3A009846577DE8711)   01/12/2025   19:57:14",
        1,
        preferred_log_type="Protheus/ADVPL"
    )

    assert event.get("parsed_successfully") is True
    assert event.get("log_subtype") == "protheus_advpl"
    assert event.get("severity") == "Crítico"
    assert event.get("category") == "application"


def test_analyzer_enriches_protheus_advpl_errors():
    analyzer = LogAnalyzer()
    analyzer.totvs_loader = TotvsErrorsLoader()

    result = analyzer.analyze_log_content(
        PROTHEUS_SAMPLE_LOG,
        enable_structured_parsing=True,
        detected_log_type="Protheus/ADVPL"
    )

    assert result["success"] is True
    assert result["log_type"] == "Protheus/ADVPL"
    assert result.get("structured_analysis") is not None

    protheus_results = [item for item in result["results"] if item.get("error_type") == "Protheus/ADVPL"]
    assert len(protheus_results) >= 4

    messages = "\n".join(item.get("clean_message", "") for item in protheus_results)
    assert "variable does not exist B2_MSIDENT" in messages
    assert "Cannot find method QLTQUERYMANAGER:VALIDATAMANHOCAMPOSCHAVENF" in messages
    assert any(item.get("product") == "Protheus/ADVPL" for item in protheus_results)