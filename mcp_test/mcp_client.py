"""MCP 클라이언트: stdio로 stock-mcp 서버와 상호작용

교육용 예시로, 다음을 수행합니다.
- 서버 프로세스를 stdio로 실행 및 초기화
- 도구/리소스/프롬프트 나열
- 예시로 get_stock_price 호출
- 예시로 extract-stock-code 프롬프트 메시지 생성
"""

import asyncio
import json
import os
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ABS_SERVER_PATH = "./mcp_test/mcp_server.py"


async def print_tool_list(session: ClientSession) -> None:
    """서버에서 제공하는 도구를 나열합니다."""
    tools = await session.list_tools()
    print("\n[Tools]")
    for tool in tools.tools:
        print(f"- {tool.name}: {tool.description}")


async def print_resource_list_and_help(session: ClientSession) -> None:
    """리소스를 나열하고, help 리소스가 있으면 내용을 읽어 출력합니다."""
    resources = await session.list_resources()
    print("\n[Resources]")
    for r in resources.resources:
        print(f"- {r.uri}: {getattr(r, 'description', '')}")

    for r in resources.resources:
        if str(r.uri).endswith("help.md"):
            read_result = await session.read_resource(r.uri)
            print("\n[help.md]")
            for content in getattr(read_result, "contents", []) or []:
                text = getattr(content, "text", None)
                if text is not None:
                    print(text)


async def print_prompt_list_and_example(session: ClientSession) -> None:
    """프롬프트를 나열하고 extract-stock-code 예시 메시지를 출력합니다."""
    prompts = await session.list_prompts()
    print("\n[Prompts]")
    for p in prompts.prompts:
        print(f"- {p.name}: {getattr(p, 'description', '')}")

    # extract-stock-code 프롬프트 사용 예시
    prompt_result = await session.get_prompt("extract-stock-code", {"user_input": "삼성전자 주가 알려줘"})
    print("\n[Prompt: extract-stock-code -> messages]")
    for msg in getattr(prompt_result, "messages", []) or []:
        # 각 메시지의 텍스트 콘텐츠 출력
        contents = getattr(msg, "content", []) or []
        for c in contents:
            text = getattr(c, "text", None)
            if text is not None:
                print(text)


def _print_content_item(item: Any) -> None:
    """MCP content 항목을 안전하게 출력합니다."""
    if hasattr(item, "text") and getattr(item, "text") is not None:
        print(getattr(item, "text"))
        return

    if hasattr(item, "json") and getattr(item, "json") is not None:
        try:
            print(json.dumps(getattr(item, "json"), ensure_ascii=False, indent=2))
        except (TypeError, ValueError):
            print(getattr(item, "json"))
        return

    # 기타 타입: 대표 속성들로 유추 출력
    for attr in ("data", "value", "uri"):
        if hasattr(item, attr):
            print(getattr(item, attr))
            return

    print(repr(item))


async def demo_calls(session: ClientSession) -> None:
    """예시 호출: get_stock_price 도구를 호출하고 결과를 출력합니다."""
    result = await session.call_tool(
        "get_stock_price",
        {"args": {"ticker": "005930.KS"}},
    )
    print("\n[Call Tool: get_stock_price]")
    for item in getattr(result, "content", []) or []:
        _print_content_item(item)


async def main() -> None:
    """stdio로 서버를 실행하고 기본 상호작용 데모를 수행합니다."""
    server_params = StdioServerParameters(
        command="python",
        args=[ABS_SERVER_PATH],
        env=dict(os.environ),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await print_tool_list(session)
            await print_resource_list_and_help(session)
            await print_prompt_list_and_example(session)
            await demo_calls(session)


if __name__ == "__main__":
    asyncio.run(main())
