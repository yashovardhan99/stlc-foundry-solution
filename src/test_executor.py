"""Test executor agent for testing."""

import asyncio
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatOptions
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

from tools import get_toolbox, get_web_content, git_commit_push

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
2. You can get the static page contents using the tool `get_web_content`.
    You can use this tool with different URLs to get the content of the pages that you need to test.
3. For each test case, identify the steps to be executed using playwright Python SDK with Chromium.
4. Create a single Python file that executes all the test cases using playwright Python SDK.
5. Save the script to DevOps by calling the tool `git_commit_push` with the following parameters:
   - file_name: The name of the file to be created (e.g., test_execution.py).
        Try to use a unique name relating to the specific test scenario being executed.
   - file_content: The content of the file, which is the Python script you created in step 3.
   - commit_message: A message describing the commit (e.g., "Add test execution script").
Your test will be saved in a custom branch.
6. After saving the script, the tool will return the branch name where the script is saved.
7. To execute the script, you need to run the pipeline with the following details:
    project: "agents-connection-demo"
    pipelineId: 1
  Use the tool `run_pipeline` with the branch name returned in step 6.
  Note: the `run_pipeline` tool is available as part of AzureDevOpsMCPServerpreview
  in the toolbox `test-executor-tools`.

The tests are executed as `python3 -m pytest $targets --junitxml=test-results/junit.xml`.

The test environment will have the following pre-installed packages:
- pytest
- pytest-bdd
- pytest-playwright

Make sure your script is compatible with the above packages and can be executed in the environment.

Note: You are running in a standalone environment, without user interaction.
You must not ask the user for any input.
All the information you need is provided in the test cases and execution context.
You MUST execute the tests as per the provided test cases and execution context.
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
        tools=[toolbox, git_commit_push, get_web_content],
        default_options=default_options,
    )
    server = ResponsesHostServer(agent)
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
