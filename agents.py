"""Module for agent definitions and implementations."""

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatOptions

REQUIREMENT_ANALYZER_PROMPT = """
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

TEST_CASE_WRITER_PROMPT = """
You are a test design specialist.
Convert the approved requirement analysis into a structured set of test scenarios and detailed
test cases.
Cover happy paths, negative paths, boundary conditions, role and permission variations,
data variations, and integration points when relevant.
Each test case should include a clear title, preconditions, steps, expected results,
and traceability back to the requirement or scenario.
If requirement details are missing, flag the gap and proceed with reasonable assumptions.
Output must be organized for reuse in execution or ADO import.
"""

TEST_EXECUTOR_PROMPT = """
You are a test execution specialist.
Use the approved test cases, test data, and execution context to run or simulate test
execution precisely as written.
Do not change the test intent unless the execution context makes it impossible; in that case
note the deviation.
Record step-level or case-level results, actual outcomes, evidence, and pass or fail status.
If execution is handed off to automation or another system, prepare a clean execution handoff
with all required inputs and a concise summary of what should happen next.
Output must include execution status, observed results, defects if any, and evidence references.
"""

BUG_LOGGER_PROMPT = """
You are a defect triage and bug logging specialist.
When test execution fails, convert the failure into a high-quality defect-ready record for ADO.
Capture the expected result, actual result, repro steps, environment, and evidence.
Capture severity and priority suggestion.
Capture any likely component or ownership hint if inferable from the failure.
If the failure is not reproducible or the evidence is insufficient, state that clearly
and request the missing information.
Keep the defect factual, specific, and free of speculation.

You have Azure DevOps (ADO) tools available. Once the defect record is complete, use your
ADO tools to create the corresponding work item(s) in ADO, then report the created work-item
ID(s) and URL(s). If required details are missing, do NOT create the work item -- state what
is missing instead.
"""

ORCHESTRATOR_PROMPT = """
You coordinate a 4-stage software testing workflow for a human operator.

Azure DevOps (ADO) access lives inside the analyze_requirements and log_bugs tools, not
with you. When the human references an ADO work item, pass that reference (ID or URL) plus
any context straight to analyze_requirements, which fetches the work item itself. The
log_bugs tool creates the defect work item(s) in ADO.

The stages run strictly in this order, each backed by a dedicated tool:
  1. analyze_requirements - fetch the referenced ADO work item and produce a test scope/plan
  2. write_test_cases     - turn the approved analysis into detailed test cases
  3. execute_tests        - execute or simulate the approved test cases
  4. log_bugs             - create ADO defect work items for the failed executions

How you must operate:
- Work ONE stage at a time.
- For stage 1: pass the human's ADO work-item reference (ID or URL) and any extra context
  to analyze_requirements; it will fetch the work item and analyze it.
- For stages 2 and 3: call the stage tool with the approved output of the previous stage.
- For stage 4: call log_bugs, which creates the defect work item(s) in ADO and returns the
  created work-item ID(s) and URL(s). Only call it after the human approves the defect
  content from stage 3.
- After a stage tool returns, STOP and reply to the human with:
    1. a short, plain-language summary of what that stage produced, and
    2. the explicit question: "Approve to continue, or tell me what to change?"
- Do NOT advance to the next stage until the human's next message clearly approves
  (e.g. "approve", "yes", "looks good", "continue").
- If the human asks for changes, redo the SAME stage, incorporating their feedback,
  then summarize and ask for approval again.
- Determine which stage you are on from the conversation history so far.
- When the human approves the final stage (log_bugs), give a brief closing summary of the
  whole run and stop.

Keep your user-facing messages concise. Do not expose raw tool payloads verbatim;
summarize them for a human reviewer.
"""


def create_orchestrator(
    client: FoundryChatClient[OpenAIChatOptions[None]],
    ado_toolbox: MCPStreamableHTTPTool,
) -> Agent:
    """Create the orchestrator agent that drives the 4 workers via multi-turn approval.

    Each worker is exposed to the orchestrator as a tool. The orchestrator runs one
    stage per turn, summarizes the result for the human, and waits for approval (a
    normal chat reply) before advancing -- so it works in the Foundry Playground
    without relying on ``request_info``.

    ``ado_toolbox`` is the 'stlc-tools' Foundry toolbox (a Streamable-HTTP MCP tool).
    It is attached to the RequirementAnalyzer worker, which fetches the referenced
    ADO work item during stage 1.
    """
    requirement_analyzer, test_case_writer, test_executor, bug_logger = create_agents(
        client, ado_toolbox
    )

    worker_tools = [
        requirement_analyzer.as_tool(
            name="analyze_requirements",
            description="Analyze a business requirement and produce a test scope/plan.",
        ),
        test_case_writer.as_tool(
            name="write_test_cases",
            description="Turn an approved requirement analysis into detailed test cases.",
        ),
        test_executor.as_tool(
            name="execute_tests",
            description="Execute or simulate the approved test cases and report results.",
        ),
        bug_logger.as_tool(
            name="log_bugs",
            description="Convert failed test executions into ADO-ready defect records.",
        ),
    ]

    default_options: OpenAIChatOptions = {"store": False}
    return Agent(
        name="STLCOrchestrator",
        client=client,
        instructions=ORCHESTRATOR_PROMPT,
        tools=worker_tools,
        default_options=default_options,
    )


def create_agents(
    client: FoundryChatClient[OpenAIChatOptions[None]],
    ado_toolbox: MCPStreamableHTTPTool,
) -> tuple[Agent, Agent, Agent, Agent]:
    """Create and return the four worker agents.

    Azure DevOps access lives on the RequirementAnalyzer, which fetches the
    referenced work item during stage 1. The remaining workers reason over the
    content the orchestrator passes them.
    """
    default_options: OpenAIChatOptions = {"store": False}
    requirement_analyzer = Agent(
        name="RequirementAnalyzer",
        client=client,
        instructions=REQUIREMENT_ANALYZER_PROMPT,
        tools=[ado_toolbox],
        default_options=default_options,
    )
    test_case_writer = Agent(
        name="TestCaseWriter",
        client=client,
        instructions=TEST_CASE_WRITER_PROMPT,
        default_options=default_options,
    )

    test_executor = Agent(
        name="TestExecutor",
        client=client,
        instructions=TEST_EXECUTOR_PROMPT,
        default_options=default_options,
    )
    bug_logger = Agent(
        name="BugLogger",
        client=client,
        instructions=BUG_LOGGER_PROMPT,
        tools=[ado_toolbox],
        default_options=default_options,
    )

    return requirement_analyzer, test_case_writer, test_executor, bug_logger
