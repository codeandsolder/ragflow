from pathlib import Path

p = Path(__file__).parent / "pyproject.toml"
text = p.read_text().splitlines()
out = []
mode = False
for l in text:
    if l.strip() in ("dependencies = [", "test = [", "dependency-groups"):
        mode = True
        out.append(l)
        continue
    if mode and l.strip() == "]":
        mode = False
        out.append(l)
        continue
    if mode and l.strip().startswith('"'):
        if "git+" in l:
            out.append(l)
            continue
        c = l.replace("==", ">=")
        if c != l:
            print("convert", l.strip(), "=>", c.strip())
        out.append(c)
    else:
        out.append(l)
p.write_text("\n".join(out) + "\n")
print("done", sum(1 for l in out if ">=" in l and "==" not in l and l.strip().startswith('"')))
