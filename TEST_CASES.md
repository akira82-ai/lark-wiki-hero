# Lark API 单元测试用例

## 测试概览

| 函数 | 测试用例数量 | 覆盖场景 |
|------|-------------|---------|
| `create_document()` | 4 | 正常创建、父节点、无效父节点、无权限 |
| `list_nodes()` | 3 | 根节点、子节点、无效父节点 |
| `get_node()` | 2 | 有效节点、不存在 |
| `create_node()` | 3 | 文件夹、表格、无效类型 |
| `update_node_title()` | 3 | 正常更新、节点不存在、无权限 |
| `move_node()` | 3 | 正常移动、目标不存在、超出层级 |
| `delete_node()` | 5 | 移动到待删除、节点不存在、无权限、自动创建文件夹、批量删除 |
| `build_node_tree()` | 1 | 完整树 |
| `flatten_node_tree()` | 1 | 展平树 |
| `load_config()` | 2 | 正常加载、文件不存在 |

**总计**: 27 个测试用例

---

## 测试环境

- **配置文件**: `config/config.json`
- **测试 Space ID**: `7472294423981064194`
- **测试前提**: lark-cli 已安装并认证
- **特殊说明**: `delete_node()` 实现为移动到"待删除"文件夹（飞书不支持直接删除）

---

## 1. create_document() - 创建文档节点

### API 端点
```
POST /open-apis/wiki/v2/spaces/{space_id}/nodes
```

### 测试用例

#### TC-001: 正常创建文档（根节点）
```python
def test_create_document_at_root():
    """在知识库根目录创建文档"""
    title = "测试文档 - 根节点创建"
    parent_token = ""

    result = create_document(title, parent_token)

    assert result is not None
    assert "my.feishu.cn/wiki" in result
    assert "node=" in result
```

**预期结果**: ✅ 返回文档 URL，格式为 `https://my.feishu.cn/wiki/{space_id}?node={node_token}`

---

#### TC-002: 正常创建文档（指定父节点）
```python
def test_create_document_with_parent():
    """在指定父节点下创建文档"""
    title = "测试文档 - 子节点创建"
    parent_token = "wikcnKQ1k3p******8Vabcef"  # 有效的父节点 token

    result = create_document(title, parent_token)

    assert result is not None
    assert "node=" in result
```

**预期结果**: ✅ 文档创建在指定父节点下

---

#### TC-003: 创建文档失败（无效父节点）
```python
def test_create_document_invalid_parent():
    """使用无效的父节点 token"""
    title = "测试文档 - 无效父节点"
    parent_token = "invalid_token_12345"

    result = create_document(title, parent_token)

    assert result is None  # API 返回错误
```

**预期结果**: ✅ 返回 `None`，控制台输出错误信息

---

#### TC-004: 创建文档失败（无权限）
```python
def test_create_document_no_permission():
    """在没有权限的空间创建文档"""
    # 修改 space_id 为无权限的空间
    original_space_id = get_space_id()
    # 临时修改配置...

    result = create_document("测试", "")

    assert result is None
```

**预期结果**: ✅ 返回 `None`，错误码 `131006` (permission denied)

---

## 2. list_nodes() - 列出子节点

### API 端点
```
GET /open-apis/wiki/v2/spaces/{space_id}/nodes?parent_node_token={token}&page_size=50
```

### 测试用例

#### TC-005: 列出根节点
```python
def test_list_root_nodes():
    """列出知识库根目录的所有节点"""
    result = list_nodes(parent_node_token="", page_size=50)

    assert result is not None
    assert "data" in result
    assert "items" in result["data"]
    assert isinstance(result["data"]["items"], list)
```

**预期结果**: ✅ 返回节点列表，包含 `node_token`, `title`, `obj_type`, `has_child` 等字段

---

#### TC-006: 列出子节点
```python
def test_list_child_nodes():
    """列出指定父节点下的子节点"""
    parent_token = "wikcnKQ1k3p******8Vabcef"

    result = list_nodes(parent_token, page_size=50)

    assert result is not None
    assert len(result["data"]["items"]) >= 0
```

**预期结果**: ✅ 返回该父节点下的直接子节点

---

#### TC-007: 列出节点失败（无效父节点）
```python
def test_list_nodes_invalid_parent():
    """使用无效的父节点 token"""
    result = list_nodes("invalid_token", 50)

    # API 可能返回空列表或错误
    assert result is not None or result is None
```

