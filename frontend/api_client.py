# frontend/api_client.py 역할:
# → 프론트와 백엔드 사이에서 HTTP/SSE 요청을 보내고 응답을 받아오는 연결 창구 역할을 한다.

from __future__ import annotations

import os
from typing import Any
from collections.abc import Iterator

import httpx
from dotenv import load_dotenv

load_dotenv()


def get_backend_url() -> str:
    return os.getenv("BACKEND_URL", "http://localhost:8000")


def post_interview_message(message: str) -> dict[str, Any]:
    with httpx.Client(base_url=get_backend_url(), timeout=10.0) as client:
        response = client.post("/chat", json={"message": message})
        response.raise_for_status()
        return response.json()


def stream_interview_message(message: str) -> Iterator[str]:
    payload = {"message": message}
    url = f"{get_backend_url()}/chat/stream"
    with httpx.stream("POST", url, json=payload, timeout=30.0) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            if not line.startswith("data:"):
                continue
            token = line[5:].strip()
            if token == "[DONE]":
                break
            yield token


def render_streaming_answer(placeholder: Any, message: str) -> str:
    full_text = ""
    for token in stream_interview_message(message):
        full_text += token
        placeholder.markdown(full_text)
    return full_text
