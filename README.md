## MCP 예제: 주식 질의 서버/클라이언트

이 레포는 MCP(Model Context Protocol) 스타일로 서버(`src/mcp_server.py`)와 클라이언트(`src/mcp_client.py`)를 분리한 교육용 예제입니다. 서버는 결정적 도구(tools)와 프롬프트(prompts), 리소스(resources)를 제공하고, 클라이언트는 stdio로 서버에 연결해 상호작용하며 LLM 호출을 담당합니다.

### 구성
- `src/mcp_server.py`
  - tools
    - `get_stock_price(ticker)`: 야후 파이낸스에서 주가 정보 조회 (결정적)
  - prompts
    - `extract-stock-code(user_input)`: 종목코드 추출용 메시지 템플릿
    - `stock-answer(user_input, ...)`: 답변 작성용 메시지 템플릿
  - resources
    - `help`: 사용법 요약 텍스트 리소스

- `src/mcp_client.py`
  - stdio로 서버 프로세스를 실행하고 연결
  - 도구/리소스/프롬프트 목록 조회 및 시연
  - LLM 호출(종목코드 추출 → 주가 조회 → 답변 작성) 클라이언트에서 수행

참고: MCP Prompt API는 FastMCP 버전에 따라 시그니처가 달라질 수 있어 본 예제에서는 필수 요소인 tools/resources 위주로 구성했습니다. 필요 시 서버에 `@mcp.prompt`를 추가해 확장할 수 있습니다.

### 사전 준비
1) Python 3.12 이상
2) 환경변수
```
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-nano  # 필요시 변경
```
`.env` 파일을 프로젝트 루트에 두면 `src/settings.py`에서 자동 로드됩니다.

### 실행 흐름
1) 클라이언트 실행: 서버를 stdio로 자동 실행하여 연결합니다.
```
python -m src.mcp_client
```

2) 출력 예시
- [tools] 도구 목록
- [resources] 리소스 URI 목록
- [help] 도움말 리소스 본문
- [prompts] 프롬프트 목록
- [extract-stock-code] 추출 결과
- [get_stock_price] 조회 결과
- [final-answer] 최종 답변

### 동작 설명
1) `ask_stock("카페24 주가")` 요청
   - `extract_stock_code`로 종목코드 추출 → 예: `034730` (샘플)
   - `get_stock_price("034730.KS")` 조회
   - `compose_answer`로 자연어 답변 생성

### 주의사항
- OpenAI API 호출이 포함되어 있으므로 키가 필요합니다.
- `yfinance`의 데이터 응답은 환경/시간대에 따라 달라질 수 있습니다.


