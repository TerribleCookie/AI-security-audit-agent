# 🚀 AI Code Security Audit Agent

一个结合 **规则检测 + LLM解释 + Dify工作流** 的 Python 代码安全审计系统，  
支持代码片段与仓库级自动扫描，并生成结构化安全报告。

---

## ✨ 项目特点

- 🔍 基于规则的静态安全检测（keyword / regex）
- ⚡ 支持 Python 代码片段与仓库级扫描
- 🌐 Flask API 服务化调用
- 🤖 LLM 自动生成风险解释与修复建议
- 🔗 集成 Dify，实现自动化安全审计工作流
- 📄 自动生成 Markdown 安全报告
## 🧠 系统架构

```

用户输入代码
↓
Dify 工作流
↓
HTTP API (Flask)
↓
规则检测引擎
↓
LLM 风险解释
↓
结构化结果 / Markdown 报告

```

---

## 📁 项目结构

```

ai_security_dify_audit/
│
├── scripts/        # 核心逻辑
│   ├── rule_matcher_v2.py
│   ├── scan_api.py
│   ├── llm_explainer.py
│   ├── audit_agent.py
│   ├── repo_audit_agent.py
│   └── github_repo_audit.py
│
├── rules/          # 安全规则库
│   └── security_rules_v1.csv
│
├── samples/        # 测试代码
├── reports/        # 扫描结果
├── docs/           # 文档
├── screenshots/    # 演示截图
└── README.md

````

---

## ⚡ 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
````

---

### 2. 启动 API 服务

```bash
python scripts/scan_api.py
```

访问健康检查：

```
http://127.0.0.1:8008/health
```

---

### 3. 测试代码扫描

```
POST /scan
```

请求示例：

```json
{
  "file_name": "demo.py",
  "code_text": "result = eval(input())"
}
```

---

## 🔥 示例效果

输入代码：

```python
result = eval(input())
```

输出：

* 🚨 High 风险
* ⚠️ 动态代码执行（Arbitrary Code Execution）
* 💡 提供修复建议（避免 eval）

---

## 📦 仓库扫描

### 本地仓库扫描

```bash
python scripts/repo_audit_agent.py --target ./samples
```

---

### GitHub 仓库扫描

```bash
python scripts/github_repo_audit.py --repo_url https://github.com/xxx/xxx.git
```

---

## 🤖 Dify 集成

在 Dify 工作流中：

* 使用 HTTP 节点调用 `/scan`
* 输入变量：

  * `file_name`
  * `code_text`
* 输出结合 LLM 节点进行安全解释

---

## 🛠️ 技术栈

* Python
* Flask
* Regex / Rule Engine
* LLM（Qwen / GPT）
* Dify 工作流

---

## 📌 未来优化方向

* 多语言代码支持（Java / JS）
* AST 级语义分析
* 风险评分系统
* CI/CD 自动审计
* IDE 插件集成

---

## 👨‍💻 作者

TerribleCookie

---

## ⭐ 项目定位

本项目为 **AI + 安全 + Agent** 方向的工程实践，
目标是探索大模型在代码安全审计中的应用。

```
```
