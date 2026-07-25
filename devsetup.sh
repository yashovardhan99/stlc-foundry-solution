#!/bin/sh
if ! command -v uv >/dev/null 2>&1; then
  echo "uv binary not found. Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
echo "Setting up development environment..."
uv sync --dev
# Install prek hooks
uv run prek install
# Check if the user has a .env file, if not copy the example one
if [ ! -f .env ]; then
  cp .env.template .env
  echo "Created .env file from .env.template. Please review and update the .env file with your configuration."
fi

# Install/update Azure Developer CLI (azd)
echo "Installing/updating Azure Developer CLI (azd)..."
curl -fsSL https://aka.ms/install-azd.sh | bash

echo "Development environment setup complete."
