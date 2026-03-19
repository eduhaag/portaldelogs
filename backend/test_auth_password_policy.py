#!/usr/bin/env python3
"""Valida a política de senha do cadastro de usuários."""

import asyncio
import importlib
import sys
from pathlib import Path
import local_pattern_store
from log_analyzer import LogAnalyzer


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


POLICY_MESSAGE = "A senha deve ter no mínimo 8 caracteres, incluindo letra maiúscula, número e caractere especial."


def _load_server_module(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb://127.0.0.1:27017")
    monkeypatch.setenv("DB_NAME", "centralizador_test")

    if "server" in sys.modules:
        del sys.modules["server"]

    return importlib.import_module("server")


def _configure_temp_local_store(monkeypatch, tmp_path):
    monkeypatch.setattr(local_pattern_store, "STORE_PATH", tmp_path / "local_pattern_store.json")


def test_password_policy_accepts_valid_password(monkeypatch):
    server = _load_server_module(monkeypatch)

    assert server._validate_auth_password("Senha@123") is None


def test_password_policy_rejects_short_password(monkeypatch):
    server = _load_server_module(monkeypatch)

    assert server._validate_auth_password("Ab@123") == POLICY_MESSAGE


def test_password_policy_rejects_password_without_uppercase(monkeypatch):
    server = _load_server_module(monkeypatch)

    assert server._validate_auth_password("senha@123") == POLICY_MESSAGE


def test_password_policy_rejects_password_without_number(monkeypatch):
    server = _load_server_module(monkeypatch)

    assert server._validate_auth_password("Senha@Teste") == POLICY_MESSAGE


def test_password_policy_rejects_password_without_special_character(monkeypatch):
    server = _load_server_module(monkeypatch)

    assert server._validate_auth_password("Senha1234") == POLICY_MESSAGE


def test_auth_username_validation_accepts_simple_login(monkeypatch):
    server = _load_server_module(monkeypatch)

    assert server._validate_auth_username("portal.suporte_1") is None


def test_auth_username_validation_rejects_invalid_characters(monkeypatch):
    server = _load_server_module(monkeypatch)

    assert server._validate_auth_username("portal suporte") == (
        "O usuário pode conter apenas letras, números, ponto, traço e sublinhado."
    )


def test_auth_email_validation_rejects_invalid_email(monkeypatch):
    server = _load_server_module(monkeypatch)

    assert server._validate_auth_email("usuario-invalido") == "Informe um e-mail válido para concluir o acesso."


def test_auth_probe_switches_immediately_to_local_store(monkeypatch):
    server = _load_server_module(monkeypatch)

    class FailingAdmin:
        async def command(self, *_args, **_kwargs):
            raise RuntimeError("connection refused")

    class FakeClient:
        admin = FailingAdmin()

    monkeypatch.setattr(server, "client", FakeClient())
    monkeypatch.setattr(server, "force_local_store", False)
    monkeypatch.setattr(server, "last_auth_store_probe_at", 0.0)
    monkeypatch.setattr(server, "AUTH_STORE_PROBE_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(server, "AUTH_STORE_PROBE_INTERVAL_SECONDS", 0.0)

    result = asyncio.run(server._ensure_auth_store_ready())

    assert result is True
    assert server.force_local_store is True


def test_startup_event_uses_local_runtime_after_fast_probe(monkeypatch):
    server = _load_server_module(monkeypatch)

    async def _probe_local_store():
        server.force_local_store = True
        return True

    calls = []

    async def _load_custom_patterns(db):
        calls.append(("custom", db))

    async def _init_datasul(db):
        calls.append(("datasul", db))
        return True

    async def _init_logix(db):
        calls.append(("logix", db))
        return True

    async def _init_totvs(db):
        calls.append(("totvs", db))
        return True

    monkeypatch.setattr(server, "_ensure_auth_store_ready", _probe_local_store)
    monkeypatch.setattr(server.analyzer, "load_custom_patterns_from_db", _load_custom_patterns)
    monkeypatch.setattr(server.analyzer, "initialize_datasul_loader", _init_datasul)
    monkeypatch.setattr(server.analyzer, "initialize_logix_loader", _init_logix)
    monkeypatch.setattr(server.analyzer, "initialize_totvs_loader", _init_totvs)

    asyncio.run(server.startup_event())

    assert calls == [
        ("custom", None),
        ("datasul", None),
        ("logix", None),
        ("totvs", None),
    ]


def test_load_log_analysis_records_uses_local_fallback(monkeypatch, tmp_path):
    server = _load_server_module(monkeypatch)
    _configure_temp_local_store(monkeypatch, tmp_path)

    local_pattern_store.insert_record(
        "log_analysis",
        {
            "id": "analysis-1",
            "filename": "fallback.log",
            "timestamp": "2026-03-18T12:00:00",
            "total_results": 3,
        },
    )

    class FailingCollection:
        def find(self, *_args, **_kwargs):
            raise RuntimeError("connection refused")

    class FailingDb:
        log_analysis = FailingCollection()

    monkeypatch.setattr(server, "db", FailingDb())
    monkeypatch.setattr(server, "force_local_store", False)

    records = asyncio.run(server.load_log_analysis_records(10))

    assert len(records) == 1
    assert records[0]["id"] == "analysis-1"
    assert server.force_local_store is True


def test_issue_helpers_support_local_crud(monkeypatch, tmp_path):
    server = _load_server_module(monkeypatch)
    _configure_temp_local_store(monkeypatch, tmp_path)
    monkeypatch.setattr(server, "force_local_store", True)

    issue = {
        "id": "issue-1",
        "ticket": "TCK-1",
        "issue": "ISSUE-1",
        "cliente": "Cliente A",
        "rotina": "SIGACFG",
        "situacao": "Falha ao abrir rotina",
        "status": "Aberto",
        "data_criacao": "18/03/2026",
        "liberado_versoes": "",
    }

    saved = asyncio.run(server.save_issue_record(issue))
    found = asyncio.run(server.find_issue_record({"ticket": "TCK-1"}))
    updated = asyncio.run(server.update_issue_records({"id": "issue-1"}, {"status": "Fechado"}))
    listed = asyncio.run(server.list_issue_records())
    deleted = asyncio.run(server.delete_issue_records({"id": "issue-1"}))

    assert saved["id"] == "issue-1"
    assert found is not None
    assert found["ticket"] == "TCK-1"
    assert updated == 1
    assert listed[0]["status"] == "Fechado"
    assert deleted == 1
    assert asyncio.run(server.find_issue_record({"id": "issue-1"})) is None


def test_log_analyzer_load_custom_patterns_falls_back_to_local_store(monkeypatch, tmp_path):
    _configure_temp_local_store(monkeypatch, tmp_path)
    local_pattern_store.insert_record(
        "custom_patterns",
        {
            "id": "pattern-1",
            "pattern": "CUSTOM ERROR",
            "active": True,
            "created_at": "2026-03-18T13:00:00",
        },
    )

    class FailingCustomPatternsCollection:
        def find(self, *_args, **_kwargs):
            raise RuntimeError("connection refused")

    class FailingDb:
        custom_patterns = FailingCustomPatternsCollection()

    analyzer = LogAnalyzer()

    asyncio.run(analyzer.load_custom_patterns_from_db(FailingDb()))

    assert "CUSTOM ERROR" in analyzer.get_custom_patterns()