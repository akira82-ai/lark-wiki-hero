# Lark Wiki CLI 参考手册

> 本文档收录 lark-cli 操作飞书知识库的各种方法，供技能执行时查阅。
> 所有操作均使用 `lark-cli api` 格式，遵循飞书知识库 API 规范。

---

## 模块一：文档原子操作（增删改查 + 移动）

### 资源概念

| 资源 | 说明 |
|------|------|
| **space_id** | 知识空间的唯一标识 |
| **node_token** | 节点的唯一标识（用于定位节点） |
| **obj_token** | 节点对应真实文档的 token（用于编辑文档内容） |
| **obj_type** | 节点类型：`docx`、`sheet`、`bitable`、`file`、`folder` 等 |

### 通用调用格式

```bash
lark-cli api <METHOD> <PATH> [--params <JSON>] [--data <JSON>]
```

- `--params`：GET 请求查询参数，JSON 字符串
- `--data`：POST/PATCH 请求体，JSON 字符串
- 中文内容需要 `ensure_ascii=False`

---

### 1. 创建节点（增）

创建文档节点（docx）、文件夹等：

```bash
lark-cli api POST "/open-apis/wiki/v2/spaces/{space_id}/nodes" \
  --data '{
    "parent_node_token": "<父节点token>",
    "obj_type": "docx",
    "node_type": "origin",
    "title": "文档标题"
  }'
```

> `parent_node_token` 为空表示在根目录创建。

---

### 2. 读取节点（查）

**2.1 获取子节点列表**

```bash
lark-cli api GET "/open-apis/wiki/v2/spaces/{space_id}/nodes" \
  --params '{"parent_node_token": "<父节点token>", "page_size": "50"}'
```

**2.2 获取节点信息**

```bash
lark-cli api GET "/open-apis/wiki/v2/spaces/get_node" \
  --params '{"node_token": "<node_token>"}'
```

返回 `obj_token`（真实文档 token）和 `obj_type`。

---

### 3. 更新节点（改）

**3.1 更新节点标题**

```bash
lark-cli api PATCH "/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}" \
  --data '{
    "node_type": "origin",
    "title": "新标题"
  }'
```

> 注意：需要先通过"获取节点信息"确认 `node_type`。

---

### 4. 移动节点

在同一知识空间内移动节点：

```bash
lark-cli api POST "/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}/move" \
  --data '{"target_parent_token": "<新父节点token>"}'
```

---

### 5. 删除节点（删）

飞书 Wiki 不支持直接删除，通过移动到"待删除"文件夹实现类删除：

```python
from lark_api import delete_node
delete_node(node_token="<node_token>")
```

函数逻辑：
1. 在根目录查找或创建"待删除"文件夹
2. 将目标节点移动到"待删除"文件夹

---

### 6. 添加已有云文档至知识库

将已存在的飞书云文档（docx/sheet/bitable 等）挂载到知识库：

```bash
lark-cli api POST "/open-apis/wiki/v2/spaces/{space_id}/nodes/move_docs_to_wiki" \
  --data '{
    "target_parent_node_token": "<父节点token>",
    "docs_token": "<云文档obj_token>",
    "docs_type": "docx"
  }'
```

---

### 7. 获取异步任务结果

对于耗时操作（如添加已有云文档至知识库），返回 task_id：

```bash
lark-cli api GET "/open-apis/wiki/v2/tasks/{task_id}"
```

---

## 模块二：PDF 上传要求

### 核心约束

- PDF **不能**直接作为 wiki 节点上传
- 必须：**创建文档节点 → 插入 PDF 到文档**

### 操作流程

**步骤 1：创建空文档节点**

```bash
lark-cli api POST "/open-apis/wiki/v2/spaces/{space_id}/nodes" \
  --data '{
    "parent_node_token": "<父节点token>",
    "obj_type": "docx",
    "node_type": "origin",
    "title": "文档标题"
  }'
```

记录返回的 `node_token`。

**步骤 2：将 PDF 复制到当前工作目录**

```bash
cp "/原始路径/文件.pdf" ./temp_upload.pdf
```

> `lark-cli docs +media-insert` 要求文件在**当前工作目录**，必须使用相对路径。

**步骤 3：插入 PDF 到文档**

```bash
lark-cli docs +media-insert \
  --doc "https://my.feishu.cn/wiki/{node_token}" \
  --file ./temp_upload.pdf \
  --type file
```

**步骤 4：清理临时文件**

