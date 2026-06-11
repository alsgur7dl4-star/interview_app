"""tools.py - 면접 코치 도구 함수"""

from roles import get_role


def make_interview_question(role_key: str, difficulty: str = "기초") -> str:
    """
    지원 직무와 난이도를 받아 면접 질문 한 개를 만듭니다.
    Args:
      role_key: 면접관 유형 키. tech, personality, executive, structured
      difficulty: 질문 난이도, 기초 또는 심화
    """
    role = get_role(role_key)
    if difficulty == "심화":
        return (
            f"[{role.name}] {role.key} 직무에서 장애 상황이나 실패 경험을 "
            f"발견했을 때 원인 분석과 해결 순서를 설명해 주세요."
        )
    return (
        f"[{role.name}] {role.key} 직무에서 최근에 해결한 문제를 "
        f"한 가지 구체적으로 설명해 주세요."
    )


def score_answer(answer: str) -> str:
    """
    지원자의 면접 답변을 규칙 기반으로 채점합니다.
    Agrs:
      answer: 지원자가 작성한 면접 답변 텍스트
    """
    positive_keywords = ["프로젝트", "경험", "사례", "결과", "수치", "개선", "해결"]
    found = [kw for kw in positive_keywords if kw in answer]
    score = min(5, 1 + len(found))
    if score >= 4:
        reason = f"구체적 사례가 잘 드러납니다. (키워드: {', '.join(found)})"
    elif score >= 2:
        reason = f"기본 구조는 있으나 구체성이 부족합니다. (키워드: {', '.join(found)})"
    else:
        reason = f"구체적 사례나 결과가 없습니다.."
    return f"{score}/5 - {reason}"


def make_feedback(answer: str) -> str:
    """
    지원자의 답변에 대해 다음 답변에서 고칠 행동을 제안합니다.
    Args:
      answer: 지원자가 작성한 답변 텍스트
    """
    tips: list[str] = []
    if "상황" not in answer and "문제" not in answer:
        tips.append("문제 상황을 한 문장으로 먼저 시작하세요.")
    if len(answer) < 50:
        tips.append(
            "답변이 너무 짧습니다. STAR 프레임워크 (상황-과제-행동-결과)로 구조화하세요."
        )
    if not any(kw in answer for kw in ["수치", "결과", "%", "건", "명"]):
        tips.append("결과를 숫자나 구체적 반응으로 마무리하세요.")
    if not any(kw in answer for kw in ["행동", "했", "맡", "개발", "설계", "작성"]):
        tips.append("본인이 한 행동을 동사 중심으로 말하세요")

    if not tips:
        tips.append("좋은 답변입니다. 시간 제한(2분) 안에 말하는 연습을 추가하세요.")
    return "\n".join(f" {i + 1}) {tip}" for i, tip in enumerate(tips))


if __name__ == "__main__":
    print(make_interview_question("tech", "기초"))
    print(make_interview_question("tech", "심화"))
    print()
    sample = "저는 팀 프로젝트에서 API 설계와 문서화를 맡은 경험이 있습니다."
    print(score_answer(sample))
    print()
    print(make_feedback(sample))
