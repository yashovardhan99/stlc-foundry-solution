"""Test executor agent for testing."""

import asyncio
import os
from pathlib import Path

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatOptions
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

from tools import get_github_mcp, get_web_content, validate_pytest_script

default_options: OpenAIChatOptions = {"store": False}

PROMPT_PATH = Path(__file__).parent / "prompts" / "test_executor.md"

# Env vars without a safe in-code default; missing values fail fast at startup.
REQUIRED_ENV_VARS = (
    "FOUNDRY_PROJECT_ENDPOINT",
    "AZURE_KEY_VAULT_URL",
    "GITHUB_OWNER",
    "GITHUB_REPO",
)


def require_env() -> None:
    """Raise if any required environment variable is missing."""
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )


def build_instructions(owner: str, repo: str) -> str:
    """Render the agent instructions with the target repository context."""
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.replace("__OWNER__", owner).replace("__REPO__", repo)


async def main():
    """Entry point for the test executor agent."""
    require_env()
    credential = DefaultAzureCredential()
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME", os.environ.get("FOUNDRY_MODEL", "gpt-5")
        ),
        credential=credential,
        function_invocation_configuration={"include_detailed_errors": True},
    )
    toolbox = get_github_mcp()
    instructions = build_instructions(
        os.environ["GITHUB_OWNER"], os.environ["GITHUB_REPO"]
    )
    agent = Agent(
        name="TestExecutor",
        client=client,
        instructions=instructions,
        tools=[toolbox, get_web_content, validate_pytest_script],
        default_options=default_options,
    )
    server = ResponsesHostServer(agent)
    await server.run_async()


def run() -> None:
    """Console-script entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
