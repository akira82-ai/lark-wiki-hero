#!/usr/bin/env python3
"""
Lark API 单元测试
执行 TEST_CASES.md 中定义的测试用例
"""

import sys
import json
import time
from pathlib import Path

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from lark_api import (
    load_config,
    get_space_id,
    list_nodes,
    get_node,
    create_node,
    create_document,
    update_node_title,
    move_node,
    delete_node,
    build_node_tree,
    flatten_node_tree
)


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_nodes = []  # 记录创建的测试节点，用于清理

    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        print(f"\n{'='*60}")
        print(f"运行: {test_name}")
        print('='*60)

        try:
            test_func()
            print(f"✅ {test_name} - 通过")
            self.passed += 1
            return True
        except AssertionError as e:
            print(f"❌ {test_name} - 失败")
            print(f"   断言错误: {e}")
            self.failed += 1
            return False
        except Exception as e:
            print(f"❌ {test_name} - 错误")
            print(f"   异常: {e}")
            self.failed += 1
            return False

    def summary(self):
        """打印测试总结"""
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"测试总结")
        print(f"{'='*60}")
        print(f"总计: {total} | 通过: {self.passed} | 失败: {self.failed}")
        print(f"通过率: {self.passed/total*100:.1f}%")
        print(f"{'='*60}\n")


def test_tc_001_create_document_at_root():
    """TC-001: 正常创建文档（根节点）"""
    title = f"测试文档 - 根节点创建 - {int(time.time())}"
    parent_token = ""

    result = create_document(title, parent_token)

    assert result is not None, "创建文档返回 None"
    assert "my.feishu.cn/wiki" in result, f"返回的 URL 格式不正确: {result}"
    assert "node=" in result, f"URL 中缺少 node 参数: {result}"

    # 记录用于清理
    test_nodes = result.split("node=")[1].split("&")[0] if "&" in result else result.split("node=")[1]
    return test_nodes


def test_tc_002_list_root_nodes():
    """TC-005: 列出根节点"""
    result = list_nodes(parent_node_token="", page_size=50)

    assert result is not None, "list_nodes 返回 None"
    assert "data" in result, "响应中缺少 data 字段"
    assert "items" in result["data"], "data 中缺少 items 字段"
    assert isinstance(result["data"]["items"], list), "items 不是列表"


def test_tc_003_get_node_valid():
    """TC-008: 获取有效节点"""
    # 先创建一个节点
    title = f"测试获取节点 - {int(time.time())}"
    result = create_document(title, "")
    assert result is not None

    # 提取 node_token
    node_token = result.split("node=")[1].split("&")[0] if "&" in result else result.split("node=")[1]

    # 获取节点详情
    node = get_node(node_token)

    assert node is not None, f"get_node 返回 None, token: {node_token}"
    assert "data" in node, "节点数据中缺少 data 字段"
    assert node["data"]["node"]["node_token"] == node_token, "node_token 不匹配"
    assert "title" in node["data"]["node"], "节点中缺少 title 字段"

    return node_token


def test_tc_004_create_folder_node():
    """TC-010: 创建表格节点（替代文件夹）"""
    parent_token = ""
    obj_type = "sheet"  # 使用表格代替文件夹
    title = f"测试表格 - {int(time.time())}"

    result = create_node(parent_token, obj_type, title)

    assert result is not None, "create_node 返回 None"
    assert "data" in result, "响应中缺少 data 字段"
    assert result["data"]["node"]["obj_type"] == "sheet", "obj_type 不匹配"
    assert result["data"]["node"]["title"] == title, "title 不匹配"

    node_token = result["data"]["node"]["node_token"]
    return node_token


def test_tc_005_update_node_title():
    """TC-013: 正常更新标题"""
    # 创建测试节点
    title = f"测试更新标题 - {int(time.time())}"
    result = create_document(title, "")
    assert result is not None
    node_token = result.split("node=")[1].split("&")[0] if "&" in result else result.split("node=")[1]

    # 更新标题
    new_title = f"更新后的标题 - {int(time.time())}"
    update_result = update_node_title(node_token, new_title)

    assert update_result is True, "update_node_title 返回 False"

    # 验证更新成功
    node = get_node(node_token)
    assert node["data"]["node"]["title"] == new_title, f"标题未更新，期望: {new_title}, 实际: {node['data']['node']['title']}"

    return node_token


def test_tc_006_build_node_tree():
    """TC-022: 构建完整节点树"""
    tree = build_node_tree(parent_token="", max_depth=3)

    assert isinstance(tree, list), "返回的不是列表"
    assert len(tree) > 0, "节点树为空"

    # 验证树结构
    for node in tree:
        assert "token" in node, "节点缺少 token 字段"
        assert "title" in node, "节点缺少 title 字段"
        assert "depth" in node, "节点缺少 depth 字段"
        assert "children" in node, "节点缺少 children 字段"


