import shutil
import subprocess
import tempfile
from pathlib import Path

from rule_matcher_v2 import load_rules, iter_python_files, scan_file, build_scan_summary
from llm_explainer import explain_results

BASE_DIR = Path(__file__).resolve().parent.parent


def clone_repo(repo_url: str, work_dir: Path) -> Path:
    repo_name = repo_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    clone_path = work_dir / repo_name

    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(clone_path)],
        check=True
    )
    return clone_path


def scan_local_repo(repo_path: Path, rules):
    py_files = iter_python_files(repo_path)
    all_results = []

    for py_file in py_files:
        try:
            file_results = scan_file(py_file, rules)
            all_results.extend(file_results)
        except Exception as e:
            print(f"[警告] 扫描失败: {py_file} -> {e}")

    return py_files, all_results


def generate_markdown_report(repo_name: str, summary: dict, llm_result: dict, results: list) -> str:
    md = []
    md.append(f"# GitHub仓库安全审计报告：{repo_name}\n")

    md.append("## 一、总体情况")
    md.append(f"- 扫描文件数：{summary.get('scanned_file_count', 0)}")
    md.append(f"- 风险命中数：{summary.get('hit_count', 0)}")

    severity_summary = summary.get("severity_summary", {})
    md.append(f"- High：{severity_summary.get('High', 0)}")
    md.append(f"- Medium：{severity_summary.get('Medium', 0)}")
    md.append(f"- Low：{severity_summary.get('Low', 0)}\n")

    md.append("## 二、AI分析")
    md.append(llm_result.get("risk_summary", "无"))
    md.append("")

    details = llm_result.get("details", [])
    if details:
        for item in details:
            md.append(f"- **规则**：{item.get('rule', '')}")
            md.append(f"  - 风险：{item.get('risk', '')}")
            md.append(f"  - 影响：{item.get('impact', '')}")
            md.append(f"  - 修复：{item.get('fix', '')}")
            md.append("")

    md.append("## 三、详细命中")
    if not results:
        md.append("- 未发现明显风险\n")
    else:
        for r in results:
            md.append(f"- [{r['severity']}] **{r['rule_name']}**")
            md.append(f"  - 文件：`{r['file_path']}`")
            md.append(f"  - 行号：{r['line_no']}")
            md.append(f"  - 代码：`{r['line_content']}`")
            md.append(f"  - 说明：{r['description']}")
            md.append(f"  - 修复建议：{r['fix_suggestion']}")
            md.append("")

    return "\n".join(md)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GitHub 仓库安全审计 Agent")
    parser.add_argument("--repo_url", type=str, required=True, help="GitHub 仓库 URL")
    parser.add_argument("--rules", type=str, default="rules/security_rules_v1.csv", help="规则文件路径")
    parser.add_argument("--output", type=str, default="reports/github_repo_audit_report.md", help="Markdown 报告输出路径")
    args = parser.parse_args()

    rule_file = (BASE_DIR / args.rules).resolve()
    output_file = (BASE_DIR / args.output).resolve()
    rules = load_rules(rule_file)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        print(f"开始克隆仓库: {args.repo_url}")
        repo_path = clone_repo(args.repo_url, tmp_path)
        print(f"仓库已克隆到: {repo_path}")

        py_files, results = scan_local_repo(repo_path, rules)
        summary = build_scan_summary(results, py_files)
        llm_result = explain_results(results)

        report_md = generate_markdown_report(repo_path.name, summary, llm_result, results)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(report_md, encoding="utf-8")

        print(f"扫描文件数: {len(py_files)}")
        print(f"命中风险数: {len(results)}")
        print(f"报告已生成: {output_file}")


if __name__ == "__main__":
    main()