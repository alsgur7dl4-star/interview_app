# interview_app/frontend/pages/interview.py
# 책임 메모:
# - Day 3에서 완성한 면접 질문 입력과 SSE 응답 표시를 이어받습니다.
# - st.session_state.settings에서 모델과 temperature를 읽습니다.
# - 8주차 agents 역할 파일(coach_agents.py), roles.py, tools.py는 수정하지 않습니다.

import streamlit as st

from frontend.api_client import stream_interview_agent

settings = st.session_state.get("settings", {})

st.title("면접 연습")
st.caption(f"현재 역할 프리셋: {settings.get('role_preset', '기술 면접')}")
st.caption(
    f"모델: {settings.get('model', 'gpt-4o-mini')} · "
    f"temperature: {settings.get('temperature', 0.7)}"
)

if "interview_messages" not in st.session_state:
    st.session_state.interview_messages = []

for message in st.session_state.interview_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("면접 답변 또는 질문을 입력해 주세요.")
if user_input:
    st.session_state.interview_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        for event in stream_interview_agent(user_input):
            if event.get("type") == "token":
                full_text += event.get("delta", "")
                placeholder.markdown(full_text)

    st.session_state.interview_messages.append(
        {"role": "assistant", "content": full_text}
    )
