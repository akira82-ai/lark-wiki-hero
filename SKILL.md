---
name: lark-wiki-hero
version: 2.1.0
description: "飞书知识库智能管理工具。当用户提到飞书知识库、wiki 文档管理、上传文档到飞书、整理知识库结构、格式化 Markdown 文档，或任何与飞书/Lark 知识空间相关的操作时，必须使用此技能。支持智能自动分类上传、知识库结构分析与优化、文件规范化处理。即使使用'飞书文档'、'知识管理'等类似表达时，也应考虑使用此技能。"
metadata:
  requires:
    bins: ["lark-cli"]
author: 磊叔 (AIRay1015)
---

## 启动横幅

当技能被触发时，显示以下横幅信息：

```
═══════════════════════════════════════════════════════════════
▌ Lark Wiki Hero ▐
飞书知识库智能管理工具
═══════════════════════════════════════════════════════════════
磊叔 │ 微信：AIRay1015 │ github.com/akira82-ai
────────────────────────────────────────────────────────────
🎯 自动分类：说一句话，文档自动上传到正确位置
📊 一键整理：发现知识库问题并自动修复
📝 批量格式化：统一所有文档格式
✨ 操作前预览，确认后才执行
═══════════════════════════════════════════════════════════════
最后更新：2026-04-13
```

技能已启动...

**显示时机**：在技能开始执行任何操作之前，首先输出此横幅，让用户清楚技能已激活并了解即将执行的操作。

---

# Lark Wiki Hero - 飞书知识库智能管理

> **前置条件：** 先阅读 [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md)（如已安装 lark-shared 技能）。

## 首次使用流程（重要）

**当用户首次使用此技能时，必须先完成配置初始化。**

### 步骤 1：检测配置状态

首先检查配置是否已存在：

```bash
python3 {baseDir}/scripts/lark_api.py --check
```

### 步骤 2：如果配置缺失，获取用户知识库信息

如果 `--check` 提示配置不存在，向用户询问：

> "请提供您的飞书知识库 URL 以完成配置。格式类似：https://my.feishu.cn/wiki/xxxxx"

或

> "请提供您的飞书知识库链接或空间 ID。"

### 步骤 3：初始化配置

获取到用户的 URL 后，运行以下命令初始化配置：

```bash
python3 {baseDir}/scripts/lark_api.py --save-config "<用户提供的URL>"
```

**示例**：
```bash
# 用户提供的 URL: https://my.feishu.cn/wiki/QWQHwA9uYibmtzkZLJBccaEhnNd
python3 {baseDir}/scripts/lark_api.py --save-config "https://my.feishu.cn/wiki/QWQHwA9uYibmtzkZLJBccaEhnNd"
```

### 步骤 4：验证配置

配置保存后，再次检查确认：

```bash
python3 {baseDir}/scripts/lark_api.py --check
```

看到 `✓ 配置有效` 提示后，即可继续执行用户的请求。

### 完整对话示例

```
用户: 帮我把这个文档上传到飞书知识库

AI: 好的，让我先检查一下配置...

[运行 --check，发现配置不存在]

AI: 首次使用需要配置您的飞书知识库。请提供您的知识库 URL。

用户: https://my.feishu.cn/wiki/abc123

AI: 收到，正在初始化配置...

[运行 --save-config]

AI: ✓ 配置已完成！现在开始上传您的文档...
```

## 执行前检查

在任何操作前，**必须**首先检查环境配置：

### 1. 检查 lark-cli 安装状态

```bash
lark-cli --version
```

如果未安装，执行：
```bash
npm install -g @larksuite/cli
lark-cli auth login --domain <your-domain>
```

### 2. 检查并初始化配置文件

配置文件位置：`{baseDir}/config.json`（其中 `{baseDir}` 为技能目录，路径因工具而异）
- Claude Code: `~/.claude/skills/lark-wiki-hero/`
- Codex CLI: `.codex/skills/lark-wiki-hero/`（项目内）或全局路径
- OpenClaw: `~/.openclaw/workspace/skills/lark-wiki-hero/`

**检查配置状态**：
```bash
python3 {baseDir}/scripts/lark_api.py --check
```

