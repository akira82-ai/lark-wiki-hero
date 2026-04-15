#!/usr/bin/env python3
"""
Lark API 封装模块

处理飞书 API 调用，解决中文编码问题。
复用 airay-lark-wiki-agent 的 API 调用模式。
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


# ================================
# 配置路径
# ================================

CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.json"


# ================================
# 配置管理
# ================================

def load_config() -> Dict[str, Any]:
    """
    加载配置文件

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
        json.JSONDecodeError: 配置文件格式错误
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {CONFIG_PATH}\n"
            f"\n"
            f"请先初始化配置:\n"
            f"  python3 {Path(__file__).parent}/startup_check.py --save-config \"<您的URL>\""
        )

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"配置文件格式错误: {e}\n"
            f"请删除 {CONFIG_PATH} 后重新配置。"
        )


def get_space_id() -> str:
    """获取知识空间 ID"""
    config = load_config()
    return config.get("space_id", "")


def require_config() -> Dict[str, Any]:
    """
    要求配置存在，用于脚本入口

    Returns:
        配置字典

    Raises:
        SystemExit: 配置不存在时退出
    """
    if not CONFIG_PATH.exists():
        print("=" * 60)
        print("Lark Wiki Hero - 首次配置")
        print("=" * 60)
        print()
        print("⚠️ 检测到首次使用，需要配置您的飞书知识库信息")
        print()
        print("请提供您的知识库 URL，格式如下：")
        print("  https://my.feishu.cn/wiki/<token>")
        print()
        print("配置初始化命令：")
        print(f"  python3 {Path(__file__).parent}/startup_check.py --save-config \"<您的URL>\"")
        print()
        print("配置完成后，请重新执行您的操作。")
        print("=" * 60)
        sys.exit(1)

    return load_config()


# ================================
# Lark API 调用
# ================================

def lark_api(method: str, path: str,
             data: Optional[Dict[str, Any]] = None,
             params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
    """
    调用 Lark API

    Args:
        method: HTTP 方法 (GET, POST, PATCH, DELETE)
        path: API 路径
        data: 请求体数据 (POST/PATCH)
        params: 查询参数 (GET)

    Returns:
        API 响应数据，失败返回 None
    """
    cmd = ["lark-cli", "api", method, path]

    if params:
        cmd.extend(["--params", json.dumps(params, ensure_ascii=False)])

    if data:
        cmd.extend(["--data", json.dumps(data, ensure_ascii=False)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"API 调用失败: {result.stderr}")
            return None

    except Exception as e:
        print(f"API 调用异常: {e}")
        return None


# ================================
# 节点操作
# ================================

def list_nodes(parent_node_token: str = "", page_size: int = 50) -> Optional[Dict]:
    """
    列出子节点

    Args:
        parent_node_token: 父节点 token，空字符串表示顶级
        page_size: 每页数量

    Returns:
        节点列表数据
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes"

    params = {
        "parent_node_token": parent_node_token,
        "page_size": str(page_size)
    }

    return lark_api("GET", path, params=params)


def get_node(node_token: str) -> Optional[Dict]:
    """
    获取单个节点详情

    Args:
        node_token: 节点 token

    Returns:
        节点详情数据
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}"

    return lark_api("GET", path)


def create_node(parent_node_token: str, obj_type: str, title: str) -> Optional[Dict]:
    """
    创建节点（文件夹、表格等非文档类型）

    Args:
        parent_node_token: 父节点 token
        obj_type: 节点类型 (docx, sheet, bitable, slides 等)
        title: 节点标题

    Returns:
        创建的节点数据
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes"

    data = {
        "parent_node_token": parent_node_token,
        "obj_type": obj_type,
        "node_type": "origin",  # 必需参数
        "title": title
    }

    return lark_api("POST", path, data=data)


def update_node_title(node_token: str, new_title: str) -> bool:
    """
    更新节点标题

    Args:
        node_token: 节点 token
        new_title: 新标题

    Returns:
        是否成功

    注意:
        需要先获取节点信息以确定 node_type
    """
    space_id = get_space_id()

    # 先获取节点信息
    node_info = get_node(node_token)
    if not node_info:
        return False

    node_type = node_info["data"]["node"].get("node_type", "origin")

    # 使用 PATCH 方法更新节点
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}"

    data = {
        "node_type": node_type,
        "title": new_title
    }

    result = lark_api("PATCH", path, data=data)

    return result is not None


def move_node(node_token: str, target_parent_token: str) -> bool:
    """
    移动节点

    Args:
        node_token: 要移动的节点 token
        target_parent_token: 目标父节点 token

    Returns:
        是否成功
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}/move"

    data = {"target_parent_token": target_parent_token}
    result = lark_api("POST", path, data=data)

    return result is not None


