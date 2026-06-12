# interview_app/frontend/report.py

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict
import uuid

import pandas as pd
import streamlit as st

MAX_CONTENT_PREVIEW = 80


class InterviewMessage(TypedDict):
    """면접 대화 메시지 한 건입니다."""

    role: str
    content: str


class InterviewSession(TypedDict):
    """UUID 세션 하나에 연결되는 제목과 메시지 목록입니다."""

    title: str
    messages: list[InterviewMessage]


def get_selected_conversation() -> InterviewSession | None:
    """리포트로 내보낼 현재 면접 세션을 반환한다."""
    conversations = st.session_state.get("conversations", {})
    current_id = st.session_state.get("current_session_id")
    if not current_id or current_id not in conversations:
        return None
    return conversations[current_id]


def ensure_session_state() -> None:
    """면접 세션 저장소와 현재 세션 ID를 초기화한다."""
    # rerun 시마다 새 세션이 생기지 않도록 없을 때만 만든다.
    if "conversations" not in st.session_state:
        first_id = str(uuid.uuid4())
        st.session_state.conversations = {
            first_id: {"title": "면접 세션 1", "messages": []}
        }
        st.session_state.current_session_id = first_id


def add_new_session() -> None:
    """새 UUID 면접 세션을 추가하고 현재 세션으로 전환한다."""
    ensure_session_state()
    conversations = st.session_state.conversations
    # UUID 생성은 반드시 이 함수 안에서만 실행한다. (rerun 시 중복 생성 방지)
    new_id = str(uuid.uuid4())
    conversations[new_id] = {
        "title": f"면접 세션 {len(conversations) + 1}",
        "messages": [],
    }
    st.session_state.current_session_id = new_id


def delete_current_session() -> None:
    """현재 세션을 삭제하고 남은 세션으로 안전하게 이동한다."""
    conversations = st.session_state.get("conversations", {})
    current_id = st.session_state.get("current_session_id")
    if not current_id or current_id not in conversations:
        return
    # 마지막 세션은 삭제하지 않고 메시지만 비운다. (KeyError 방지)
    if len(conversations) == 1:
        conversations[current_id]["messages"] = []
        return
    del conversations[current_id]
    st.session_state.current_session_id = next(iter(conversations))


def render_final_dashboard(usage_summary: dict) -> None:
    """최종 제출 전 사용량과 진행 상태를 대시보드로 표시한다."""
    usage_summary = usage_summary or {}

    request_count = usage_summary.get("request_count", 0)
    total_tokens = usage_summary.get("total_tokens", 0)
    st.metric("총 요청 수", f"{request_count}회")
    st.metric("총 토큰", f"{total_tokens:,}")

    prompt_tokens = usage_summary.get("prompt_tokens", 0)
    completion_tokens = usage_summary.get("completion_tokens", 0)
    token_data = pd.DataFrame(
        {"토큰 수": [prompt_tokens, completion_tokens]},
        index=["입력(prompt)", "출력(completion)"],
    )
    st.bar_chart(token_data)

    # st.progress()는 0.0~1.0 범위만 받는다. 하한/상한을 모두 방어한다.
    try:
        ratio = float(usage_summary.get("daily_limit_ratio", 0.0))
    except (TypeError, ValueError):
        ratio = 0.0
    ratio = min(max(ratio, 0.0), 1.0)
    st.progress(ratio)
    st.caption(f"일일 한도 소진율: {ratio:.0%}")


def build_interview_report(
    conversation: dict[str, Any],
    usage_summary: dict[str, Any],
    feedback_summary: dict[str, int] | None = None,
) -> str:
    """선택된 면접 세션을 마크다운 리포트 문자열로 만든다."""
    # 주의: API 키, .env 값, 시스템 프롬프트 원문은 리포트에 넣지 않는다.
    title = conversation.get("title", "면접 세션")
    lines = [f"# 면접 리포트 - {title}"]
    lines.append("")
    lines.append(f"- 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 세션 제목: {title}")
    lines.append("")

    lines.append("## 면접 대화 내역")
    lines.append("")
    messages = conversation.get("messages", [])
    if messages:
        lines.append("| 순번 | 역할 | 내용 |")
        lines.append("| --- | --- | --- |")
        for i, msg in enumerate(messages, start=1):
            content = msg.get("content", "")[:MAX_CONTENT_PREVIEW]
            content = content.replace("\n", " ").replace("|", "\\|")
            lines.append(f"| {i} | {msg.get('role', '')} | {content} |")
    else:
        lines.append("(아직 기록된 메시지가 없습니다.)")
    lines.append("")

    lines.append("## 피드백 요약")
    lines.append("")
    if feedback_summary:
        lines.append(f"- 👍 좋아요: {feedback_summary.get('up', 0)}건")
        lines.append(f"- 👎 싫어요: {feedback_summary.get('down', 0)}건")
    else:
        lines.append("- 수집된 피드백이 없습니다.")
    lines.append("")

    lines.append("## 사용량 요약")
    lines.append("")
    usage_summary = usage_summary or {}
    lines.append(f"- 총 요청 수: {usage_summary.get('request_count', 0)}회")
    lines.append(f"- 총 토큰: {usage_summary.get('total_tokens', 0):,}")
    lines.append(f"- 입력(prompt) 토큰: {usage_summary.get('prompt_tokens', 0):,}")
    lines.append(
        f"- 출력(completion) 토큰: {usage_summary.get('completion_tokens', 0):,}"
    )
    lines.append("")

    # Day 4 self2에서 저장한 이력서 질문 흐름이 있으면 함께 요약한다.
    resume_file_name = st.session_state.get("resume_file_name")
    resume_questions = st.session_state.get("resume_questions")
    resume_question_count = st.session_state.get("resume_question_count")
    if resume_file_name or resume_questions:
        lines.append("## 이력서 질문 요약")
        lines.append("")
        if resume_file_name:
            lines.append(f"- 이력서 파일: {resume_file_name}")
        if resume_question_count:
            lines.append(f"- 생성 질문 수: {resume_question_count}개")
        if resume_questions:
            for i, question in enumerate(resume_questions, start=1):
                lines.append(f"{i}. {str(question)[:MAX_CONTENT_PREVIEW]}")
        lines.append("")

    lines.append("## 9주차 완성 기능")
    lines.append("")
    lines.append("- Streamlit 프론트 + FastAPI 백엔드 분리 실행")
    lines.append("- SSE 스트리밍 면접 대화")
    lines.append("- 멀티에이전트 / 이력서 기반 질문 생성")
    lines.append("- 면접·이력서·설정 멀티페이지 구조")
    lines.append("- 로딩·에러·피드백·검색 UX 기능")
    lines.append("")

    return "\n".join(lines)


def render_report_download(
    session_id: str,
    conversation: dict[str, Any] | None,
    usage_summary: dict[str, Any],
) -> None:
    """리포트 생성 조건을 확인하고 다운로드 버튼을 표시한다."""
    if not conversation:
        st.info("리포트를 만들 세션을 먼저 선택하세요.")
        return
    messages = conversation.get("messages", [])
    if not messages:
        st.warning("선택한 세션에 메시지가 없습니다.")
        return
    report_md = build_interview_report(conversation, usage_summary)
    st.download_button(
        "리포트 다운로드",
        data=report_md,
        file_name=f"interview_{session_id}.md",
        mime="text/markdown",
    )
