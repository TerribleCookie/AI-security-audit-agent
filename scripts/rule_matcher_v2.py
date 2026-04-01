import re
import csv
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
from collections import Counter, defaultdict


def read_text_with_fallback(file_path: Path) -> str:
    """
    尝试用多种编码读取文本，兼容 Windows / WPS / Excel 导出的文件。
    """
    encodings = [
        "utf-8-sig",
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "gbk",
        "gb18030",
    ]
    last_error = None
    for enc in encodings:
        try:
            return file_path.read_text(encoding=enc)
        except Exception as e:
            last_error = e
    raise RuntimeError(f"无法读取文件: {file_path}\n最后错误: {last_error}")


def detect_csv_delimiter(sample_text: str) -> str:
    """
    自动判断分隔符，兼容逗号分隔和制表符分隔。
    """
    try:
        dialect = csv.Sniffer().sniff(sample_text[:2048], delimiters=",\t;")
        return dialect.delimiter
    except Exception:
        if "\t" in sample_text:
            return "\t"
        return ","


def load_rules(rule_file: Path) -> List[Dict]:
    """
    读取规则表，支持 CSV / TSV。
    必须包含以下列：
    rule_id, rule_name, severity, pattern_type, pattern, description, fix_suggestion
    """
    raw_text = read_text_with_fallback(rule_file)
    delimiter = detect_csv_delimiter(raw_text)

    reader = csv.DictReader(raw_text.splitlines(), delimiter=delimiter)
    required_fields = {
        "rule_id",
        "rule_name",
        "severity",
        "pattern_type",
        "pattern",
        "description",
        "fix_suggestion",
    }

    if reader.fieldnames is None:
        raise ValueError("规则文件表头读取失败，请检查文件格式。")

    fieldnames = [f.strip() for f in reader.fieldnames]
    missing = required_fields - set(fieldnames)
    if missing:
        raise ValueError(f"规则文件缺少字段: {missing}\n当前字段: {fieldnames}")

    rules = []
    for row in reader:
        if not row:
            continue

        normalized = {
            k.strip(): (v.strip() if v is not None else "")
            for k, v in row.items()
        }

        pattern_type = normalized["pattern_type"].lower()
        if pattern_type not in {"keyword", "regex"}:
            print(
                f"[警告] 跳过规则 {normalized.get('rule_id', '')}: "
                f"不支持的 pattern_type={pattern_type}"
            )
            continue

        compiled_pattern = None
        if pattern_type == "regex":
            try:
                compiled_pattern = re.compile(normalized["pattern"])
            except re.error as e:
                print(
                    f"[警告] 跳过规则 {normalized.get('rule_id', '')}: "
                    f"正则表达式错误 -> {e}"
                )
                continue

        rules.append(
            {
                "rule_id": normalized["rule_id"],
                "rule_name": normalized["rule_name"],
                "severity": normalized["severity"],
                "pattern_type": pattern_type,
                "pattern": normalized["pattern"],
                "compiled_pattern": compiled_pattern,
                "description": normalized["description"],
                "fix_suggestion": normalized["fix_suggestion"],
            }
        )

    return rules


def iter_python_files(target_path: Path) -> List[Path]:
    """
    如果传入文件，就扫描该文件；
    如果传入目录，就递归扫描目录下所有 .py 文件。
    """
    if target_path.is_file():
        if target_path.suffix.lower() == ".py":
            return [target_path]
        raise ValueError(f"目标文件不是 .py 文件: {target_path}")

    if target_path.is_dir():
        return sorted(target_path.rglob("*.py"))

    raise FileNotFoundError(f"目标路径不存在: {target_path}")


def truncate_text(text: str, max_len: int = 100) -> str:
    text = text.replace("\n", "\\n")
    return text if len(text) <= max_len else text[:max_len] + "..."


