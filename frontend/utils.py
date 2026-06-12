# interview_app/frontend/utils.py
# Day 5 self1: 로딩 UX · 에러 핸들링 · 응답 피드백 · 대화 검색 함수 골격
# (8주차 roles.py, tools.py, agents 역할 파일(coach_agents.py)은 이 파일에서 import하지 않습니다.)

from __future__ import annotations

from typing import Any

import httpx
import streamlit as st


# === 2단계: 로딩·빈 상태 표시 함수 골격 ===


def render_waiting_state(message: str) -> None:
    """면접 코치 응답 대기 상태를 화면에 표시한다."""
    with st.spinner(message):
        pass


def render_empty_interview_state(message_count: int) -> None:
    """아직 면접이 시작되지 않았을 때 첫 화면 안내를 표시한다."""
    placeholder = st.empty()
    if message_count == 0:
        placeholder.info("아직 면접이 시작되지 않았습니다. 질문을 입력해 면접을 시작해 보세요.")


def render_streaming_answer(tokens) -> str:
    """수신 토큰을 하나의 placeholder에 누적 표시한다."""
    placeholder = st.empty()
    answer = ""
    for token in tokens:
        answer += token
        placeholder.markdown(answer + "▌")
    placeholder.markdown(answer)
    return answer


# === 3단계: 에러 핸들링 유틸 골격 ===


def format_error_message(error: Exception) -> dict[str, str]:
    """프론트엔드에서 보여 줄 오류 메시지와 표시 수준을 만든다."""
    # API 키, payload 원문, traceback은 사용자 메시지에 넣지 않는다.
    if isinstance(error, httpx.ConnectError):
        return {
            "level": "error",
            "message": "백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요.",
        }
    if isinstance(error, httpx.TimeoutException):
        return {
            "level": "warning",
            "message": "응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.",
        }
    if isinstance(error, httpx.HTTPStatusError):
        return {
            "level": "error",
            "message": "서버가 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        }
    return {"level": "error", "message": "알 수 없는 오류가 발생했습니다."}


def show_api_error(error: Exception) -> None:
    """오류 종류에 맞는 Streamlit 메시지를 표시한다."""
    formatted = format_error_message(error)
    if formatted["level"] == "warning":
        st.warning(formatted["message"])
    else:
        st.error(formatted["message"])


def check_backend_health(backend_url: str = "http://localhost:8000") -> bool:
    """FastAPI /health endpoint를 호출해 백엔드 생존 여부를 확인한다."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{backend_url}/health")
            response.raise_for_status()
            return response.json().get("status") == "ok"
    except Exception:
        return False


# === 4단계: st.feedback 연결 골격 ===


def render_feedback_widget(message_id: str, conversation_id: str, index: int) -> None:
    """AI 응답에 대한 thumbs 피드백 입력 위치를 만든다."""
    feedback_value = st.feedback("thumbs", key=f"fb_{message_id}_{index}")
    # 0(싫어요)도 유효한 값이므로 is not None으로 검사한다.
    if feedback_value is not None:
        rating = "up" if feedback_value == 1 else "down"
        payload = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "rating": rating,
        }
        safe_post_feedback(payload)


def safe_post_feedback(payload: dict[str, Any]) -> dict[str, Any] | None:
    """피드백 저장 요청을 보내고 사용자 친화적인 오류 메시지를 표시한다."""
    try:
        response = httpx.post(
            "http://localhost:8000/feedback", json=payload, timeout=5.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as error:
        show_api_error(error)
        return None


# === 5단계: 대화 검색·필터링 골격 ===


def filter_conversations(
    messages: list[dict[str, str]],
    keyword: str,
    roles: list[str],
) -> list[dict[str, str]]:
    """대화 내역에서 조건에 맞는 메시지를 찾는다."""
    # 핵심 규칙:
    # 1) keyword가 비어 있으면 내용 조건은 항상 통과
    # 2) roles가 비어 있으면 역할 조건은 항상 통과
    # 3) 검색어와 본문 모두 .strip().lower()로 정규화 후 비교
    normalized_keyword = keyword.strip().lower()
    filtered: list[dict[str, str]] = []
    for message in messages:
        content = message.get("content", "").strip().lower()
        keyword_matches = not normalized_keyword or normalized_keyword in content
        role_matches = not roles or message.get("role") in roles
        if keyword_matches and role_matches:
            filtered.append(message)
    return filtered


# === 6단계: 대시보드 입력 위치 확인 ===
# TODO: fetch_usage()로 GET http://localhost:8000/usage를 호출하는 함수 위치
# TODO: st.metric으로 요청 수와 총 토큰을 표시하는 사이드바 위치
# TODO: st.bar_chart로 prompt vs completion 토큰 비율을 표시하는 위치
# TODO: st.progress로 일일 한도 소진율을 표시하는 위치
# → 이 네 위치는 day5-self2에서 render_final_dashboard()로 묶어 완성합니다.


# === Day 5 self1 완료 상태 ===
# [x] render_waiting_state / render_empty_interview_state / render_streaming_answer 골격 작성
# [x] format_error_message / show_api_error / check_backend_health 골격 작성
# [x] render_feedback_widget / safe_post_feedback 골격 작성
# [x] filter_conversations 골격 작성
# [x] 대시보드 입력 위치 메모 완료

# === Day 5 self2 인계 항목 ===
# - 멀티 세션 관리: st.session_state.conversations + UUID 세션 관리 연결
# - 리포트 내보내기: frontend/report.py + st.download_button 완성
# - README 최종 작성: Q9-1 5개 기준 확인표 포함
# - 대시보드 완성: render_final_dashboard()로 대시보드 표시 묶기
