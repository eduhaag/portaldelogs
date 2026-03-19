#!/usr/bin/env python3
"""Valida a política de senha do cadastro de usuários."""

import asyncio
import importlib
import sys
from pathlib import Path


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