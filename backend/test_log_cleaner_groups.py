#!/usr/bin/env python3
"""Testes direcionados para agrupamento e limpeza multi-família do log cleaner."""

from log_cleaner import (
    LogCleaner,
    build_grouped_category_matches,
    get_categories_for_log_type,
    resolve_cleaner_log_type,
)


def test_log_cleaner_exposes_supported_category_groups():
    cleaner = LogCleaner()

    info = cleaner.get_category_info()

    assert "pasoe" in info["groups"]
    assert "appserver" in info["groups"]
    assert "logix" in info["groups"]
    assert "protheus" in info["groups"]
    assert "web_java" in info["groups"]
    assert "generic" in info["groups"]


def test_log_cleaner_filters_categories_by_selected_log_type():
    progress_categories = get_categories_for_log_type("progress")
    pasoe_categories = get_categories_for_log_type("pasoe")
    protheus_categories = get_categories_for_log_type("protheus")

    assert "traducao" in progress_categories
    assert "4gltrace" in progress_categories
    assert "pasoe_catalina" not in progress_categories

    assert "pasoe_catalina" in pasoe_categories
    assert "traducao" not in pasoe_categories

    assert "protheus_runtime" in protheus_categories
    assert "protheus_repository" in protheus_categories
    assert "traducao" not in protheus_categories


def test_log_cleaner_auto_uses_detected_type_and_keeps_progress_family():
    selected_log_type, effective_log_type = resolve_cleaner_log_type("auto", "datasul")
    info = LogCleaner().get_category_info(effective_log_type)

    assert selected_log_type == "auto"
    assert effective_log_type == "datasul"
    assert "traducao" in info["categories"]
    assert "4gltrace" in info["categories"]
    assert "pasoe_catalina" not in info["categories"]


def test_log_cleaner_auto_maps_protheus_advpl_alias_to_protheus_family():
    selected_log_type, effective_log_type = resolve_cleaner_log_type("auto", "Protheus/ADVPL")
    info = LogCleaner().get_category_info(effective_log_type)

    assert selected_log_type == "auto"
    assert effective_log_type == "protheus"
    assert "protheus_runtime" in info["categories"]
    assert "protheus_infra" in info["categories"]
    assert "traducao" not in info["categories"]


def test_log_cleaner_groups_supported_log_families():
    cleaner = LogCleaner()
    content = """
09:00:00,225 ERROR [com.fluig.foundation] Dataset timeout while processing request
2024-01-20 10:30:45 ERROR [org.jboss.as.controller.management-operation] WFLYCTL0013: Operation failed
10.80.73.148 - - [08/Sep/2017:11:24:44 -0300] "GET /app HTTP/1.1" 500 25363
2024-01-20 10:30:46 INFO: service started successfully
[25/11/24@10:22:09.922-0300] SEVERE: Exception in WebHandler
[25/11/24@10:22:11.200-0300] P-002448 T-013058 Agent process started
TOTVS - FRW: Starting application
[25/11/24@10:22:10.100-0300] P-002448 T-001164 2 4GL CONNECTS connection established
THREAD ERROR ([275], TP|SD|HTTP@T1|TRUE_, 7C971194EB7C4AD3A009846577DE8711)   01/12/2025   19:57:14
""".strip()

    analysis = cleaner.analyze_log(content)
    grouped = build_grouped_category_matches(analysis)

    assert grouped["negocio"]["items"]["fluig"]["count"] >= 1
    assert grouped["progress"]["items"]["dbconnects"]["count"] >= 1
    assert grouped["pasoe"]["items"]["pasoe_webhandler"]["count"] >= 1
    assert grouped["appserver"]["items"]["appserver_agent"]["count"] >= 1
    assert grouped["logix"]["items"]["logix_framework"]["count"] >= 1
    assert grouped["protheus"]["items"]["protheus_runtime"]["count"] >= 1
    assert grouped["web_java"]["items"]["jboss"]["count"] >= 1
    assert grouped["web_java"]["items"]["web_access"]["count"] >= 1


def test_log_cleaner_detects_and_removes_protheus_categories():
    cleaner = LogCleaner()
    content = """
THREAD ERROR ([275], TP|SD|HTTP@T1|TRUE_, 7C971194EB7C4AD3A009846577DE8711)   01/12/2025   19:57:14
variable does not exist B2_MSIDENT
Invalid ReadMSInt in file /usr/local/lib/memstream.hpp at line 657
Linha funcional que deve permanecer no arquivo final.
""".strip()

    analysis = cleaner.analyze_log(content)
    grouped = build_grouped_category_matches(analysis, allowed_categories=get_categories_for_log_type("protheus"))
    result = cleaner.clean_log(content, ["protheus_runtime", "protheus_infra"])

    assert analysis["format_info"]["format"] == "protheus"
    assert grouped["protheus"]["items"]["protheus_runtime"]["count"] >= 1
    assert grouped["protheus"]["items"]["protheus_infra"]["count"] >= 1
    assert "THREAD ERROR" not in result["cleaned_content"]
    assert "Invalid ReadMSInt" not in result["cleaned_content"]
    assert "Linha funcional que deve permanecer" in result["cleaned_content"]


def test_log_cleaner_removes_non_progress_supported_families():
    cleaner = LogCleaner()
    content = """
2024-01-20 10:30:45 ERROR [org.jboss.as.controller.management-operation] WFLYCTL0013: Operation failed
10.80.73.148 - - [08/Sep/2017:11:24:44 -0300] "GET /app HTTP/1.1" 500 25363
Linha funcional que deve permanecer no arquivo final.
""".strip()

    result = cleaner.clean_log(content, ["jboss", "web_access"])

    assert result["success"] is True
    assert "WFLYCTL0013" not in result["cleaned_content"]
    assert 'GET /app HTTP/1.1' not in result["cleaned_content"]
    assert "Linha funcional que deve permanecer" in result["cleaned_content"]
    assert result["statistics"]["removed_lines"] == 2