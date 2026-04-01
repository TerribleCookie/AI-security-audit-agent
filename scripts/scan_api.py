from pathlib import Path
from flask import Flask, request, jsonify

from rule_matcher_v2 import load_rules, scan_code_text, build_scan_summary
from llm_explainer import explain_results
app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
RULE_FILE = BASE_DIR / "rules" / "security_rules_v1.csv"
RULES = load_rules(RULE_FILE)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(force=True)
    code_text = data.get("code_text", "")
    file_name = data.get("file_name", "input.py")
    results = scan_code_text(code_text, file_name, RULES)
    explain = explain_results(results)
    summary = build_scan_summary(results, [Path(file_name)])

    return jsonify({
        "meta": {
            "file_name": file_name,
            "hit_count": len(results)
        },
        "summary": summary,
        "llm": explain,  # ⚠️ 这里是JSON，不是字符串
        "results": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8008, debug=True)