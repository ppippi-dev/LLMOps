import asyncio
import logging
import os
import warnings

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm  # For multi-model support
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types  # For creating message Content/Parts

# Ignore all warnings
warnings.filterwarnings("ignore")


logging.basicConfig(level=logging.ERROR)

print("Libraries imported.")
MODEL_GPT_5_NANO = "openai/gpt-5-nano"  # You can also try: gpt-4.1-mini, gpt-4o etc.


openai_llm = LiteLlm(
    model=MODEL_GPT_5_NANO,
    api_key=os.environ.get("OPENAI_API_KEY"),
)


# @title Define the get_weather Tool
def get_weather(city: str) -> dict[str, str]:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather called for city: {city} ---")  # Log tool execution
    city_normalized = city.lower().replace(" ", "")  # Basic normalization

    mock_weather_db = {
        "newyork": {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25°C.",
        },
        "london": {
            "status": "success",
            "report": "It's cloudy in London with a temperature of 15°C.",
        },
        "tokyo": {
            "status": "success",
            "report": "Tokyo is experiencing light rain and a temperature of 18°C.",
        },
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have weather information for '{city}'.",
        }


weather_agent = Agent(
    name="weather_agent_v1",
    model=openai_llm,  # OpenAI 모델은 LiteLlm로 전달
    description="Provides weather information for specific cities.",
    instruction="You are a helpful weather assistant. "
    "When the user asks for the weather in a specific city, "
    "use the 'get_weather' tool to find the information. "
    "If the tool returns an error, inform the user politely. "
    "If the tool is successful, present the weather report clearly.",
    tools=[get_weather],  # Pass the function directly
)

# ADK가 찾을 수 있도록 루트 에이전트를 노출합니다.
root_agent = weather_agent

session_service = InMemorySessionService()

APP_NAME = "weather_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# 세션 생성은 임포트 시점이 아닌 실행 시점에 수행하도록 지연시킵니다.

runner = Runner(
    agent=weather_agent,  # The agent we want to run
    app_name=APP_NAME,  # Associates runs with our app
    session_service=session_service,  # Uses our session manager
)


async def call_agent_async(query: str, agent_runner: Runner, user_id: str, session_id: str):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")

    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."

    async for event in agent_runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break

    print(f"<<< Agent Response: {final_response_text}")


async def init_session():
    # 웹 환경(이미 이벤트 루프가 실행 중)에서 임포트 시 에러가 나지 않도록,
    # 세션 생성은 명시적으로 호출될 때만 수행합니다.
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)


async def run_conversation():
    await call_agent_async(
        "What is the weather like in London?",
        agent_runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    await call_agent_async("How about Paris?", agent_runner=runner, user_id=USER_ID, session_id=SESSION_ID)

    await call_agent_async(
        "Tell me the weather in New York",
        agent_runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


if __name__ == "__main__":

    async def run_demo():
        await init_session()
        await run_conversation()

    asyncio.run(run_demo())
