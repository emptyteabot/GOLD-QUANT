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
    "只输出4行中文，必须完全符合格式，不得添加任何解释或标题：\n"
    "市场状态：强/弱/震荡\n"
    "短线动能：上/下/弱\n"
    "风险：高/中/低\n"
    "关键位：支撑xx-xx，阻力xx-xx\n\n" + raw[:6000]
)

text = gemini_generate(prompt) or 'Gemini: 无响应'
send_feishu(text, level='info', title='AURUM 参考')
print(text)