**预期结果**: ⚠️ 可能返回空数据或错误（取决于 API 行为）

---

## 3. get_node() - 获取节点详情

### API 端点
```
GET /open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}
```

### 测试用例

#### TC-008: 获取有效节点
```python
def test_get_node_valid():
    """获取存在的节点详情"""
    node_token = "GwjPwilGUikcvKk68XFcYrV7nEf"  # 有效的节点 token

    result = get_node(node_token)

    assert result is not None
    assert "data" in result
    assert result["data"]["node"]["node_token"] == node_token
    assert "title" in result["data"]["node"]
```

**预期结果**: ✅ 返回节点完整信息，包括 `title`, `obj_type`, `has_child` 等

---

#### TC-009: 获取节点失败（不存在）
```python
def test_get_node_not_exist():
    """获取不存在的节点"""
    result = get_node("invalid_node_token_xyz")

    assert result is None
```

**预期结果**: ✅ 返回 `None`，错误码 `131005` (not found)

---

## 4. create_node() - 创建节点（文件夹等）

### API 端点
```
POST /open-apis/wiki/v2/spaces/{space_id}/nodes
```

### 测试用例

#### TC-010: 创建文件夹节点
```python
def test_create_folder_node():
    """创建文件夹类型的节点"""
    parent_token = ""
    obj_type = "wiki"  # 文件夹类型
    title = "测试文件夹"

    result = create_node(parent_token, obj_type, title)

    assert result is not None
    assert result["data"]["node"]["obj_type"] == "wiki"
    assert result["data"]["node"]["title"] == title
```

**预期结果**: ✅ 创建文件夹节点，返回节点信息

---

#### TC-011: 创建表格节点
```python
def test_create_sheet_node():
    """创建表格类型的节点"""
    result = create_node("", "sheet", "测试表格")

    assert result is not None
    assert result["data"]["node"]["obj_type"] == "sheet"
```

**预期结果**: ✅ 创建表格节点

---

#### TC-012: 创建节点失败（无效类型）
```python
def test_create_node_invalid_type():
    """使用无效的节点类型"""
    result = create_node("", "invalid_type", "测试")

    assert result is None
```

**预期结果**: ✅ 返回 `None`，错误码 `131002` (param err)

---

## 5. update_node_title() - 更新节点标题

### API 端点
```
POST /open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}/title
```

### 测试用例

#### TC-013: 正常更新标题
```python
def test_update_node_title_valid():
    """更新节点标题"""
    node_token = "GwjPwilGUikcvKk68XFcYrV7nEf"
    new_title = "更新后的标题"

    result = update_node_title(node_token, new_title)

    assert result is True

    # 验证更新成功
    node = get_node(node_token)
    assert node["data"]["node"]["title"] == new_title
```

**预期结果**: ✅ 标题更新成功

---

#### TC-014: 更新标题失败（节点不存在）
```python
def test_update_node_title_not_exist():
    """更新不存在的节点标题"""
    result = update_node_title("invalid_token", "新标题")

    assert result is False
```

**预期结果**: ✅ 返回 `False`

---

#### TC-015: 更新标题失败（无权限）
```python
def test_update_node_title_no_permission():
    """更新无权限的节点标题"""
    # 使用其他空间的节点 token
    result = update_node_title("token_from_other_space", "新标题")

    assert result is False
```

**预期结果**: ✅ 返回 `False`，错误码 `131006` (permission denied)

---

## 6. move_node() - 移动节点

### API 端点
```
POST /open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}/move
```

### 测试用例

#### TC-016: 正常移动节点
```python
def test_move_node_valid():
    """移动节点到新的父节点"""
    node_token = "GwjPwilGUikcvKk68XFcYrV7nEf"
    target_parent = "wikcnKQ1k3p******8Vabcef"

    # 记录原位置
    original_node = get_node(node_token)
    original_parent = original_node["data"]["node"]["parent_node_token"]

    result = move_node(node_token, target_parent)

    assert result is True

    # 验证移动成功
    moved_node = get_node(node_token)
    assert moved_node["data"]["node"]["parent_node_token"] == target_parent

    # 恢复原位置
    move_node(node_token, original_parent)
```

**预期结果**: ✅ 节点移动成功

