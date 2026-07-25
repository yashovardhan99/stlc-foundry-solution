"""Module for creating the orchestrator agent."""

import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

from agents import create_orchestrator
from tools import get_ado_toolbox


def _require_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    raise RuntimeError(f"Missing required environment variable: {' or '.join(names)}")


def get_orchestrator() -> Agent:
    """Create and return the orchestrator agent.

    The orchestrator wraps the four worker agents as tools and drives them one
    stage at a time, pausing for human approval between stages via normal chat
    turns (Foundry Playground friendly; no ``request_info`` required).
    """
    credential = DefaultAzureCredential()
    client = FoundryChatClient(
        project_endpoint=_require_env("FOUNDRY_PROJECT_ENDPOINT"),
        model=_require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME", "FOUNDRY_MODEL"),
        credential=credential,
    )
    ado_toolbox = get_ado_toolbox(credential)
    return create_orchestrator(client, ado_toolbox)
