from pathlib import Path
p = Path(r"C:\\Users\\陈盈桦\\Desktop\\黄金\\.env.trading")
if p.exists():
    txt = p.read_text(encoding="utf-8", errors="replace")
else:
    txt = ""
lines = txt.splitlines()
found_force = False
out = []
for line in lines:
    if line.strip().startswith('FEISHU_FORCE_ASCII='):
        out.append('FEISHU_FORCE_ASCII=0')
        found_force = True
    else:
        out.append(line)
if not found_force:
    out.append('FEISHU_FORCE_ASCII=0')

found_type = False
final = []
for line in out:
    if line.strip().startswith('FEISHU_MSG_TYPE='):
        final.append('FEISHU_MSG_TYPE=text')
        found_type = True
    else:
        final.append(line)
if not found_type:
    final.append('FEISHU_MSG_TYPE=text')

p.write_text('\n'.join(final) + '\n', encoding='utf-8')
