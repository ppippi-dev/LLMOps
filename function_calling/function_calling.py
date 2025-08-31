"""AI 에이전트 메인 파일"""

import json

import openai
import yfinance as yf
from openai.types.chat import ChatCompletionMessageParam

from settings import settings

# OpenAI API 키 설정
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


def get_stock_code_from_gpt(user_input: str):
    """주식 종목 코드를 반환하기 위한 함수"""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "Get current stock price for provided stock name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stock_code": {"type": "string"},
                    },
                    "required": ["stock_code"],
                    "additionalProperties": False,
                },
            },
        },
    ]

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "user",
            "content": (
                "유저의 질문을 통해 주식 종목 코드를 알려줘. "
                "주식 종목 코드는 000000 같은 6자리 숫자 형식을 가졌어. "
                "이후 종목 코드를 통해 주식 가격을 얻고싶어.\n"
                f"유저의 질문: {user_input}"
            ),
        },
    ]
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        max_tokens=150,
        temperature=0.7,
        tools=tools,
        tool_choice="required",
    )

    print(response)

    # 응답에서 tool_calls 정보 추출
    if response.choices and response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        if tool_call.function.name == "get_stock_price":
            try:
                args = json.loads(tool_call.function.arguments)
                stock_code = args.get("stock_code")
                if stock_code:
                    answer_data = get_stock_price(stock_code)
            except json.JSONDecodeError:
                return {"success": False, "error": "응답 파싱 오류"}
        else:
            return {"success": False, "error": "적절한 함수 호출을 찾을 수 없음"}

    messages = [
        {
            "role": "system",
            "content": "너는 유저의 질문에 대한 답변을 만들어주는 프로그램이야. 유저의 질문에 대한 답변을 만들어줘",
        },
        {
            "role": "user",
            "content": f"유저의 질문: {user_input}, 데이터: {answer_data}",
        },
    ]
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
    )

    return response.choices[0].message.content


def get_stock_price(stock_code: str) -> dict:
    """주식 가격 정보를 가져오기 위한 함수"""
    try:
        if not stock_code.endswith(".KS"):
            ticker_symbol = f"{stock_code}.KS"
        else:
            ticker_symbol = stock_code

        # yfinance 라이브러리를 사용하여 주식 정보 가져오기
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # 필요한 정보 추출
        current_price = info.get("currentPrice", "정보 없음")
        previous_close = info.get("previousClose", "정보 없음")
        company_name = info.get("longName", ticker_symbol)

        # 가격 변동 계산
        if current_price != "정보 없음" and previous_close != "정보 없음":
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            change_str = f"{change:.2f} ({change_percent:.2f}%)"
        else:
            change_str = "정보 없음"

        return {
            "success": True,
            "company_name": company_name,
            "ticker": ticker_symbol,
            "current_price": current_price,
            "previous_close": previous_close,
            "change": change_str,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """main function"""
    response = get_stock_code_from_gpt("기아차 주가")
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
