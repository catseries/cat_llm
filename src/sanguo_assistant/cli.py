"""Command line client for a Three Kingdoms history assistant powered by Zhipu AI."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable
from typing import Any

DEFAULT_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4-plus"
SYSTEM_PROMPT = """
你是“三国史小助手”，专注回答东汉末年至西晋统一前后三国相关历史问题。
请遵守以下规则：
1. 优先区分正史《三国志》《后汉书》《资治通鉴》与小说《三国演义》的差异。
2. 回答时尽量给出人物、时间、地点、事件背景和影响；不确定的信息要明确说明。
3. 用户要求简短时用要点回答；用户要求深入时按“背景—经过—影响—史料辨析”组织。
4. 不编造史料出处；涉及争议观点时说明“史书记载”“后世演义”或“学界常见看法”。
5. 默认使用中文回答，语气亲切、清晰、适合历史学习者。
""".strip()


def build_messages(question: str) -> list[dict[str, str]]:
    """Build chat messages for the Three Kingdoms assistant."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]


def build_payload(
    question: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    stream: bool = False,
) -> dict[str, Any]:
    """Build the Zhipu AI chat completions payload."""
    return {
        "model": model,
        "messages": build_messages(question),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }


def post_chat_completion(
    api_key: str,
    payload: dict[str, Any],
    api_url: str = DEFAULT_API_URL,
    timeout: int = 60,
) -> dict[str, Any]:
    """Send a non-streaming chat completion request to Zhipu AI."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def stream_chat_completion(
    api_key: str,
    payload: dict[str, Any],
    api_url: str = DEFAULT_API_URL,
    timeout: int = 60,
) -> Iterable[str]:
    """Yield text deltas from a Zhipu AI streaming chat completion response."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line or not line.startswith("data:"):
                continue
            data = line.removeprefix("data:").strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content")
            if content:
                yield content


def extract_answer(response: dict[str, Any]) -> str:
    """Extract assistant text from a non-streaming Zhipu AI response."""
    return response["choices"][0]["message"]["content"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="调用智谱 API，运行一个三国历史知识小助手。"
    )
    parser.add_argument("question", nargs="*", help="要提问的三国历史问题")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"智谱模型名，默认：{DEFAULT_MODEL}")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="智谱 Chat Completions API 地址")
    parser.add_argument("--temperature", type=float, default=0.3, help="生成随机性，默认：0.3")
    parser.add_argument("--max-tokens", type=int, default=2048, help="最大输出 token 数，默认：2048")
    parser.add_argument("--stream", action="store_true", help="使用流式输出")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    api_key = os.getenv("ZAI_API_KEY") or os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        print(
            "请先设置环境变量 ZAI_API_KEY（或 ZHIPUAI_API_KEY），例如：\n"
            "export ZAI_API_KEY='你的智谱API Key'",
            file=sys.stderr,
        )
        return 2

    question = " ".join(args.question).strip()
    if not question:
        question = input("请输入你的三国历史问题：").strip()
    if not question:
        print("问题不能为空。", file=sys.stderr)
        return 2

    payload = build_payload(
        question=question,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        stream=args.stream,
    )

    try:
        if args.stream:
            for text in stream_chat_completion(api_key, payload, args.api_url):
                print(text, end="", flush=True)
            print()
        else:
            response = post_chat_completion(api_key, payload, args.api_url)
            print(extract_answer(response))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        print(f"智谱 API HTTP 错误 {err.code}: {detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as err:
        print(f"无法连接智谱 API: {err.reason}", file=sys.stderr)
        return 1
    except KeyError as err:
        print(f"智谱 API 响应格式异常，缺少字段: {err}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as err:
        print(f"智谱 API 响应不是合法 JSON: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
