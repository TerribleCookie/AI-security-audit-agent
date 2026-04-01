import json

def build_prompt(results):
    return f"""
你是一个代码安全专家，请分析以下Python安全扫描结果：

要求：
1. 用一句话总结整体风险
2. 对每个漏洞说明：
   - 风险原因
   - 可能攻击方式
   - 修复建议
3. 输出必须是JSON格式

扫描结果：
{json.dumps(results, ensure_ascii=False, indent=2)}
"""


def fake_llm_call(prompt: str) -> dict:
    """
    模拟 LLM（因为你现在可能没接API）
    """
    return {
        "risk_summary": "检测到潜在高危风险，涉及动态代码执行",
        "details": [
            {
                "rule": "R003 eval",
                "risk": "用户输入被直接执行",
                "impact": "可能导致远程代码执行",
                "fix": "避免使用 eval，改用安全解析"
            }
        ]
    }


def explain_results(results):
    if not results:
        return {
            "risk_summary": "未发现风险",
            "details": []
        }

    prompt = build_prompt(results)

    # ⚠️ 后面可以替换成真实 LLM
    return fake_llm_call(prompt)