def scan_file(file_path: Path, rules: List[Dict]) -> List[Dict]:
    """
    扫描单个 Python 文件，返回命中结果列表。
    """
    content = read_text_with_fallback(file_path)
    lines = content.splitlines()
    results = []

    for idx, line in enumerate(lines, start=1):
        for rule in rules:
            if rule["pattern_type"] == "keyword":
                keyword = rule["pattern"]
                if keyword in line:
                    results.append(
                        {
                            "file_path": str(file_path),
                            "file_name": file_path.name,
                            "line_no": idx,
                            "rule_id": rule["rule_id"],
                            "rule_name": rule["rule_name"],
                            "severity": rule["severity"],
                            "matched_text": truncate_text(keyword),
                            "line_content": truncate_text(line),
                            "description": rule["description"],
                            "fix_suggestion": rule["fix_suggestion"],
                        }
                    )

            elif rule["pattern_type"] == "regex":
                matches = list(rule["compiled_pattern"].finditer(line))
                for m in matches:
                    matched_text = m.group(0)
                    results.append(
                        {
                            "file_path": str(file_path),
                            "file_name": file_path.name,
                            "line_no": idx,
                            "rule_id": rule["rule_id"],
                            "rule_name": rule["rule_name"],
                            "severity": rule["severity"],
                            "matched_text": truncate_text(matched_text),
                            "line_content": truncate_text(line),
                            "description": rule["description"],
                            "fix_suggestion": rule["fix_suggestion"],
                        }
                    )

    return results


def save_results_to_csv(results: List[Dict], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "file_path",
        "file_name",
        "line_no",
        "rule_id",
        "rule_name",
        "severity",
        "matched_text",
        "line_content",
        "description",
        "fix_suggestion",
    ]

    with output_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def save_results_to_json(
    results: List[Dict],
    py_files: List[Path],
    json_output_file: Path,
    summary: Dict,
) -> None:
    json_output_file.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "scan_meta": {
            "scanned_file_count": len(py_files),
            "scanned_files": [str(p) for p in py_files],
            "hit_count": len(results),
        },
        "summary": summary,
        "results": results,
    }

    with json_output_file.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def print_results(results: List[Dict]) -> None:
    if not results:
        print("未发现命中规则。")
        return

    print("=" * 100)
    print(f"共发现 {len(results)} 条命中结果")
    print("=" * 100)

    for item in results:
        print(
            f"[{item['severity']}] {item['rule_id']} {item['rule_name']} | "
            f"{item['file_path']}:{item['line_no']}"
        )
        print(f"  命中内容: {item['matched_text']}")
        print(f"  代码行  : {item['line_content']}")
        print(f"  说明    : {item['description']}")
        print(f"  修复建议: {item['fix_suggestion']}")
        print("-" * 100)


def summarize_by_severity(results: List[Dict]) -> Dict[str, int]:
    severity_count = Counter()
    for item in results:
        severity_count[item["severity"]] += 1
    return dict(sorted(severity_count.items()))


def summarize_by_rule_id(results: List[Dict]) -> Dict[str, int]:
    rule_count = Counter()
    for item in results:
        rule_count[item["rule_id"]] += 1
    return dict(sorted(rule_count.items()))


def summarize_by_rule_name(results: List[Dict]) -> Dict[str, int]:
    rule_name_count = Counter()
    for item in results:
        rule_name_count[item["rule_name"]] += 1
    return dict(sorted(rule_name_count.items()))


def summarize_by_file(results: List[Dict]) -> Dict[str, int]:
    file_count = Counter()
    for item in results:
        file_count[item["file_name"]] += 1
    return dict(sorted(file_count.items()))


def build_scan_summary(results: List[Dict], py_files: List[Path]) -> Dict:
    severity_summary = summarize_by_severity(results)
    rule_id_summary = summarize_by_rule_id(results)
    rule_name_summary = summarize_by_rule_name(results)
    file_summary = summarize_by_file(results)

    top_rule_names = sorted(
        rule_name_summary.items(), key=lambda x: x[1], reverse=True
    )[:3]
    top_risks = [name for name, _ in top_rule_names]

    summary = {
        "scanned_file_count": len(py_files),
        "hit_count": len(results),
        "severity_summary": severity_summary,
        "rule_id_summary": rule_id_summary,
        "rule_name_summary": rule_name_summary,
        "file_summary": file_summary,
        "top_risks": top_risks,
    }
    return summary


