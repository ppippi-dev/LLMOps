import asyncio
import os

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from settings import settings

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


async def main():
    async with MCPServerStdio(
        params={
            "command": "uv",
            "args": ["run", "-m", "openai_agent_sdk.mcp_server"],
        },
    ) as server:
        agent = Agent(
            name="test",
            instructions="test",
            model=settings.OPENAI_MODEL,
            mcp_servers=[server],
        )

        result = await Runner.run(agent, "삼성전자 주가 얼마야?")
        print(result)
        print(result.context_wrapper)


if __name__ == "__main__":
    asyncio.run(main())
