---
name: lark-wiki-hero
version: 2.3.1
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
🎯 自动分类：AI 语义分析，自动推荐最佳分类路径
📤 智能上传：文档自动上传到正确的知识库目录
📊 知识库分析：结构诊断 + 健康度评分 + 问题检测
✨ 操作前预览，确认后才执行
═══════════════════════════════════════════════════════════════
最后更新：2026-04-15
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
python3 {baseDir}/scripts/startup_check.py --check
```

### 步骤 2：如果配置缺失，获取用户知识库信息

如果 `--check` 提示配置不存在，向用户询问：

> "请提供您的飞书知识库 URL 以完成配置。格式类似：https://my.feishu.cn/wiki/xxxxx"

或

> "请提供您的飞书知识库链接或空间 ID。"

### 步骤 3：初始化配置

获取到用户的 URL 后，运行以下命令初始化配置：

```bash
python3 {baseDir}/scripts/startup_check.py --save-config "<用户提供的URL>"
```

**示例**：
```bash
# 用户提供的 URL: https://my.feishu.cn/wiki/QWQHwA9uYibmtzkZLJBccaEhnNd
python3 {baseDir}/scripts/startup_check.py --save-config "https://my.feishu.cn/wiki/QWQHwA9uYibmtzkZLJBccaEhnNd"
```

### 步骤 4：验证配置

配置保存后，再次检查确认：

```bash
python3 {baseDir}/scripts/startup_check.py --check
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
python3 {baseDir}/scripts/startup_check.py --check
```

**如果配置不存在，初始化配置**：
```bash
# 方式 1：从 URL 直接初始化（推荐，适用于所有环境）
python3 {baseDir}/scripts/startup_check.py --save-config "https://my.feishu.cn/wiki/<token>"

# 方式 2：交互式初始化（仅适用于手动终端，不适用于 Claude Code）
python3 {baseDir}/scripts/startup_check.py --init
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

Lark Wiki Hero 是一个智能飞书知识库管理工具，提供三大核心功能：

1. **智能分类** - AI 语义分析，自动推荐最佳分类路径
2. **智能上传** - 基于语义理解自动分析文档内容，匹配知识库最佳分类目录
3. **知识库分析** - 全面分析知识库结构，生成健康度评分和问题诊断报告

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

根据功能 1 的分类结果，将文件上传到知识库指定的分类目录下。

### 核心设计原则

> **重要**：本功能的知识库操作能力，严格基于 lark-cli API 的要求，参考 [`lark-wiki-cli-reference.md`](./lark-wiki-cli-reference.md)。

### 前置条件

**必须先完成功能 1**，功能 2 依赖 `config/categorize_result.json` 中的分类结果。

如果用户直接请求上传而未经过功能 1，先询问用户是否要先进行分类。

### 执行步骤

1. **读取分类结果**：从 `config/categorize_result.json` 读取功能 1 的分类结果
2. **生成执行计划**：根据分类结果和文件类型，生成上传命令计划，存入 `config/upload_plan.json`
3. **执行上传**：根据 `upload_plan.json` 逐一执行上传命令
4. **返回结果**：汇总上传结果，返回文档链接列表

### 文件类型与上传方式

| 文件类型 | 上传方式 |
|---------|---------|
| `.pdf` | 多步操作（参考 lark-wiki-cli-reference.md 模块二） |
| `.md` / `.mdx` / `.txt` | 单一命令（参考 lark-wiki-cli-reference.md 模块一） |

### 执行示例

**用户请求**（PDF）：
> "上传这个文档：OpenClaw在企业办公中的应用.pdf"

```
1. 读取 categorize_result.json → token: LRMHwS2kFiHAHzkGn9ccSUz4nRh
2. 生成 upload_plan.json:
   {
     "file": "OpenClaw在企业办公中的应用.pdf",
     "type": "pdf",
     "steps": [
       {"step": 1, "command": "lark-cli api POST ... --data '{\"parent_node_token\": \"LRMHwS2kFiHAHzkGn9ccSUz4nRh\", ...}'", "note": "创建文档节点"},
       {"step": 2, "command": "cp \"./OpenClaw在企业办公中的应用.pdf\" ./temp_upload.pdf", "note": "复制 PDF 到当前目录"},
       {"step": 3, "command": "lark-cli docs +media-insert ...", "note": "插入 PDF 到文档"},
       {"step": 4, "command": "rm ./temp_upload.pdf", "note": "清理临时文件"}
     ]
   }
3. 执行上传（参考 lark-wiki-cli-reference.md 模块二）
4. 返回文档链接
```

**用户请求**（Markdown）：
> "上传这份教程：Python异步编程.md"

