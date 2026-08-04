"""Get tools via Foundry toolboxes."""

import os
import uuid
from collections.abc import Callable
from pathlib import Path

import httpx
from agent_framework import MCPStreamableHTTPTool, tool
from azure.devops.connection import Connection
from azure.devops.v7_1.core.core_client import CoreClient
from azure.devops.v7_1.core.models import TeamProject
from azure.devops.v7_1.git.git_client import GitClient
from azure.devops.v7_1.git.models import (
    Change,
    GitCommitRef,
    GitItem,
    GitPush,
    GitRef,
    GitRefUpdate,
    GitRepository,
    GitUserDate,
    ItemContent,
)
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from msrest.authentication import BasicAuthentication

TOOLBOX_SCOPE = "https://ai.azure.com/.default"
MAX_WEB_CONTENT_CHARS = 20_000


class _ToolboxAuth(httpx.Auth):
    """Inject a fresh Entra bearer token on every request."""

    def __init__(self, token_provider: Callable[[], str]) -> None:
        self._get_token = token_provider

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        yield request


def get_toolbox(name: str, credential: DefaultAzureCredential) -> MCPStreamableHTTPTool:
    """Return a foundry toolbox as an MCP tool."""
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    if not endpoint:
        raise RuntimeError(
            "Missing required environment variable: FOUNDRY_PROJECT_ENDPOINT"
        )

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


@tool
def git_commit_push(file_name: str, file_content: str, commit_message: str) -> str:
    """Commit and push a file to the repository.

    Args:
        file_name: The name of the file to commit and push.
        file_content: The content of the file to commit and push.
        commit_message: The commit message to use.

    Returns:
        The name of the branch where the file was committed and pushed.
    """
    # Fill in with your personal access token and org URL
    personal_access_token = os.environ.get("AZURE_DEVOPS_PAT")
    organization_url = "https://dev.azure.com/STLC-PoC/"
    project_name = "agents-connection-demo"

    credentials = BasicAuthentication("", personal_access_token)

    # Create a connection to the org
    connection = Connection(organization_url, credentials)

    # Get a client (the "core" client provides access to projects, teams, etc)
    core_client: CoreClient = connection.clients.get_core_client()

    # Get the first page of projects
    project: TeamProject = core_client.get_project(project_name)

    # Get the Git client
    git_client: GitClient = connection.clients.get_git_client()

    repository: GitRepository = git_client.get_repository(
        project.name, project=project.name
    )

    # Create a new branch
    new_branch_name = "test-executor-" + str(uuid.uuid4())
    base_branch_name = "main"

    base_branch: GitRef = git_client.get_refs(
        repository.id, filter=f"heads/{base_branch_name}"
    )[0]

    ref_update = GitRefUpdate(
        name=f"refs/heads/{new_branch_name}",
        old_object_id=base_branch.object_id,
    )

    if not file_name.startswith("test_"):
        file_name = "test_" + file_name

    file_path = Path("generated_tests") / Path(file_name)

    change = Change(
        "add",
        GitItem(path=file_path.as_posix()),
        ItemContent(content=file_content, content_type="rawtext"),
    )

    user = GitUserDate(
        name="Test Executor Agent",
        email="test.executor.agent@example.com",
    )

    commit = GitCommitRef(author=user, comment=commit_message, changes=[change])

    push = GitPush(ref_updates=[ref_update], commits=[commit])

    git_client.create_push(
        push,
        repository.id,
        project=project.name,
    )

    return new_branch_name


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
