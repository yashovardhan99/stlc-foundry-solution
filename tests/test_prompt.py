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


def test_prompt_includes_pull_request_and_issue_steps():
    instructions = test_executor.build_instructions("acme", "widgets")
    assert "create_pull_request" in instructions
    assert "issue_read" in instructions


def test_github_pat_requires_vault_url(monkeypatch):
    monkeypatch.delenv("AZURE_KEY_VAULT_URL", raising=False)
    tools._github_pat.cache_clear()
    with pytest.raises(RuntimeError, match="AZURE_KEY_VAULT_URL"):
        tools._github_pat()


def test_get_github_mcp_uses_default_url(monkeypatch):
    monkeypatch.delenv("GITHUB_MCP_URL", raising=False)
    mcp = tools.get_github_mcp()
    assert mcp.url == tools.GITHUB_MCP_URL_DEFAULT


def test_get_github_mcp_uses_default_allowed_tools(monkeypatch):
    monkeypatch.delenv("GITHUB_MCP_ALLOWED_TOOLS", raising=False)
    mcp = tools.get_github_mcp()
    assert mcp.allowed_tools is not None
    assert tuple(mcp.allowed_tools) == tools.DEFAULT_ALLOWED_TOOLS


def test_get_github_mcp_honors_allowed_tools_env(monkeypatch):
    monkeypatch.setenv("GITHUB_MCP_ALLOWED_TOOLS", "create_branch, issue_read")
    mcp = tools.get_github_mcp()
    assert mcp.allowed_tools is not None
    assert tuple(mcp.allowed_tools) == ("create_branch", "issue_read")