**如果配置不存在，初始化配置**：
```bash
# 方式 1：从 URL 直接初始化（推荐，适用于所有环境）
python3 {baseDir}/scripts/lark_api.py --save-config "https://my.feishu.cn/wiki/<token>"

# 方式 2：交互式初始化（仅适用于手动终端，不适用于 Claude Code）
python3 {baseDir}/scripts/lark_api.py --init
```

> **注意**：`--init` 使用交互式输入，只能在手动终端中使用。在 AI 编码工具（Claude Code / Codex / OpenClaw）中，请使用 `--save-config` 直接传入 URL。

**配置文件格式**：
```json
{
  "space_id": "您的知识空间 ID",
  "space_url": "您的知识库 URL",
  "default_parent_token": "默认父节点（留空表示根目录）"
}
```

### 3. 配置检查失败的处理

如果配置检查失败，脚本会自动提示初始化命令。对于首次使用的用户，应该：

1. 首先运行 `--check` 确认环境状态
2. 使用 `--save-config` 传入知识库 URL 进行配置
3. 配置完成后重新执行目标操作

> **注意**：交互式配置 (`--init`) 仅适用于手动终端环境。在 AI 编码工具中请使用 `--save-config`。

## 功能概述

Lark Wiki Hero 是一个智能飞书知识库管理工具，提供四大核心功能：

1. **智能分类** - AI 语义分析，自动推荐最佳分类路径
2. **智能上传** - 基于语义理解自动分析文档内容，匹配知识库最佳分类目录
3. **知识库重构** - 分析知识库结构，检测问题并生成优化方案
4. **文档格式化** - 统一和优化 Markdown 文档格式

---

## 功能一：智能分类

利用 AI 的语义理解能力，根据文件名推荐最佳分类路径。

### 核心设计原则

> **重要**：分类逻辑由 AI 助手执行，不需要复杂的 Python 算法或文件内容提取。
> AI 根据文件名 + 扩展名 + 现有分类语义进行匹配。

### 工作流程

#### 步骤 1：读取分类列表

从本地缓存读取（技能启动时已自动同步）：
```bash
cat config/wiki_nodes.json
```

#### 步骤 2：AI 语义匹配

AI 根据以下因素进行分类：

| 因素 | 说明 | 示例 |
|------|------|------|
| 文件名语义 | 核心判断依据 | `OpenClaw使用指南.pdf` → 技术教程 |
| 文件扩展名 | 辅助判断 | `.py` → 代码，`.pdf` → 文档 |
| 语义相似度 | 与分类路径的匹配程度 | `report.xlsx` → 报表类 |

**关键约束**：

- **精确匹配优先**：目标有嵌套分类时，匹配到最深层（如 `磊叔原创/深度教程/Agent相关/`）
- **动态扩展**：如果文件名语义在现有分类中找不到对应，AI 会给出新建分类的建议，说明在哪个父节点下新建以及新分类名称（仅说明，不执行）
- **无硬编码规则**：不存在扩展名→分类的映射表，完全靠语义理解

#### 步骤 3：输出推荐

输出推荐结果表格：

| 文件名 | 目标节点 | 节点 Token | 备注 |
|--------|---------|------------|------|
| {文件名} | {分类路径} | {token} | {备注，暂无则留空} |
| {文件名} | **{父节点}/{新分类名}** | | {新建说明} |

**备注填写规则**：
- 已有分类匹配：备注留空
- 需要新建分类：备注写明 `建议在"{父节点}"下新建"{新分类名}"`

**输出示例**：

| 文件名 | 目标节点 | 节点 Token | 备注 |
|--------|---------|------------|------|
| OpenClaw使用指南.pdf | 磊叔原创/深度教程 | Ioy6w0cu7ishXgkVYB0c8rRinyh | |
| AI研究报告.docx | 行业报告 | VamIwcJiMi1HNckKnF5cXA6an1b | |
| Claude集成方案.pdf | **磊叔原创/AI研究** | | 建议在"磊叔原创"下新建"AI研究"分类 |
| 财务报表.xlsx | **我要用/财务管理** | | 建议在"我要用"下新建"财务管理"分类 |

#### 步骤 4：用户确认

