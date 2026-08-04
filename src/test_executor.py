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
7. You MUST execute the script by calling the `run_pipeline` tool from the
    `test-executor-tools` toolbox immediately after `git_commit_push` returns the branch name.
    Pass the branch name from step 6 and these fixed values:
    - project: "agents-connection-demo"
    - pipelineId: 1
8. Treat the `run_pipeline` tool call as a required completion gate. Do not finish,
    summarize, or claim that testing is complete until the call has returned. If it fails,
    report the failure and its returned details; do not silently skip it or substitute a
    simulated pipeline run.
9. In your final response, report the committed branch and the pipeline run identifier or
    status returned by `run_pipeline`.

Required tool-call order:
1. Read the feature file and any needed web content.
2. Generate the Playwright test script.
3. Call `git_commit_push` and retain its returned branch name.
4. Call `run_pipeline` with that exact branch name.
5. Only then provide the final response.

The tests are executed as `python3 -m pytest $targets --junitxml=test-results/junit.xml`.

The test environment will have the following pre-installed packages:
- pytest
- pytest-bdd
- pytest-playwright

Generated-script requirements:
- Use pytest-discoverable test functions: every executable test function name MUST start with
    `test_` and must not require arguments that pytest does not provide.
- Use documented Playwright Python APIs and do not infer an API signature from another language
    binding. Consult official documentation only when an API signature is genuinely uncertain;
    prefer a narrowly targeted `web_search` result when available. Do not retrieve broad
    documentation pages with `get_web_content` during normal test generation.
- For partial URL checks, use the documented Python URL matcher types: a string or compiled
    regular expression. For example, import `re` and use
    `expect(page).to_have_url(re.compile(r".*overview\\.htm.*"))`; do not pass a lambda or other
    callable.
- Prefer Playwright auto-waiting assertions (`expect(...)`) over fixed delays. Close the browser
    reliably, including when an assertion fails.
- Before committing, inspect the generated script for Python syntax errors, pytest discovery
    compatibility, and valid Playwright API usage.

Make sure your script is compatible with the above packages and can be executed in the environment.

Note: You are running in a standalone environment, without user interaction.
You must not ask the user for any input.
All the information you need is provided in the test cases and execution context.
You MUST execute the tests as per the provided test cases and execution context.

You may use the `web_search` tool to search for any additional information you need for generating
the tests, including playwright python API documentation.
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