def print_summary(summary: Dict) -> None:
    print("\n统计信息：")

    print("按严重级别统计：")
    for k, v in summary["severity_summary"].items():
        print(f"  {k}: {v}")

    print("按规则 ID 统计：")
    for k, v in summary["rule_id_summary"].items():
        print(f"  {k}: {v}")

    print("按规则名称统计：")
    for k, v in summary["rule_name_summary"].items():
        print(f"  {k}: {v}")

    print("按文件统计：")
    for k, v in summary["file_summary"].items():
        print(f"  {k}: {v}")

    high_count = summary["severity_summary"].get("High", 0)
    medium_count = summary["severity_summary"].get("Medium", 0)
    low_count = summary["severity_summary"].get("Low", 0)

    top_risk_text = "、".join(summary["top_risks"]) if summary["top_risks"] else "暂无明显集中风险"

    print("\n扫描摘要：")
    print(
        f"共扫描 {summary['scanned_file_count']} 个 Python 文件，"
        f"发现 {summary['hit_count']} 条风险命中。"
    )
    print(
        f"其中 High 级别 {high_count} 条，"
        f"Medium 级别 {medium_count} 条，"
        f"Low 级别 {low_count} 条。"
    )
    print(f"主要风险集中在 {top_risk_text}。")


def main():
    parser = argparse.ArgumentParser(description="基于规则表的 Python 安全代码匹配器 v2")
    parser.add_argument(
        "--rules",
        type=str,
        default="rules/security_rules_v1.csv",
        help="规则文件路径，默认 rules/security_rules_v1.csv",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="samples",
        help="待扫描的目标文件或目录，默认 samples",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/match_results_v1.csv",
        help="输出结果 CSV 路径，默认 reports/match_results_v1.csv",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    rule_file = (base_dir / args.rules).resolve()
    target_path = (base_dir / args.target).resolve()
    output_file = (base_dir / args.output).resolve()
    json_output_file = output_file.with_suffix(".json")

    if not rule_file.exists():
        raise FileNotFoundError(f"规则文件不存在: {rule_file}")

    rules = load_rules(rule_file)
    print(f"已加载规则数: {len(rules)}")

    py_files = iter_python_files(target_path)
    print(f"待扫描 Python 文件数: {len(py_files)}")

    all_results = []
    for py_file in py_files:
        file_results = scan_file(py_file, rules)
        all_results.extend(file_results)

    print_results(all_results)

    summary = build_scan_summary(all_results, py_files)
    print_summary(summary)

    save_results_to_csv(all_results, output_file)
    save_results_to_json(all_results, py_files, json_output_file, summary)

    print(f"\n扫描完成，CSV 结果已保存到: {output_file}")
    print(f"扫描完成，JSON 结果已保存到: {json_output_file}")

def scan_code_text(code_text: str, virtual_file_name: str, rules: List[Dict]) -> List[Dict]:
    lines = code_text.splitlines()
    results = []

    for idx, line in enumerate(lines, start=1):
        for rule in rules:
            if rule["pattern_type"] == "keyword":
                keyword = rule["pattern"]
                if keyword in line:
                    results.append(
                        {
                            "file_path": virtual_file_name,
                            "file_name": virtual_file_name,
                            "line_no": idx,
                            "rule_id": rule["rule_id"],
                            "rule_name": rule["rule_name"],
                            "severity": rule["severity"],
                            "matched_text": truncate_text(keyword),
                            "line_content": truncate_text(line),
                            "description": rule["description"],
                            "fix_suggestion": rule["fix_suggestion"],
                        }
                    )
            elif rule["pattern_type"] == "regex":
                matches = list(rule["compiled_pattern"].finditer(line))
                for m in matches:
                    results.append(
                        {
                            "file_path": virtual_file_name,
                            "file_name": virtual_file_name,
                            "line_no": idx,
                            "rule_id": rule["rule_id"],
                            "rule_name": rule["rule_name"],
                            "severity": rule["severity"],
                            "matched_text": truncate_text(m.group(0)),
                            "line_content": truncate_text(line),
                            "description": rule["description"],
                            "fix_suggestion": rule["fix_suggestion"],
                        }
                    )

    return results

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[错误] {e}")
        sys.exit(1)