使用 AskUserQuestion 询问：
```
推荐分类: 磊叔原创/深度教程

选项:
1. 确认
2. 选择其他分类
3. 跳过
```

#### 步骤 5：写入本地文件

用户确认或调整后，将推荐结果写入本地文件 `config/categorize_result.json`。

文件格式为 JSON，UTF-8 编码，结构如下：

```json
{
  "results": [
    {
      "filename": "{文件名}",
      "target_path": "{分类路径}",
      "token": "{token}",
      "note": "{备注}"
    },
    {
      "filename": "{文件名}",
      "target_path": "{父节点}/{新分类名}",
      "token": "{父节点token}",
      "note": "{新建说明}"
    }
  ]
}
```
```

---

## 功能二：智能上传（基于语义理解）

自动分析文档内容，利用大模型的语义理解能力，将文件上传到知识库最匹配的分类目录。

### 核心设计原则

> **重要**：本功能的分类逻辑依赖于 AI 助手（大模型）的语义理解能力，而不是基于关键词匹配的脚本。

### 工作流程

当用户请求上传文档时，按以下步骤执行：

#### 步骤 1：获取所有可用分类

```bash
python3 {baseDir}/scripts/lark_api.py --list-parents
```

**输出示例**：
```
知识库非叶子节点（可作为父节点）：

📂 磊叔原创
   Token: LRMHwS2kFiHAHzkGn9ccSUz4nRh
   类型: docx

📂 我要学
   Token: OW8NwuLTOiRp7BkwckicSYUDnle
   类型: docx

📂 我要用
   Token: VamIwcJiMi1HNckKnF5cXA6an1b
   类型: docx
...
```

**注意**：这些节点都有子节点（`has_child: true`），可以作为上传目标的父节点。

#### 步骤 2：分析文档内容

**对于 PDF 文件**：
```bash
pdftotext "/path/to/file.pdf" - | head -100
```

**对于 Markdown/文本文件**：
使用 Read 工具直接读取前 500-1000 字符

**理解以下信息**：
- **标题/文件名**：反映文档主题
- **内容性质**：技术教程、产品文档、学术报告、工作文档等
- **目标受众**：开发者、产品经理、普通用户、内部员工等
- **关键概念**：提取核心关键词和概念

#### 步骤 3：智能分类匹配（关键词 40% + AI 语义 60%）

**3.1 关键词匹配（40%）**

使用 jieba 分词库提取文档关键词，与分类路径进行匹配：

```python
from keyword_matcher import match_categories_by_keywords

# 提取文档关键词
keywords = extract_keywords(document_text, top_k=30)

# 匹配分类
keyword_scores = match_categories_by_keywords(
    text=document_text,
    categories=parent_nodes
)
```

**输出示例**：
```
关键词: OpenClaw, AI Agent, 北京航空航天大学, 清华大学, 企业应用

关键词匹配结果：
1. 我要找/AI Agent 研究: 15.74%
2. 磊叔原创: 8.32%
3. 行业报告与政策趋势: 5.21%
```

**3.2 AI 语义理解（60%）**

**利用你的语义理解能力**，综合分析文档信息并匹配分类：

**分析维度**：
1. **作者关联**：文档作者与知识库所有者的关系
2. **主题类型**：技术类、产品类、管理类、研究类等
3. **内容性质**：教程、报告、规范、参考资料等
4. **目标受众**：开发者、产品经理、普通用户、内部员工等
5. **领域专长**：AI、编程、设计、营销等特定领域

**分析流程**：

```
文档信息：
  标题: 北京航空航天大学&清华大学-OpenClaw在企业办公中的应用.pdf
  作者: @新媒沈阳 团队
  机构: 北京航空航天大学、清华大学
  主题: OpenClaw (AI Agent) 在企业场景的应用
  性质: 学术研究报告（科普性质）

