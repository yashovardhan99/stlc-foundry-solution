# Agent Orchestrator PoC

PoC for orchestrating agents using Foundry and Microsoft Agent Framework for STLC use-case.

## Approach

Different orchestration techniques can be found at [Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/) and [GitHub](https://github.com/microsoft/agent-framework/tree/main/python/samples/03-workflows/orchestrations#readme).

Key approaches include:

### Concurrent

This is meant for running multiple agents concurrently. This is not applicable to our use-case. We may use this for concurrent steps in the process if needed (similar to `/fleet` mode in GitHub Copilot or Claude).

### Sequential (Recommended)

Here, the agents execute sequentially as per a defined order. An orchestrator then needs to decide when we can move on to the next agent in the sequence. This supports our use-case of 4 agents running one-after-the-other almost perfectly. The child agents should use structured output so our orchestrator can understand what to do. Additionally, an agent can be added to the orchestrator as well to ensure it can summarize inputs and outputs from different child agents for our human operator.

### Handoff

An agent directly delegates control to another specific agent based on context (e.g., Requirement Agent hands off to Test Generator). While this can be used for our use-case, it relies on each agent knowing which agent comes next. It also makes it harder to use human-in-the-loop as there is no central orchestrator.

### Group Chat

All agents converse in a shared room where a manager or LLM dynamically routes who speaks next. While this may seem suitable, it is actually not suitable for our use-case. There is a high risk of agents getting stuck in conversational loops or drifting off-topic, which makes running strict sequential processes unreliable for a live demo.

### Magentic (Recommended alternative)

A central Orchestrator LLM maintains a task ledger, dynamically creating plans and delegating sub-tasks to worker agents. This may be slightly overkill for our PoC. It can be a good showcase for agent autonamy and problem-solving - how an orchestrator can easily manage complex interactions, however, this will involve higher latency and token usage, with the potential for somewhat unreliable execution path.

### Decisions

For our use-case, it makes sense to use either sequential or magentic orchestration. Based on my analysis, it seems like sequential approach would suit us best.

## Developer tooling

Certain dev dependencies have been included to make this project easier to manage and develop. These are not included in any builds.

- [uv package manager](https://docs.astral.sh/uv/)
- [ruff for linting](https://docs.astral.sh/ruff/)
- [ty for type checking](https://docs.astral.sh/ty/)
- [prek for pre-commit](https://prek.j178.dev/)

## Environment Setup

### Automatic setup

If running on a linux shell, simply run the `devsetup.sh` script using `./devsetup.sh` to install all dependencies.

### Manual setup

After [installing `uv`](https://docs.astral.sh/uv/getting-started/installation/), simply run `uv sync --dev` to install all dependencies.

Install prek pre-commit hooks using `uv run prek install`.

Add the foundry project endpoint and a deployed model name in `.env`. (Check out `.env.template` for reference.)

### Usage

To run the code, use `uv run main.py`.
To add new dependencies, use `uv add <dependency>`.

## Sample

Refer to the `samples/` directory for some selected reference samples we can build upon.
