<div align="center">

# Lark Wiki Hero

**一句话，文档自动归位 -- 飞书知识库智能管理 Skill**

[![飞书 CLI 创作者大赛](https://img.shields.io/badge/飞书CLI-创作者大赛-blue)](https://bytedance.larkoffice.com/docx/HWgKdWfeSoDw36xu7EYctBrUnsg)
[![Version](https://img.shields.io/badge/version-2.3.1-green)]()

[功能特性](#功能特性) · [真实案例](#真实案例) · [快速开始](#快速开始) · [安装](#安装)

如果这个项目对你有帮助，请给一个 Star ⭐

</div>

---

## 这是什么

管理飞书知识库是一件痛苦的事：

- 200+ 文档散落本地，手动分类上传要花半天
- 知识库层级混乱，空分类、命名不一致到处都是
- 文档格式五花八门，空行、标题、链接风格不统一

**Lark Wiki Hero** 是一个飞书 CLI Skill，用一条自然语言指令解决这些问题：

```
/lark-wiki-hero 帮我把 notes 文件夹里的文档智能上传到飞书知识库
```

系统会自动阅读每篇文档、理解内容语义、匹配知识库最佳分类，然后批量上传。你只需要说一句话。

## 功能特性

| 功能 | 做什么 | 怎么用 |
|------|--------|--------|
| **智能分类** | 语义分析文件名，自动推荐最佳分类路径 | `/lark-wiki-hero 帮我分类这些文档` |
| **智能上传** | 基于语义理解，自动匹配知识库分类，准确率 95%+ | `/lark-wiki-hero 上传知识库` |
| **知识库重构** | 分析结构问题（空分类、层级过深、命名混乱），一键优化 | `/lark-wiki-hero 整理知识库` |
| **文档格式化** | 统一 Markdown 格式：空行、标题、列表、链接 | `/lark-wiki-hero 格式化文档` |

### 核心亮点：语义理解分类

不同于关键词匹配，Lark Wiki Hero 利用大模型的语义理解能力来分类：

```
文档: "Python异步编程完全指南"
  → 理解: 技术教程，面向想学 Python 的开发者
  → 匹配知识库: "我要学" (学习教程类) ✓

文档: "2026 Q1 季度行业报告"
  → 理解: 行业分析报告，面向管理层
  → 匹配知识库: "行业报告与政策趋势" ✓
```

分类准确率从 v1.0 的 88%（关键词匹配）提升到 v2.0 的 **95%+**。

## 真实案例

### 智能上传

**案例 1：新人入职文档归档**

HR 给你发了 50+ 份新人入职材料 -- 培训手册、产品介绍、制度规范、工具指南，文件名全是 `新建文档(1).md`、`会议纪要-最终版.md` 这种。你要把它们分门别类上传到知识库对应目录。

手动操作：每个文件打开看一遍内容 → 判断属于哪个分类 → 上传。大约 **2 小时**。

```
/lark-wiki-hero 帮我把 onboarding-docs 下的文档智能上传到飞书知识库
```

3 分钟完成，自动分类到"培训材料"、"产品文档"、"制度规范"等目录。

---

**案例 2：会议资料批量入库**

产品经理开完周会后，把 20+ 份 PRD、竞品分析、用户调研报告丢到一个共享文件夹。一周积累下来，文件夹里已经混了上百份不同类型的文档，再不整理就找不到了。

```
/lark-wiki-hero 把 weekly-docs 下的所有文档上传到知识库
```

每份文档根据内容语义自动归入"产品需求"、"竞品分析"、"用户研究"等分类，不用逐个打开看。

---

### 知识库重构

**案例 3：一年没整理的知识库**

知识库用了大半年，大家随手建文件夹，命名风格五花八门 -- 有的叫"2024总结"，有的叫"2024 年度总结"，有的叫"24总结"，中文空格英文空格混用。还有 5 层深的嵌套目录，新人都找不到东西在哪。

```
/lark-wiki-hero 分析一下我的知识库结构有什么问题
```

自动检测出：8 个命名不一致节点、5 个空分类、3 个超过 4 层的深目录。确认后一键修复。

---

**案例 4：从 Notion/Confluence 迁移后的大扫除**

团队从 Notion 迁移到飞书知识库，导出了 300+ 页面。迁移后目录结构跟 Notion 原版一样 -- 分类逻辑对不上飞书的使用习惯，还遗留了一堆空文件夹和临时节点。

```
/lark-wiki-hero 分析知识库结构，然后执行优化
```

清理空分类 15 个、重命名不一致节点 12 个、扁平化过深层级，知识库从"别人家的迁移残留"变成"自己人能看懂的结构"。

---

### 文档格式化

**案例 5：多人协作的格式灾难**

团队 5 个人都在往知识库写文档。小王从 Word 复制粘贴，标题用全角空格；小李从网页复制，带一堆 `&nbsp;`；老张习惯标题前不加空格。打开知识库一看，同样的标题有 4 种写法。

```
/lark-wiki-hero 帮我格式化 wiki-docs 下的所有 markdown
```

统一空行规范、标准化标题格式（`#标题` → `# 标题`）、清理行尾空格、修复列表缩进。150+ 文档一次搞定。

---

**案例 6：批量导入后的格式修复**

用工具从其他平台批量导入了一批 Markdown 到飞书，结果打开一看：标题和正文之间没有空行、列表项缩进混乱、链接格式不统一。手动逐个改要改到怀疑人生。

```
/lark-wiki-hero 格式化 imported-docs 下的文档
```

自动修复所有格式问题，大文件（>100KB）智能跳过复杂处理，避免误伤。

---

## 快速开始

### 前置条件

- [飞书 CLI](https://github.com/larksuite/cli) 已安装并完成 `lark-cli auth login`
- AI 编码工具（以下任一）：
  - [Claude Code](https://claude.ai/claude-code)
  - [Codex CLI](https://github.com/openai/codex)
  - [OpenClaw](https://github.com/openclaw/openclaw)
- Python 3.9+

### 安装

```bash
# Claude Code
git clone https://github.com/akira82-ai/lark-wiki-hero.git ~/.claude/skills/lark-wiki-hero

# Codex CLI（项目内）
git clone https://github.com/akira82-ai/lark-wiki-hero.git .codex/skills/lark-wiki-hero

# OpenClaw
git clone https://github.com/akira82-ai/lark-wiki-hero.git ~/.openclaw/workspace/skills/lark-wiki-hero
```

### 使用

在 AI 编码工具中输入 `/lark-wiki-hero` 加上你的需求：

```
/lark-wiki-hero 帮我把 notes 文件夹里的文档上传到飞书知识库
/lark-wiki-hero 分析一下我的知识库结构有什么问题
/lark-wiki-hero 格式化 wiki-docs 下的所有 markdown
```

首次使用会提示配置知识库 URL，之后即可直接使用。

## 架构

```
用户 → /lark-wiki-hero <自然语言指令>
                ↓
         语义理解 + API 调用
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
 lark_api    uploader    formatter
 analyzer    optimizer
    ↓
 lark-cli → 飞书 OpenAPI → 知识库
```

技术栈：Python 3.9+ / [lark-cli](https://github.com/larksuite/cli) / 飞书 OpenAPI

## 技能结构

```
~/.claude/skills/lark-wiki-hero/     # Claude Code
.codex/skills/lark-wiki-hero/        # Codex CLI（项目内）
~/.openclaw/workspace/skills/...     # OpenClaw
├── SKILL.md                 # 技能定义
├── config.json              # 配置（首次使用自动生成）
├── README.md
└── scripts/
    ├── lark_api.py          # 飞书 API 封装
    ├── uploader.py          # 智能上传
    ├── analyzer.py          # 结构分析
    ├── optimizer.py         # 优化执行
    └── formatter.py         # 文档格式化
```

## 权限要求

| 操作 | 所需 scope |
|------|-----------|
| 创建/读取/更新/删除/移动节点 | `wiki:wiki`（完整权限） |

## 致谢

- [飞书 CLI](https://github.com/larksuite/cli) -- 飞书官方 CLI 工具

## License

MIT

*最后更新：2026-04-15*

---

**作者**：磊叔 (AIRay1015) | 微信：AIRay1015 | [github.com/akira82-ai](https://github.com/akira82-ai)
