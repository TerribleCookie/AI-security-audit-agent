import json
from pathlib import Path
from rule_matcher_v2 import load_rules, scan_file, iter_python_files
from llm_explainer import explain_results
from rule_matcher_v2 import build_scan_summary  # 如果你有这个函数

BASE_DIR = Path(__file__).resolve().parent.parent


def scan_project(project_path: Path, rules):
    py_files = iter_python_files(project_path)
    all_results = []

    for f in py_files:
        results = scan_file(f, rules)
        all_results.extend(results)

    return py_files, all_results


def generate_markdown_report(summary, llm_result, results):
    md = []
    md.append("# 🛡️ 代码安全审计报告\n")

    md.append("## 📊 总体情况")
    md.append(f"- {summary}\n")

    md.append("## 🤖 AI分析")
    md.append(f"**总结：** {llm_result.get('risk_summary','')}\n")

    for item in llm_result.get("details", []):
        md.append(f"- **规则**: {item.get('rule')}")
        md.append(f"  - 风险: {item.get('risk')}")
        md.append(f"  - 影响: {item.get('impact')}")
        md.append(f"  - 修复: {item.get('fix')}\n")

    md.append("## 🔍 详细命中")

    for r in results:
        md.append(f"- [{r['severity']}] {r['rule_name']} | {r['file_path']}:{r['line_no']}")
        md.append(f"  - 代码: `{r['line_content']}`")
        md.append(f"  - 建议: {r['fix_suggestion']}\n")

    return "\n".join(md)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="自动代码安全审计 Agent")
    parser.add_argument("--target", type=str, default="samples")
    parser.add_argument("--rules", type=str, default="rules/security_rules_v1.csv")
    parser.add_argument("--output", type=str, default="reports/audit_report.md")

    args = parser.parse_args()

    project_path = (BASE_DIR / args.target).resolve()
    rule_file = (BASE_DIR / args.rules).resolve()
    output_file = (BASE_DIR / args.output).resolve()

    rules = load_rules(rule_file)

    print(f"开始扫描项目: {project_path}")

    py_files, results = scan_project(project_path, rules)

    print(f"扫描文件数: {len(py_files)}")
    print(f"命中风险数: {len(results)}")

    summary = build_scan_summary(results, py_files)
    llm_result = explain_results(results)

    report_md = generate_markdown_report(summary, llm_result, results)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report_md, encoding="utf-8")

    print(f"\n✅ 审计报告已生成: {output_file}")


if __name__ == "__main__":
    main()