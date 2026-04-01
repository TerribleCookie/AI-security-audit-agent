import sys

file_path = sys.argv[1]
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()
print(content)