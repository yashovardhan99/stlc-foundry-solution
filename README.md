# Agent Orchestrator PoC

PoC for STLC agents using Foundry and Microsoft Agent Framework.

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

To run the code, use `azd ai agent run ...`.
To add new dependencies, use `uv add <dependency>`.
