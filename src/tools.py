"""Get tools via Foundry toolboxes."""

import ast
import json
import os
from collections.abc import Callable
from functools import lru_cache

import httpx
from agent_framework import MCPStreamableHTTPTool, tool
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

GITHUB_MCP_URL_DEFAULT = "https://api.githubcopilot.com/mcp/"
# Key Vault secret name, not a credential value.
DEFAULT_PAT_SECRET_NAME = "github-test-executor-pat"  # noqa: S105
MAX_WEB_CONTENT_CHARS = 20_000


class _BearerAuth(httpx.Auth):
    """Inject a bearer token on every request."""

    def __init__(self, token_provider: Callable[[], str]) -> None:
        self._get_token = token_provider

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        yield request


@lru_cache(maxsize=1)
def _github_pat() -> str:
    """Read the GitHub PAT from Key Vault using the hosted agent identity."""
    vault_url = os.environ.get("AZURE_KEY_VAULT_URL")
    if not vault_url:
        raise RuntimeError("Missing required environment variable: AZURE_KEY_VAULT_URL")

    secret_name = os.environ.get("GITHUB_PAT_SECRET_NAME", DEFAULT_PAT_SECRET_NAME)
    client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
    secret = client.get_secret(secret_name)
    if not secret.value:
        raise RuntimeError(f"Key Vault secret '{secret_name}' has no value.")
    return secret.value


def get_github_mcp() -> MCPStreamableHTTPTool:
    """Return the remote GitHub MCP server as an MCP tool, authed with a Key Vault PAT."""
    url = os.environ.get("GITHUB_MCP_URL", GITHUB_MCP_URL_DEFAULT)

    http_client = httpx.AsyncClient(
        auth=_BearerAuth(_github_pat),
        timeout=120.0,
    )

    return MCPStreamableHTTPTool(
        name="github",
        url=url,
        http_client=http_client,
        load_prompts=False,
        approval_mode="never_require",
    )


@tool
def get_web_content(url: str) -> str:
    """Get up to 20,000 characters from a web page.

    Args:
        url: The URL of the web page to get.

    Returns:
        The page content, truncated when necessary to protect the agent context window.
    """
    response = httpx.get(url)
    response.raise_for_status()
    content = response.text
    if len(content) <= MAX_WEB_CONTENT_CHARS:
        return content

    return (
        content[:MAX_WEB_CONTENT_CHARS]
        + "\n\n[Content truncated to protect the agent context window.]"
    )


def _validate_pytest_script(file_content: str) -> str:
    """Run static smoke checks on generated pytest/Playwright script content.

    Returns a JSON string: {"valid": bool, "errors": [str], "warnings": [str]}.
    """
    errors: list[str] = []
    warnings: list[str] = []

    tree: ast.Module | None = None
    try:
        tree = ast.parse(file_content)
    except SyntaxError as exc:
        errors.append(
            f"Syntax error at line {exc.lineno}, column {exc.offset}: {exc.msg}"
        )

    if tree is not None:
        test_functions = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        ]
        if not test_functions:
            errors.append(
                "No pytest-discoverable tests found. Add at least one function named with "
                "the 'test_' prefix."
            )

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if isinstance(node.func, ast.Attribute) and node.func.attr == "to_have_url":
                if node.args and isinstance(node.args[0], ast.Lambda):
                    errors.append(
                        "Invalid Playwright usage: expect(page).to_have_url() cannot take "
                        "a lambda in Python. Use a string or compiled regex."
                    )

            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "time"
                    and node.func.attr == "sleep"
                ):
                    warnings.append(
                        "Avoid fixed waits with time.sleep; prefer Playwright auto-waiting "
                        "assertions and locator actions."
                    )

    if "to_have_utl(" in file_content:
        errors.append(
            "Possible typo detected: 'to_have_utl'. Did you mean 'to_have_url'?"
        )

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
    return json.dumps(result)


@tool
def validate_pytest_script(file_content: str) -> str:
    """Run static smoke checks on generated pytest/Playwright script content.

    Args:
        file_content: Generated Python test script content.

    Returns:
        JSON string with shape: {"valid": bool, "errors": [str], "warnings": [str]}.

    Notes:
        This is a static checker. It does not execute the test script and does not guarantee
        runtime correctness for all Playwright APIs.
    """
    return _validate_pytest_script(file_content)
