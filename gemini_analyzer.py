import asyncio
from datetime import datetime
import config
from gemini_client import gemini_generate
from feishu_notifier import send_feishu


def parse_interval_seconds(value: str) -> int:
    if not value:
        return 0
    v = value.strip().lower()
    if v.endswith('s'):
        return int(v[:-1])
    if v.endswith('m'):
        return int(v[:-1]) * 60
    if v.endswith('h'):
        return int(v[:-1]) * 3600
    return int(v)


async def main():
    prompt = (
        "You are a trading assistant. Summarize the opportunity concisely (max 6 lines) in English only. "
        "Do not repeat raw indicators. Focus on: trend bias, risk flags, and whether to wait for confirmation."
        "\n\n"
        "Context: OKX indicators + account snapshot will be provided by the caller."
    )
    text = gemini_generate(prompt)
    if text:
        send_feishu(text, level="info", title="Gemini Analysis")

if __name__ == "__main__":
    asyncio.run(main())
