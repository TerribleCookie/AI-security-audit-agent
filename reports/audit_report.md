# 🛡️ 代码安全审计报告

## 📊 总体情况
- {'scanned_file_count': 10, 'hit_count': 6, 'severity_summary': {'High': 4, 'Medium': 2}, 'rule_id_summary': {'R001': 1, 'R002': 1, 'R003': 1, 'R006': 1, 'R007': 1, 'R008': 1}, 'rule_name_summary': {'pickle反序列化': 1, 'subprocess执行': 1, 'yaml.load风险': 1, '危险函数eval': 1, '硬编码API密钥': 1, '硬编码密码': 1}, 'file_summary': {'sample_eval.py': 1, 'sample_pickle.py': 1, 'sample_secret.py': 2, 'sample_subprocess.py': 1, 'sample_yaml.py': 1}, 'top_risks': ['pickle反序列化', 'subprocess执行', 'yaml.load风险']}

## 🤖 AI分析
**总结：** 检测到潜在高危风险，涉及动态代码执行

- **规则**: R003 eval
  - 风险: 用户输入被直接执行
  - 影响: 可能导致远程代码执行
  - 修复: 避免使用 eval，改用安全解析

## 🔍 详细命中
- [High] 危险函数eval | D:\ai_security_dify_audit\samples\sample_eval.py:3
  - 代码: `    result = eval(user_input)`
  - 建议: 避免使用eval处理外部输入

- [High] pickle反序列化 | D:\ai_security_dify_audit\samples\sample_pickle.py:4
  - 代码: `obj = pickle.loads(data.encode())`
  - 建议: 避免加载不可信数据

- [High] 硬编码API密钥 | D:\ai_security_dify_audit\samples\sample_secret.py:1
  - 代码: `API_KEY = "sk-test-12345678"`
  - 建议: 不要在源码中保存密钥，改用环境变量或密钥管理服务

- [High] 硬编码密码 | D:\ai_security_dify_audit\samples\sample_secret.py:2
  - 代码: `password = "admin123"`
  - 建议: 将敏感信息移入环境变量或密钥管理服务

- [Medium] subprocess执行 | D:\ai_security_dify_audit\samples\sample_subprocess.py:4
  - 代码: `subprocess.run(cmd, shell=True)`
  - 建议: 限制命令来源，避免shell=True，并做好参数校验

- [Medium] yaml.load风险 | D:\ai_security_dify_audit\samples\sample_yaml.py:4
  - 代码: `data = yaml.load(text)`
  - 建议: 改用safe_load
