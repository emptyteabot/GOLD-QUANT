import sys
from pathlib import Path
base = Path(r"C:\\Users\\陈盈桦\\Desktop\\黄金")
if str(base) not in sys.path:
    sys.path.insert(0, str(base))

import subprocess
from gemini_client import gemini_generate
from feishu_notifier import send_feishu

cmd=[r"C:\\Users\\陈盈桦\\AppData\\Local\\Programs\\Python\\Python313\\python.exe", r"C:\\Users\\陈盈桦\\.codex\\skills\\okx-indicators-account\\scripts\\okx_indicators_account.py"]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
raw = (res.stdout or '').strip()
lines = raw.splitlines()
raw = '\n'.join(lines[-120:])
if not raw:
    raw = (res.stderr or '').strip()[:2000]

prompt = (
    "You are a trading assistant. Output max 4 lines, English only.\n"
    "Focus on trend bias, risk flags, and whether to wait for confirmation.\n"
    "Do not repeat raw indicators.\n\n" + raw[:6000]
)

text = gemini_generate(prompt) or 'Gemini: no response'
send_feishu(text, level='info', title='Gemini Analysis')
print(text)
