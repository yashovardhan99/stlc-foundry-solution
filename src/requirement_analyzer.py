"""Requirement analyzer agent for testing."""

import asyncio
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatOptions
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

from tools import get_toolbox

default_options: OpenAIChatOptions = {"store": False}

PROMPT = """
You are a requirement analysis specialist for testing.
Read the provided business requirement, backlog item, and supporting documents carefully.

You have Azure DevOps (ADO) tools available. If the input references an ADO work item
(an ID or URL), use your ADO tools to fetch that work item first, then analyze its content
together with any context you were given. If key details are still missing, note the gap
explicitly rather than guessing.

Identify the testing objective, in-scope and out-of-scope behavior, business rules,
dependencies, risks, edge cases, and ambiguity.
Summarize the testing scope in a structured way.
List clarification questions only when they materially affect test design or execution.
Prefer practical testing implications over paraphrasing the story.
Output must include: requirement summary, inferred scope, assumptions,
risks/gaps, and open questions.
"""


async def main():
    """Entry point for the requirement analyzer agent."""
    credential = DefaultAzureCredential()
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME", os.environ.get("FOUNDRY_MODEL", "gpt-5")
        ),
        credential=credential,
    )
    toolbox = get_toolbox("requirement-analyzer-tools", credential)
    agent = Agent(
        name="RequirementAnalyzer",
        client=client,
        instructions=PROMPT,
        tools=[toolbox],
        default_options=default_options,
    )
    server = ResponsesHostServer(agent)
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
