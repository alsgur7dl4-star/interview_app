# frontend/app.py 역할:
# → 멀티페이지 앱의 진입점으로, st.Page 등록과 st.navigation 라우팅만 담당한다.

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

st.set_page_config(
    page_title="AI 면접 코치",
    page_icon="🎤",
)


def build_pages():
    """면접 코치 앱의 세 페이지를 등록하고 실행합니다."""
    interview_page = st.Page("pages/interview.py", title="면접 연습")
    resume_page = st.Page("pages/resume.py", title="이력서 분석")
    settings_page = st.Page("pages/settings.py", title="설정")

    pg = st.navigation([interview_page, resume_page, settings_page])
    pg.run()


build_pages()