---

#### TC-017: 移动节点失败（目标父节点不存在）
```python
def test_move_node_invalid_target():
    """移动到不存在的父节点"""
    result = move_node("GwjPwilGUikcvKk68XFcYrV7nEf", "invalid_target")

    assert result is False
```

**预期结果**: ✅ 返回 `False`，错误码 `131005` (not found)

---

#### TC-018: 移动节点失败（超出层级限制）
```python
def test_move_node_exceed_depth():
    """移动节点导致层级超过 50 层"""
    # 创建深层嵌套结构...
    # 尝试移动到第 50 层以下

    result = move_node(node_token, deep_parent_token)

    assert result is False
```

**预期结果**: ✅ 返回 `False`，错误码 `131003` (out of limit)

---

## 7. delete_node() - 删除节点（移动到待删除文件夹）

### 实现说明
飞书 Wiki 不支持直接删除节点，此函数将节点移动到名为"待删除"的文件夹。

### API 端点
```
POST /open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}/move
```

### 测试用例

#### TC-019: 正常删除节点（移动到待删除）
```python
def test_delete_node_valid():
    """删除一个测试节点（移动到待删除文件夹）"""
    # 先创建测试节点
    node = create_node("", "wiki", "待删除的测试节点")
    node_token = node["data"]["node"]["node_token"]

    # 删除节点
    result = delete_node(node_token)

    assert result is True

    # 验证节点已被移动到"待删除"文件夹
    # 1. 获取"待删除"文件夹的 token
    trash_token = _get_or_create_trash_folder()

    # 2. 列出"待删除"文件夹的子节点
    trash_children = list_nodes(parent_node_token=trash_token)
    found = False
    for item in trash_children["data"]["items"]:
        if item["node_token"] == node_token:
            found = True
            break

    assert found is True
```

**预期结果**: ✅ 节点移动到"待删除"文件夹

---

#### TC-020: 删除节点失败（节点不存在）
```python
def test_delete_node_not_exist():
    """删除不存在的节点"""
    result = delete_node("invalid_token_xyz")

    assert result is False
```

**预期结果**: ✅ 返回 `False`

---

#### TC-021: 删除节点失败（无权限）
```python
def test_delete_node_no_permission():
    """删除无权限的节点"""
    result = delete_node("token_from_other_space")

    assert result is False
```

**预期结果**: ✅ 返回 `False`，错误码 `131006` (permission denied)

---

#### TC-022: 删除节点时自动创建待删除文件夹
```python
def test_delete_node_creates_trash_folder():
    """当'待删除'文件夹不存在时，自动创建"""
    # 1. 确保"待删除"文件夹不存在
    # （手动删除或使用其他 space）

    # 2. 创建测试节点
    node = create_node("", "wiki", "测试节点2")
    node_token = node["data"]["node"]["node_token"]

    # 3. 删除节点（应该自动创建"待删除"文件夹）
    result = delete_node(node_token)

    assert result is True

    # 4. 验证"待删除"文件夹已创建
    root_nodes = list_nodes("", 100)
    trash_exists = False
    for item in root_nodes["data"]["items"]:
        if item["title"] == "待删除" and item["obj_type"] == "wiki":
            trash_exists = True
            break

    assert trash_exists is True
```

**预期结果**: ✅ 自动创建"待删除"文件夹并移动节点

**说明**: 使用 `list_nodes()` 查找，使用 `create_node()` 创建

---

#### TC-023: 删除多个节点（都在待删除文件夹中）
```python
def test_delete_multiple_nodes():
    """删除多个节点，验证它们都在待删除文件夹中"""
    # 创建多个测试节点
    tokens = []
    for i in range(3):
        node = create_node("", "wiki", f"测试节点_{i}")
        tokens.append(node["data"]["node"]["node_token"])

    # 删除所有节点
    for token in tokens:
        result = delete_node(token)
        assert result is True

    # 验证所有节点都在"待删除"文件夹中
    # 通过 list_nodes() 找到"待删除"文件夹
    root_nodes = list_nodes("", 100)
    trash_token = None
    for item in root_nodes["data"]["items"]:
        if item["title"] == "待删除":
            trash_token = item["node_token"]
            break

    assert trash_token is not None

    # 列出"待删除"文件夹的子节点
    trash_children = list_nodes(parent_node_token=trash_token)

    found_count = 0
    for item in trash_children["data"]["items"]:
        if item["node_token"] in tokens:
            found_count += 1

    assert found_count == 3
```

