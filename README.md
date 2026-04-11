# Lark Wiki Hero

飞书知识库智能管理工具 - 使用 Claude Code 技能自动化管理飞书知识库。

## 功能特性

### 1. 智能上传 🎯
- 自动分析文档内容，匹配知识库最佳分类目录
- 支持单文件和批量上传
- 基于关键词的智能分类算法

### 2. 知识库重构 📊
- 分析知识库结构，检测潜在问题
- 识别层级过深、命名不一致、空分类等问题
- 生成优化建议并执行重构操作

### 3. 文件预处理 📝
- 学习知识库命名规范，智能重命名文件
- Markdown 格式化：统一空行、清理空格、标准化格式
- 大文件检测（>100KB 自动跳过复杂格式化）

## 安装

```bash
# 技能已安装到 ~/.claude/skills/lark-wiki-hero/
```

## 首次使用

首次使用时，技能会自动询问您的知识库 URL：

```
请输入您的飞书知识库 URL: https://my.feishu.cn/wiki/xxxxx
```

配置会保存到 `~/.claude/skills/lark-wiki-hero/config.json`。

## 使用方式

### 在 Claude Code 中触发

使用以下关键词自动触发技能：

**中文**：
- "上传知识库"、"智能上传文档"
- "整理知识库"、"重构知识库"
- "预处理文档"、"格式化 markdown"

**英文**：
- "upload to wiki"
- "organize wiki"
- "format markdown"

### 直接运行脚本

```bash
# 智能上传
cd ~/.claude/skills/lark-wiki-hero
python3 scripts/uploader.py ~/Documents/notes/Python教程.md

# 批量上传
python3 scripts/uploader.py --dir ~/Documents/notes

# 知识库分析
python3 scripts/analyzer.py --analyze --verbose

# Markdown 格式化
python3 scripts/formatter.py messy_document.md

# 学习命名规范
python3 scripts/naming.py --learn-only

# 智能重命名
python3 scripts/naming.py --learn-and-rename document.md
```

## 技能结构

```
~/.claude/skills/lark-wiki-hero/
├── SKILL.md                 # 技能定义（Claude Code 读取）
├── config.json              # 配置文件（首次使用自动生成）
├── README.md                # 本文件
└── scripts/
    ├── __init__.py
    ├── lark_api.py          # Lark API 封装
    ├── classifier.py        # 智能分类器
    ├── uploader.py          # 批量上传
    ├── formatter.py         # Markdown 格式化
    ├── naming.py            # 命名规则学习
    ├── analyzer.py          # 结构分析
    └── optimizer.py         # 优化执行
```

## 依赖要求

- Python 3.9+
- lark-cli（飞书官方 CLI 工具）
- 已通过 `lark-cli auth login` 完成认证

## 权限要求

| 操作 | 所需 scope |
|------|-----------|
| 创建节点 | `wiki:node:create` 或 `wiki:wiki` |
| 读取节点 | `wiki:node:read` 或 `wiki:wiki:readonly` |
| 更新节点 | `wiki:node:update` 或 `wiki:wiki` |
| 删除节点 | `wiki:node:delete` 或 `wiki:wiki` |
| 移动节点 | `wiki:node:move` 或 `wiki:wiki` |

## 作者

磊叔 (AIRay1015)

## 版本

1.0.0
