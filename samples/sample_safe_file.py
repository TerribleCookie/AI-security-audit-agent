from pathlib import Path

base_dir = Path("data")
file_name = "config.txt"
target = (base_dir / file_name).resolve()

with open(target, "r", encoding="utf-8") as f:
    content = f.read()

print(content)