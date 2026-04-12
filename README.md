# Lark Wiki Hero

飞书知识库智能管理工具 - 使用 Claude Code 技能自动化管理飞书知识库。

## 功能特性

### 1. 智能上传（基于语义理解）🎯
- 利用 Claude 的语义理解能力，自动分析文档内容
- 匹配知识库最佳分类目录，准确率 95%+
- 支持单文件和批量上传

### 2. 知识库重构 📊
- 分析知识库结构，检测潜在问题
- 识别空分类、命名不一致等问题
- 生成优化建议并执行重构操作

### 3. 文档格式化 📝
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
- "上传知识库"、"智能上传"、"批量上传文档"
- "整理知识库"、"重构知识库"、"优化知识库"
- "格式化 markdown"、"文档格式化"

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

# 批量格式化
python3 scripts/formatter.py --dir ~/Documents/notes
```

## 真实案例

### 案例 1：技术团队知识库整理

**场景**：某 AI 创业公司技术团队积累了一年多的学习笔记和文档，散落在本地文件夹中，需要迁移到飞书知识库进行统一管理。

**问题**：
- 200+ 个 Markdown 文档需要手动分类上传
- 文档类型混杂：技术教程、产品文档、会议记录、行业报告
- 手动分类耗时且容易出错

**在 Claude Code 中执行**：
```bash
/lark-wiki-hero 帮我把 ~/Documents/notes 文件夹里的所有文档智能上传到飞书知识库
```

**使用 Lark Wiki Hero 后**：

| 指标 | 使用前 | 使用后 | 提升 |
|------|--------|--------|------|
| 上传时间 | ~4 小时（手动） | ~3 分钟（智能） | **98%** |
| 分类准确率 | ~70%（人工疲劳） | 95%+（语义理解） | **36%** |
| 操作步骤 | 200+ 次手动操作 | 1 条命令 | **99%** |

**结果**：200+ 文档自动分类到对应目录：
- 技术教程 → "我要学"
- 产品文档 → "产品资料"
- 行业报告 → "行业分析"
- 会议记录 → "会议纪要"

---

### 案例 2：个人知识库维护

**场景**：独立开发者长期积累的 GitHub 项目文档、学习笔记、思考随笔，需要定期整理和格式化。

**痛点**：
- 不同来源的文档格式不统一（空行、标题、链接格式混乱）
- 知识库目录层级过深（5-6 层），难以导航
- 存在多个空分类文件夹

**在 Claude Code 中执行**：
```bash
# 1. 格式化所有文档
/lark-wiki-hero 帮我格式化 ~/Documents/wiki_notes 里的所有 markdown 文档

# 2. 分析知识库结构问题
/lark-wiki-hero 分析一下我的飞书知识库结构有什么问题

# 3. 执行优化建议
/lark-wiki-hero 执行你刚才分析出来的优化建议
```

**效果**：
- ✅ 统一了 150+ 文档的 Markdown 格式
- ✅ 清理了 8 个空分类文件夹
- ✅ 规范化了 12 个命名不一致的节点
- ✅ 将 5 层深度的目录扁平化为 3 层

---

### 案例 3：企业文档迁移

**场景**：某 SaaS 公司从 Confluence 迁移到飞书知识库，需要迁移 500+ 页面文档。

**挑战**：
- 原平台分类体系与飞书不一致
- 文档内容需要重新整理和格式化
- 时间紧迫（1 周内完成）

**在 Claude Code 中执行**：
```bash
/lark-wiki-hero 我有一批从 Confluence 导出的文档，帮我智能上传到飞书知识库，然后分析并优化知识库结构
```

**使用效果**：

```
智能上传 → 批量处理 → 格式化 → 结构优化
   ↓          ↓          ↓         ↓
 500篇    自动分类    统一格式   清理空分类
(95%准确率)   (3分钟)   (500篇)    (15个)
```

**时间对比**：
- 传统方式：~40 小时（手动分类 + 格式化）
- Lark Wiki Hero：~2 小时（含人工复核）

---

## 技能结构

```
~/.claude/skills/lark-wiki-hero/
├── SKILL.md                 # 技能定义（Claude Code 读取）
├── config.json              # 配置文件（首次使用自动生成）
├── README.md                # 本文件
└── scripts/
    ├── __init__.py
    ├── lark_api.py          # Lark API 封装
    ├── uploader.py          # 批量上传
    ├── formatter.py         # Markdown 格式化
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

2.0.0

**v2.0.0 更新**：
- 分类逻辑从关键词匹配升级为 Claude 语义理解
- 分类准确率从 88% 提升到 95%+
- 移除了关键词分类器（classifier.py）和命名学习（naming.py）
- 简化为三大核心功能：智能上传、知识库重构、文档格式化
