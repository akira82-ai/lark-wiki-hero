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


# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def check_lark_cli_installed() -> bool:
    """
    检查 lark-cli 是否已安装

    Returns:
        是否已安装
    """
    try:
        result = subprocess.run(
            ["lark-cli", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def extract_space_id_from_url(space_url: str) -> Optional[str]:
    """
    从知识库 URL 中提取 space_id 或 node_token

    Args:
        space_url: 知识库 URL

    Returns:
        space_id 或 node_token，失败返回 None
    """
    # 去除 URL 中的查询参数（? 及其后面的内容）
    clean_url = space_url.split('?')[0]

    # 从 URL 中提取 token
    # URL 格式:
    #   - https://my.feishu.cn/wiki/space/{space_id}
    #   - https://my.feishu.cn/wiki/{token}
    import re

    # 优先匹配 /wiki/space/{数字ID} 格式
    match = re.search(r'/wiki/space/(\d+)', clean_url)
    if match:
        return match.group(1)

    # 回退到 /wiki/{token} 格式
    match = re.search(r'/wiki/([a-zA-Z0-9]+)', clean_url)
    if match:
        return match.group(1)

    return None


def get_space_id_from_api() -> Optional[str]:
    """
    通过 API 获取用户的知识空间列表

    Returns:
        第一个可用的 space_id，失败返回 None
    """
    result = lark_api("GET", "/open-apis/wiki/v2/spaces")
    if result and "data" in result:
        spaces = result["data"].get("items", [])
        if spaces:
            return spaces[0].get("space_id")
    return None


def init_config_from_url(space_url: str, default_parent_token: str = "") -> Dict[str, Any]:
    """
    从知识库 URL 初始化配置

    Args:
        space_url: 知识库 URL
        default_parent_token: 默认父节点 token

    Returns:
        创建的配置字典
    """
    # 去除 URL 中的查询参数（? 及其后面的内容）
    clean_url = space_url.split('?')[0]

    # 提取 space_id
    space_id = extract_space_id_from_url(clean_url)

    # 如果 URL 中没有提取到，尝试通过 API 获取
    if not space_id:
        print(f"⚠️ 无法从 URL 提取 space_id，尝试通过 API 获取...")
        space_id = get_space_id_from_api()
        if not space_id:
            raise ValueError("无法获取 space_id，请检查 URL 或确保已登录 lark-cli")

    config = {
        "space_id": space_id,
        "space_url": clean_url,
        "default_parent_token": default_parent_token
    }

    save_config(config)
    return config


def init_config_interactive() -> Dict[str, Any]:
    """
    交互式初始化配置

    Returns:
        创建的配置字典
    """
    print("=" * 60)
    print("Lark Wiki Hero - 首次配置")
    print("=" * 60)
    print()
    print("请提供您的飞书知识库信息以完成配置。")
    print()

    # 检查 lark-cli 是否安装
    if not check_lark_cli_installed():
        print("❌ 错误: 未检测到 lark-cli")
        print()
        print("请先安装 lark-cli:")
        print("  npm install -g @larksuite/cli")
        print()
        print("安装完成后，请登录:")
        print("  lark-cli auth login --domain <your-domain>")
        print()
        sys.exit(1)

    # 询问知识库 URL
    print("请输入您的飞书知识库 URL:")
    print("  格式: https://my.feishu.cn/wiki/<token>")
    print("  或者直接按回车使用默认知识空间")
    print()

    space_url = input("知识库 URL (留空使用默认): ").strip()

    if not space_url:
        # 尝试获取默认空间
        print("正在获取默认知识空间...")
        space_id = get_space_id_from_api()
        if not space_id:
            print("❌ 无法获取默认知识空间，请提供 URL")
            sys.exit(1)
        space_url = f"https://my.feishu.cn/wiki/{space_id}"
        print(f"✓ 使用默认空间: {space_url}")

    # 询问默认父节点
    print()
    default_parent = input("默认父节点 token (留空表示根目录): ").strip()

    # 创建配置
    config = init_config_from_url(space_url, default_parent)

    print()
    print("✓ 配置已保存!")
    print(f"  Space ID: {config['space_id']}")
    print(f"  配置文件: {CONFIG_PATH}")
    print()

    return config


def ensure_config_exists() -> Dict[str, Any]:
    """
    确保配置存在，如果不存在则初始化

    Returns:
        配置字典
    """
    if not CONFIG_PATH.exists():
        return init_config_interactive()
    return load_config()


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
            f"  python3 {Path(__file__).parent}/lark_api.py --init\n"
            f"\n"
            f"或在 AI 编码工具中运行此技能时，会自动引导您完成配置。"
        )

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"配置文件格式错误: {e}\n"
            f"请删除 {CONFIG_PATH} 后重新配置。"
        )


