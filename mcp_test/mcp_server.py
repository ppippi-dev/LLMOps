"""MCP 서버: tools/resources/prompt로 구성된 주식 질의 서버

교육용으로 이해하기 쉽게 작성되었습니다. 클라이언트는 stdio를 통해 이 서버를 실행하고
tool 호출로 상호작용합니다.
"""

import logging
import os
from typing import Optional

import yfinance as yf
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# 로깅 설정
_log_level_name = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("stock-mcp")

# MCP 서버 인스턴스
mcp = FastMCP(
    name="stock-mcp",
)


class UserQuery(BaseModel):
    """자연어로 된 사용자 질문"""

    query: str = Field(..., description="사용자 입력 질문 문장")


class StockPriceRequest(BaseModel):
    """주가 조회 요청 (야후 파이낸스 심볼)"""

    ticker: str = Field(..., description="야후 파이낸스 심볼, 예: 005930.KS")


class StockPrice(BaseModel):
    """주가 조회 결과"""

    success: bool
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[str] = None
    error: Optional[str] = None


# ===== Tools =====


@mcp.tool("get_stock_price", description="야후 파이낸스에서 주가 정보를 조회합니다.")
def get_stock_price(args: StockPriceRequest) -> StockPrice:
    try:
        logger.info("Tool get_stock_price 호출: ticker=%s", args.ticker)
        ticker = yf.Ticker(args.ticker)
        info = ticker.info

        current_price = info.get("currentPrice")
        previous_close = info.get("previousClose")
        company_name = info.get("longName", args.ticker)

        if current_price is not None and previous_close is not None:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0.0
            change_str = f"{change:.2f} ({change_percent:.2f}%)"
        else:
            change_str = None

        result = StockPrice(
            success=True,
            company_name=company_name,
            ticker=args.ticker,
            current_price=current_price,
            previous_close=previous_close,
            change=change_str,
        )
        logger.info(
            "Tool get_stock_price 결과: success=%s company=%s ticker=%s current=%s prev=%s change=%s",
            result.success,
            result.company_name,
            result.ticker,
            result.current_price,
            result.previous_close,
            result.change,
        )
        return result
    except Exception as e:
        logger.exception("Tool get_stock_price 에러")
        return StockPrice(success=False, error=str(e))


# ===== Resources =====


@mcp.resource("file://help.md", description="서버 사용법과 제공 도구 설명")
def help_resource() -> str:
    logger.debug("Resource help.md 요청")
    return (
        "# stock-mcp 도움말\n\n"
        "- get_stock_price(ticker): 야후 파이낸스 심볼로 주가 조회 (예: 005930.KS)\n"
        "- prompts:\n"
        "  - extract-stock-code: 종목코드 추출용 메시지 템플릿\n"
        "  - stock-answer: 답변 작성용 메시지 템플릿\n"
        "\n(LLM 호출은 클라이언트에서 수행하세요)\n"
    )


@mcp.prompt(
    "extract-stock-code",
    description="질문에서 한국 주식 종목코드(6자리 숫자)만 추출하는 프롬프트",
)
def extract_stock_code_prompt(user_input: str) -> dict:
    logger.debug(
        "Prompt extract-stock-code 요청: input_len=%s",
        len(user_input) if user_input else 0,
    )
    return {
        "role": "user",
        "content": (f"아래 질문에서 종목코드만 반환해. 예시는 '005930' 처럼 6자리 숫자야.\n질문: {user_input}"),
    }


@mcp.prompt(
    "stock-answer",
    description="주가 데이터 답변 템플릿 (클라이언트에서 이 프롬프트로 LLM 호출)",
)
def stock_answer_prompt(
    user_input: str,
    company_name: Optional[str] = None,
    ticker: Optional[str] = None,
    current_price: Optional[float] = None,
    previous_close: Optional[float] = None,
    change: Optional[str] = None,
) -> list[dict]:
    logger.debug(
        "Prompt stock-answer 요청: company=%s ticker=%s current=%s prev=%s change=%s",
        company_name,
        ticker,
        current_price,
        previous_close,
        change,
    )
    return [
        {
            "role": "user",
            "content": (
                "다음 정보를 이용해 한 문단으로 간결하게 설명해줘.\n"
                f"질문: {user_input}\n"
                f"회사: {company_name or '-'} / 티커: {ticker or '-'}\n"
                f"현재가: {current_price} / 전일: {previous_close} / 변동: {change}"
            ),
        },
    ]


if __name__ == "__main__":
    # stdio 기반 실행. 호스트/클라이언트가 이 프로세스를 소환해 연결합니다.
    logger.info("FastMCP 서버 시작: log_level=%s", _log_level_name)
    mcp.run()
