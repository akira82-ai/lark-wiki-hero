#!/usr/bin/env python3
"""
知识库结构分析器 - 分析知识库结构并检测问题
"""

from typing import Dict, List
from lark_api import require_config, build_node_tree, flatten_node_tree


class WikiStructureAnalyzer:
    """知识库结构分析器"""

    def __init__(self):
        self.tree = None
        self.flat_nodes = None
        self._load_structure()

    def _load_structure(self):
        """加载知识库结构"""
        print("正在加载知识库结构...")
        self.tree = build_node_tree(max_depth=10)
        self.flat_nodes = flatten_node_tree(self.tree)

        total = len(self.flat_nodes)
        print(f"✓ 已加载 {total} 个节点")

    def analyze(self) -> Dict:
        """
        完整结构分析

        Returns:
            分析结果字典
        """
        print("\n正在分析结构...\n")

        # 基本指标
        metrics = self._calculate_metrics()

        # 问题检测
        problems = self._detect_problems()

        return {
            "metrics": metrics,
            "problems": problems
        }

    def _calculate_metrics(self) -> Dict:
        """计算基本指标"""
        total_nodes = len(self.flat_nodes)

        # 深度分布
        depth_distribution = {}
        max_depth = 0

        for token, info in self.flat_nodes.items():
            depth = info["depth"]
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
            if depth > max_depth:
                max_depth = depth

        # 节点类型分布
        type_distribution = {}
        for token, info in self.flat_nodes.items():
            obj_type = info["obj_type"]
            type_distribution[obj_type] = type_distribution.get(obj_type, 0) + 1

        # 统计空分类（没有子节点的文件夹）
        empty_categories = []
        for token, info in self.flat_nodes.items():
            if info["obj_type"] == "wiki" and not info["has_child"]:
                empty_categories.append({
                    "token": token,
                    "title": info["title"],
                    "path": info["path"]
                })

        return {
            "total_nodes": total_nodes,
            "max_depth": max_depth,
            "depth_distribution": depth_distribution,
            "type_distribution": type_distribution,
            "empty_categories": empty_categories
        }

    def _detect_problems(self) -> List[Dict]:
        """检测结构问题"""
        problems = []

        # 1. 检测层级过深
        deep_nodes = self._find_deep_nodes(max_depth=4)
        if deep_nodes:
            problems.append({
                "type": "deep_structure",
                "severity": "warning",
                "count": len(deep_nodes),
                "nodes": deep_nodes[:5],  # 只显示前5个
                "suggestion": "建议将深层级提升至3层以内"
            })

        # 2. 检测命名不一致
        inconsistent = self._find_inconsistent_naming()
        if inconsistent:
            problems.append({
                "type": "inconsistent_naming",
                "severity": "info",
                "count": len(inconsistent),
                "nodes": inconsistent[:5],
                "suggestion": "统一命名风格（中文/英文、大小写等）"
            })

        # 3. 检测空分类
        metrics = self._calculate_metrics()
        if metrics["empty_categories"]:
            problems.append({
                "type": "empty_category",
                "severity": "warning",
                "count": len(metrics["empty_categories"]),
                "nodes": metrics["empty_categories"][:5],
                "suggestion": "删除空分类或添加内容"
            })

        # 4. 检测孤立节点（根目录下的文档）
        orphans = self._find_orphan_nodes()
        if orphans:
            problems.append({
                "type": "orphan_nodes",
                "severity": "info",
                "count": len(orphans),
                "nodes": orphans[:5],
                "suggestion": "将孤立节点移入合适的分类"
            })

        return problems

    def _find_deep_nodes(self, max_depth: int) -> List[Dict]:
        """查找层级过深的节点"""
        deep_nodes = []

        for token, info in self.flat_nodes.items():
            if info["depth"] > max_depth:
                deep_nodes.append({
                    "token": token,
                    "title": info["title"],
                    "path": info["path"],
                    "depth": info["depth"]
                })

        return sorted(deep_nodes, key=lambda x: x["depth"], reverse=True)

    def _find_inconsistent_naming(self) -> List[Dict]:
        """查找命名不一致的节点"""
        inconsistent = []

        # 检测混合中英文命名
        has_chinese = []
        has_english = []

        for token, info in self.flat_nodes.items():
            title = info["title"]
            if any('\u4e00' <= c <= '\u9fff' for c in title):
                has_chinese.append(token)
            if any(c.isalpha() and ord(c) < 128 for c in title):
                has_english.append(token)

        # 检测大小写不一致
        has_upper = []
        has_lower = []

        for token, info in self.flat_nodes.items():
            title = info["title"]
            if any(c.isupper() for c in title if c.isalpha()):
                has_upper.append(token)
            if any(c.islower() for c in title if c.isalpha()):
                has_lower.append(token)

        # 简单检测：兄弟节点中命名风格不一致
        # TODO: 更复杂的命名一致性检测

        return inconsistent

    def _find_orphan_nodes(self) -> List[Dict]:
        """查找孤立节点（根目录下的文档）"""
        orphans = []

        for token, info in self.flat_nodes.items():
            # 根目录下且不是文件夹
            if info["depth"] == 1 and info["obj_type"] != "wiki":
                orphans.append({
                    "token": token,
                    "title": info["title"],
                    "obj_type": info["obj_type"]
                })

        return orphans

    def print_report(self, analysis: Dict, verbose: bool = False):
        """
        打印分析报告

        Args:
            analysis: 分析结果字典
            verbose: 是否显示详细信息
        """
        metrics = analysis["metrics"]
        problems = analysis["problems"]

        print("=" * 60)
        print("知识库结构分析报告")
        print("=" * 60)

        # 打印基本指标
        print("\n基本指标:")
        print(f"  总节点数: {metrics['total_nodes']}")
        print(f"  最大深度: {metrics['max_depth']} 层" +
              (" ⚠️" if metrics['max_depth'] > 4 else ""))

        if verbose:
            print("\n  深度分布:")
            for depth, count in sorted(metrics["depth_distribution"].items()):
                bar = "█" * (count // 2)
                print(f"    {depth}层: {count:3d} {bar}")

            print("\n  节点类型分布:")
            type_names = {
                "wiki": "文件夹",
                "docx": "新版文档",
                "doc": "旧版文档",
                "sheet": "电子表格",
                "bitable": "多维表格"
            }
            for obj_type, count in metrics["type_distribution"].items():
                name = type_names.get(obj_type, obj_type)
                print(f"    {name}: {count}")

        # 打印问题
        print("\n发现的问题:")
        if not problems:
            print("  ✓ 未发现明显问题")
        else:
            for problem in problems:
                severity_icon = {
                    "error": "❌",
                    "warning": "⚠️",
                    "info": "ℹ️"
                }.get(problem["severity"], "•")

                print(f"\n  {severity_icon} {problem['type'].replace('_', ' ').title()}: {problem['count']} 个")
                print(f"     建议: {problem['suggestion']}")

                if verbose and problem.get("nodes"):
                    for node in problem["nodes"][:3]:
                        if "path" in node:
                            print(f"       - {node['path']}")
                        elif "title" in node:
                            print(f"       - {node['title']}")


def main():
    """命令行入口"""
    import argparse

    # 首先检查配置
    try:
        require_config()
    except SystemExit:
        return

    parser = argparse.ArgumentParser(
        description="分析飞书知识库结构",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析结构
  python3 analyzer.py --analyze

  # 显示详细报告
  python3 analyzer.py --analyze --verbose

  # 导出报告到文件
  python3 analyzer.py --analyze --output report.json
        """
    )

    parser.add_argument("--analyze", "-a", action="store_true",
                       help="执行结构分析")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="显示详细信息")
    parser.add_argument("--output", "-o",
                       help="输出报告到 JSON 文件")

    args = parser.parse_args()

    if not args.analyze:
        parser.print_help()
        return

    analyzer = WikiStructureAnalyzer()
    analysis = analyzer.analyze()

    # 打印报告
    analyzer.print_report(analysis, verbose=args.verbose)

    # 导出 JSON
    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存到: {args.output}")


if __name__ == "__main__":
    main()