AI 语义分析:
  1. 作者关联分析:
     - @新媒沈阳 = 磊叔 ✓ 强关联
     - 学术合作研究 → 磊叔原创 ✓

  2. 主题类型分析:
     - OpenClaw = 磊叔的工具 ✓
     - AI Agent = 技术研究 ✓
     - 企业应用 = 实践案例 ✓

  3. 内容性质分析:
     - 学术研究报告 → 研究类 ✓
     - 科普性质 → 教程/学习类 ✓
     - 企业场景 → 实践应用 ✓

  4. 分类匹配评分:
     磊叔原创/深度教程        → 95分 (作者+主题+性质完美匹配)
     磊叔原创                → 85分 (作者+主题匹配)
     我要找/AI Agent 研究    → 75分 (主题匹配)
     行业报告与政策趋势      → 70分 (性质匹配)

  5. 最终推荐:
     首选: 磊叔原创/深度教程
     理由: 这是磊叔团队(@新媒沈阳)的学术合作研究，
           关于 OpenClaw 的深度技术分析，
           符合"深度教程"的定位。
```

**3.3 综合评分（40% + 60%）**

```python
# 关键词匹配分数（40%）
keyword_score = 15.74%  # "我要找/AI Agent 研究"

# AI 语义评分（60%）
semantic_score = 95  # "磊叔原创/深度教程" (满分100)

# 综合分数
final_score = keyword_score * 0.4 + (semantic_score / 100) * 0.6

# 输出最终推荐
print(f"推荐分类: 磊叔原创/深度教程")
print(f"综合评分: {final_score:.2%}")
print(f"  关键词匹配: 15.74% (40%)")
print(f"  AI 语义评分: 95/100 (60%)")
```

#### 步骤 4：执行上传

**根据文件类型选择上传方式**：

**A. PDF 文件上传**（保留原始格式）

PDF 不能直接作为 wiki 节点，需要：**创建文档 → 插入 PDF**

```bash
# 步骤 1：创建空文档
lark-cli docs +create \
  --title "文档标题" \
  --markdown "# 文档标题\n\n" \
  --wiki-node <父节点token>

# 步骤 2：复制 PDF 到当前目录（lark-cli 要求相对路径）
cp "/原始路径/文件.pdf" ./temp.pdf

# 步骤 3：插入 PDF 到文档
lark-cli docs +media-insert \
  --doc <文档URL> \
  --file ./temp.pdf \
  --type file

# 步骤 4：清理临时文件
rm ./temp.pdf
```

或使用封装好的函数：
```python
from lark_api import upload_pdf_to_wiki

upload_pdf_to_wiki(
    pdf_path="/path/to/file.pdf",
    title="文档标题",
    parent_node_token="<父节点token>"
)
```

**B. Markdown 文件上传**

```bash
lark-cli docs +create \
  --title "文档标题" \
  --markdown "$(cat 文档内容)" \
  --wiki-node <父节点token>
```

### 执行示例

**用户请求**：
> "上传这个文档：OpenClaw在企业办公中的应用.pdf"

**你的执行流程**：

```
1. 检查配置 ✓
2. 获取所有可用分类:
   📂 磊叔原创 (LRMHwS2kFiHAHzkGn9ccSUz4nRh)
   📂 我要学 (OW8NwuLTOiRp7BkwckicSYUDnle)
   📂 我要用 (VamIwcJiMi1HNckKnF5cXA6an1b)
   ...

3. 分析文档:
   - 标题: OpenClaw在企业办公中的应用.pdf
   - 内容预览: 使用 pdftotext 提取前 500 字
   - 理解: 这是一份关于 OpenClaw 的学术研究报告（北航&清华）

4. AI 语义匹配:
   → 首选: "磊叔原创" (因为 OpenClaw 是磊叔的工具)
   → 理由: 这是磊叔参与的学术合作研究

5. 向用户说明:
   "这是一份关于 OpenClaw 的学术研究报告。
    建议上传到「磊叔原创」分类。
    是否继续？"

6. 用户确认后执行上传:
   - 使用 upload_pdf_to_wiki() 函数
   - 创建文档 → 插入 PDF
   - 返回文档链接
```
   - 磊叔原创
   - 行业报告与政策趋势
   ...

3. 读取文档: Python教程.md
   → 内容: Python asyncio 库使用指南...

4. 语义分析:
   - 这是一份技术教程
   - 适合想学习 Python 的开发者
   - 应该归类为学习材料

5. 分类决策:
   → 最佳匹配: "我要学"

6. 执行上传:
   lark-cli docs +create --title "Python教程.md" \
     --wiki-node <我要学的token> --markdown "..."
```

