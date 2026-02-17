from pathlib import Path
p = Path(r"C:\\Users\\陈盈桦\\Desktop\\黄金\\.env.trading")
if p.exists():
    txt = p.read_text(encoding="utf-8", errors="replace")
else:
    txt = ""
lines = txt.splitlines()
found = False
out = []
for line in lines:
    if line.strip().startswith('GEMINI_BASE_URL='):
        out.append('GEMINI_BASE_URL=https://hk.12ai.org/v1')
        found = True
    else:
        out.append(line)
if not found:
    out.append('GEMINI_BASE_URL=https://hk.12ai.org/v1')

p.write_text('\n'.join(out) + '\n', encoding='utf-8')
