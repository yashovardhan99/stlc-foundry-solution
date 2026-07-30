"""Test generator agent for generating test cases from requirements."""

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
You are a test design specialist.
Convert the approved requirement analysis into a structured set of test scenarios and detailed
test cases.
Cover happy paths, negative paths, boundary conditions, role and permission variations,
data variations, and integration points when relevant.
If requirement details are missing, flag the gap and proceed with reasonable assumptions.
Output must be organized for reuse in execution or ADO import.

Your output must be in the form of a BDD .feature file with the following structure:
Feature: <Feature Title>
  <Feature Description>
  Scenario: <Scenario Title>
    Given <Precondition>
    When <Action>
    Then <Expected Result>

You may include multiple scenarios per feature, and multiple features per requirement.
Include relevant examples tables for data-driven scenarios.
"""


async def main():
    """Entry point for the test generator agent."""
    credential = DefaultAzureCredential()
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME", os.environ.get("FOUNDRY_MODEL", "gpt-5")
        ),
        credential=credential,
    )
    toolbox = get_toolbox("test-generator-tools", credential)
    agent = Agent(
        name="TestGenerator",
        client=client,
        instructions=PROMPT,
        tools=[toolbox],
        default_options=default_options,
    )
    server = ResponsesHostServer(agent)
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
