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

Lark Wiki Hero 是一个智能飞书知识库管理工具，提供三大核心功能：

1. **智能上传** - 基于语义理解自动分析文档内容，匹配知识库最佳分类目录
2. **知识库重构** - 分析知识库结构，检测问题并生成优化方案
3. **文档格式化** - 统一和优化 Markdown 文档格式

## 功能一：智能上传（基于语义理解）

自动分析文档内容，利用大模型的语义理解能力，将文件上传到知识库最匹配的分类目录。

### 核心设计原则

> **重要**：本功能的分类逻辑依赖于 AI 助手（大模型）的语义理解能力，而不是基于关键词匹配的脚本。

### 工作流程

当用户请求上传文档时，按以下步骤执行：

#### 步骤 1：获取知识库结构

```bash
python3 {baseDir}/scripts/lark_api.py --check
python3 {baseDir}/scripts/lark_api.py --get-structure
```

**重要**：注意输出中的 `[可用分类]` 标记
- 📂 **[可用分类]** = 有子节点的节点，可以作为上传目标
- 📄 = 叶子节点（没有子节点），不能作为上传目标

**选择策略**：
- 优先选择与文档主题语义最匹配的 `[可用分类]`
- 如果知识库是扁平结构（所有节点都是叶子节点），使用根目录（空 parent_token）

#### 步骤 2：读取并理解文档内容

使用 Read 工具读取用户要上传的文档，理解其：
- **主题类型**：技术教程、产品文档、学习笔记、行业报告等
- **内容性质**：原创内容、转载内容、工作文档等
- **目标受众**：开发者、产品经理、普通用户等

#### 步骤 3：语义匹配分类

**利用你的语义理解能力**，将文档与知识库结构进行匹配：

```
文档: "Python异步编程完全指南"
  → 理解: 这是一份技术教程
  → 知识库扫描:
    - "我要学" (学习教程类) ✓ 匹配
    - "我要用" (工具使用类) ✗ 不匹配
    - "磊叔原创" (原创内容) ✗ 不匹配
  → 决策: 上传到"我要学"下
```

**匹配优先级**：
1. 主题匹配（技术类 → 技术目录）
2. 用途匹配（教程 → 学习/笔记）
3. 受众匹配（内部文档 → 相关部门）

#### 步骤 4：执行上传

使用 `lark-cli docs +create` 创建文档：

```bash
lark-cli docs +create \
  --title "文档标题" \
  --markdown "$(cat 文档内容)" \
  --wiki-node <父节点token>
```

### 执行示例

**用户请求**：
> "帮我把 Python教程.md 上传到飞书知识库"

**你的执行流程**：

```
1. 检查配置 ✓
2. 获取知识库结构:
   - 我要学
   - 我要用
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

## 功能二：知识库重构

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

## 功能三：文档格式化

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
| 单文件上传 | `python3 {baseDir}/scripts/uploader.py <file.md>` |
| 批量上传 | `python3 {baseDir}/scripts/uploader.py --dir <dir>` |
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
python3 {baseDir}/scripts/uploader.py <file>
```

查看日志文件位置：
```bash
# lark-cli 日志
~/.lark-cli/logs/
```
