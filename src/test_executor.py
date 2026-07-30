"""Test executor agent for testing."""

import asyncio
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatOptions
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

from tools import get_toolbox, git_commit_push

default_options: OpenAIChatOptions = {"store": False}


PROMPT = """
You are a test execution specialist.
Use the approved test cases, test data, and execution context to run or simulate test
execution precisely as written.
Do not change the test intent unless the execution context makes it impossible; in that case
note the deviation.

You will be provided with test cases in BBD .feature file format,
you are supposed to test the provided website as per the given test cases.
To do so, you need to execute the following steps:
1. Read the test cases from the provided .feature file.
2. For each test case, identify the steps to be executed using playwright Python SDK.
3. Create a single python script that executes all the test cases using playwright Python SDK.
4. Save the script to DevOps by calling the tool `git_commit_push` with the following parameters:
   - file_name: The name of the file to be created (e.g., test_execution.py).
   - file_content: The content of the file, which is the Python script you created in step 3.
   - commit_message: A message describing the commit (e.g., "Add test execution script").
5. After saving the script, the tool will return the branch name where the script is saved.
6. To execute the script, you need to run the pipeline `<pipeline_name>`
    by using the tool `run_pipeline`.
"""


async def main():
    """Entry point for the test executor agent."""
    credential = DefaultAzureCredential()
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME", os.environ.get("FOUNDRY_MODEL", "gpt-5")
        ),
        credential=credential,
    )
    toolbox = get_toolbox("test-executor-tools", credential)
    agent = Agent(
        name="TestExecutor",
        client=client,
        instructions=PROMPT,
        tools=[toolbox, git_commit_push],
        default_options=default_options,
    )
    server = ResponsesHostServer(agent)
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
