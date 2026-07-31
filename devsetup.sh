#!/bin/sh
if ! command -v uv >/dev/null 2>&1; then
  echo "uv binary not found. Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
echo "Setting up development environment..."
uv sync --dev
# Install prek hooks
uv run prek install -f

# Install/update Azure Developer CLI (azd)
echo "Installing/updating Azure Developer CLI (azd)..."
curl -fsSL https://aka.ms/install-azd.sh | bash

azd extension install azure.ai.agents
azd extension install azure.ai.inspector # Optional, but recommended for local development and testing of AI agents
azd extension install azure.ai.projects

echo "Development environment setup complete. Please set environment variables using azd env set <key> <value>."