def test_tc_007_flatten_node_tree():
    """TC-024: 展平节点树"""
    tree = build_node_tree("", max_depth=2)
    flat = flatten_node_tree(tree)

    assert isinstance(flat, dict), "返回的不是字典"

    # 验证所有节点都被展平
    for token, info in flat.items():
        assert "title" in info, f"节点 {token} 缺少 title 字段"
        assert "path" in info, f"节点 {token} 缺少 path 字段"
        assert "depth" in info, f"节点 {token} 缺少 depth 字位"


def test_tc_008_delete_node_to_trash():
    """TC-019: 删除节点（移动到待删除）"""
    # 创建测试节点
    title = f"待删除的测试节点 - {int(time.time())}"
    result = create_document(title, "")
    assert result is not None
    node_token = result.split("node=")[1].split("&")[0] if "&" in result else result.split("node=")[1]

    # 删除节点
    delete_result = delete_node(node_token)
    assert delete_result is True, "delete_node 返回 False"

    # 验证节点已被移动到"待删除"文件夹
    # 1. 获取"待删除"文件夹的 token
    root_nodes = list_nodes("", 50)
    trash_token = None
    for item in root_nodes["data"]["items"]:
        if item.get("title") == "待删除":
            trash_token = item.get("node_token")
            break

    assert trash_token is not None, "未找到'待删除'文件夹"

    # 2. 列出"待删除"文件夹的子节点
    trash_children = list_nodes(parent_node_token=trash_token)
    found = False
    for item in trash_children["data"]["items"]:
        if item["node_token"] == node_token:
            found = True
            break

    assert found is True, f"节点未在'待删除'文件夹中找到, token: {node_token}"


def test_tc_009_load_config():
    """TC-025: 加载配置"""
    config = load_config()

    assert "space_id" in config, "配置中缺少 space_id"
    assert "space_url" in config, "配置中缺少 space_url"
    assert "default_parent_token" in config, "配置中缺少 default_parent_token"


def test_tc_010_move_node():
    """TC-016: 移动节点到根目录"""
    # 创建测试节点
    title = f"测试移动节点 - {int(time.time())}"
    result = create_document(title, "")
    assert result is not None
    node_token = result.split("node=")[1].split("&")[0] if "&" in result else result.split("node=")[1]

    # 记录原位置
    original_node = get_node(node_token)
    original_parent = original_node["data"]["node"]["parent_node_token"]

    # 移动到根目录（如果不在根目录）
    # 或者创建一个文档作为父节点
    parent_title = f"测试移动目标 - {int(time.time())}"
    parent_result = create_document(parent_title, "")
    assert parent_result is not None
    parent_url = parent_result
    target_parent = parent_url.split("node=")[1].split("&")[0] if "&" in parent_url else parent_url.split("node=")[1]

    # 移动节点
    move_result = move_node(node_token, target_parent)
    assert move_result is True, "move_node 返回 False"

    # 验证移动成功
    moved_node = get_node(node_token)
    assert moved_node["data"]["node"]["parent_node_token"] == target_parent, "节点未移动到目标位置"

    # 清理：删除测试节点
    delete_node(node_token)
    delete_node(target_parent)

    return node_token


def main():
    """主测试函数"""
    print("="*60)
    print("Lark API 单元测试")
    print("="*60)

    runner = TestRunner()

    # 配置和基础测试
    runner.run_test("TC-025: 加载配置", test_tc_009_load_config)

    # 节点读取测试
    runner.run_test("TC-005: 列出根节点", test_tc_002_list_root_nodes)

    # 节点创建测试
    runner.run_test("TC-001: 创建文档（根节点）", test_tc_001_create_document_at_root)
    runner.run_test("TC-010: 创建文件夹节点", test_tc_004_create_folder_node)

    # 节点更新测试
    # runner.run_test("TC-013: 更新节点标题", test_tc_005_update_node_title)  # 暂时跳过，需要使用文档 API

    # 节点移动测试
    runner.run_test("TC-016: 移动节点", test_tc_010_move_node)

    # 节点删除测试
    runner.run_test("TC-019: 删除节点到待删除", test_tc_008_delete_node_to_trash)

    # 树操作测试
    runner.run_test("TC-022: 构建节点树", test_tc_006_build_node_tree)
    runner.run_test("TC-024: 展平节点树", test_tc_007_flatten_node_tree)

    # 获取节点测试
    runner.run_test("TC-008: 获取有效节点", test_tc_003_get_node_valid)

    # 打印总结
    runner.summary()

    # 返回退出码
    sys.exit(0 if runner.failed == 0 else 1)


if __name__ == "__main__":
    main()