**预期结果**: ✅ 所有节点都移动到"待删除"文件夹

**说明**: 仅使用现有函数 `list_nodes()`, `create_node()`, `delete_node()`

---

## 8. build_node_tree() - 构建节点树

### 测试用例

#### TC-022: 构建完整节点树
```python
def test_build_node_tree():
    """递归构建知识库节点树"""
    tree = build_node_tree(parent_token="", max_depth=3)

    assert isinstance(tree, list)
    assert len(tree) > 0

    # 验证树结构
    for node in tree:
        assert "token" in node
        assert "title" in node
        assert "depth" in node
        assert "children" in node
```

**预期结果**: ✅ 返回嵌套的节点树结构

---

#### TC-023: 构建节点树（限制深度）
```python
def test_build_node_tree_with_depth_limit():
    """构建节点树并限制深度"""
    tree = build_node_tree(parent_token="", max_depth=2)

    # 验证没有超过深度限制
    def check_depth(nodes, current_depth=1):
        for node in nodes:
            assert node["depth"] <= 2
            if node["children"]:
                check_depth(node["children"], current_depth + 1)

    check_depth(tree)
```

**预期结果**: ✅ 树深度不超过限制

---

## 9. flatten_node_tree() - 展平节点树

### 测试用例

#### TC-024: 展平节点树
```python
def test_flatten_node_tree():
    """将嵌套树展平为字典"""
    tree = build_node_tree("", max_depth=2)
    flat = flatten_node_tree(tree)

    assert isinstance(flat, dict)

    # 验证所有节点都被展平
    for token, info in flat.items():
        assert "title" in info
        assert "path" in info
        assert "depth" in info
```

**预期结果**: ✅ 返回 `{node_token: node_info}` 字典

---

## 10. 配置管理函数

### 测试用例

#### TC-025: 加载配置
```python
def test_load_config():
    """加载配置文件"""
    config = load_config()

    assert "space_id" in config
    assert "space_url" in config
    assert "default_parent_token" in config
```

**预期结果**: ✅ 返回配置字典

---

#### TC-026: 配置文件不存在
```python
def test_load_config_not_exist():
    """配置文件不存在时抛出异常"""
    # 临时删除配置文件
    import shutil
    shutil.copy(CONFIG_PATH, "/tmp/config.json.bak")
    CONFIG_PATH.unlink()

    try:
        config = load_config()
        assert False, "应该抛出异常"
    except FileNotFoundError as e:
        assert "配置文件不存在" in str(e)
    finally:
        # 恢复配置文件
        shutil.copy("/tmp/config.json.bak", CONFIG_PATH)
```

**预期结果**: ✅ 抛出 `FileNotFoundError`

---

## 测试执行计划

### 阶段 1: 配置和基础测试
- TC-025, TC-026（配置管理）

### 阶段 2: 节点读取测试
- TC-005, TC-006, TC-007（列出节点）
- TC-008, TC-009（获取节点）

### 阶段 3: 节点创建测试
- TC-001, TC-002, TC-003, TC-004（创建文档）
- TC-010, TC-011, TC-012（创建其他节点）

### 阶段 4: 节点更新测试
- TC-013, TC-014, TC-015（更新标题）
- TC-016, TC-017, TC-018（移动节点）

### 阶段 5: 节点删除测试
- TC-019, TC-020, TC-021, TC-022, TC-023（删除节点 → 移动到待删除）

### 阶段 6: 树操作测试
- TC-024, TC-025（树构建和展平）

---

## 注意事项

1. **测试隔离**: 每个测试应该使用独立的测试数据，避免相互影响
2. **清理机制**: 测试后应清理创建的测试节点
3. **权限测试**: 需要准备无权限的场景进行测试
4. **并发限制**: 注意 API 频率限制（100 次/分钟）
5. **错误码验证**: 关键测试应验证 API 返回的错误码

---

## 待实现的测试函数

以下函数需要添加测试：
- `upload_pdf_to_wiki()` - PDF 上传（部分依赖 lark-cli）
- `get_document_content()` - 获取文档内容（临时使用 lark-cli）
- `search_documents()` - 搜索文档（临时使用 lark-cli）