def delete_node(node_token: str) -> bool:
    """
    删除节点（通过移动到"待删除"文件夹）

    飞书 Wiki 不支持直接删除节点，此函数将节点移动到名为"待删除"的文件夹。

    Args:
        node_token: 要删除的节点 token

    Returns:
        是否成功

    注意:
        - 会自动在根目录创建"待删除"文件夹（如果不存在）
        - 节点会被移动到"待删除"文件夹下
    """
    space_id = get_space_id()
    trash_title = "待删除"

    # 1. 查找"待删除"文件夹
    result = list_nodes(parent_node_token="", page_size=50)

    trash_folder_token = None
    if result and "data" in result:
        items = result["data"].get("items", [])
        # 查找名为"待删除"的文件夹
        for item in items:
            if (item.get("title") == trash_title and
                item.get("obj_type") == "docx"):  # 文件夹也是 docx 类型
                trash_folder_token = item.get("node_token")
                break

    # 2. 如果没找到，创建"待删除"文件夹
    if not trash_folder_token:
        print("正在创建'待删除'文件夹...")
        create_result = create_node(
            parent_node_token="",
            obj_type="docx",  # 文件夹使用 docx 类型
            title=trash_title
        )
        if create_result and "data" in create_result:
            trash_folder_token = create_result["data"]["node"]["node_token"]
        else:
            print("无法创建'待删除'文件夹")
            return False

    # 3. 移动节点到"待删除"文件夹
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}/move"
    data = {"target_parent_token": trash_folder_token}

    result = lark_api("POST", path, data=data)

    return result is not None


# ================================
# 文档操作
# ================================

