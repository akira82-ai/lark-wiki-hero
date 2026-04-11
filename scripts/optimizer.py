#!/usr/bin/env python3
"""
知识库优化执行器 - 生成并执行优化计划
"""

import sys
from typing import Dict, List
from analyzer import WikiStructureAnalyzer
from lark_api import require_config, move_node, update_node_title, delete_node


class WikiOptimizer:
    """知识库优化执行器"""

    def __init__(self):
        self.analyzer = WikiStructureAnalyzer()
        self.rollback_log = []

    def generate_optimization_plan(self, analysis: Dict = None) -> Dict:
        """
        生成优化计划

        Args:
            analysis: 分析结果（如果为 None 则重新分析）

        Returns:
            优化计划字典
        """
        if analysis is None:
            analysis = self.analyzer.analyze()

        problems = analysis["problems"]
        actions = []

        for problem in problems:
            if problem["type"] == "deep_structure":
                # 生成扁平化操作
                for node in problem["nodes"]:
                    actions.append({
                        "type": "flatten",
                        "node_token": node["token"],
                        "title": node["title"],
                        "current_depth": node["depth"],
                        "reason": f"层级过深 ({node['depth']}层)",
                        "suggestion": "提升至更合适的父节点"
                    })

            elif problem["type"] == "empty_category":
                # 生成删除操作
                for node in problem["nodes"]:
                    actions.append({
                        "type": "delete",
                        "node_token": node["token"],
                        "title": node["title"],
                        "reason": "空分类",
                        "suggestion": "删除空文件夹"
                    })

            elif problem["type"] == "inconsistent_naming":
                # 生成重命名操作
                for node in problem["nodes"]:
                    actions.append({
                        "type": "rename",
                        "node_token": node["token"],
                        "title": node.get("title", ""),
                        "reason": "命名不一致",
                        "suggestion": "统一命名风格"
                    })

            elif problem["type"] == "orphan_nodes":
                # 生成移动操作
                for node in problem["nodes"]:
                    actions.append({
                        "type": "move_to_category",
                        "node_token": node["token"],
                        "title": node["title"],
                        "reason": "孤立节点",
                        "suggestion": "移入合适的分类"
                    })

        return {
            "actions": actions,
            "summary": {
                "total": len(actions),
                "by_type": self._group_actions_by_type(actions)
            },
            "risk_assessment": self._assess_risks(actions)
        }

    def _group_actions_by_type(self, actions: List[Dict]) -> Dict[str, int]:
        """按类型分组操作"""
        groups = {}
        for action in actions:
            action_type = action["type"]
            groups[action_type] = groups.get(action_type, 0) + 1
        return groups

    def _assess_risks(self, actions: List[Dict]) -> str:
        """评估操作风险"""
        risk_level = "low"

        # 有删除操作
        if any(a["type"] == "delete" for a in actions):
            risk_level = "high"

        # 有大量移动操作
        move_count = sum(1 for a in actions if a["type"] in ["move", "move_to_category", "flatten"])
        if move_count > 10:
            risk_level = "medium"

        return risk_level

    def print_plan(self, plan: Dict):
        """打印优化计划"""
        print("=" * 60)
        print("知识库优化计划")
        print("=" * 60)

        print(f"\n总操作数: {plan['summary']['total']}")

        print("\n操作分类:")
        for action_type, count in plan["summary"]["by_type"].items():
            print(f"  - {action_type}: {count}")

        risk_icons = {"low": "🟢", "medium": "🟡", "high": "🔴"}
        risk_names = {"low": "低", "medium": "中", "high": "高"}
        risk = plan["risk_assessment"]
        print(f"\n风险评估: {risk_icons[risk]} {risk_names[risk]}")

        if plan["actions"]:
            print("\n详细操作列表:")
            for i, action in enumerate(plan["actions"][:10], 1):
                print(f"\n  {i}. {action['type'].upper()}")
                print(f"     节点: {action.get('title', 'N/A')}")
                print(f"     原因: {action['reason']}")
                print(f"     建议: {action['suggestion']}")

            if len(plan["actions"]) > 10:
                print(f"\n  ... 还有 {len(plan['actions']) - 10} 个操作")

    def execute_plan(self, plan: Dict, dry_run: bool = True) -> Dict:
        """
        执行优化计划

        Args:
            plan: 优化计划
            dry_run: 是否预览模式（不实际执行）

        Returns:
            执行结果
        """
        print("=" * 60)
        print("执行优化" if not dry_run else "预览模式（不会实际执行）")
        print("=" * 60)

        results = {
            "total": len(plan["actions"]),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }

        for i, action in enumerate(plan["actions"], 1):
            print(f"\n[{i}/{results['total']}] {action['type']}: {action.get('title', 'N/A')}")

            if dry_run:
                print(f"  [预览] {action['suggestion']}")
                results["skipped"] += 1
                continue

            # 实际执行操作
            result = self._execute_action(action)
            results["details"].append(result)

            if result["status"] == "success":
                print(f"  ✓ {action['suggestion']}")
                results["success"] += 1
                # 记录到回滚日志
                self.rollback_log.append({
                    "action": action,
                    "result": result
                })
            elif result["status"] == "skipped":
                print(f"  ⊘ {result['message']}")
                results["skipped"] += 1
            else:
                print(f"  ✗ {result['message']}")
                results["failed"] += 1

        # 打印总结
        print("\n" + "=" * 60)
        print("执行总结")
        print("=" * 60)
        print(f"总数: {results['total']}")
        print(f"成功: {results['success']} ✓")
        print(f"失败: {results['failed']} ✗")
        print(f"跳过: {results['skipped']} ⊘")

        return results

    def _execute_action(self, action: Dict) -> Dict:
        """
        执行单个操作

        Args:
            action: 操作字典

        Returns:
            执行结果
        """
        action_type = action["type"]
        node_token = action["node_token"]

        # TODO: 实现各种操作的具体逻辑
        # 目前返回 skipped 状态，因为需要用户确认目标位置等参数

        if action_type == "delete":
            # 删除空分类
            # success = delete_node(node_token)
            return {
                "status": "skipped",
                "message": "删除操作需要手动确认"
            }

        elif action_type == "rename":
            # 重命名
            # new_title = self._generate_consistent_name(action["title"])
            # success = update_node_title(node_token, new_title)
            return {
                "status": "skipped",
                "message": "重命名操作需要指定新名称"
            }

        elif action_type in ["move", "move_to_category", "flatten"]:
            # 移动节点
            # 需要确定目标父节点
            return {
                "status": "skipped",
                "message": "移动操作需要指定目标位置"
            }

        return {
            "status": "skipped",
            "message": "未知操作类型"
        }


def main():
    """命令行入口"""
    import argparse

    # 首先检查配置
    try:
        require_config()
    except SystemExit:
        return

    parser = argparse.ArgumentParser(
        description="优化飞书知识库结构",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成优化计划
  python3 optimizer.py --plan

  # 执行优化（预览模式）
  python3 optimizer.py --execute --dry-run

  # 执行优化（实际执行）
  python3 optimizer.py --execute
        """
    )

    parser.add_argument("--plan", "-p", action="store_true",
                       help="生成优化计划")
    parser.add_argument("--execute", "-e", action="store_true",
                       help="执行优化")
    parser.add_argument("--dry-run", "-n", action="store_true",
                       help="预览模式，不实际执行")

    args = parser.parse_args()

    optimizer = WikiOptimizer()

    # 生成计划
    if args.plan or args.execute:
        plan = optimizer.generate_optimization_plan()
        optimizer.print_plan()

        if not args.execute:
            return

        # 询问是否继续
        if args.dry_run:
            print("\n预览模式，不会实际执行")
        else:
            response = input("\n是否执行此计划？(yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("已取消")
                return

        # 执行计划
        optimizer.execute_plan(plan, dry_run=args.dry_run)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
