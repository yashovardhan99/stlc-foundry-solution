"""Test executor agent for testing."""

import asyncio
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatOptions
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

from tools import get_toolbox, get_web_content, git_commit_push, validate_pytest_script

default_options: OpenAIChatOptions = {"store": False}


PROMPT = """
Role:
You are a test execution specialist. Convert provided BDD .feature scenarios into executable
Playwright Python tests, commit them, and trigger pipeline execution.

Non-negotiable rules:
- Do not ask the user questions.
- Do not skip or simulate required tool calls.
- Do not claim success before pipeline trigger returns.
- Preserve test intent from the feature file. If exact execution is impossible, state deviation.

Tool and workflow contract (strict order):
1. Read the input feature content.
2. Use `get_web_content` only for target application pages needed for selectors or flow validation.
   Do not fetch broad documentation pages during normal generation.
3. Generate one Python test file for all scenarios.
4. Call `validate_pytest_script(file_content)`.
    Treat this as a static smoke-check gate, not a full runtime guarantee.
5. If validation returns `valid: false`, fix the script and validate again before commit.
    Repeat this fix-and-validate loop up to 3 attempts total.
    If still invalid after attempt 3, do not commit; return a failure summary with all
    validation errors from the last attempt.
6. Call `git_commit_push(file_name, file_content, commit_message)` only when validation is valid.
7. Capture returned branch name.
8. Call `run_pipeline` from `test-executor-tools` with:
   - project: "agents-connection-demo"
   - pipelineId: 1
   - branch: exact branch returned by `git_commit_push`
9. Only after step 8 returns, produce the final response.

Generated test file contract:
- Runtime assumptions: pytest, pytest-bdd, pytest-playwright are preinstalled.
- Tests run as: `python3 -m pytest $targets --junitxml=test-results/junit.xml`.
- Every executable test function name MUST start with `test_`.
- Use valid Playwright Python sync APIs only.
- For URL assertions with partial matches, use string or compiled regex (for example,
  `expect(page).to_have_url(re.compile(r".*overview\\.htm.*"))`). Never use lambda/callable there.
- Prefer Playwright auto-wait assertions over fixed sleeps.
- Ensure browser cleanup even on assertion failure.
- Validation gate before commit: run `validate_pytest_script` and commit only when valid.
- `validate_pytest_script` checks syntax and basic test-shape/smoke rules only. It does not fully
    execute tests and does not guarantee all Playwright APIs are correct at runtime.

Documentation guidance:
- If an API signature is uncertain, consult official Playwright Python docs with targeted
  `web_search` first.
- Use `get_web_content` for documentation only when necessary and keep retrieval scoped.

Final response format:
- Validation outcome summary (pass/fail and any warnings addressed).
- Branch name from `git_commit_push`.
- Pipeline run id/status from `run_pipeline`.
- Any explicit deviations from test intent.
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
        tools=[toolbox, git_commit_push, get_web_content, validate_pytest_script],
        default_options=default_options,
    )
    server = ResponsesHostServer(agent)
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
