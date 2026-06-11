"""config.py - 공통 설정: .evn 로딩, 모델명 상수, 환경점검"""

import os
from dotenv import load_dotenv


def ini_env() -> bool:
    load_dotenv()
    required = ["OPENAI_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"환경변수 누락: {', '.join(missing)}")
        print("프로젝트 루트 .env 파일에 해당 키를 추가합니다.")
        return False
    print("환경 변수 확인 완료")
    return True


# 모델명 상수
MODEL_NAME = "gpt-5.4-nano"

if __name__ == "__main__":
    ini_env()
