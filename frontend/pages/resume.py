# interview_app/frontend/pages/resume.py
# 책임 메모:
# - Day 4 self2에서 이력서 업로드와 맞춤 질문 생성을 확장할 자리입니다.
# - 오늘은 입력 영역과 TODO 위치만 표시합니다.
# - 면접 채팅 로직을 이 파일 안에 복사하지 않습니다.

import streamlit as st

settings = st.session_state.get("settings", {})

st.title("이력서 분석")
st.caption(f"현재 질문 역할: {settings.get('role_preset', '기술 면접')}")

st.info("Day 4 self2에서 이력서 업로드와 맞춤 질문 생성을 완성합니다.")

# TODO(self2): st.file_uploader를 배치해요.
# TODO(self2): 이력서 텍스트를 읽고 질문 생성 요청 dict를 만들어요.
# TODO(self2): 질문 목록과 Function Calling 확인 데이터를 분리해 표시해요.
