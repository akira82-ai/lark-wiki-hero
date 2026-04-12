# Changelog

## [2.0.0] - 2026-04-12

### Added
- 语义理解智能分类（利用 Claude LLM 能力）
- 知识库完整层级结构显示（支持 20 层深度）
- 智能标识可用分类节点 `[可用分类]`
- 完整的测试报告和分类准确性验证
- API 调用重试机制
- subprocess 超时保护

### Changed
- 分类方式：关键词匹配 → 语义理解
- 分类准确率：88% → 95%+
- 目录识别：obj_type 判断 → has_child 智能判断
- 版本号：1.0.0 → 2.0.0

### Fixed
- Bug #1: 列表格式化正则表达式错误
- Bug #2: formatter.py 缺少 require_config 导入
- Bug #3: optimizer.py print_plan() 缺少参数
- Bug #4: analyzer.py 命名不一致检测失效
- Bug #5: optimizer.py _execute_action() 所有操作返回 skipped

### Technical Details
- 删除操作：空分类现在可以被实际删除
- 重命名操作：自动生成符合规范的名称
- 命名检测：检测中英文空格、特殊字符、连续空格等问题

## [1.0.0] - 2026-04-10

### Added
- 智能上传功能（基于关键词匹配）
- 知识库结构分析
- Markdown 文档格式化
- 命名规范学习
- 配置管理

### Features
- 单文件和批量上传
- 知识库层级分析（深度、空分类、孤立节点）
- Markdown 格式标准化（空行、标题、列表、链接）
- 命名规范自动学习和重命名