def save_config(config: Dict[str, Any]) -> None:
    """保存配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


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


def get_space_id() -> str:
    """获取知识空间 ID"""
    config = load_config()
    return config.get("space_id", "")


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
        obj_type: 节点类型 (wiki, sheet, bitable, etc.)
        title: 节点标题

    Returns:
        创建的节点数据
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes"

    data = {
        "parent_node_token": parent_node_token,
        "obj_type": obj_type,
        "title": title
    }

    return lark_api("POST", path, data=data)


def create_document(title: str, parent_node_token: str = "",
                   markdown: str = "") -> Optional[str]:
    """
    创建文档（使用 lark-cli docs +create）

    Args:
        title: 文档标题
        parent_node_token: 父节点 token（知识库位置）
        markdown: Markdown 内容

    Returns:
        创建的文档 URL 或 token
    """
    cmd = [
        "lark-cli", "docs", "+create",
        "--title", title,
        "--wiki-node", parent_node_token
    ]

    if markdown:
        cmd.extend(["--markdown", markdown])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            # 返回结果中包含文档 URL
            output = result.stdout.strip()
            return output
        else:
            print(f"创建文档失败: {result.stderr}")
            return None

    except Exception as e:
        print(f"创建文档异常: {e}")
        return None


def update_node_title(node_token: str, new_title: str) -> bool:
    """
    更新节点标题

    Args:
        node_token: 节点 token
        new_title: 新标题

    Returns:
        是否成功
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}/title"

    data = {"title": new_title}
    result = lark_api("POST", path, data=data)

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
    删除节点

    Args:
        node_token: 节点 token

    Returns:
        是否成功
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}"

    result = lark_api("DELETE", path)

    return result is not None


def search_documents(query: str, page_size: int = 10) -> Optional[Dict]:
    """
    搜索文档

    Args:
        query: 搜索关键词
        page_size: 每页数量

    Returns:
        搜索结果
    """
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


def get_document_content(doc_url_or_token: str) -> Optional[str]:
    """
    获取文档内容

    Args:
        doc_url_or_token: 文档 URL 或 token

    Returns:
        Markdown 内容
    """
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


def check_and_prompt_config() -> bool:
    """
    检查配置状态并提示用户

    Returns:
        配置是否有效
    """
    # 检查 lark-cli
    if not check_lark_cli_installed():
        print("⚠️ 未检测到 lark-cli")
        print()
        print("请先安装 lark-cli:")
        print("  npm install -g @larksuite/cli")
        print()
        print("安装完成后，请登录:")
        print("  lark-cli auth login --domain <your-domain>")
        print()
        return False

    # 检查配置文件
    if not CONFIG_PATH.exists():
        print("⚠️ 配置文件不存在，需要初始化配置")
        print()
        print("在 AI 编码工具中使用时，请提供您的飞书知识库 URL。")
        print()
        print("知识库 URL 格式: https://my.feishu.cn/wiki/<token>")
        print()
        print("配置初始化命令:")
        print(f"  python3 {Path(__file__).parent}/lark_api.py --save-config \"<您的URL>\"")
        print()
        return False

    # 验证配置
    try:
        config = load_config()
        if not config.get("space_id"):
            print("⚠️ 配置文件无效: 缺少 space_id")
            print(f"请删除 {CONFIG_PATH} 后重新配置")
            return False

        print(f"✓ 配置有效 (Space ID: {config['space_id']})")
        return True

    except Exception as e:
        print(f"⚠️ 配置文件错误: {e}")
        print(f"请删除 {CONFIG_PATH} 后重新配置")
        return False


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
        print(f"  python3 {Path(__file__).parent}/lark_api.py --save-config \"<您的URL>\"")
        print()
        print("配置完成后，请重新执行您的操作。")
        print("=" * 60)
        sys.exit(1)

    return load_config()


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Lark Wiki Hero - 配置管理工具"
    )

    parser.add_argument("--init", action="store_true",
                       help="交互式初始化配置")
    parser.add_argument("--check", action="store_true",
                       help="检查配置状态")
    parser.add_argument("--save-config", metavar="URL",
                       help="从 URL 保存配置")

    args = parser.parse_args()

    if args.init:
        init_config_interactive()
    elif args.check:
        check_and_prompt_config()
    elif args.save_config:
        init_config_from_url(args.save_config)
        print(f"✓ 配置已保存到: {CONFIG_PATH}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