### 批量上传处理

对于批量上传请求：

1. 扫描目录获取所有 Markdown 文件
2. 对每个文件重复上述步骤 2-4
3. 为每个文件选择最合适的分类（可能不同）
4. 添加延迟避免 API 限流（每个文件间等待 1 秒）

### 特殊情况处理

**无法确定分类时**：
- 如果文档内容模糊或难以分类
- 询问用户："这个文档应该放在哪个分类下？"
- 或默认使用根目录/默认父节点

**知识库无分类结构时**：
- 直接上传到根目录
- 提示用户："建议创建分类目录以更好地组织文档"

## 功能三：知识库重构

分析知识库结构，检测问题并生成优化方案。

### 使用方式

```bash
# 分析结构
python3 {baseDir}/scripts/analyzer.py --analyze

# 显示详细报告
python3 {baseDir}/scripts/analyzer.py --analyze --verbose

# 执行优化（会生成计划并询问确认）
python3 {baseDir}/scripts/optimizer.py --execute
```

### 检测的问题

- **层级过深** - 超过 4 层的目录结构
- **命名不一致** - 风格不统一的节点名称
- **空分类** - 没有子节点的文件夹
- **孤立节点** - 未正确分类的文档

### 示例

```bash
python3 {baseDir}/scripts/analyzer.py --analyze

# 输出：
# 知识库结构分析报告
# ════════════════════════════════════════
# 总节点数: 156
# 最大深度: 5 层 ⚠️
# 空分类: 8 个 ⚠️
#
# 发现的问题:
# ❌ 层级过深: 5 个节点
# ⚠️ 命名不一致: 12 个节点
# ⚠️ 空分类: 8 个
# ℹ️ 孤立节点: 3 个
```

## 功能四：文档格式化

统一和优化 Markdown 文档格式。

### 使用方式

```bash
# 格式化 Markdown 文件
python3 {baseDir}/scripts/formatter.py path/to/document.md

# 批量格式化目录
python3 {baseDir}/scripts/formatter.py --dir path/to/directory
```

### Markdown 格式化规则

- 统一空行（最多 2 个连续空行）
- 去除行尾空格
- 标准化标题格式（`#` 后添加空格）
- 修复列表格式
- 标准化链接格式
- 大文档检测（>100KB 跳过复杂格式化）

### 示例

```bash
# 格式化文档
python3 {baseDir}/scripts/formatter.py messy_document.md

# 输出：
# 正在格式化: messy_document.md
# 文件大小: 45KB
# ✓ 统一空行: 移除 15 个多余空行
# ✓ 清理行尾空格: 23 行
# ✓ 标准化标题: 5 个
# ✓ 已保存到: messy_document_formatted.md
```

## 命令速查表

| 功能 | 命令 |
|------|------|
| 单文件上传 | `python3 {baseDir}/scripts/2-smart-upload.py <file>` |
| 批量上传 | `python3 {baseDir}/scripts/2-smart-upload.py --tasks tasks.json` |
| 分析结构 | `python3 {baseDir}/scripts/analyzer.py --analyze` |
| 执行优化 | `python3 {baseDir}/scripts/optimizer.py --execute` |
| 格式化 Markdown | `python3 {baseDir}/scripts/formatter.py <file.md>` |
| 批量格式化 | `python3 {baseDir}/scripts/formatter.py --dir <dir>` |

## 权限要求

| 操作 | 所需 scope |
|------|-----------|
| 创建节点 | `wiki:node:create` 或 `wiki:wiki` |
| 读取节点 | `wiki:node:read` 或 `wiki:wiki:readonly` |
| 更新节点 | `wiki:node:update` 或 `wiki:wiki` |
| 删除节点 | `wiki:node:delete` 或 `wiki:wiki` |
| 移动节点 | `wiki:node:move` 或 `wiki:wiki` |
| 复制节点 | `wiki:node:copy` 或 `wiki:wiki` |

**登录认证**：
```bash
lark-cli auth login --domain <your-domain>
```