```bash
rm ./temp_upload.pdf
```

### Python 封装函数

```python
from lark_api import upload_pdf_to_wiki

upload_pdf_to_wiki(
    pdf_path="/path/to/file.pdf",
    title="文档标题",
    parent_node_token="<父节点token>"
)
```

### 注意事项

- 临时文件必须用完即删，避免污染工作目录
- PDF 插入后文档内容为 PDF 预览，保留原始格式
- 文档 URL 格式：`https://my.feishu.cn/wiki/{node_token}`

---

## 模块三：批量上传要求

### 核心约束

- 每文件间隔 **1 秒**（避免 API 限流）
- 逐文件执行，不并发

### 任务文件格式（upload_plan.json）

```json
[
  {
    "file": "path/to/file.md",
    "type": "markdown",
    "command": "lark-cli api POST \"/open-apis/wiki/v2/spaces/{space_id}/nodes\" --data '{\"parent_node_token\": \"...\", \"obj_type\": \"docx\", \"node_type\": \"origin\", \"title\": \"文档标题\"}'"
  },
  {
    "file": "path/to/file.pdf",
    "type": "pdf",
    "steps": [
      {
        "step": 1,
        "command": "lark-cli api POST \"/open-apis/wiki/v2/spaces/{space_id}/nodes\" --data '{\"parent_node_token\": \"...\", \"obj_type\": \"docx\", \"node_type\": \"origin\", \"title\": \"文档标题\"}'",
        "note": "创建文档节点"
      },
      {
        "step": 2,
        "command": "cp \"/path/to/file.pdf\" ./temp_upload.pdf",
        "note": "复制 PDF 到当前目录"
      },
      {
        "step": 3,
        "command": "lark-cli docs +media-insert --doc \"https://...\" --file ./temp_upload.pdf --type file",
        "note": "插入 PDF 到文档"
      },
      {
        "step": 4,
        "command": "rm ./temp_upload.pdf",
        "note": "清理临时文件"
      }
    ]
  }
]
```

### JSON 字段说明

**一级（每个文件）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | string | 文件路径 |
| `type` | string | 文件类型：`markdown`、`pdf` |
| `command` | string | 非 PDF：单一创建命令 |
| `steps` | array | PDF：多步操作数组 |

**二级（PDF 的 steps）：**

| 字段 | 说明 |
|------|------|
| `step` | 执行顺序号 |
| `command` | 要执行的完整命令 |
| `note` | 该步骤的作用说明 |

### 执行模板

```python
import time
import subprocess

def execute_plan(plan: list[dict]):
    results = []
    for i, item in enumerate(plan, 1):
        print(f"[{i}/{len(plan)}] {item['file']}...")
        if item["type"] == "markdown":
            subprocess.run(item["command"], shell=True)
        elif item["type"] == "pdf":
            for step in item["steps"]:
                subprocess.run(step["command"], shell=True)
        results.append({"file": item["file"], "ok": True})
        if i < len(plan):
            time.sleep(1.0)
    return results
```

---

## 附录：API PATH 速查

| 操作 | PATH |
|------|------|
| 创建知识空间 | `POST /open-apis/wiki/v2/spaces` |
| 获取知识空间列表 | `GET /open-apis/wiki/v2/spaces` |
| 获取知识空间信息 | `GET /open-apis/wiki/v2/spaces/:space_id` |
| 创建节点 | `POST /open-apis/wiki/v2/spaces/:space_id/nodes` |
| 获取子节点列表 | `GET /open-apis/wiki/v2/spaces/:space_id/nodes` |
| 获取节点信息 | `GET /open-apis/wiki/v2/spaces/get_node` |
| 更新节点标题 | `PATCH /open-apis/wiki/v2/spaces/:space_id/nodes/:node_token` |
| 移动节点 | `POST /open-apis/wiki/v2/spaces/:space_id/nodes/:node_token/move` |
| 添加已有云文档至知识库 | `POST /open-apis/wiki/v2/spaces/:space_id/nodes/move_docs_to_wiki` |
| 获取异步任务结果 | `GET /open-apis/wiki/v2/tasks/:task_id` |

## 附录：权限要求

| 操作 | 所需 scope |
|------|-----------|
| 知识空间操作 | `wiki:wiki` 或 `wiki:wiki:readonly` |
| 节点增删改查 | `wiki:wiki` |
| 节点移动 | `wiki:wiki` |

登录认证：
```bash
lark-cli auth login --domain <your-domain>
```
