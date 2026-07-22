# Agent Orchestrator PoC

More details to be added later.

I was thinking of using a [magentic workflow from Microsoft Agent Framework](https://github.com/microsoft/agent-framework/tree/main/python/samples/03-workflows/orchestrations#magentic) as the orchestrator. That has had some research done on it, and can be quite successful for our work.

Alternatively, we can also use a [group chat workflow](https://github.com/microsoft/agent-framework/tree/main/python/samples/03-workflows/orchestrations#group-chat) for a much simpler execution. However, it seems like magentic is much more powerful.

## Suggested tooling

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

I have added a sample magentic workflow from the Microsoft agent framework GitHub repository here.
