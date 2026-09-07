"""Unit tests for prompt rendering and GitHub PAT lookup."""

import pytest

import test_executor
import tools


def test_build_instructions_substitutes_owner_and_repo():
    instructions = test_executor.build_instructions("acme", "widgets")
    assert "acme" in instructions
    assert "widgets" in instructions
    assert "__OWNER__" not in instructions
    assert "__REPO__" not in instructions


def test_github_pat_requires_vault_url(monkeypatch):
    monkeypatch.delenv("AZURE_KEY_VAULT_URL", raising=False)
    tools._github_pat.cache_clear()
    with pytest.raises(RuntimeError, match="AZURE_KEY_VAULT_URL"):
        tools._github_pat()


def test_get_github_mcp_uses_default_url(monkeypatch):
    monkeypatch.delenv("GITHUB_MCP_URL", raising=False)
    mcp = tools.get_github_mcp()
    assert mcp.url == tools.GITHUB_MCP_URL_DEFAULT
