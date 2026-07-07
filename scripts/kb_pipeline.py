# Tianquan 知识库流水线 — 把芥末堆新闻 + 网页抓取转化为结构化知识库
# 数据源：芥末堆新闻列表 + 可汗/谷歌/教育部等公开网页

import os
import sys
import json
import time
import requests
import re
from pathlib import Path
from datetime import datetime

API_BASE = os.environ.get("API_BASE", "https://iz2ze93ogksv8bwaz3pk8hz.taildec4f9.ts.net/api")
API_KEY = os.environ.get("API_KEY", "")
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5  # seconds


def call_llm_structure(text, title):
    """调用 LLM 把原始文章转为结构化 JSON。"""
    prompt = f"""请把以下文章转为结构化 JSON。

文章标题：{title}

文章正文：
{text}

要求：
1. 输出严格的 JSON
2. 包含字段：title, summary, key_points, tags, audience
3. 不要输出任何 JSON 之外的文字

JSON："""

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                f"{API_BASE}/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": "deepseek-v4-flash",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
                timeout=60,
            )

            # 429 限流 / 5xx 服务端错误 → 等待后重试
            if resp.status_code == 429 or resp.status_code >= 500:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  API error {resp.status_code}, retrying in {delay:.0f}s...")
                time.sleep(delay)
                continue

            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            # 尝试从 ```json ... ``` 块里提取
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if m:
                content = m.group(1)
            return json.loads(content)
        except Exception as e:
            print(f"  attempt {attempt+1} error: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
    return None
