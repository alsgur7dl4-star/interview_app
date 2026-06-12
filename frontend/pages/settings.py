# interview_app/frontend/pages/settings.py
# 책임 메모:
# - 앱 전체에서 공유할 모델, temperature, system_prompt, role_preset 값을 관리합니다.
# - API 키를 입력받지 않습니다.
# - 저장 버튼을 눌렀을 때만 st.session_state.settings를 갱신합니다.

import streamlit as st

DEFAULT_SETTINGS = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "system_prompt": "당신은 전문 면접관입니다. 지원자의 역량을 파악하는 심층 질문을 해주세요.",
    "role_preset": "기술 면접",
}

ROLE_PRESETS = {
    "기술 면접": "기술 역량을 중심으로 질문합니다.",
    "인성 면접": "협업과 태도를 중심으로 질문합니다.",
    "임원 면접": "비전과 조직 기여도를 중심으로 질문합니다.",
}


def ensure_settings() -> dict:
    """앱 전체에서 공유할 설정 dict를 준비합니다."""
    if "settings" not in st.session_state:
        st.session_state.settings = DEFAULT_SETTINGS.copy()
    return st.session_state.settings


st.title("설정")
st.caption("면접 코치 앱 전체에서 공유할 설정을 관리합니다.")

settings = ensure_settings()

model_options = ["gpt-4o-mini", "gpt-4o"]
selected_model = st.selectbox(
    "모델",
    model_options,
    index=model_options.index(settings["model"])
    if settings["model"] in model_options
    else 0,
)

selected_temperature = st.slider(
    "temperature",
    min_value=0.0,
    max_value=1.0,
    value=float(settings["temperature"]),
    step=0.1,
)

role_keys = list(ROLE_PRESETS.keys())
selected_role = st.selectbox(
    "역할 프리셋",
    role_keys,
    index=role_keys.index(settings["role_preset"])
    if settings["role_preset"] in role_keys
    else 0,
)

selected_prompt = st.text_area("시스템 프롬프트", value=settings["system_prompt"])

if st.button("설정 저장"):
    st.session_state.settings = {
        "model": selected_model,
        "temperature": selected_temperature,
        "system_prompt": selected_prompt,
        "role_preset": selected_role,
    }
    st.success("설정을 저장했습니다.")
