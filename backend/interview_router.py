# backend/interview_router.py 역할:
# → FastAPI에서 면접 요청을 받아 SSE 형식으로 응답을 스트리밍한다.
#
# ===== self2 이후 연결 지점 TODO =====
# TODO 1: UUID 세션 관리
#   from interview_app.backend.sessions import create_session, add_message, get_history
#   -> day2-self2에서 연결. session_id 를 InterviewStreamRequest 에서 받아 get_history() 로 이전 이력을 꺼낸다.
# TODO 2: 예외 핸들러
#   from interview_app.backend.errors import register_exception_handlers
#   -> backend/main.py 에서 register_exception_handlers(app) 로 등록한다.
#   -> RateLimitError -> 429, APIError -> 502 로 변환.
# TODO 3: 토큰 사용량 추적
#   from interview_app.backend.usage import record_usage
#   -> stream 경로에서 usage 기록 시점이 제한될 수 있으므로 일반 /interview 엔드포인트에서 먼저 연결했습니다.
# TODO 4: 8주차 역할 프리셋 재사용
#   from interview_app.core.roles import ROLE_PROMPTS  (8주차 roles.py 이미 있으면 import만)
#   -> 본 파일의 ROLE_PROMPTS 와 8주차 코드를 비교해 import 중심으로 재사용. 재작성 금지.

import os
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# day2-self2: UUID 면접 세션 저장소 함수 연결
# (현재 실행 구조 `uvicorn backend.main:app` 기준으로 `backend.sessions` import)
from backend.sessions import (
    add_message,
    clear_session,
    create_session,
    get_history,
    get_session_role,
    set_session_role,
)

load_dotenv()

router = APIRouter(prefix="/interview", tags=["interview"])


class InterviewStreamRequest(BaseModel):
    """면접 코치 `/interview/stream` 엔드포인트가 받는 요청 모델입니다."""

    question: str = Field(
        ...,
        min_length=1,
        description="면접관이 제시한 질문입니다.",
        examples=["자기소개를 해 주세요."],
    )
    answer: str = Field(
        ...,
        min_length=1,
        description="지원자가 입력한 답변입니다.",
        examples=["안녕하세요, 저는 ..."],
    )
    role: str = Field(
        default="general",
        description="면접관 유형입니다. general · technical · hr 중 하나를 사용합니다.",
        examples=["technical"],
    )
    session_id: str | None = Field(
        default=None,
        description="UUID 기반 면접 세션 ID입니다. self2에서 연결합니다.",
    )
    model: str = Field(default="gpt-4o-mini", description="사용할 OpenAI 모델명입니다.")


def get_interview_openai_client() -> AsyncOpenAI:
    """환경 변수에서 OPENAI_API_KEY를 읽어 AsyncOpenAI 클라이언트를 만듭니다."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured",
        )

    return AsyncOpenAI(api_key=api_key)


# 면접관 유형별 시스템 프롬프트 매핑
ROLE_PROMPTS: dict[str, str] = {
    "general": "당신은 일반 면접관입니다. 지원자의 답변을 종합적으로 평가하고 개선점을 한국어로 피드백하세요.",
    "technical": "당신은 기술 면접관입니다. 지원자의 기술 역량과 문제 해결 방식을 집중 평가하고 한국어로 피드백하세요.",
    "hr": "당신은 인사 면접관입니다. 지원자의 인성, 협업 능력, 조직 적합성을 평가하고 한국어로 피드백하세요.",
}


async def interview_event_generator(
    request: InterviewStreamRequest,
) -> AsyncIterator[str]:
    """면접 코치 피드백을 SSE data 이벤트로 스트리밍합니다."""
    client = get_interview_openai_client()

    system_prompt = ROLE_PROMPTS.get(request.role, ROLE_PROMPTS["general"])

    # TODO 세션 이력 연결 (day2-self2 / Day3에서 활용):
    #   if request.session_id:
    #       history = get_history(request.session_id)
    #       # history 를 messages 앞에 붙인다.

    # TODO 예외 핸들러 연결:
    #   try: ... except RateLimitError: ... except APIError: ...
    #   -> backend/main.py 에서 register_exception_handlers(app) 로 등록하면
    #      여기서 직접 except 없어도 429/502 로 자동 변환.

    stream = await client.chat.completions.create(
        model=request.model,
        stream=True,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"질문: {request.question}\n지원자 답변: {request.answer}",
            },
        ],
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield f"data: {delta.content}\n\n"

    # TODO 토큰 사용량 추적:
    #   stream 경로에서는 usage 기록 시점이 chunk 마지막에 올 수 있다.
    #   stream=True + stream_options={"include_usage": True} 로 요청하면
    #   마지막 chunk 에서 usage 를 받을 수 있다.
    #   from interview_app.backend.usage import record_usage
    #   record_usage(request.session_id, last_chunk.usage)

    yield "data: [DONE]\n\n"


@router.post("/stream")
async def interview_stream(request: InterviewStreamRequest) -> StreamingResponse:
    """면접관 유형에 맞는 피드백을 SSE 형식으로 스트리밍합니다."""
    return StreamingResponse(
        interview_event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ===== day2-self2: 면접 세션 API =====


class SessionCreateRequest(BaseModel):
    role: str = Field(default="general", description="초기 면접관 유형")


class SessionCreateResponse(BaseModel):
    session_id: str
    role: str


@router.post("/session/create", response_model=SessionCreateResponse)
async def create_interview_session(
    body: SessionCreateRequest,
) -> SessionCreateResponse:
    """새 면접 세션을 만들고 UUID session_id 를 반환합니다."""
    session_id = create_session(body.role)
    return SessionCreateResponse(session_id=session_id, role=body.role)


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[dict[str, str]]
    role: str
    message_count: int


@router.get("/session/{session_id}/history", response_model=HistoryResponse)
async def get_interview_history(session_id: str) -> HistoryResponse:
    """세션 ID 로 면접 이력을 조회합니다."""
    try:
        messages = get_history(session_id)
        role = get_session_role(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")

    return HistoryResponse(
        session_id=session_id,
        messages=messages,
        role=role,
        message_count=len(messages),
    )


# 허용 면접관 유형
ALLOWED_ROLES = {"general", "technical", "hr"}


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., description="변경할 면접관 유형 (general · technical · hr)")


class RoleUpdateResponse(BaseModel):
    session_id: str
    role: str
    message: str


@router.patch("/session/{session_id}/role", response_model=RoleUpdateResponse)
async def update_interview_role(
    session_id: str, body: RoleUpdateRequest
) -> RoleUpdateResponse:
    """세션의 면접관 유형을 변경합니다. 허용 유형은 general · technical · hr 입니다."""
    if body.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="invalid role")

    try:
        set_session_role(session_id, body.role)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")

    return RoleUpdateResponse(
        session_id=session_id,
        role=body.role,
        message="role updated",
    )