```
1. 读取 categorize_result.json → token: OW8NwuLTOiRp7BkwckicSYUDnle
2. 生成 upload_plan.json:
   {
     "file": "Python异步编程.md",
     "type": "markdown",
     "command": "lark-cli api POST \"/open-apis/wiki/v2/spaces/{space_id}/nodes\" --data '{\"parent_node_token\": \"OW8NwuLTOiRp7BkwckicSYUDnle\", \"obj_type\": \"docx\", \"node_type\": \"origin\", \"title\": \"Python异步编程\"}'"
   }
3. 执行上传（参考 lark-wiki-cli-reference.md 模块一）
4. 返回文档链接
```

### 特殊情况处理

**categorize_result.json 不存在时**：
- 询问用户："请先运行功能 1 进行智能分类"
- 或使用根目录（`parent_node_token` 为空）

**note 字段包含新建分类建议时**：
- 如果 `note` 非空（如 `建议在"磊叔原创"下新建"AI研究"分类`），先调用 `create_node` 在指定父节点下创建分类目录，再用新 token 执行上传

**无法确定分类时**：
- 询问用户："这个文档应该放在哪个分类下？"
- 或默认使用根目录

**知识库无分类结构时**：
- 直接上传到根目录
- 提示用户："建议创建分类目录以更好地组织文档"

## 功能三：知识库分析

对知识库进行全面分析，包括结构诊断、健康度评分和问题检测。

**⚠️ 重要：本功能必须实时获取知识库数据，不得依赖 `wiki_nodes.json` 缓存文件。**

### 分析流程

1. **遍历所有节点** - 实时获取完整知识库结构
2. **量化打分** - 从结构健康度、组织规范度、内容丰富度三个维度评分
3. **诊断具体问题** - 检测深层级、孤立节点、命名不一致等问题
4. **输出完整报告** - 控制台可视化 + JSON 数据 + Markdown 文档

### 使用方式

```bash
# 分析知识库（自动保存 JSON 和 Markdown 报告到 ./reports/）
python3 {baseDir}/scripts/analyzer.py --analyze --verbose

# 指定输出目录
python3 {baseDir}/scripts/analyzer.py --analyze -o ./custom_reports
```

### 评分体系

| 维度 | 权重 | 说明 |
|------|------|------|
| **结构健康度** | 40% | 层级合理性、深度分布 |
| **组织规范度** | 35% | 孤立节点、空分类检测 |
| **内容丰富度** | 25% | 节点数量、类型多样性 |

### 评分等级

| 等级 | 分数范围 | 说明 |
|------|---------|------|
| **S** | 95-100 | 优秀 - 知识库状态极佳 |
| **A** | 85-94 | 良好 - 健康度高，有小问题 |
| **B** | 70-84 | 中等 - 存在明显问题需改进 |
| **C** | 60-69 | 较差 - 多项指标不达标 |
| **D** | <60 | 不健康 - 需要全面重构 |

### 输出报告

分析器会实时获取数据并生成以下报告：

- **控制台输出**：可视化文本报告（评分、进度条、状态图标）
- **JSON 文件**：结构化数据，供后续处理或导入其他工具
- **Markdown 文件**：格式化报告，适合文档归档

**输出文件命名**：
- `wiki_analysis_{timestamp}.json`
- `wiki_analysis_{timestamp}.md`

### 检测的问题

- **层级过深** - 超过 4 层的目录结构
- **命名不一致** - 风格不统一的节点名称
- **空分类** - 没有子节点的文件夹
- **孤立节点** - 未正确分类的文档

分析完成后，直接输出分析报告，不推荐任何下一步操作。

---

## 命令速查表

| 功能 | 命令 |
|------|------|
| 智能分类 | `python3 {baseDir}/scripts/classifier.py <files...>` |
| 单文件上传 | `python3 {baseDir}/scripts/2-smart-upload.py <file>` |
| 批量上传 | `python3 {baseDir}/scripts/2-smart-upload.py --tasks tasks.json` |
| 知识库分析 | `python3 {baseDir}/scripts/analyzer.py --analyze --verbose` |

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

## 注意事项

1. **API 限流**：批量操作时自动添加延迟（1000ms/次）
2. **中文编码**：所有 API 调用使用 UTF-8 编码
3. **写操作确认**：所有修改操作前都会请求用户确认
4. **大文件处理**：文件 >100KB 时跳过复杂格式化

## 故障排除

### 诊断工具

首先运行诊断命令检查环境状态：

```bash
python3 {baseDir}/scripts/startup_check.py --check
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
python3 ~/.claude/skills/lark-wiki-hero/scripts/startup_check.py --save-config "https://my.feishu.cn/wiki/<token>"

# 或者：在手动终端中使用交互式初始化
# python3 ~/.claude/skills/lark-wiki-hero/scripts/startup_check.py --init
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
python3 {baseDir}/scripts/startup_check.py --save-config "https://my.feishu.cn/wiki/<space_id>"

# 或者：在手动终端中使用交互式初始化
# python3 {baseDir}/scripts/startup_check.py --init
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
