import os
from io import BytesIO

import version_compare_service
from version_compare_service import VersionCompareService


def _write_r_file(path: str, embedded_version: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as file_handle:
        file_handle.write(f"header[[[{embedded_version}[[[footer".encode("ascii"))


def _write_r_file_without_embedded_version(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as file_handle:
        file_handle.write(b"header-without-embedded-version")


def test_compare_content_searches_current_fix_then_falls_back(tmp_path):
    repo_root = tmp_path / "ems2"
    fix_8_root = repo_root / "12.1.2407.8-SNAPSHOT" / "progress_12" / "bin-gui"
    fix_7_root = repo_root / "12.1.2407.7-SNAPSHOT" / "progress_12" / "bin-gui"

    _write_r_file(str(fix_8_root / "ftp" / "FT0527B.r"), "3.00.00.005")
    _write_r_file(str(fix_7_root / "btb" / "BTR800.R"), "2.00.00.010")

    service = VersionCompareService(base_lib_directory=str(repo_root))

    extrato = """
Versao Produto .: EMS 12.1.2407.8
FTP/FT0527B.R 3.00.00.001 PAI 17/03/26 10:00:00
BTB/BTR800.R 2.00.00.001 PAI 17/03/26 10:00:00
""".strip()

    result = service.compare_content(extrato)

    assert result["summary"]["desatualizados"] == 2

    exact_match = next(item for item in result["desatualizados"] if item["programa"] == "FT0527B.R")
    fallback_match = next(item for item in result["desatualizados"] if item["programa"] == "BTR800.R")

    assert exact_match["deveria_estar"] == "3.00.00.005"
    assert exact_match["fix_encontrada"] == "12.1.2407.8-SNAPSHOT"
    assert exact_match["caminho_encontrado"].endswith(f"ftp{os.sep}FT0527B.r")

    assert fallback_match["deveria_estar"] == "2.00.00.010"
    assert fallback_match["fix_encontrada"] == "12.1.2407.7-SNAPSHOT"
    assert fallback_match["caminho_encontrado"].endswith(f"btb{os.sep}BTR800.R")


def test_compare_content_reuses_relative_path_without_recursive_walk(tmp_path, monkeypatch):
    repo_root = tmp_path / "ems2"
    fix_8_root = repo_root / "12.1.2407.8-SNAPSHOT" / "progress_12" / "bin-gui"
    fix_7_root = repo_root / "12.1.2407.7-SNAPSHOT" / "progress_12" / "bin-gui"

    _write_r_file(str(fix_8_root / "ftp" / "FT0527B.r"), "3.00.00.005")
    _write_r_file(str(fix_7_root / "ftp" / "FT0527B.r"), "3.00.00.004")

    service = VersionCompareService(base_lib_directory=str(repo_root))

    def _unexpected_walk(*_args, **_kwargs):
        raise AssertionError("os.walk nao deveria ser chamado quando o caminho relativo ja eh conhecido")

    monkeypatch.setattr(version_compare_service.os, "walk", _unexpected_walk)

    extrato = """
Versao Produto .: EMS 12.1.2407.8
FTP/FT0527B.R 3.00.00.001 PAI 17/03/26 10:00:00
""".strip()

    result = service.compare_content(extrato)

    assert result["summary"]["desatualizados"] == 1

    exact_match = result["desatualizados"][0]
    assert exact_match["fix_encontrada"] == "12.1.2407.8-SNAPSHOT"
    assert exact_match["caminho_encontrado"].endswith(f"ftp{os.sep}FT0527B.r")


def test_compare_content_fallback_uses_relative_hint_without_indexing_lower_fix(tmp_path, monkeypatch):
    repo_root = tmp_path / "ems2"
    fix_7_root = repo_root / "12.1.2407.7-SNAPSHOT" / "progress_12" / "bin-gui"

    _write_r_file(str(fix_7_root / "btb" / "BTR800.R"), "2.00.00.010")

    service = VersionCompareService(base_lib_directory=str(repo_root))
    indexed_versions: list[str] = []
    original_ensure_program_file_index = service._ensure_program_file_index

    def _record_indexed_version(version: str):
        indexed_versions.append(version)
        return original_ensure_program_file_index(version)

    monkeypatch.setattr(service, "_ensure_program_file_index", _record_indexed_version)

    extrato = """
Versao Produto .: EMS 12.1.2407.8
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
BTB/BTR800.R                          2.00.00.001    PAI                           17/03/26  10:00:00
""".strip()

    result = service.compare_content(extrato)

    assert result["summary"]["desatualizados"] == 1
    assert indexed_versions == []
    assert result["desatualizados"][0]["fix_encontrada"] == "12.1.2407.7-SNAPSHOT"


def test_compare_content_limits_fallback_to_two_previous_fixes_and_fix_one(tmp_path):
    repo_root = tmp_path / "ems2"
    progress_root = tmp_path / "progress_ems2"
    fix_4_root = repo_root / "12.1.2403.4-SNAPSHOT" / "progress_12" / "bin-gui"
    progress_version_root = progress_root / "12.1.2403-SNAPSHOT" / "progress_12" / "bin-gui"

    _write_r_file(str(progress_version_root / "ftp" / "FT0527B.r"), "3.00.00.001")
    os.makedirs(fix_4_root, exist_ok=True)

    service = VersionCompareService(base_lib_directory=str(repo_root), progress_lib_directory=str(progress_root))

    extrato = """
Versao Produto .: EMS 12.1.2403.4
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
FTP/FT0527B.R                         3.00.00.000    PAI                           17/03/26  10:00:00
""".strip()

    result = service.compare_content(extrato)

    assert result["summary"]["desatualizados"] == 1
    assert result["desatualizados"][0]["fix_encontrada"] == "12.1.2403-SNAPSHOT"
    assert result["compare_metrics"]["candidate_versions"] == 1
    assert result["compare_metrics"]["progress_repository_hits"] == 1


def test_compare_content_finds_bodi_program_in_dibo_progress_directory(tmp_path):
    repo_root = tmp_path / "ems2"
    progress_root = tmp_path / "progress_ems2"
    fix_10_root = repo_root / "12.1.2507.10-SNAPSHOT" / "progress_12" / "bin-gui"
    progress_version_root = progress_root / "12.1.2507-SNAPSHOT" / "progress_12" / "bin-gui"

    _write_r_file(str(progress_version_root / "dibo" / "BODI317IN.R"), "2.00.00.030")
    os.makedirs(fix_10_root, exist_ok=True)

    service = VersionCompareService(base_lib_directory=str(repo_root), progress_lib_directory=str(progress_root))

    extrato = """
Versao Produto .: EMS 12.1.2507.10
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
BODI317IN                             2.00.00.001    PAI                           17/03/26  10:00:00
""".strip()

    result = service.compare_content(extrato)

    assert result["summary"]["desatualizados"] == 1
    assert result["desatualizados"][0]["fix_encontrada"] == "12.1.2507-SNAPSHOT"
    assert result["desatualizados"][0]["caminho_encontrado"].endswith(f"dibo{os.sep}BODI317IN.R")
    assert result["compare_metrics"]["progress_repository_hits"] == 1


def test_compare_content_prefers_fix_minus_one_before_fix_one(tmp_path):
    repo_root = tmp_path / "ems2"
    fix_4_root = repo_root / "12.1.2403.4-SNAPSHOT" / "progress_12" / "bin-gui"
    fix_3_root = repo_root / "12.1.2403.3-SNAPSHOT" / "progress_12" / "bin-gui"

    _write_r_file_without_embedded_version(str(fix_4_root / "ftp" / "FT0527B.r"))
    _write_r_file(str(fix_3_root / "ftp" / "FT0527B.r"), "3.00.00.003")

    service = VersionCompareService(base_lib_directory=str(repo_root))

    extrato = """
Versao Produto .: EMS 12.1.2403.4
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
FTP/FT0527B.R                         3.00.00.000    PAI                           17/03/26  10:00:00
""".strip()

    result = service.compare_content(extrato)

    assert result["summary"]["desatualizados"] == 1
    assert result["desatualizados"][0]["fix_encontrada"] == "12.1.2403.3-SNAPSHOT"
    assert result["desatualizados"][0]["deveria_estar"] == "3.00.00.003"
    assert result["compare_metrics"]["files_without_embedded_version"] == 1


def test_extract_product_version_rejects_blank_header_value():
    extrato_sem_versao = """
Criado por .....:navila
Criado em ......:17/03/26 - 08:58:59
Versao Produto .:
Empresa ........:99
""".strip()

    try:
        VersionCompareService.extract_product_version(extrato_sem_versao)
    except ValueError as exc:
        assert str(exc) == "Extrato nao possui versao no cabecalho."
    else:
        raise AssertionError("Era esperado erro para extrato sem versao no cabecalho")


def test_compare_content_returns_partial_payload_when_header_version_is_blank(tmp_path):
    repo_root = tmp_path / "ems2"
    service = VersionCompareService(base_lib_directory=str(repo_root))

    extrato = """
Criado por .....:navila
Criado em ......:17/03/26 - 08:58:59
Versao Produto .:
Empresa ........:99
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
BODI317EF                             2.00.01.189GB1 ft4003                        12/03/26  13:54:33
  APPC:  cdp/cdapi655.p
  UPC :  prmupc/prmupc-bodi317sd.p
CD7070 | SPP-NT2019001 | no | BODI317ef.p
SPP_LOCALIZ_SUL_AMERICA                   no
""".strip()

    result = service.compare_content(extrato)

    assert result["product_version"] == ""
    assert result["summary"]["total_programas_cliente"] == 1
    assert result["summary"]["total_comparados"] == 0
    assert result["summary"]["com_upc"] == 1
    assert result["summary"]["funcoes_ativas"] == 2
    assert result["programas_com_upc"] == [{"programa": "BODI317EF", "caminho": "prmupc/prmupc-bodi317sd.p", "tipo": "UPC"}]
    assert result["funcoes_ativas"][0] == {
        "ativa": False,
        "origem": "CD7070",
        "funcao": "SPP-NT2019001",
        "valor": "no",
        "programa": "BODI317ef.p",
    }
    assert result["index_warning"] == (
        "Extrato nao possui versao no cabecalho. "
        "A comparacao de versoes nao foi executada, mas os dados extras do extrato foram carregados."
    )
    assert result["compare_metrics"]["programs_compared"] == 0


def test_extract_all_client_data_uses_unique_program_and_accepts_version_suffixes():
    extrato = """
Versao Produto .:12.1.2507.9
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
BODI317IN                             2.00.00.030    ft4003                        12/03/26  13:54:27
BODI317                               2.00.00.056    ft4003                        12/03/26  13:54:27
BODI317EF                             2.00.01.188    ft4003a                       10/03/26  15:43:37
BODI317EF                             2.00.01.189GB1 ft4003                        12/03/26  13:54:33
BODI317                               2.00.00.055    ft4002                        11/03/26  10:00:00
""".strip()

    client_data = VersionCompareService.extract_all_client_data(extrato)
    sources = client_data["sources"]

    assert sources["BODI317IN"]["versao"] == "2.00.00.030"
    assert sources["BODI317"]["versao"] == "2.00.00.056"
    assert sources["BODI317EF"]["versao"] == "2.00.01.189GB1"
    assert len([key for key in sources if key == "BODI317"]) == 1


def test_extract_all_client_data_parses_appc_upc_and_functions_until_terminal_section():
    extrato = """
Versao Produto .:12.1.2507.9
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
BODI317EF                             2.00.01.189GB1 ft4003                        12/03/26  13:54:33
  APPC:  cdp/cdapi655.p
  UPC :  prmupc/prmupc-bodi317sd.p
CD7070 | SPP-NT2019001 | no | BODI317ef.p
SPP_LOCALIZ_SUL_AMERICA                   no
Matriz Trad Org  Empresa Ext  Estab Ext  Matriz Trad Dest  Empresa Dest  Estab Dest
  APPC:  deve/ser-ignorado.p
""".strip()

    client_data = VersionCompareService.extract_all_client_data(extrato)

    assert client_data["programs_with_appc"] == [{"programa": "BODI317EF", "caminho": "cdp/cdapi655.p", "tipo": "APPC"}]
    assert client_data["programs_with_upc"] == [{"programa": "BODI317EF", "caminho": "prmupc/prmupc-bodi317sd.p", "tipo": "UPC"}]
    assert client_data["funcoes_ativas"][0] == {
        "ativa": False,
        "origem": "CD7070",
        "funcao": "SPP-NT2019001",
        "valor": "no",
        "programa": "BODI317ef.p",
    }
    assert client_data["funcoes_ativas"][1] == {"funcao": "SPP_LOCALIZ_SUL_AMERICA", "valor": "no", "ativa": False}


def test_extract_all_client_data_parses_pipe_function_without_program_column():
    extrato = """
Versao Produto .:12.1.2507.9
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
BODI317EF                             2.00.01.189GB1 ft4003                        12/03/26  13:54:33
CD7070 | SPP-ISS-RETIDO | no |
CD7070 | SPP-ISS-ATIVO | sim |
""".strip()

    client_data = VersionCompareService.extract_all_client_data(extrato)

    assert client_data["funcoes_ativas"] == [
        {
            "origem": "CD7070",
            "funcao": "SPP-ISS-RETIDO",
            "valor": "no",
            "ativa": False,
        },
        {
            "origem": "CD7070",
            "funcao": "SPP-ISS-ATIVO",
            "valor": "sim",
            "ativa": True,
        },
    ]


def test_compare_content_returns_timings_and_compared_total_excludes_not_found(tmp_path):
    repo_root = tmp_path / "ems2"
    fix_8_root = repo_root / "12.1.2407.8-SNAPSHOT" / "progress_12" / "bin-gui"

    _write_r_file(str(fix_8_root / "ftp" / "FT0527B.r"), "3.00.00.005")

    service = VersionCompareService(base_lib_directory=str(repo_root))

    extrato = """
Versao Produto .: EMS 12.1.2407.8
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
FTP/FT0527B.R                         3.00.00.001    PAI                           17/03/26  10:00:00
BODI999.R                            1.00.00.001    PAI                           17/03/26  10:00:00
""".strip()

    result = service.compare_content(extrato)

    assert result["summary"]["total_comparados"] == 1
    assert result["summary"]["nao_encontrado"] == 1
    assert result["timings"]["extract_client_data_ms"] >= 0
    assert result["timings"]["compare_versions_ms"] >= 0
    assert result["compare_metrics"]["programs_compared"] == 1
    assert result["compare_metrics"]["full_index_lookups"] == 0


def test_extract_embedded_versions_from_stream_handles_find_style_binary_markers():
    payload = (
        b"\x00\x01header"
        b"[[[2.00.00.091[[["
        b"\x10\x11\x12"
        b"\xe2[[[2.00.00.091[[["
        b"\r\n[[[2.00.00.091[[[footer"
    )

    versions = VersionCompareService._extract_embedded_versions_from_stream(BytesIO(payload))

    assert versions == ["2.00.00.091", "2.00.00.091", "2.00.00.091"]


def test_compare_content_skips_known_program_without_embedded_version(tmp_path):
    repo_root = tmp_path / "ems2"
    fix_4_root = repo_root / "12.1.2403.4-SNAPSHOT" / "progress_12" / "bin-gui"
    fix_3_root = repo_root / "12.1.2403.3-SNAPSHOT" / "progress_12" / "bin-gui"

    os.makedirs(fix_4_root, exist_ok=True)
    _write_r_file_without_embedded_version(str(fix_3_root / "ftp" / "FT0527B.r"))

    service = VersionCompareService(base_lib_directory=str(repo_root))

    extrato = """
Versao Produto .: EMS 12.1.2403.4
Programa                              Versao         Programa Pai                  Data      Hora
------------------------------------- -------------- ----------------------------- --------- ----------
FTP/FT0527B.R                         3.00.00.000    PAI                           17/03/26  10:00:00
""".strip()

    result = service.compare_content(extrato)

    assert result["summary"]["total_programas_cliente"] == 1
    assert result["summary"]["total_comparados"] == 0
    assert result["summary"]["nao_encontrado"] == 0
    assert result["compare_metrics"]["skipped_known_programs"] == 1


def test_relative_program_resolution_reuses_cached_directory_listing(tmp_path, monkeypatch):
    repo_root = tmp_path / "ems2"
    search_root = repo_root / "12.1.2407.8-SNAPSHOT" / "progress_12" / "bin-gui"
    target_file = search_root / "ftp" / "FT0527B.R"
    _write_r_file(str(target_file), "3.00.00.005")

    service = VersionCompareService(base_lib_directory=str(repo_root))
    original_listdir = version_compare_service.os.listdir
    listdir_calls: list[str] = []

    def _record_listdir(path: str):
        listdir_calls.append(path)
        return original_listdir(path)

    monkeypatch.setattr(version_compare_service.os, "listdir", _record_listdir)

    resolved_first = service._resolve_relative_program_path(str(search_root), "ftp/FT0527B.R")
    resolved_second = service._resolve_relative_program_path(str(search_root), "ftp/FT0527B.R")

    assert resolved_first == str(target_file)
    assert resolved_second == str(target_file)
    assert listdir_calls.count(str(search_root)) == 1
    assert listdir_calls.count(str(search_root / "ftp")) == 1