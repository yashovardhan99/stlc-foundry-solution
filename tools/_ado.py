"""Azure DevOps tools via the Foundry 'stlc-tools' MCP toolbox.

The Foundry project exposes the toolbox as a Streamable-HTTP MCP endpoint. We
connect to it with agent-framework's ``MCPStreamableHTTPTool``, authenticating
every request with a fresh Entra bearer token and the Foundry Toolboxes preview
header. Tool calls run without an approval gate (``approval_mode="never_require"``).
"""

import os
from collections.abc import Callable

import httpx
from agent_framework import MCPStreamableHTTPTool
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

TOOLBOX_NAME = "stlc-tools"
TOOLBOX_SCOPE = "https://ai.azure.com/.default"


class _ToolboxAuth(httpx.Auth):
    """Inject a fresh Entra bearer token on every request."""

    def __init__(self, token_provider: Callable[[], str]) -> None:
        self._get_token = token_provider

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        yield request


def get_ado_toolbox(credential: DefaultAzureCredential) -> MCPStreamableHTTPTool:
    """Return the 'stlc-tools' Foundry toolbox as an MCP tool.

    ``credential`` is reused from the caller (shared with the chat client) so a
    single identity authenticates both the model and the toolbox. The toolbox URL
    is derived from ``FOUNDRY_PROJECT_ENDPOINT``; the name is overridable via
    ``ADO_TOOLBOX_NAME``.
    """
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    if not endpoint:
        raise RuntimeError(
            "Missing required environment variable: FOUNDRY_PROJECT_ENDPOINT"
        )

    name = os.environ.get("ADO_TOOLBOX_NAME", TOOLBOX_NAME)
    url = f"{endpoint.rstrip('/')}/toolboxes/{name}/mcp?api-version=v1"

    token_provider = get_bearer_token_provider(credential, TOOLBOX_SCOPE)
    http_client = httpx.AsyncClient(
        auth=_ToolboxAuth(token_provider),
        headers={"Foundry-Features": "Toolboxes=V1Preview"},
        timeout=120.0,
    )

    return MCPStreamableHTTPTool(
        name=name,
        url=url,
        http_client=http_client,
        load_prompts=False,
        approval_mode="never_require",
    )
