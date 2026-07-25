"""Main entry point for the agent orchestrator."""

import asyncio

from agent_framework_foundry_hosting import ResponsesHostServer

from workflow import get_orchestrator


async def main():
    """Main entry point for the agent orchestrator."""
    orchestrator = get_orchestrator()

    server = ResponsesHostServer(orchestrator)
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
