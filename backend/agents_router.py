# interview_app/backend/agents_router.py
"""
Day 3 self2 책임 메모
---------------------
- 이 파일이 담당하는 것:
  → 8주차 에이전트를 감싸고 SSE로 내보내는 백엔드 라우터
- 이 파일이 담당하지 않는 것:
  → 화면 표시, 사용자 입력 처리, AI 키 관리
- Day 3 self1의 api_client.py와의 관계:
  → 프론트 api_client.py가 이 파일의 /agents/stream 엔드포인트를 호출한다
- 8주차 파일 재사용 원칙:
  → roles.py, tools.py, agents.py 역할 파일(coach_agents.py)은 재작성하지 않고 import만 한다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents import Runner, RunItemStreamEvent
from openai.types.responses import ResponseTextDeltaEvent

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.coach_agents import question_agent, triage_agent


router = APIRouter(prefix="/agents", tags=["agents"])


class InterviewAgentRequest(BaseModel):
    """면접 에이전트 스트림 요청 값을 담습니다."""

    message: str
    mode: str = "single"


async def run_interview_agent_stream(message: str, mode: str):
    """면접 질문을 에이전트 스트림으로 실행합니다.

    Args:
        message: 면접 질문 문자열
        mode: "single" (일반) 또는 "multi" (멀티에이전트)

    Yields:
        에이전트 스트림 이벤트 객체
    """
    agent = triage_agent if mode == "multi" else question_agent
    stream_result = Runner.run_streamed(agent, message)

    async for event in stream_result.stream_events():
        yield event


async def iter_agent_events(agent_stream):
    """에이전트 스트림 이벤트를 SSE 형식으로 정리합니다."""
    async for event in agent_stream:
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            payload = {"type": "token", "delta": event.data.delta}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        elif isinstance(event, RunItemStreamEvent):
            payload = {"type": "status", "label": "run_item"}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            if "handoff" in event.name:
                payload = {"type": "status", "label": "handoff_detected"}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/stream")
async def stream_interview_agent_endpoint(request: InterviewAgentRequest):
    """면접 에이전트의 스트리밍 응답을 SSE로 전달합니다."""
    agent_stream = run_interview_agent_stream(request.message, request.mode)
    return StreamingResponse(
        iter_agent_events(agent_stream),
        media_type="text/event-stream",
    )