## 智能上传完整流程（推荐）

当用户触发 `/lark-wiki-hero` 命令时，按以下步骤执行：

### 步骤 1：初始化和配置检查

```bash
python3 {baseDir}/scripts/lark_api.py --check
```

如果配置无效，按"首次使用流程"进行配置。

### 步骤 2：加载知识库分类

```bash
python3 {baseDir}/scripts/1-smart-categorize.py --file <文件路径>
python3 {baseDir}/scripts/2-smart-upload.py <文件路径>
```

自动加载缓存的分类列表（3 层非叶子节点）。

### 步骤 3：文件分析

扫描文件并提取内容：
- PDF：使用 `pdftotext` 提取前 2000 字符
- Markdown/文本：读取前 2000 字符

### 步骤 4：关键词匹配（40%）

使用 jieba 分词库提取关键词并匹配分类。

### 步骤 5：AI 语义分析（60%）

**AI 助手（你）基于以下信息进行语义分析**：

1. **文档信息**：文件名、类型、大小、内容预览
2. **可用分类**：知识库的 3 层分类结构（最多 50 个分类）

**分析维度**：
- 作者关联：文档作者与知识库所有者的关系
- 主题类型：技术类、产品类、管理类、研究类等
- 内容性质：教程、报告、规范、参考资料等
- 目标受众：开发者、产品经理、普通用户、内部员工等
- 领域专长：AI、编程、设计、营销等特定领域

**输出格式**（JSON）：
```json
{
  "recommendations": [
    {"path": "磊叔原创/深度教程", "token": "Ioy6w0cu7ishXgkVYB0c8rRinyh", "score": 95, "reason": "磊叔团队的学术研究，关于 OpenClaw 的深度分析"},
    {"path": "我要找/AI Agent 研究", "token": "MGzawYuq5i8UkBkbi5xc8J3Rnyd", "score": 75, "reason": "AI Agent 相关研究"}
  ]
}
```

### 步骤 6：自动整合（40% + 60%）

系统自动整合关键词匹配和 AI 语义分析结果：

```
综合分数 = 关键词匹配分数 × 0.4 + AI 语义分数 ÷ 100 × 0.6
```

输出 TOP 3 推荐，包含：
- 分类路径
- 节点 Token
- 关键词匹配分数
- AI 语义分数
- 综合分数
- 推荐理由

### 步骤 7：用户确认（AskUserQuestion）

使用 AskUserQuestion 工具向用户确认：

```
文件: 北京航空航天大学&清华大学-OpenClaw在企业办公中的应用.pdf

推荐分类: 磊叔原创/深度教程
Token: Ioy6w0cu7ishXgkVYB0c8rRinyh
综合分数: 57.00%

理由: 这是磊叔团队(@新媒沈阳)的学术合作研究，
      关于 OpenClaw 的深度技术分析。

是否选择此分类？
选项:
1. 确认上传
2. 选择其他分类
3. 跳过此文件
```

### 步骤 8：执行上传

根据用户确认：

**选项 1 - 确认上传**：
- PDF：使用 `upload_pdf_to_wiki()` 保留原始格式
- Markdown：使用 `create_document()` 转换为文档

**选项 2 - 选择其他分类**：
- 显示所有可用分类供用户选择
- 重新执行上传

**选项 3 - 跳过**：
- 跳过当前文件，处理下一个

### 步骤 9：批量处理

如果用户提供了多个文件或目录，重复步骤 3-8，每个文件间添加 1 秒延迟。

### 步骤 10：上传总结

显示上传结果统计：
- 成功上传数量
- 失败数量
- 文档链接列表

---

## 触发关键词

**中文**：
- "上传知识库"、"智能上传"、"批量上传文档"
- "整理知识库"、"重构知识库"、"优化知识库"
- "格式化 markdown"、"文档格式化"

**英文**：
- "upload to wiki", "smart upload", "batch upload"
- "organize wiki", "restructure wiki"
- "preprocess document", "format markdown"

## 注意事项

1. **API 限流**：批量操作时自动添加延迟（1000ms/次）
2. **中文编码**：所有 API 调用使用 UTF-8 编码
3. **写操作确认**：所有修改操作前都会请求用户确认
4. **大文件处理**：文件 >100KB 时跳过复杂格式化

