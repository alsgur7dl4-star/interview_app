# interview_app/frontend/pages/resume.py
"""
Day 4 self2 책임 메모
---------------------
- 이 파일이 담당하는 것:
  → 이력서 .txt 업로드, 텍스트 읽기, 맞춤 질문 생성 요청 준비,
    Function Calling 확인 데이터 표시, 질문 생성 대시보드.
- 이 파일이 담당하지 않는 것:
  → 면접 채팅 전체 화면 복사, API 키 입력, 8주차 agents 파일 수정.
- Day 5 self1로 넘길 값:
  → resume_file_name, resume_questions, resume_question_count,
    resume_step4b_done.
"""

import pandas as pd
import streamlit as st

MIN_RESUME_LENGTH = 30

DEFAULT_SETTINGS = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "system_prompt": "당신은 전문 면접관입니다. 지원자의 역량을 파악하는 심층 질문을 해주세요.",
    "role_preset": "기술 면접",
}


def read_resume_text(uploaded_file):
    """업로드된 이력서 파일에서 면접 질문 생성용 텍스트를 준비합니다."""
    if uploaded_file is None:
        return None

    try:
        resume_text = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        st.error("UTF-8로 읽을 수 없는 파일입니다. utf-8 .txt로 저장한 뒤 다시 업로드하세요.")
        return None

    resume_text = resume_text.strip()

    if not resume_text:
        st.warning("이력서 파일이 비어 있습니다. 내용을 채운 뒤 다시 업로드하세요.")
        return None

    if len(resume_text) < MIN_RESUME_LENGTH:
        st.warning(f"이력서 텍스트가 너무 짧습니다 ({MIN_RESUME_LENGTH}자 이상 필요). 질문 생성 요청으로 보내지 않습니다.")
        return None

    return resume_text


def build_resume_question_request(resume_text: str, question_count: int) -> dict:
    """이력서 기반 면접 질문 생성 요청 값을 만듭니다."""
    settings = st.session_state.get("settings", {})
    return {
        "resume_text": resume_text,
        "question_count": question_count,
        "model": settings.get("model", DEFAULT_SETTINGS["model"]),
        "temperature": settings.get("temperature", DEFAULT_SETTINGS["temperature"]),
        "system_prompt": settings.get("system_prompt", DEFAULT_SETTINGS["system_prompt"]),
        "role_preset": settings.get("role_preset", DEFAULT_SETTINGS["role_preset"]),
    }


def make_temp_result(request: dict) -> dict:
    role_preset = request["role_preset"]
    resume_text = request["resume_text"]
    question_count = request["question_count"]

    question_templates = [
        f"[{role_preset}] 이력서에서 가장 강조하고 싶은 프로젝트와 본인의 역할을 설명해 주세요.",
        f"[{role_preset}] 이력서에 적힌 기술 중 가장 자신 있는 것을 실제 사용 경험과 함께 말해 주세요.",
        f"[{role_preset}] 프로젝트 진행 중 겪은 가장 어려운 문제와 해결 과정을 설명해 주세요.",
        f"[{role_preset}] 협업 과정에서 의견 충돌이 있었을 때 어떻게 조율했는지 말해 주세요.",
        f"[{role_preset}] 이력서의 경험이 지원 직무에 어떻게 연결되는지 설명해 주세요.",
        f"[{role_preset}] 최근에 새로 학습한 기술과 학습 방법을 공유해 주세요.",
        f"[{role_preset}] 본인이 작성한 코드나 산출물의 품질을 어떻게 검증하나요?",
        f"[{role_preset}] 일정이 촉박한 상황에서 우선순위를 정한 경험을 말해 주세요.",
        f"[{role_preset}] 실패했던 경험과 그로부터 배운 점을 설명해 주세요.",
        f"[{role_preset}] 입사 후 1년 안에 이루고 싶은 목표는 무엇인가요?",
    ]
    questions = question_templates[:question_count]

    keywords = resume_text.split()[:5]
    tool_calls = [
        {
            "name": "extract_resume_keywords",
            "arguments": {"section": "projects"},
            "result": {"keywords": keywords},
        }
    ]

    return {"questions": questions, "tool_calls": tool_calls}


def render_function_call_result(result: dict) -> None:
    """질문 생성 결과와 도구 호출 확인 데이터를 분리해 표시합니다."""
    questions = result.get("questions", [])

    st.subheader("생성된 면접 질문")
    if questions:
        for i, question in enumerate(questions, start=1):
            st.markdown(f"{i}. {question}")
    else:
        st.warning("생성된 질문이 없습니다.")

    tool_calls = result.get("tool_calls", [])
    with st.expander("Function Calling 확인 데이터"):
        if tool_calls:
            st.json(tool_calls)
        else:
            st.write("호출 없음")


def save_resume_question_state(file_name: str, questions: list[str]) -> None:
    """이력서 기반 질문 생성 결과를 세션 상태에 저장합니다."""
    # Day 5 report.py가 읽을 key: resume_file_name, resume_questions,
    # resume_question_count, resume_step4b_done
    st.session_state.resume_file_name = file_name
    st.session_state.resume_questions = questions
    st.session_state.resume_question_count = len(questions)
    st.session_state.resume_step4b_done = bool(questions)


def render_resume_dashboard() -> None:
    """이력서 기반 질문 생성 결과를 대시보드로 표시합니다."""
    st.subheader("질문 생성 대시보드")

    questions = st.session_state.get("resume_questions", [])
    question_count = st.session_state.get("resume_question_count", 0)

    st.metric("생성 질문 수", question_count)

    if questions:
        short_count = sum(1 for q in questions if len(q) <= 30)
        medium_count = sum(1 for q in questions if 30 < len(q) <= 60)
        long_count = sum(1 for q in questions if len(q) > 60)
        length_dist = pd.DataFrame(
            {"질문 수": [short_count, medium_count, long_count]},
            index=["30자 이하", "31~60자", "60자 초과"],
        )
        st.bar_chart(length_dist)
    else:
        st.info("아직 생성된 질문이 없습니다. 이력서를 업로드하고 질문을 생성하세요.")

    goal_count = 10
    progress = min(question_count / goal_count, 1.0)
    st.progress(progress, text=f"Step 4-B 진행률 (목표 {goal_count}문제): {question_count}/{goal_count}")


settings = st.session_state.get("settings", {})

st.title("이력서 분석")
st.caption(f"현재 질문 역할: {settings.get('role_preset', '기술 면접')}")

uploaded_file = st.file_uploader(
    "이력서 텍스트 파일을 업로드하세요",
    type=["txt"],
)

resume_text = read_resume_text(uploaded_file)

if resume_text:
    st.text_area("이력서 미리보기", value=resume_text[:500], height=200, disabled=True)
else:
    st.info("utf-8로 저장한 .txt 이력서 파일을 업로드하면 맞춤 면접 질문을 생성할 수 있습니다.")

question_count = st.number_input(
    "생성할 질문 수",
    min_value=3,
    max_value=10,
    value=5,
    step=1,
)

if st.button("이력서 기반 질문 생성"):
    if not resume_text:
        st.warning("먼저 이력서 .txt 파일을 업로드하세요.")
    else:
        request = build_resume_question_request(resume_text, int(question_count))

        with st.expander("질문 생성 요청 확인"):
            st.json(request)

        result = make_temp_result(request)

        questions = result.get("questions", [])
        save_resume_question_state(uploaded_file.name, questions)

        render_function_call_result(result)

st.divider()
render_resume_dashboard()