def create_document(title: str, parent_node_token: str = "",
                   markdown: str = "") -> Optional[str]:
    """
    创建文档（使用原生 API）

    Args:
        title: 文档标题
        parent_node_token: 父节点 token（知识库位置）
        markdown: Markdown 内容

    Returns:
        创建的文档 URL 或 node_token
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes"

    # 使用 API 创建节点
    data = {
        "obj_type": "docx",
        "parent_node_token": parent_node_token,
        "node_type": "origin",
        "title": title
    }

    result = lark_api("POST", path, data=data)

    if not result or "data" not in result:
        print(f"创建文档失败: 无效响应")
        return None

    node_token = result["data"].get("node", {}).get("node_token")
    if not node_token:
        print(f"创建文档失败: 未返回 node_token")
        return None

    # 如果有 Markdown 内容，需要通过文档 API 写入内容
    # 注意：这需要额外的文档 API 调用
    if markdown:
        # TODO: 调用文档内容更新 API
        # 目前先返回 node_token，内容更新需要单独实现
        pass

    # 返回知识库节点 URL
    return f"https://my.feishu.cn/wiki/{node_token}"


def upload_pdf_to_wiki(pdf_path: str, title: str,
                       parent_node_token: str = "") -> Optional[str]:
    """
    上传 PDF 到知识库：创建文档并插入 PDF 文件

    Args:
        pdf_path: PDF 文件路径
        title: 文档标题
        parent_node_token: 父节点 token

    Returns:
        创建的文档 URL，失败返回 None

    注意：
        - 创建文档节点后，需要通过文档块 API 插入文件
        - 文件上传需要调用文档媒体 API
    """
    import shutil
    import os

    try:
        # 1. 创建文档节点
        space_id = get_space_id()
        path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes"

        data = {
            "obj_type": "docx",
            "parent_node_token": parent_node_token,
            "node_type": "origin",
            "title": title
        }

        result = lark_api("POST", path, data=data)

        if not result or "data" not in result:
            return None

        node_token = result["data"].get("node", {}).get("node_token")
        obj_token = result["data"].get("node", {}).get("obj_token")

        if not node_token or not obj_token:
            return None

        doc_url = f"https://my.feishu.cn/wiki/{node_token}"

        # 2. 上传 PDF 文件到文档
        # lark-cli docs +media-insert 要求：
        # - 文件必须在当前工作目录（相对路径）
        # - 文档 URL 使用 node_token
        skill_dir = Path(__file__).parent.parent
        temp_filename = f"__temp_upload__{Path(pdf_path).name}"
        temp_path = skill_dir / temp_filename
        orig_cwd = os.getcwd()

        try:
            shutil.copy2(pdf_path, temp_path)
            os.chdir(skill_dir)

            cmd = [
                "lark-cli", "docs", "+media-insert",
                "--doc", f"https://my.feishu.cn/wiki/{node_token}",
                "--file", f"./{temp_filename}",
                "--type", "file"
            ]

            insert_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if insert_result.returncode == 0:
                return f"https://my.feishu.cn/wiki/{node_token}"
            else:
                print(f"插入 PDF 失败: {insert_result.stderr}")
                return f"https://my.feishu.cn/wiki/{node_token}"

        finally:
            if temp_path.exists():
                temp_path.unlink()
            os.chdir(orig_cwd)

    except Exception as e:
        print(f"上传 PDF 异常: {e}")
        return None


def get_document_content(doc_url_or_token: str) -> Optional[str]:
    """
    获取文档内容（使用原生 API）

    Args:
        doc_url_or_token: 文档 URL 或 node_token

    Returns:
        Markdown 内容

    注意：
        需要调用文档块 API 获取完整内容
        API: GET /open-apis/docx/v1/documents/{document_id}/blocks/{block_id}
    """
    # TODO: 实现纯 API 调用
    # 临时方案：使用 lark-cli
    cmd = [
        "lark-cli", "docs", "+fetch",
        "--doc", doc_url_or_token
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            return result.stdout
        else:
            print(f"获取文档内容失败: {result.stderr}")
            return None

    except Exception as e:
        print(f"获取文档内容异常: {e}")
        return None


def search_documents(query: str, page_size: int = 10) -> Optional[Dict]:
    """
    搜索文档（使用原生 API）

    Args:
        query: 搜索关键词
        page_size: 每页数量

    Returns:
        搜索结果

    注意：
        API: POST /open-apis/search/v2/message
        需要指定搜索类型为文档
    """
    # TODO: 实现纯 API 调用
    # 临时方案：使用 lark-cli
    cmd = [
        "lark-cli", "docs", "+search",
        "--query", query,
        "--page-size", str(page_size)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"搜索失败: {result.stderr}")
            return None

    except Exception as e:
        print(f"搜索异常: {e}")
        return None


# ================================
# 节点树操作
# ================================

def fetch_all_nodes_live(max_depth: int = 10) -> List[Dict]:
    """
    实时递归获取知识库的所有节点（不依赖缓存）

    ⚠️ 重要：本函数直接调用 lark-cli API 实时获取数据，
    不得依赖 wiki_nodes.json 缓存文件。

    Args:
        max_depth: 最大递归深度

    Returns:
        完整的节点列表，每个节点包含：
        - token: 节点 token
        - title: 节点标题
        - obj_type: 对象类型 (docx, bitable, etc.)
        - obj_edit_time: 编辑时间戳
        - has_child: 是否有子节点
        - parent_node_token: 父节点 token
        - depth: 层级深度
        - path: 完整路径
    """
    space_id = get_space_id()
    all_nodes = []

    def fetch_recursive(parent_token: str = "", depth: int = 0, path: str = ""):
        """递归获取节点"""
        # 调用 API 获取当前层级的节点
        path_param = f"/open-apis/wiki/v2/spaces/{space_id}/nodes"
        params = {
            "parent_node_token": parent_token,
            "page_size": "50"  # API 限制：最大 50
        }

        result = lark_api("GET", path_param, params=params)

        if not result or "data" not in result:
            return

        items = result["data"].get("items", [])

        for item in items:
            node_token = item.get("node_token", "")
            title = item.get("title", "")
            obj_type = item.get("obj_type", "")
            obj_edit_time = item.get("obj_edit_time", "")
            has_child = item.get("has_child", False)

            # 构建完整路径
            current_path = f"{path}/{title}" if path else title

            # 添加到结果列表
            all_nodes.append({
                "token": node_token,
                "title": title,
                "obj_type": obj_type,
                "obj_edit_time": obj_edit_time,
                "has_child": has_child,
                "parent_node_token": parent_token,
                "depth": depth,
                "path": current_path
            })

            # 如果有子节点且未达到最大深度，递归获取
            if has_child and depth < max_depth:
                fetch_recursive(node_token, depth + 1, current_path)

    # 开始递归获取
    fetch_recursive()

    return all_nodes


def build_node_tree(parent_token: str = "", max_depth: int = 10,
                   current_depth: int = 0) -> List[Dict]:
    """
    递归构建节点树

    Args:
        parent_token: 父节点 token
        max_depth: 最大深度
        current_depth: 当前深度

    Returns:
        节点树列表
    """
    if current_depth >= max_depth:
        return []

    result = list_nodes(parent_token)
    if not result or "data" not in result:
        return []

    nodes = result["data"].get("items", [])

    tree = []
    for node in nodes:
        node_data = {
            "token": node.get("node_token"),
            "title": node.get("title"),
            "obj_type": node.get("obj_type"),
            "has_child": node.get("has_child", False),
            "depth": current_depth + 1,
            "children": []
        }

        # 如果有子节点，递归获取
        if node.get("has_child") and node.get("obj_type") == "wiki":
            node_data["children"] = build_node_tree(
                node["node_token"],
                max_depth,
                current_depth + 1
            )

        tree.append(node_data)

    return tree


def flatten_node_tree(tree: List[Dict], parent_path: str = "") -> Dict[str, Dict]:
    """
    将节点树展平为字典，便于快速查找

    Args:
        tree: 节点树
        parent_path: 父节点路径

    Returns:
        {node_token: node_info} 字典
    """
    flat = {}

    for node in tree:
        token = node["token"]
        title = node["title"]
        current_path = f"{parent_path}/{title}" if parent_path else title

        flat[token] = {
            "title": title,
            "obj_type": node["obj_type"],
            "path": current_path,
            "depth": node["depth"],
            "has_child": node["has_child"]
        }

        # 递归处理子节点
        if node["children"]:
            flat.update(flatten_node_tree(node["children"], current_path))

    return flat
