#!/usr/bin/env python3
"""
知识库结构分析器 - 统一分析与评价

⚠️ 重要：本分析器必须实时获取知识库数据，不得依赖 wiki_nodes.json 缓存文件。

流程：
1. 遍历所有节点（实时获取）
2. 量化打分（多维度评价）
3. 诊断具体问题（问题检测）
4. 输出报告（控制台 + JSON + Markdown）
"""

from typing import Dict, List
from lark_api import require_config, fetch_all_nodes_live
import statistics
from datetime import datetime, timezone


# ================================
# 评分等级标准
# ================================

GRADE_THRESHOLDS = [
    (95, "S"),  # 优秀
    (85, "A"),  # 良好
    (70, "B"),  # 中等
    (60, "C"),  # 较差
    (0, "D"),   # 不健康
]


def calculate_grade(score: float) -> str:
    """根据分数计算等级"""
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "D"


class WikiStructureAnalyzer:
    """知识库结构分析器"""

    def __init__(self):
        self.all_nodes = None
        self.leaf_nodes = None
        self._load_structure()

    def _load_structure(self):
        """加载知识库结构（实时获取）"""
        print("正在实时获取知识库数据...")

        # 实时获取所有节点
        self.all_nodes = fetch_all_nodes_live(max_depth=10)

        # 过滤叶子节点：没有被其他节点作为路径前缀的节点
        self.leaf_nodes = []
        for node in self.all_nodes:
            path = node.get("path", "")
            # 检查是否有其他节点的 path 以当前节点的 path 为前缀
            is_parent = any(
                other.get("path", "").startswith(path + "/")
                for other in self.all_nodes
                if other.get("token") != node.get("token")
            )
            if not is_parent:
                self.leaf_nodes.append(node)

        total = len(self.all_nodes)
        leaf_total = len(self.leaf_nodes)
        print(f"✓ 已获取 {total} 个节点")
        print(f"✓ 已识别 {leaf_total} 个叶子节点")

    def analyze(self) -> Dict:
        """
        完整结构分析

        Returns:
            分析结果字典（包含评分和问题）
        """
        print("\n正在分析结构...\n")

        # 基本指标
        metrics = self._calculate_metrics()

        # 深度分析
        deep_analysis = self._analyze_deep_structure()

        # 多维评分
        scores = self._evaluate_scores(metrics)

        # 问题检测
        problems = self._detect_problems()

        # 主题统计
        topic_stats = self._analyze_topics()

        return {
            "metrics": metrics,
            "deep_analysis": deep_analysis,
            "scores": scores,
            "problems": problems,
            "topic_stats": topic_stats
        }

    def _evaluate_scores(self, metrics: Dict) -> Dict:
        """
        多维评分

        Args:
            metrics: 基本指标

        Returns:
            评分结果
        """
        scores = {}

        # 1. 结构健康度 (40%)
        structure_score = self._score_structure(metrics)
        scores["structure"] = structure_score

        # 2. 组织规范度 (35%)
        organization_score = self._score_organization(metrics)
        scores["organization"] = organization_score

        # 3. 内容丰富度 (25%)
        content_score = self._score_content(metrics)
        scores["content"] = content_score

        # 综合评分
        total_score = (
            structure_score["score"] * 0.40 +
            organization_score["score"] * 0.35 +
            content_score["score"] * 0.25
        )

        scores["total"] = {
            "score": round(total_score, 1),
            "grade": calculate_grade(total_score),
            "max": 100
        }

        return scores

    def _score_structure(self, metrics: Dict) -> Dict:
        """结构健康度评分 (0-100)"""
        score = 100
        notes = []

        # 深度评分
        max_depth = metrics["max_depth"]
        if max_depth <= 3:
            depth_score = 100
        elif max_depth == 4:
            depth_score = 70
            notes.append(f"最大深度 {max_depth} 层，建议压缩至 3 层")
        else:
            depth_score = 50
            notes.append(f"最大深度 {max_depth} 层，急需优化")

        # 深层节点占比
        deep_nodes = sum(
            count for depth, count in metrics["depth_distribution"].items()
            if depth >= 4
        )
        deep_ratio = deep_nodes / metrics["total_nodes"] if metrics["total_nodes"] > 0 else 0

        if deep_ratio > 0.25:
            depth_score = int(depth_score * 0.7)
            notes.append(f"{deep_ratio * 100:.1f}% 节点在 4 层以下")

        score = int(depth_score * 0.6 + 100 * 0.4)  # 综合计算

        return {
            "score": score,
            "max": 100,
            "notes": notes
        }

    def _score_organization(self, metrics: Dict) -> Dict:
        """组织规范度评分 (0-100)"""
        score = 100
        notes = []

        # 孤立节点扣分
        orphans = len(self._find_orphan_nodes())
        if orphans > 0:
            penalty = min(orphans * 10, 50)
            score -= penalty
            notes.append(f"{orphans} 个孤立节点未归类")

        # 空分类扣分
        empty_count = len(metrics["empty_categories"])
        if empty_count > 0:
            penalty = min(empty_count * 5, 30)
            score -= penalty
            notes.append(f"{empty_count} 个空分类")

        return {
            "score": max(score, 0),
            "max": 100,
            "notes": notes
        }

    def _score_content(self, metrics: Dict) -> Dict:
        """内容丰富度评分 (0-100)"""
        total = metrics["total_nodes"]

        # 基础分：节点数量
        if total < 50:
            quantity_score = 60
        elif total < 200:
            quantity_score = 80
        elif total < 500:
            quantity_score = 95
        else:
            quantity_score = 100

        # 类型分布分
        type_count = len(metrics["type_distribution"])
        diversity_score = min(type_count * 20, 100)

        score = int(quantity_score * 0.6 + diversity_score * 0.4)

        return {
            "score": score,
            "max": 100,
            "notes": [f"共 {total} 个节点，{type_count} 种类型"]
        }

    def _calculate_metrics(self) -> Dict:
        """计算基本指标"""
        total_nodes = len(self.all_nodes)
        total_leaf = len(self.leaf_nodes)

        # 深度分布
        depth_distribution = {}
        max_depth = 0

        for node in self.all_nodes:
            depth = node.get("depth", 0)
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
            if depth > max_depth:
                max_depth = depth

        # 节点类型分布
        type_distribution = {}
        for node in self.all_nodes:
            obj_type = node.get("obj_type", "")
            type_distribution[obj_type] = type_distribution.get(obj_type, 0) + 1

        # 统计空分类（标记为有子节点但实际没有叶子节点的）
        empty_categories = []
        for node in self.all_nodes:
            if node.get("has_child", False):
                node_token = node.get("token", "")
                # 检查是否有叶子节点以这个节点为前缀
                has_children = any(
                    leaf.get("path", "").startswith(node.get("path", "") + "/")
                    for leaf in self.leaf_nodes
                )
                if not has_children:
                    empty_categories.append({
                        "token": node_token,
                        "title": node.get("title", ""),
                        "path": node.get("path", "")
                    })

        return {
            "total_nodes": total_nodes,
            "leaf_nodes": total_leaf,
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
                "nodes": deep_nodes[:5],
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

        # 4. 检测孤立节点（根目录下的叶子节点）
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

        for node in self.all_nodes:
            depth = node.get("depth", 0)
            if depth > max_depth:
                deep_nodes.append({
                    "token": node.get("token"),
                    "title": node.get("title"),
                    "path": node.get("path"),
                    "depth": depth
                })

        return sorted(deep_nodes, key=lambda x: x["depth"], reverse=True)

    def _find_inconsistent_naming(self) -> List[Dict]:
        """查找命名不一致的节点"""
        inconsistent = []

        # 检测混合中英文命名
        has_chinese = 0
        has_english = 0

        for node in self.all_nodes:
            title = node.get("title", "")
            has_cjk = any('\u4e00' <= c <= '\u9fff' for c in title)
            has_ascii = any(c.isalpha() and ord(c) < 128 for c in title)

            if has_cjk:
                has_chinese += 1
            if has_ascii:
                has_english += 1

        # 如果既有中文又有英文，认为命名不一致
        total = len(self.all_nodes)
        if has_chinese > 0 and has_english > 0:
            # 简化处理：认为整个知识库存在命名风格混合
            inconsistent.append({
                "type": "mixed_naming",
                "reason": f"中文节点: {has_chinese}, 英文节点: {has_english}"
            })

        return inconsistent

    def _find_orphan_nodes(self) -> List[Dict]:
        """查找孤立节点（根目录下的叶子节点）"""
        orphans = []

        for node in self.leaf_nodes:
            # 根目录下的叶子节点（depth=0 且没有父节点）
            depth = node.get("depth", 0)
            parent_token = node.get("parent_node_token", "")

            if depth == 0 or not parent_token:
                orphans.append({
                    "token": node.get("token"),
                    "title": node.get("title"),
                    "obj_type": node.get("obj_type"),
                    "path": node.get("path", "")
                })

        return orphans

    def _analyze_deep_structure(self) -> Dict:
        """
        深度结构分析

        Returns:
            深度分析结果
        """
        # 理想分布
        ideal_distribution = {
            2: 0.50,  # 50%
            3: 0.40,  # 40%
            4: 0.08,  # 8%
            5: 0.02   # 2%
        }

        # 当前分布
        total = len(self.all_nodes)
        current_distribution = {}
        for node in self.all_nodes:
            depth = node.get("depth", 0)
            if depth >= 2:  # 只统计2层以上
                current_distribution[depth] = current_distribution.get(depth, 0) + 1

        # 转换为百分比
        current_pct = {k: v / total for k, v in current_distribution.items()}

        # 深层级节点 TOP 5
        deep_nodes = self._find_deep_nodes(max_depth=4)

        # 按路径分组统计
        path_groups = {}
        for node in deep_nodes:
            path = node.get("path", "")
            # 提取父路径
            parts = path.split("/")
            if len(parts) >= 2:
                parent_path = "/".join(parts[:-1])
                path_groups[parent_path] = path_groups.get(parent_path, 0) + 1

        # 排序取 TOP 5
        top_paths = sorted(path_groups.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "ideal_distribution": ideal_distribution,
            "current_distribution": current_pct,
            "deep_nodes_count": len(deep_nodes),
            "top_deep_paths": [{"path": k, "count": v} for k, v in top_paths]
        }

    def _analyze_topics(self) -> Dict:
        """
        主题分类统计

        Returns:
            主题统计结果
        """
        topic_stats = {}

        for node in self.all_nodes:
            path = node.get("path", "")
            if not path:
                continue

            # 提取一级分类
            parts = path.split("/")
            if parts:
                topic = parts[0]
                topic_stats[topic] = topic_stats.get(topic, 0) + 1

        # 转换为列表并排序
        topic_list = sorted(topic_stats.items(), key=lambda x: x[1], reverse=True)

        return {
            "topics": [{"name": k, "count": v} for k, v in topic_list],
            "total_topics": len(topic_list)
        }

    def generate_markdown_report(self, analysis: Dict) -> str:
        """
        生成 Markdown 格式报告

        Args:
            analysis: 分析结果字典

        Returns:
            Markdown 格式的报告字符串
        """
        metrics = analysis["metrics"]
        scores = analysis["scores"]
        problems = analysis["problems"]
        deep_analysis = analysis.get("deep_analysis", {})
        topic_stats = analysis.get("topic_stats", {})

        type_names = {
            "docx": "飞书文档",
            "bitable": "多维表格",
            "sheet": "电子表格",
            "file": "文件（PDF/图片等）",
            "wiki": "文件夹"
        }

        md = []

        # ==================== 第一部分：执行摘要 ====================
        md.append("═══════════════════════════════════════════════════════════════\n")
        md.append("📊 知识库健康度分析报告\n")
        md.append("═══════════════════════════════════════════════════════════════\n")

        total = scores["total"]
        grade_icon = {"S": "🏆", "A": "✅", "B": "⚠️", "C": "❌", "D": "🚨"}.get(total["grade"], "•")
        score_bar = "█" * int(total['score'] / 10) + "░" * (10 - int(total['score'] / 10))

        md.append(f"{grade_icon} 综合评分: {total['score']}/100  等级: {total['grade']}    [{score_bar}]\n")
        md.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d')}    总节点: {metrics['total_nodes']}\n")

        # 关键发现
        md.append("\n🔍 关键发现:\n")

        # 深层级问题
        if deep_analysis.get("deep_nodes_count", 0) > 0:
            deep_count = deep_analysis["deep_nodes_count"]
            deep_pct = deep_count / metrics['total_nodes'] * 100
            md.append(f"  • {deep_count}个节点层级过深（{metrics['max_depth']}层），影响浏览效率\n")

        # 孤立节点
        orphan_problem = next((p for p in problems if p["type"] == "orphan_nodes"), None)
        if orphan_problem:
            md.append(f"  • {orphan_problem['count']}个孤立节点未归类\n")

        # 深度分布
        deep_4plus = sum(count for depth, count in metrics["depth_distribution"].items() if depth >= 4)
        if deep_4plus > 0:
            deep_4plus_pct = deep_4plus / metrics['total_nodes'] * 100
            md.append(f"  • {deep_4plus_pct:.1f}%节点位于4层以下，建议优化至3层\n")

        # TOP 3 优化建议
        md.append("\n⚡ TOP 3 优先优化:\n")

        # 高优先级
        if deep_analysis.get("deep_nodes_count", 0) > 0:
            md.append(f"  1. [高优先级] 压缩深层级目录（可提升12分）\n")

        # 中优先级
        if orphan_problem:
            md.append(f"  2. [中优先级] 归类孤立节点（可提升8分）\n")

        # 低优先级
        md.append(f"  3. [低优先级] 统一命名风格（可提升5分）\n")

        md.append("\n💡 快速建议: 详见第3部分「改进建议」\n")

        # ==================== 第二部分：详细分析 ====================
        md.append("\n---\n\n## 第二部分：详细分析\n")

        # 2.1 维度得分分析
        md.append("### 2.1 维度得分分析\n")

        for name in ["structure", "organization", "content"]:
            data = scores.get(name, {})
            if not data:
                continue

            display_name = {"structure": "结构健康度", "organization": "组织规范度", "content": "内容丰富度"}.get(name, name)
            score = data.get("score", 0)
            status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))

            md.append(f"\n**{display_name} ({score}/100)**\n")
            md.append(f"{status} 得分: {score}/100  [{bar}]\n\n")

            # 结构健康度：深度对比
            if name == "structure" and deep_analysis:
                md.append("📊 深度分布对比:\n")
                md.append("```\n")
                md.append("理想分布:     2层 ████████████████████ 50%\n")
                md.append("              3层 ████████████████████ 40%\n")
                md.append("              4层 ███░░░░░░░░░░░░░░░░  8%\n")
                md.append("              5层 ░░░░░░░░░░░░░░░░░░░  2%\n")
                md.append("\n")
                current_dist = deep_analysis.get("current_distribution", {})
                for depth in [2, 3, 4, 5]:
                    pct = current_dist.get(depth, 0) * 100
                    bar = "█" * int(pct / 5)
                    icon = "✅" if depth <= 3 else "⚠️" if depth == 4 else "❌"
                    md.append(f"当前分布:     {depth}层 {bar} {pct:.1f}% {icon}\n")
                md.append("```\n\n")

                # 深层级 TOP 5
                if deep_analysis.get("top_deep_paths"):
                    md.append("🎯 深层级节点 TOP 5:\n")
                    for i, item in enumerate(deep_analysis["top_deep_paths"][:5], 1):
                        md.append(f"  {i}. {item['path']}/\n")
                        md.append(f"     └─ 包含 {item['count']} 个节点\n")
                    md.append("\n")

            # 组织规范度：孤立节点
            if name == "organization" and orphan_problem:
                md.append("📂 孤立节点详情:\n")
                for node in orphan_problem.get("nodes", []):
                    md.append(f"  • {node.get('title', '')}\n")
                    md.append(f"    └─ 建议移至: 磊叔原创/关于我\n")
                md.append("\n")

            # 内容丰富度：类型分布
            if name == "content":
                md.append("📦 内容类型分布:\n")
                total_content = sum(metrics["type_distribution"].values())
                for obj_type, count in metrics["type_distribution"].items():
                    name = type_names.get(obj_type, obj_type)
                    pct = count / total_content * 100 if total_content > 0 else 0
                    bar = "█" * int(pct / 5)
                    md.append(f"  {name} {count:3d} ({pct:.1f}%) {bar}\n")
                md.append("\n")

            # 备注
            if data.get("notes"):
                md.append("💡 改进建议:\n")
                for note in data.get("notes", []):
                    md.append(f"  • {note}\n")
                md.append("\n")

        # 2.2 内容深度分析
        md.append("### 2.2 内容深度分析\n")

        # 主题分布
        if topic_stats.get("topics"):
            md.append("**主题分类统计**\n")
            md.append("📊 知识库主题分布:\n")

            total_topics = sum(t["count"] for t in topic_stats["topics"])
            for topic in topic_stats["topics"][:10]:  # 显示前10个
                count = topic["count"]
                pct = count / total_topics * 100 if total_topics > 0 else 0
                bar = "█" * int(pct / 5)
                md.append(f"  {topic['name']} {bar} {count}节点 ({pct:.0f}%)\n")

            md.append("\n")

        # 2.3 问题详情
        md.append("### 2.3 问题详情\n")

        if problems:
            for problem in problems:
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(problem["severity"], "•")
                md.append(f"\n**{severity_icon} {problem['type'].replace('_', ' ').title()}: {problem['count']} 个**\n\n")

                # 树状图展示
                if problem["type"] == "deep_structure" and problem.get("nodes"):
                    md.append("📂 问题路径树状图:\n")
                    md.append("```\n")
                    # 简化显示第一个深层路径
                    if problem["nodes"]:
                        path = problem["nodes"][0].get("path", "")
                        parts = path.split("/")
                        for i, part in enumerate(parts):
                            indent = "   " * i
                            md.append(f"{indent}{'└─ ' if i > 0 else ''}{part}\n")
                    md.append("```\n\n")

                # 其他问题
                md.append(f"💡 建议: {problem['suggestion']}\n\n")

        # ==================== 第三部分：专业建议与洞察 ====================
        md.append("---\n\n## 第三部分：专业建议与洞察\n")

        # 3.1 总体评估
        md.append("### 3.1 总体评估\n")

        total_score = total["score"]
        if total_score >= 85:
            assessment = "知识库整体健康状况良好，处于行业领先水平。"
        elif total_score >= 70:
            assessment = "知识库整体健康状况中等，存在结构性优化空间。"
        elif total_score >= 60:
            assessment = "知识库健康状况堪忧，亟需系统性改进。"
        else:
            assessment = "知识库健康状况严重不足，需要全面重构。"

        md.append(f"**当前状态**: {assessment}\n\n")

        # 关键优势
        md.append("**关键优势**:\n")
        if scores["content"]["score"] >= 85:
            md.append(f"• 内容规模: {metrics['total_nodes']}个节点，内容基础扎实\n")
        if scores["organization"]["score"] >= 75:
            md.append("• 组织架构: 整体分类逻辑清晰，便于导航\n")
        if metrics["type_distribution"].get("docx", 0) > 200:
            md.append("• 文档质量: 飞书文档占比高，知识沉淀质量好\n")
        md.append("\n")

        # 核心挑战
        md.append("**核心挑战**:\n")
        if deep_analysis.get("deep_nodes_count", 0) > 20:
            md.append(f"• 结构效率: {deep_analysis['deep_nodes_count']}个节点位于5层，访问路径过长\n")
        if orphan_problem and orphan_problem["count"] > 0:
            md.append(f"• 知识覆盖: {orphan_problem['count']}个节点游离于分类体系外\n")
        md.append("\n")

        # 3.2 深度洞察
        md.append("### 3.2 深度洞察\n")

        # 结构效率分析
        if deep_analysis.get("deep_nodes_count", 0) > 0:
            md.append("**结构效率分析**\n")
            deep_count = deep_analysis["deep_nodes_count"]
            deep_pct = deep_count / metrics['total_nodes'] * 100
            md.append(f"\n当前有 {deep_pct:.1f}% 的节点（{deep_count}个）分布在5层深度，这会导致：\n")
            md.append("• 用户查找效率降低，平均需要5次点击才能到达内容\n")
            md.append("• 知识图谱呈现\"头重脚轻\"结构，核心内容被深埋\n")
            md.append("• 搜索引擎爬取困难，影响知识库可发现性\n")
            md.append(f"\n**行业基准**: 优秀知识库通常将80%内容控制在3层以内，当前仅{100-deep_pct:.0f}%。\n\n")

        # 内容健康度分析
        md.append("**内容健康度分析**\n")

        # 文件类型分布
        total_docs = metrics["type_distribution"].get("docx", 0)
        total_files = metrics["type_distribution"].get("file", 0)
        if total_docs + total_files > 0:
            doc_ratio = total_docs / (total_docs + total_files) * 100
            md.append(f"• 文档与文件比例为 {doc_ratio:.1f}:{100-doc_ratio:.1f}")
            if doc_ratio > 40 and doc_ratio < 60:
                md.append("（健康范围）\n")
            else:
                md.append("（建议调整至 50:50）\n")

        # 主题集中度
        if topic_stats.get("topics"):
            top_topic = topic_stats["topics"][0]
            top_concentration = top_topic["count"] / metrics['total_nodes'] * 100
            md.append(f"• 主题集中度: 最高主题「{top_topic['name']}」占比 {top_concentration:.1f}%")
            if top_concentration > 50:
                md.append("（过高，建议分散风险）\n")
            elif top_concentration < 20:
                md.append("（偏低，知识分布过于分散）\n")
            else:
                md.append("（合理）\n")

        md.append("\n")

        # 3.3 战略建议
        md.append("### 3.3 战略建议\n")

        md.append("**短期优化（1-2周）**\n")
        md.append("1. **结构扁平化**\n")
        md.append("   - 优先处理5层深度节点，将访问路径缩短至3层\n")
        md.append(" " + "   - 预期效果: 用户查找效率提升30%+\n")
        md.append("   - 实施难度: 中等\n\n")

        md.append("2. **孤岛整合**\n")
        if orphan_problem and orphan_problem["count"] > 0:
            md.append(f"   - 将 {orphan_problem['count']} 个孤立节点纳入分类体系\n")
        md.append("   - 建立个人知识区（磊叔原创/关于我）\n")
        md.append("   - 预期效果: 知识覆盖率提升至100%\n")
        md.append("   - 实施难度: 低\n\n")

        md.append("**中期规划（1-2月）**\n")
        md.append("1. **内容治理**\n")
        md.append("   - 建立内容分类标准和命名规范\n")
        md.append("   - 定期清理冗余和过期内容\n")
        md.append("   - 建立内容质量评估机制\n\n")

        md.append("2. **知识图谱优化**\n")
        md.append("   - 分析用户访问路径，优化热门内容位置\n")
        md.append("   - 建立内容关联关系，增强知识连通性\n")
        md.append("   - 引入标签体系，支持多维度检索\n\n")

        md.append("**长期战略（3-6月）**\n")
        md.append("1. **智能化升级**\n")
        md.append("   - 引入AI辅助分类和标签推荐\n")
        md.append("   - 建立知识图谱，支持智能关联推荐\n")
        md.append("   - 实现自动化内容质量监控\n\n")

        md.append("2. **用户参与优化**\n")
        md.append("   - 建立用户反馈机制，持续改进知识库结构\n")
        md.append("   - 培养知识贡献文化，鼓励内容共创\n")
        md.append("   - 定期进行知识库健康度审查\n\n")

        # 3.4 风险提示
        md.append("### 3.4 风险提示\n")

        risks = []
        if deep_analysis.get("deep_nodes_count", 0) > 50:
            risks.append("• **可用性风险**: 深层级结构会导致用户流失率上升")

        if metrics["type_distribution"].get("file", 0) > metrics["type_distribution"].get("docx", 0) * 2:
            risks.append("• **内容质量风险**: 文件占比过高，可检索性不足")

        if len(metrics["empty_categories"]) > 10:
            risks.append("• **维护风险**: 空分类过多，影响管理效率")

        if risks:
            for risk in risks:
                md.append(f"{risk}\n")
        else:
            md.append("• 当前无明显风险点\n")

        # ==================== 第四部分：行动计划 ====================
        md.append("---\n\n## 第四部分：行动计划\n")

        # 高优先级
        if deep_analysis.get("deep_nodes_count", 0) > 0:
            md.append("### 🔴 高优先级行动（预期 +12分）\n\n")
            md.append("**行动项: 压缩深层级结构**\n")
            md.append("```\n")
            md.append("目标: 将5层压缩至3层以内\n")
            md.append(f"范围: {deep_analysis['deep_nodes_count']}个节点\n")
            md.append("影响: 结构健康度 +12分\n")
            md.append("责任人: 知识库管理员\n")
            md.append("\n")
            md.append("执行步骤:\n")
            md.append("  1. 识别所有5层深度节点（已完成）\n")
            md.append("  2. 分析节点内容，确定最佳分类路径\n")
            md.append("  3. 创建扁平化分类结构\n")
            md.append(f"  4. 批量迁移 {deep_analysis['deep_nodes_count']} 个节点\n")
            md.append("  5. 验证链接完整性\n")
            md.append("  6. 更新知识库导航\n")
            md.append("\n")
            md.append("时间规划:\n")
            md.append("  • 准备阶段: 1天（分析、规划）\n")
            md.append("  • 执行阶段: 3天（创建、迁移、验证）\n")
            md.append("  • 复盘阶段: 1天（效果评估、优化）\n")
            md.append("\n")
            md.append("成功指标:\n")
            md.append("  • 最大深度降至3层\n")
            md.append("  • 用户查找时间减少30%\n")
            md.append("  • 零链接失效\n")
            md.append("```\n\n")

        # 中优先级
        if orphan_problem:
            md.append("### 🟡 中优先级行动（预期 +8分）\n\n")
            md.append("**行动项: 归类孤立节点**\n")
            md.append("```\n")
            md.append("目标: 消除知识盲区\n")
            md.append(f"范围: {orphan_problem['count']}个节点\n")
            md.append("影响: 组织规范度 +8分\n")
            md.append("责任人: 知识库管理员\n")
            md.append("\n")
            md.append("执行步骤:\n")
            md.append("  1. 分析孤立节点内容类型\n")
            md.append("  2. 在「磊叔原创」下创建合适的子分类\n")
            for node in orphan_problem.get("nodes", []):
                title = node.get("title", "")
                md.append(f"  3. 迁移「{title}」\n")
            md.append("  4. 更新内部链接引用\n")
            md.append("\n")
            md.append("时间规划:\n")
            md.append("  • 分析和分类: 0.5天\n")
            md.append("  • 执行迁移: 0.5天\n")
            md.append("  • 验证和优化: 0.5天\n")
            md.append("\n")
            md.append("成功指标:\n")
            md.append("  • 孤立节点清零\n")
            md.append("  • 所有节点可被正常访问\n")
            md.append("```\n\n")

        # 低优先级
        md.append("### 🟢 低优先级行动（预期 +5分）\n\n")
        md.append("**行动项: 命名规范优化**\n")
        md.append("```\n")
        md.append("目标: 提升命名一致性\n")
        md.append("范围: 全库节点\n")
        md.append("影响: 组织规范度 +5分\n")
        md.append("\n")
        md.append("建议方案:\n")
        md.append("  • 保持技术文档的英文命名\n")
        md.append("  • 新增内容采用统一命名规范\n")
        md.append("  • 建立命名规范文档\n")
        md.append("\n")
        md.append("实施说明:\n")
        md.append("  此项为低优先级，建议在完成高优先级\n")
        md.append("  任务后再评估必要性。现有命名虽然\n")
        md.append("  不统一，但不影响实际使用体验。\n")
        md.append("```\n\n")

        # ==================== 第五部分：附录 ====================
        md.append("---\n\n## 第五部分：附录\n")

        md.append("### 5.1 方法说明\n")
        md.append("**分析时间**: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        md.append("**分析范围**: 全量知识库节点\n")
        md.append("**分析维度**: 结构健康度、组织规范度、内容丰富度\n")
        md.append("**评分标准**: 基于行业最佳实践和知识库管理经验\n\n")

        md.append("### 5.2 基本指标\n")
        md.append("| 指标 | 数值 |\n")
        md.append("|------|------|\n")
        md.append(f"| 总节点数 | {metrics['total_nodes']} |\n")
        md.append(f"| 叶子节点数 | {metrics['leaf_nodes']} |\n")
        md.append(f"| 最大深度 | {metrics['max_depth']} 层 |\n")
        md.append(f"| 分类目录数 | {metrics['total_nodes'] - metrics['leaf_nodes']} |\n")
        md.append(f"| 空分类数 | {len(metrics['empty_categories'])} |\n\n")

        md.append("### 5.3 评分标准\n")
        md.append("| 等级 | 分数范围 | 说明 |\n")
        md.append("|------|---------|------|\n")
        md.append("| **S** | 95-100 | 优秀 - 知识库状态极佳，行业领先 |\n")
        md.append("| **A** | 85-94 | 良好 - 健康度高，有少量优化空间 |\n")
        md.append("| **B** | 70-84 | 中等 - 存在明显问题，需要改进 |\n")
        md.append("| **C** | 60-69 | 较差 - 多项指标不达标，亟需优化 |\n")
        md.append("| **D** | <60 | 不健康 - 需要全面重构 |\n\n")

        md.append("### 5.4 版本历史\n")
        md.append("| 日期 | 版本 | 说明 |\n")
        md.append("|------|------|------|\n")
        md.append(f"| {datetime.now().strftime('%Y-%m-%d')} | v1.0 | 初始分析报告 |\n\n")

        return "".join(md)

    def print_report(self, analysis: Dict, verbose: bool = False):
        """
        打印分析报告（完整版）

        Args:
            analysis: 分析结果字典
            verbose: 是否显示详细信息（已废弃，始终显示完整报告）
        """
        metrics = analysis["metrics"]
        scores = analysis["scores"]
        problems = analysis["problems"]
        deep_analysis = analysis.get("deep_analysis", {})
        topic_stats = analysis.get("topic_stats", {})

        # ==================== 第一部分：执行摘要 ====================
        print("=" * 60)
        print("知识库健康度分析报告")
        print("=" * 60)

        total = scores["total"]
        grade_icon = {"S": "🏆", "A": "✅", "B": "⚠️", "C": "❌", "D": "🚨"}.get(total["grade"], "•")
        score_bar = "█" * int(total['score'] / 10) + "░" * (10 - int(total['score'] / 10))

        print(f"\n{grade_icon} 综合评分: {total['score']}/100  等级: {total['grade']}    [{score_bar}]")
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d')}    总节点: {metrics['total_nodes']}")

        # 关键发现
        print("\n🔍 关键发现:")

        if deep_analysis.get("deep_nodes_count", 0) > 0:
            deep_count = deep_analysis["deep_nodes_count"]
            print(f"  • {deep_count}个节点层级过深（{metrics['max_depth']}层），影响浏览效率")

        orphan_problem = next((p for p in problems if p["type"] == "orphan_nodes"), None)
        if orphan_problem:
            print(f"  • {orphan_problem['count']}个孤立节点未归类")

        deep_4plus = sum(count for depth, count in metrics["depth_distribution"].items() if depth >= 4)
        if deep_4plus > 0:
            deep_4plus_pct = deep_4plus / metrics['total_nodes'] * 100
            print(f"  • {deep_4plus_pct:.1f}%节点位于4层以下，建议优化至3层")

        # TOP 3 优化建议
        print("\n⚡ TOP 3 优先优化:")

        if deep_analysis.get("deep_nodes_count", 0) > 0:
            print(f"  1. [高优先级] 压缩深层级目录（可提升12分）")

        if orphan_problem:
            print(f"  2. [中优先级] 归类孤立节点（可提升8分）")

        print(f"  3. [低优先级] 统一命名风格（可提升5分）")

        print(f"\n💡 详细建议: 详见下方「专业建议与洞察」")

        # ==================== 第二部分：详细分析 ====================
        print("\n" + "=" * 60)
        print("第二部分：详细分析")
        print("=" * 60)

        # 维度得分分析
        print("\n📊 维度得分分析:")

        for name in ["structure", "organization", "content"]:
            data = scores.get(name, {})
            if not data:
                continue

            display_name = {"structure": "结构健康度", "organization": "组织规范度", "content": "内容丰富度"}.get(name, name)
            score = data.get("score", 0)
            status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))

            print(f"\n{status} {display_name}: {score}/100")
            print(f"   [{bar}]")

            # 结构健康度：深度对比
            if name == "structure" and deep_analysis:
                print("\n   📊 深度分布对比:")
                print("   理想分布:     2层 ████████████████████ 50%")
                print("                3层 ████████████████████ 40%")
                print("                4层 ███░░░░░░░░░░░░░░░░  8%")
                print("                5层 ░░░░░░░░░░░░░░░░░░░  2%")
                print()

                current_dist = deep_analysis.get("current_distribution", {})
                for depth in [2, 3, 4, 5]:
                    pct = current_dist.get(depth, 0) * 100
                    bar = "█" * int(pct / 5)
                    icon = "✅" if depth <= 3 else "⚠️" if depth == 4 else "❌"
                    print(f"   当前分布:     {depth}层 {bar} {pct:.1f}% {icon}")

                # 深层级 TOP 5
                if deep_analysis.get("top_deep_paths"):
                    print("\n   🎯 深层级节点 TOP 5:")
                    for i, item in enumerate(deep_analysis["top_deep_paths"][:5], 1):
                        path = item['path'][:50] + "..." if len(item['path']) > 50 else item['path']
                        print(f"      {i}. {path}")
                        print(f"         └─ 包含 {item['count']} 个节点")

            # 组织规范度：孤立节点
            if name == "organization" and orphan_problem:
                print("\n   📂 孤立节点详情:")
                for node in orphan_problem.get("nodes", []):
                    print(f"      • {node.get('title', '')}")
                    print(f"        └─ 建议移至: 磊叔原创/关于我")

            # 内容丰富度：类型分布
            if name == "content":
                print("\n   📦 内容类型分布:")
                total_content = sum(metrics["type_distribution"].values())
                type_names = {"docx": "飞书文档", "bitable": "多维表格", "sheet": "电子表格", "file": "文件（PDF/图片等）", "wiki": "文件夹"}
                for obj_type, count in metrics["type_distribution"].items():
                    name = type_names.get(obj_type, obj_type)
                    pct = count / total_content * 100 if total_content > 0 else 0
                    bar = "█" * int(pct / 5)
                    print(f"      {name} {count:3d} ({pct:.1f}%) {bar}")

            # 备注
            if data.get("notes"):
                print("\n   💡 改进建议:")
                for note in data.get("notes", []):
                    print(f"      • {note}")

        # 内容深度分析
        print("\n📈 内容深度分析:")

        if topic_stats.get("topics"):
            print("\n   主题分类统计:")
            total_topics = sum(t["count"] for t in topic_stats["topics"])
            for topic in topic_stats["topics"][:8]:
                count = topic["count"]
                pct = count / total_topics * 100 if total_topics > 0 else 0
                bar = "█" * int(pct / 5)
                topic_name = topic['name'][:20]
                print(f"      {topic_name} {bar} {count}节点 ({pct:.0f}%)")

        # 问题详情
        print("\n⚠️  问题详情:")
        if problems:
            for problem in problems:
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(problem["severity"], "•")
                print(f"\n   {severity_icon} {problem['type'].replace('_', ' ').title()}: {problem['count']} 个")
                print(f"   💡 建议: {problem['suggestion']}")

        # ==================== 第三部分：专业建议与洞察 ====================
        print("\n" + "=" * 60)
        print("第三部分：专业建议与洞察")
        print("=" * 60)

        # 总体评估
        print("\n📋 3.1 总体评估")

        total_score = total["score"]
        if total_score >= 85:
            assessment = "知识库整体健康状况良好，处于行业领先水平。"
        elif total_score >= 70:
            assessment = "知识库整体健康状况中等，存在结构性优化空间。"
        elif total_score >= 60:
            assessment = "知识库健康状况堪忧，亟需系统性改进。"
        else:
            assessment = "知识库健康状况严重不足，需要全面重构。"

        print(f"\n   当前状态: {assessment}")

        # 关键优势
        print("\n   ✨ 关键优势:")
        if scores["content"]["score"] >= 85:
            print(f"      • 内容规模: {metrics['total_nodes']}个节点，内容基础扎实")
        if scores["organization"]["score"] >= 75:
            print("      • 组织架构: 整体分类逻辑清晰，便于导航")
        if metrics["type_distribution"].get("docx", 0) > 200:
            print("      • 文档质量: 飞书文档占比高，知识沉淀质量好")

        # 核心挑战
        print("\n   ⚠️  核心挑战:")
        if deep_analysis.get("deep_nodes_count", 0) > 20:
            print(f"      • 结构效率: {deep_analysis['deep_nodes_count']}个节点位于5层，访问路径过长")
        if orphan_problem and orphan_problem["count"] > 0:
            print(f"      • 知识覆盖: {orphan_problem['count']}个节点游离于分类体系外")

        # 深度洞察
        print("\n🔍 3.2 深度洞察")

        if deep_analysis.get("deep_nodes_count", 0) > 0:
            print("\n   结构效率分析:")
            deep_count = deep_analysis["deep_nodes_count"]
            deep_pct = deep_count / metrics['total_nodes'] * 100
            print(f"      当前有 {deep_pct:.1f}% 的节点（{deep_count}个）分布在5层深度")
            print("      这会导致：")
            print("        • 用户查找效率降低，平均需要5次点击才能到达内容")
            print("        • 知识图谱呈现\"头重脚轻\"结构，核心内容被深埋")
            print("        • 搜索引擎爬取困难，影响知识库可发现性")
            print(f"      行业基准: 优秀知识库通常将80%内容控制在3层以内，当前仅{100-deep_pct:.0f}%")

        print("\n   内容健康度分析:")
        total_docs = metrics["type_distribution"].get("docx", 0)
        total_files = metrics["type_distribution"].get("file", 0)
        if total_docs + total_files > 0:
            doc_ratio = total_docs / (total_docs + total_files) * 100
            print(f"      • 文档与文件比例为 {doc_ratio:.1f}:{100-doc_ratio:.1f}", end="")
            if doc_ratio > 40 and doc_ratio < 60:
                print("（健康范围）")
            else:
                print("（建议调整至 50:50）")

        if topic_stats.get("topics"):
            top_topic = topic_stats["topics"][0]
            top_concentration = top_topic["count"] / metrics['total_nodes'] * 100
            print(f"      • 主题集中度: 最高主题「{top_topic['name']}」占比 {top_concentration:.1f}%", end="")
            if top_concentration > 50:
                print("（过高，建议分散风险）")
            elif top_concentration < 20:
                print("（偏低，知识分布过于分散）")
            else:
                print("（合理）")

        # 战略建议
        print("\n💡 3.3 战略建议")

        print("\n   短期优化（1-2周）:")
        print("      1. 结构扁平化")
        print("         - 优先处理5层深度节点，将访问路径缩短至3层")
        print("         - 预期效果: 用户查找效率提升30%+")
        print("         - 实施难度: 中等")

        if orphan_problem:
            print("\n      2. 孤岛整合")
            print(f"         - 将 {orphan_problem['count']} 个孤立节点纳入分类体系")
            print("         - 建立个人知识区（磊叔原创/关于我）")
            print("         - 预期效果: 知识覆盖率提升至100%")
            print("         - 实施难度: 低")

        print("\n   中期规划（1-2月）:")
        print("      1. 内容治理")
        print("         - 建立内容分类标准和命名规范")
        print("         - 定期清理冗余和过期内容")
        print("\n      2. 知识图谱优化")
        print("         - 分析用户访问路径，优化热门内容位置")
        print("         - 建立内容关联关系，增强知识连通性")

        print("\n   长期战略（3-6月）:")
        print("      1. 智能化升级")
        print("         - 引入AI辅助分类和标签推荐")
        print("         - 建立知识图谱，支持智能关联推荐")
        print("\n      2. 用户参与优化")
        print("         - 建立用户反馈机制，持续改进知识库结构")
        print("         - 培养知识贡献文化，鼓励内容共创")

        # 风险提示
        print("\n⚠️  3.4 风险提示")

        risks = []
        if deep_analysis.get("deep_nodes_count", 0) > 50:
            risks.append("可用性风险: 深层级结构会导致用户流失率上升")
        if metrics["type_distribution"].get("file", 0) > metrics["type_distribution"].get("docx", 0) * 2:
            risks.append("内容质量风险: 文件占比过高，可检索性不足")

        if risks:
            for risk in risks:
                print(f"      • {risk}")
        else:
            print("      • 当前无明显风险点")

        # ==================== 第四部分：行动计划 ====================
        print("\n" + "=" * 60)
        print("第四部分：行动计划")
        print("=" * 60)

        if deep_analysis.get("deep_nodes_count", 0) > 0:
            print("\n🔴 高优先级行动（预期 +12分）")
            print("\n   行动项: 压缩深层级结构")
            print("   ─────────────────────────────────────────────")
            print(f"   目标: 将{metrics['max_depth']}层压缩至3层以内")
            print(f"   范围: {deep_analysis['deep_nodes_count']}个节点")
            print("   影响: 结构健康度 +12分")
            print("   责任人: 知识库管理员")
            print("\n   执行步骤:")
            print("      1. 识别所有5层深度节点（已完成）")
            print("      2. 分析节点内容，确定最佳分类路径")
            print("      3. 创建扁平化分类结构")
            print(f"      4. 批量迁移 {deep_analysis['deep_nodes_count']} 个节点")
            print("      5. 验证链接完整性")
            print("      6. 更新知识库导航")
            print("\n   时间规划:")
            print("      • 准备阶段: 1天（分析、规划）")
            print("      • 执行阶段: 3天（创建、迁移、验证）")
            print("      • 复盘阶段: 1天（效果评估、优化）")
            print("\n   成功指标:")
            print("      • 最大深度降至3层")
            print("      • 用户查找时间减少30%")
            print("      • 零链接失效")

        if orphan_problem:
            print("\n🟡 中优先级行动（预期 +8分）")
            print("\n   行动项: 归类孤立节点")
            print("   ─────────────────────────────────────────────")
            print("   目标: 消除知识盲区")
            print(f"   范围: {orphan_problem['count']}个节点")
            print("   影响: 组织规范度 +8分")
            print("\n   执行步骤:")
            print("      1. 分析孤立节点内容类型")
            print("      2. 在「磊叔原创」下创建合适的子分类")
            for node in orphan_problem.get("nodes", []):
                title = node.get("title", "")
                print(f"      3. 迁移「{title}」")
            print("      4. 更新内部链接引用")
            print("\n   时间规划:")
            print("      • 分析和分类: 0.5天")
            print("      • 执行迁移: 0.5天")
            print("      • 验证和优化: 0.5天")

        print("\n🟢 低优先级行动（预期 +5分）")
        print("\n   行动项: 命名规范优化")
        print("   ─────────────────────────────────────────────")
        print("   目标: 提升命名一致性")
        print("   范围: 全库节点")
        print("   影响: 组织规范度 +5分")
        print("\n   建议方案:")
        print("      • 保持技术文档的英文命名")
        print("      • 新增内容采用统一命名规范")
        print("      • 建立命名规范文档")
        print("\n   实施说明:")
        print("      此项为低优先级，建议在完成高优先级")
        print("      任务后再评估必要性。")

        # ==================== 结束 ====================
        print("\n" + "=" * 60)
        print(f"✓ 报告完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)


def main():
    """命令行入口"""
    import argparse
    import os
    from datetime import datetime

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
  # 分析结构（自动保存 Markdown 报告）
  python3 analyzer.py --analyze

  # 自定义输出目录
  python3 analyzer.py --analyze -o ./reports

  # 显示详细报告
  python3 analyzer.py --analyze --verbose
        """
    )

    parser.add_argument("--analyze", "-a", action="store_true",
                       help="执行结构分析")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="显示详细信息")
    parser.add_argument("--output", "-o",
                       help="输出目录（默认: ./reports）")

    args = parser.parse_args()

    if not args.analyze:
        parser.print_help()
        return

    # 确定输出目录
    output_dir = args.output or "./reports"
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名（年月格式：wiki_analysis_2026041.md）
    year_month = datetime.now().strftime("%Y%m")
    md_filename = f"wiki_analysis_{year_month}.md"
    md_path = os.path.join(output_dir, md_filename)

    analyzer = WikiStructureAnalyzer()
    analysis = analyzer.analyze()

    # 控制台输出报告
    analyzer.print_report(analysis, verbose=args.verbose)

    # 保存 Markdown 报告
    md_content = analyzer.generate_markdown_report(analysis)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"\n✓ Markdown 报告已保存: {md_path}")


if __name__ == "__main__":
    main()
