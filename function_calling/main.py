"""AI 에이전트 메인 파일"""

import openai
import yfinance as yf
from pydantic import BaseModel

from settings import settings

# OpenAI API 키 설정
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


class StockCode(BaseModel):
    """주식 종목 코드를 반환하는 모델"""

    stock_code: str


def get_stock_code_from_gpt(user_input: str) -> StockCode | None:
    """주식 종목 코드를 반환하기 위한 함수"""
    messages = [
        {
            "role": "system",
            "content": (
                "너는 유저의 질문에 포함된 주식종목의 주식코드를 찾아내는 프로그램이야. "
                "유저의 질문에 포함된 주식종목의 주식코드를 찾아내서 주식코드를 반환해줘"
            ),
        },
        {
            "role": "user",
            "content": (
                "아래의 질문을 통해, 주식종목 코드를 알려줘. "
                "주식 종목 코드는 '000000'처럼, 6자리 숫자로 이루어져 있어.\n"
                f"유저의 질문: {user_input}"
            ),
        },
    ]
    response = client.beta.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=messages,
        max_tokens=150,
        temperature=0.7,
        response_format=StockCode,
    )
    return response.choices[0].message.parsed


def get_stock_price(ticker_symbol: str) -> dict:
    """주식 가격 정보를 가져오기 위한 함수"""
    try:
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


def answer_paraphrase(answer_data: dict, user_input: str) -> str | None:
    """주식 정보데이터를 가지고 답변을 위한 파라프라이즈 함수"""
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
    response = client.beta.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content


def act(user_input):
    """사용자 입력에 따라 행동 결정"""
    # 주식 가격 요청 패턴 검사

    stock_code = get_stock_code_from_gpt(user_input)
    add_ks_mark = f"{stock_code.stock_code}.KS"
    stock_info = get_stock_price(add_ks_mark)
    answer = answer_paraphrase(stock_info, user_input)
    return answer


def main():
    """main function"""

    response = act("삼성전자 주가")
    print(response)


if __name__ == "__main__":
    main()
