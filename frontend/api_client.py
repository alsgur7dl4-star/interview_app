# frontend/api_client.py 역할:
# → 프론트와 백엔드 사이에서 HTTP/SSE 요청을 보내고 응답을 받아오는 연결 창구 역할을 한다.

from __future__ import annotations

import json
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


def stream_interview_agent(message: str, mode: str = "single") -> Iterator[dict[str, Any]]:
    payload = {"message": message, "mode": mode}
    url = f"{get_backend_url()}/agents/stream"
    with httpx.stream("POST", url, json=payload, timeout=60.0) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            yield json.loads(data)


def render_streaming_answer(placeholder: Any, message: str) -> str:
    full_text = ""
    for token in stream_interview_message(message):
        full_text += token
        placeholder.markdown(full_text)
    return full_text
