#!/usr/bin/env python3
"""
Lark Wiki Hero 启动检查脚本

在技能启动时自动检查知识库更新并同步缓存。
"""

import subprocess
import json
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any


# ================================
# 路径配置
# ================================

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "config.json"
CACHE_FILE = SCRIPT_DIR.parent / "config" / "wiki_nodes.json"
MAX_CACHE_DEPTH = 3  # 缓存最多3层节点


# ================================
# lark-cli 检查
# ================================

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
            f"  python3 {SCRIPT_DIR}/startup_check.py --init\n"
            f"\n"
            f"或在 AI 编码工具中运行此技能时，会自动引导您完成配置。"
        )

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


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
    space_id = extract_space_id_from_url(space_url)

    if not space_id:
        raise ValueError(f"无法从 URL 中提取 space_id: {space_url}")

    config = {
        "space_id": space_id,
        "space_url": space_url,
        "default_parent_token": default_parent_token
    }

    # 确保配置目录存在
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 保存配置
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return config


def get_space_id() -> str:
    """获取知识空间 ID"""
    config = load_config()
    return config.get("space_id", "")


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
        print(f"  python3 {SCRIPT_DIR}/startup_check.py --save-config \"<您的URL>\"")
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


# ================================
# 缓存管理
# ================================

def get_node_children(parent_token: str = "") -> List[Dict]:
    """
    获取子节点

    Args:
        parent_token: 父节点 token，空字符串表示根目录

    Returns:
        子节点列表
    """
    space_id = get_space_id()
    path = f"/open-apis/wiki/v2/spaces/{space_id}/nodes"

    params = {"parent_node_token": parent_token} if parent_token else {}

    result = lark_api("GET", path, params=params)
    if result and result.get('code') == 0:
        return result.get('data', {}).get('items', [])
    return []


def get_parent_nodes_recursive(parent_token: str = "", path: str = "",
                                level: int = 0, max_depth: int = MAX_CACHE_DEPTH) -> List[Dict[str, Any]]:
    """
    递归获取所有非叶子节点（父节点）

    Args:
        parent_token: 父节点 token
        path: 当前路径
        level: 当前层级
        max_depth: 最大深度

    Returns:
        父节点列表
    """
    if level >= max_depth:
        return []

    nodes = get_node_children(parent_token)
    parents = []

    for node in nodes:
        title = node.get('title')
        token = node.get('node_token')
        has_child = node.get('has_child', False)
        obj_type = node.get('obj_type')
        obj_edit_time = node.get('obj_edit_time', 0)

        current_path = f"{path}/{title}" if path else title

        # 如果有子节点，加入列表并递归
        if has_child:
            parents.append({
                'title': title,
                'token': token,
                'path': current_path,
                'level': level,
                'obj_type': obj_type,
                'obj_edit_time': obj_edit_time,
                'has_child': True
            })
            # 递归获取子节点
            parents.extend(get_parent_nodes_recursive(
                token, current_path, level + 1, max_depth
            ))

    return parents


def save_cache(nodes: List[Dict]) -> None:
    """
    保存节点数据到缓存

    Args:
        nodes: 节点列表
    """
    # 确保配置目录存在
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    cache_data = {
        'version': '1.0',
        'space_id': get_space_id(),
        'last_update': int(time.time()),
        'nodes': nodes
    }

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)


def load_cache() -> Optional[Dict]:
    """
    加载缓存的节点数据

    Returns:
        缓存数据，失败返回 None
    """
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def is_cache_valid() -> bool:
    """
    检查缓存是否有效

    Returns:
        缓存是否有效
    """
    cache = load_cache()
    if not cache:
        return False

    # 检查 space_id 是否匹配
    if cache.get('space_id') != get_space_id():
        return False

    # 检查顶级节点的时间戳是否变化
    root_nodes = get_node_children("")
    cached_root_nodes = {
        node['token']: node.get('obj_edit_time', 0)
        for node in cache.get('nodes', [])
        if node.get('level') == 0
    }

    for node in root_nodes:
        token = node.get('node_token')
        edit_time = node.get('obj_edit_time', 0)

        if token not in cached_root_nodes:
            return False

        if cached_root_nodes[token] != edit_time:
            return False

    return True


def get_cached_parent_nodes(force_refresh: bool = False) -> List[Dict]:
    """
    获取缓存的父节点列表

    Args:
        force_refresh: 是否强制刷新缓存

    Returns:
        父节点列表
    """
    if not force_refresh and is_cache_valid():
        cache = load_cache()
        return cache.get('nodes', [])

    # 缓存无效或强制刷新，重新加载
    print("正在加载知识库分类结构...")
    nodes = get_parent_nodes_recursive()
    save_cache(nodes)
    print(f"✓ 已加载并缓存 {len(nodes)} 个分类节点")

    return nodes


# ================================
# 启动横幅
# ================================

def show_startup_banner() -> None:
    """显示启动横幅"""
    print("=" * 60)
    print("▌ Lark Wiki Hero ▐")
    print("飞书知识库智能管理工具")
    print("=" * 60)
    print("磊叔 │ 微信：AIRay1015 │ github.com/akira82-ai")
    print("─" * 60)
    print("• 自动分类：说一句话，文档自动上传到正确位置")
    print("• 一键整理：发现知识库问题并自动修复")
    print("• 批量格式化：统一所有文档格式")
    print("• 操作前预览，确认后才执行")
    print("=" * 60)
    print("最后更新：2026-04-13")
    print()


# ================================
# 启动检查
# ================================

