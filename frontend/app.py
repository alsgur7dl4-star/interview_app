import sys
from pathlib import Path

import streamlit as st

# frontend/app.py 에서 core/roles.py 를 import 하기 위해
# 프로젝트 루트(interview_app)를 모듈 검색 경로에 추가한다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# 8주차 roles.py import (roles.py 자체는 수정하지 않는다)
try:
    from core import roles as roles_module

    roles_import_error = None
except Exception as e:  # import 실패 시 화면에서 안내하기 위해 보관
    roles_module = None
    roles_import_error = e


# Streamlit 기본 설정
st.set_page_config(
    page_title="AI 면접 코치",
    page_icon="🎤",
)

st.title("AI 면접 코치")
st.caption("면접 답변을 입력하면 면접 코치가 확인해 드립니다.")


def get_role_presets():
    """roles.py 에서 역할 프리셋 딕셔너리를 찾아 반환한다."""
    if roles_module is None:
        return {}
    for name in ("ROLES", "ROLE_PRESETS", "PRESETS", "roles", "role_presets"):
        value = getattr(roles_module, name, None)
        if isinstance(value, dict):
            return value
    return {}


def get_system_prompt():
    """roles.py 에서 시스템 프롬프트 문자열을 찾아 반환한다."""
    if roles_module is None:
        return None
    for name in ("SYSTEM_PROMPT", "system_prompt", "DEFAULT_SYSTEM_PROMPT"):
        value = getattr(roles_module, name, None)
        if isinstance(value, str):
            return value
    return None


def initialize_messages():
    """최초 1회만 대화 메시지를 초기화한다."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "안녕하세요! AI 면접 코치입니다. 면접 답변을 입력해 주세요.",
            }
        ]


def handle_user_input(user_text: str):
    """user 메시지를 추가한 뒤 assistant 임시 응답을 추가한다."""
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.messages.append(
        {"role": "assistant", "content": "면접 답변을 확인했습니다. (임시 응답)"}
    )


initialize_messages()

# 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 사용자 입력 연결
user_input = st.chat_input("면접 답변을 입력해 주세요.")
if user_input:
    handle_user_input(user_input)
    st.rerun()

# 면접 코치 설정 확인
with st.expander("면접 코치 설정 확인"):
    if roles_import_error is not None:
        st.warning(f"roles.py import 실패: {roles_import_error}")

    role_presets = get_role_presets()
    st.write("역할 프리셋 키 목록:", list(role_presets.keys()))

    st.write("현재 messages 길이:", len(st.session_state.messages))

    system_prompt = get_system_prompt()
    if system_prompt:
        st.write("시스템 프롬프트 첫 50자:", system_prompt[:50])


# =============================
# day1-self2 TODO
# ============================
# TODO 1: 면접관 유형 사이드바 위젯 추가 (압박/편안/기술/인성 선택)
# TODO 2: 선택한 면접관 유형을 st.session_state에 저장하기
# TODO 3: st.write_stream 출력 흐름 연결 (임시 generator 사용)
# TODO 4: 면접 기록 (면접관 유형 + 질문 + 답변 + 코치 응답) 구조 설계
# ============================
