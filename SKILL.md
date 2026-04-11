---
name: lark-wiki-hero
version: 1.0.0
description: "飞书知识库智能管理工具。当用户提到飞书知识库、wiki 文档管理、上传文档到飞书、整理知识库结构、格式化 Markdown 文档，或任何与飞书/Lark 知识空间相关的操作时，必须使用此技能。支持智能自动分类上传、知识库结构分析与优化、文件规范化处理。即使使用'飞书文档'、'知识管理'等类似表达时，也应考虑使用此技能。"
metadata:
  requires:
    bins: ["lark-cli"]
author: 磊叔 (AIRay1015)
---

# Lark Wiki Hero - 飞书知识库智能管理

> **前置条件：** 先阅读 [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md)。

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

Claude: 好的，让我先检查一下配置...

[运行 --check，发现配置不存在]

Claude: 首次使用需要配置您的飞书知识库。请提供您的知识库 URL。

用户: https://my.feishu.cn/wiki/abc123

Claude: 收到，正在初始化配置...

[运行 --save-config]

Claude: ✓ 配置已完成！现在开始上传您的文档...
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

配置文件位置：`{baseDir}/config.json`（其中 `{baseDir}` 技能目录，通常为 `~/.claude/skills/lark-wiki-hero/`）

**检查配置状态**：
```bash
python3 {baseDir}/scripts/lark_api.py --check
```

**如果配置不存在，初始化配置**：
```bash
# 方式 1：交互式初始化（推荐）
python3 {baseDir}/scripts/lark_api.py --init

# 方式 2：从 URL 直接初始化
python3 {baseDir}/scripts/lark_api.py --save-config "https://my.feishu.cn/wiki/<token>"
```

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
2. 根据提示运行 `--init` 进行交互式配置
3. 配置完成后重新执行目标操作

## 功能概述

Lark Wiki Hero 是一个智能飞书知识库管理工具，提供三大核心功能：

1. **智能上传** - 自动分析文档内容，匹配知识库最佳分类目录
2. **知识库重构** - 分析知识库结构，检测问题并生成优化方案
3. **文件预处理** - 学习知识库命名规范，重命名并格式化 Markdown 文档

## 首次使用配置

首次运行时，技能会自动询问您的知识库信息并保存配置：

```bash
# 首次使用会提示输入
请输入您的飞书知识库 URL: https://my.feishu.cn/wiki/xxxxx
```

配置会保存到 `~/.claude/skills/lark-wiki-hero/config.json`：

```json
{
  "space_id": "7472294423981064194",
  "space_url": "https://my.feishu.cn/wiki/xxxxx",
  "default_parent_token": ""
}
```

## 功能一：智能上传

自动分析文档内容，将文件上传到知识库最匹配的分类目录。

### 使用方式

```bash
# 上传单个文件
python3 {baseDir}/scripts/uploader.py path/to/document.md

# 批量上传目录
python3 {baseDir}/scripts/uploader.py --dir path/to/directory

# 指定父节点（不使用自动分类）
python3 {baseDir}/scripts/uploader.py path/to/document.md --parent <node_token>
```

### 工作原理

1. 读取知识库目录结构
2. 分析文档标题和前 200 字符内容
3. 使用关键词匹配算法找到最佳分类
4. 使用 `lark-cli docs +create` 创建文档

### 示例

```bash
# 上传 Python 教程
python3 {baseDir}/scripts/uploader.py ~/Downloads/Python教程.md

# 输出：
# 正在分析文档: Python教程.md
# 检测到关键词: Python, 编程, 教程
# 匹配目录: 技术/编程/Python
# 正在上传... ✓
# 文档已创建: https://my.feishu.cn/wiki/xxxxx
```

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

## 功能三：文件预处理

学习知识库的命名规范，对本地文件进行重命名和格式化。

### 使用方式

```bash
# 格式化 Markdown 文件
python3 {baseDir}/scripts/formatter.py path/to/document.md

# 批量格式化目录
python3 {baseDir}/scripts/formatter.py --dir path/to/directory

# 学习知识库命名规范并重命名
python3 {baseDir}/scripts/naming.py --learn-and-rename path/to/file.md

# 仅学习命名规范（不执行重命名）
python3 {baseDir}/scripts/naming.py --learn-only
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
| 学习命名规范 | `python3 {baseDir}/scripts/naming.py --learn-only` |
| 智能重命名 | `python3 {baseDir}/scripts/naming.py --learn-and-rename <file.md>` |

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
- "预处理文档"、"格式化 markdown"

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
rm ~/.claude/skills/lark-wiki-hero/config.json

# 重新初始化配置
python3 ~/.claude/skills/lark-wiki-hero/scripts/lark_api.py --init
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
# 或重新运行初始化
python3 {baseDir}/scripts/lark_api.py --init
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

如果自动初始化失败，可以手动创建 `~/.claude/skills/lark-wiki-hero/config.json`：

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