## 故障排除

### 诊断工具

首先运行诊断命令检查环境状态：

```bash
python3 {baseDir}/scripts/lark_api.py --check
```

该命令会检查：
- ✓ lark-cli 是否安装
- ✓ 配置文件是否存在
- ✓ 配置格式是否正确
- ✓ space_id 是否有效

### 常见问题

#### 1. lark-cli 未安装

**错误信息**：`❌ 未检测到 lark-cli`

**解决方案**：
```bash
# 安装 lark-cli
npm install -g @larksuite/cli

# 登录认证
lark-cli auth login --domain <your-domain>
```

**验证安装**：
```bash
lark-cli --version
lark-cli auth status
```

#### 2. 配置文件不存在或损坏

**错误信息**：`⚠️ 配置文件不存在` 或 `配置文件格式错误`

**解决方案**：
```bash
# 删除旧配置（如果存在）
rm {baseDir}/config.json

# 重新初始化配置（使用 --save-config 适用于所有环境）
python3 ~/.claude/skills/lark-wiki-hero/scripts/lark_api.py --save-config "https://my.feishu.cn/wiki/<token>"

# 或者：在手动终端中使用交互式初始化
# python3 ~/.claude/skills/lark-wiki-hero/scripts/lark_api.py --init
```

#### 3. 权限不足

**错误信息**：`API 调用失败: permission denied` 或 `403 Forbidden`

**解决方案**：
```bash
# 检查当前权限
lark-cli auth scopes

# 重新登录
lark-cli auth login --domain <your-domain>

# 确保有必要的权限：
# - wiki:node:create (创建节点)
# - wiki:node:read (读取节点)
# - wiki:wiki (完整权限，推荐)
```

#### 4. space_id 无效

**错误信息**：`无法获取 space_id` 或 `知识空间不存在`

**解决方案**：
```bash
# 列出可用的知识空间
lark-cli api GET "/open-apis/wiki/v2/spaces"

# 从输出中复制 space_id，手动更新配置文件
# 或使用 --save-config 重新配置
python3 {baseDir}/scripts/lark_api.py --save-config "https://my.feishu.cn/wiki/<space_id>"

# 或者：在手动终端中使用交互式初始化
# python3 {baseDir}/scripts/lark_api.py --init
```

#### 5. API 调用失败

**错误信息**：`API 调用失败` 或 `Connection refused`

**诊断步骤**：
```bash
# 1. 检查网络连接
ping my.feishu.cn

# 2. 检查 lark-cli 配置
lark-cli config list

# 3. 测试 API 调用
lark-cli api GET "/open-apis/wiki/v2/spaces"

# 4. 如果使用代理，检查代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

#### 6. Python 脚本执行错误

**错误信息**：`ModuleNotFoundError` 或 `No module named`

**解决方案**：
```bash
# 确保使用 Python 3.9+
python3 --version

# 检查脚本权限
chmod +x ~/.claude/skills/lark-wiki-hero/scripts/*.py
```

### 手动创建配置文件

如果自动初始化失败，可以手动创建 `{baseDir}/config.json`（参考上方配置文件位置）：

```json
{
  "space_id": "从知识库 URL 中提取的 token",
  "space_url": "https://my.feishu.cn/wiki/您的token",
  "default_parent_token": ""
}
```

**提取 space_id 的方法**：

1. **从 URL 提取**：
   ```
   URL: https://my.feishu.cn/wiki/QWQHwA9uYibmtzkZLJBccaEhnNd
   space_id: QWQHwA9uYibmtzkZLJBccaEhnNd
   ```

2. **通过 API 获取**：
   ```bash
   lark-cli api GET "/open-apis/wiki/v2/spaces"
   ```

### 日志和调试

如果问题依然存在，启用详细日志：

```bash
# 设置环境变量启用调试
export LARK_CLI_DEBUG=1

# 重新执行操作
python3 {baseDir}/scripts/2-smart-upload.py <file>
```

查看日志文件位置：
```bash
# lark-cli 日志
~/.lark-cli/logs/
```