def check_knowledge_base_update() -> dict:
    """
    检查知识库是否有更新

    Returns:
        检查结果字典 {
            'has_update': bool,
            'cache_exists': bool,
            'cache_valid': bool,
            'space_id': str,
            'cached_node_count': int,
            'current_node_count': int
        }
    """
    result = {
        'has_update': False,
        'cache_exists': False,
        'cache_valid': False,
        'space_id': get_space_id(),
        'cached_node_count': 0,
        'current_node_count': 0
    }

    # 检查缓存是否存在
    cache = load_cache()
    if cache:
        result['cache_exists'] = True
        result['cached_node_count'] = len(cache.get('nodes', []))

    # 检查缓存是否有效
    if is_cache_valid():
        result['cache_valid'] = True
        result['current_node_count'] = result['cached_node_count']
    else:
        # 缓存无效，说明有更新
        result['has_update'] = True
        # 重新加载以获取当前节点数
        nodes = get_cached_parent_nodes(force_refresh=True)
        result['current_node_count'] = len(nodes)

    return result


def startup_check() -> dict:
    """
    执行启动检查

    Returns:
        检查结果字典 {
            'success': bool,
            'lark_cli_installed': bool,
            'config_valid': bool,
            'cache_status': str,
            'update_status': str
        }
    """
    result = {
        'success': False,
        'lark_cli_installed': False,
        'config_valid': False,
        'cache_status': 'unknown',
        'update_status': 'unknown'
    }

    print("🔍 系统检查")
    print("=" * 60)

    # 1. 检查 lark-cli
    print("1️⃣ 检查 lark-cli...")
    if not check_lark_cli_installed():
        print("   ❌ 未检测到 lark-cli")
        print()
        print("📋 解决方案：")
        print("   请先安装 lark-cli:")
        print("   npm install -g @larksuite/cli")
        print()
        print("   安装完成后，请登录:")
        print("   lark-cli auth login --domain <your-domain>")
        print()
        return result
    else:
        print("   ✅ lark-cli 已安装")
        result['lark_cli_installed'] = True

    # 2. 检查配置
    print()
    print("2️⃣ 检查配置文件...")
    if not check_and_prompt_config():
        print("   ❌ 配置检查失败")
        return result
    else:
        print("   ✅ 配置有效")
        result['config_valid'] = True

    # 3. 检查知识库更新
    print()
    print("3️⃣ 检查知识库缓存...")
    update_result = check_knowledge_base_update()

    if update_result['has_update']:
        print("   🔄 检测到知识库更新")
        print(f"   ✅ 已自动同步最新数据")
        print(f"   📊 缓存节点: {update_result['cached_node_count']} → {update_result['current_node_count']}")
        result['cache_status'] = 'updated'
        result['update_status'] = f"已更新 ({update_result['cached_node_count']} → {update_result['current_node_count']} 节点)"
    elif update_result['cache_valid']:
        print("   ✅ 缓存最新，无需更新")
        print(f"   📊 当前缓存: {update_result['cached_node_count']} 个节点")
        result['cache_status'] = 'valid'
        result['update_status'] = f"缓存有效 ({update_result['cached_node_count']} 节点)"
    else:
        print("   🆕 首次加载知识库")
        print(f"   ✅ 已缓存知识库结构")
        print(f"   📊 节点数: {update_result['current_node_count']}")
        result['cache_status'] = 'initialized'
        result['update_status'] = f"首次加载 ({update_result['current_node_count']} 节点)"

    result['success'] = True
    return result


# ================================
# 命令行入口
# ================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Lark Wiki Hero - 启动检查工具"
    )

    parser.add_argument("--check", action="store_true",
                       help="检查配置状态")
    parser.add_argument("--save-config", metavar="URL",
                       help="从 URL 保存配置")
    parser.add_argument("--list-parents", action="store_true",
                       help="列出所有非叶子节点（可作为父节点）")
    parser.add_argument("--refresh-cache", action="store_true",
                       help="强制刷新知识库分类缓存")

    args = parser.parse_args()

    if args.save_config:
        # 配置模式
        init_config_from_url(args.save_config)
        print(f"✓ 配置已保存到: {CONFIG_PATH}")
    elif args.list_parents:
        # 列出父节点
        parents = get_cached_parent_nodes(force_refresh=args.refresh_cache)
        if parents:
            print("知识库非叶子节点（可作为父节点）：\n")
            for node in parents:
                indent = "  " * node['level']
                print(f"📂 {indent}{node['title']}")
                print(f"   Token: {node['token']}")
                print(f"   路径: {node['path']}")
                print()
    else:
        # 默认：启动检查模式
        show_startup_banner()

        check_result = startup_check()

        print()
        print("=" * 60)
        print("📋 检查结果摘要")
        print("=" * 60)

        if check_result['success']:
            print("✅ 所有检查通过")
            print()
            print("系统状态：")
            print(f"  • lark-cli: {'✅ 已安装' if check_result['lark_cli_installed'] else '❌ 未安装'}")
            print(f"  • 配置文件: {'✅ 有效' if check_result['config_valid'] else '❌ 无效'}")
            print(f"  • 知识库缓存: {check_result['update_status']}")
            print()
            print("🚀 系统就绪，可以开始使用 Lark Wiki Hero")
        else:
            print("❌ 检查未通过")
            print()
            print("请解决上述问题后重试。如需帮助，请查看：")
            print("  https://github.com/akira82-ai/lark-wiki-hero")

        print("=" * 60)
        print()

        if not check_result['success']:
            sys.exit(1)


if __name__ == "__main__":
    main()
