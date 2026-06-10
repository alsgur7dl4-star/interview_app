# frontend/app.py 역할:
# → Streamlit 화면을 만들고 사용자의 입력과 면접 코치 응답 출력을 관리한다.

import json
import sys
import time
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from core import roles as roles_module

    roles_import_error = None
except Exception as e:
    roles_module = None
    roles_import_error = e


st.set_page_config(
    page_title="AI 면접 코치",
    page_icon="🎤",
)

st.title("AI 면접 코치")
st.caption("면접 답변을 입력하면 면접 코치가 확인해 드립니다.")


def get_interviewer_options() -> dict[str, str]:
    """roles.py 프리셋에서 {역할 키: 화면 표시 이름} 매핑을 만든다."""
    if roles_module is None:
        return {}
    return {key: role.name for key, role in roles_module.ROLES.items()}


def get_system_prompt(role_key: str) -> str:
    """선택한 role_key 로 roles.py 의 system_prompt 를 찾아 반환한다."""
    if roles_module is None:
        return "면접 코치 시스템 프롬프트를 불러오지 못했습니다."
    role = roles_module.get_role(role_key)
    return role.system_prompt


def initialize_messages():
    """최초 1회만 대화 메시지를 초기화한다."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "안녕하세요! AI 면접 코치입니다. 면접 답변을 입력해 주세요.",
            }
        ]


def generate_coach_reply(user_text: str, role_key: str) -> str:
    """선택한 면접관 유형을 반영한 임시 응답을 만든다. (실제 API 호출 없음)"""
    system_prompt = get_system_prompt(role_key)
    label = get_interviewer_options().get(role_key, role_key)
    return (
        f"[{label}] 관점에서 답변을 확인했습니다. "
        f"(프롬프트: {system_prompt[:30]}...) "
        "면접 답변을 확인했습니다. (임시 응답)"
    )


def fake_stream_generator(reply_text: str):
    """임시 응답을 단어 단위로 흘려보내는 가짜 스트림 generator."""
    for word in reply_text.split():
        time.sleep(0.08)
        yield word + " "


initialize_messages()

interviewer_options = get_interviewer_options()
if "selected_role" not in st.session_state:
    st.session_state.selected_role = next(iter(interviewer_options), "")

with st.sidebar:
    st.header("면접관 설정")

    role_keys = list(interviewer_options.keys())
    if role_keys:
        current_key = st.session_state.selected_role
        current_index = role_keys.index(current_key) if current_key in role_keys else 0
        st.session_state.selected_role = st.selectbox(
            "면접관 유형",
            role_keys,
            index=current_index,
            format_func=lambda key: interviewer_options[key],
        )

    st.divider()
    st.subheader("Day2 입력 준비 상태")

    messages = st.session_state.get("messages", [])
    last_user = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), "없음"
    )
    last_assistant = next(
        (m["content"] for m in reversed(messages) if m["role"] == "assistant"), "없음"
    )

    st.write(
        "선택된 면접관 유형:",
        interviewer_options.get(st.session_state.selected_role, "미선택"),
    )
    st.write("현재 메시지 수:", len(messages))
    st.write("마지막 user 메시지:", last_user)
    st.write("마지막 assistant 메시지(앞 50자):", last_assistant[:50])

    st.json(
        {
            "role": st.session_state.get("selected_role", "미선택"),
            "message_count": len(st.session_state.get("messages", [])),
            "ready_for_day2": len(st.session_state.get("messages", [])) >= 2,
        }
    )

    st.download_button(
        "면접 기록 다운로드 (JSON)",
        data=json.dumps(st.session_state.messages, ensure_ascii=False, indent=2),
        file_name="interview_messages.json",
        mime="application/json",
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("면접 답변을 입력해 주세요.")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    reply_text = generate_coach_reply(user_input, st.session_state.selected_role)
    with st.chat_message("assistant"):
        response_text = st.write_stream(fake_stream_generator(reply_text))

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()

with st.expander("면접 코치 설정 확인"):
    if roles_import_error is not None:
        st.warning(f"roles.py import 실패: {roles_import_error}")

    st.write("역할 프리셋 키 목록:", list(interviewer_options.keys()))
    st.write("현재 messages 길이:", len(st.session_state.messages))

    system_prompt = get_system_prompt(st.session_state.get("selected_role", ""))
    st.write("시스템 프롬프트 첫 50자:", system_prompt[:50])
