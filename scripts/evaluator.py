#!/usr/bin/env python3
"""
知识库多维评价模型

对飞书知识库进行多维度评估，包括：
- 结构健康度
- 内容分布
- 时间活跃度
- 命名规范
- 综合评分

⚠️ 重要：本评价器必须实时获取知识库数据，不得依赖 wiki_nodes.json 缓存文件。
"""

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple


# ================================
# 配置路径
# ================================

SNAPSHOT_PATH = Path(__file__).parent.parent / "config" / "evaluation_snapshot.json"


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
    """
    根据分数计算等级

    Args:
        score: 分数 (0-100)

    Returns:
        等级 (S/A/B/C/D)
    """
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "D"


# ================================
# 核心评价类
# ================================

class WikiEvaluator:
    """知识库多维评价模型"""

    def __init__(self, space_id: str = None):
        """
        初始化评价器

        Args:
            space_id: 知识空间 ID，如果为 None 则从配置文件读取
        """
        if space_id is None:
            from lark_api import get_space_id
            space_id = get_space_id()

        self.space_id = space_id

        # 实时获取所有节点
        from lark_api import fetch_all_nodes_live
        print("正在实时获取知识库数据...")
        self.all_nodes = fetch_all_nodes_live(max_depth=10)

        # 过滤叶子节点
        self.nodes = []
        for node in self.all_nodes:
            path = node.get("path", "")
            # 检查是否有其他节点的 path 以当前节点的 path 为前缀
            is_parent = any(
                other.get("path", "").startswith(path + "/")
                for other in self.all_nodes
                if other.get("token") != node.get("token")
            )
            if not is_parent:
                self.nodes.append(node)

        print(f"✓ 已获取 {len(self.all_nodes)} 个节点")
        print(f"✓ 已识别 {len(self.nodes)} 个叶子节点")

        # 当前时间戳（秒）
        self.current_time = int(datetime.now(timezone.utc).timestamp())


    def evaluate_all(self) -> Dict[str, Any]:
        """
        执行所有维度的评价

        Returns:
            完整的评价结果
        """
        # 评价各维度
        structure = self._evaluate_structure()
        content = self._evaluate_content()
        time_metrics = self._evaluate_time()
        naming = self._evaluate_naming()

        # 计算综合评分
        overall = self._calculate_overall(structure, content, time_metrics, naming)

        # 计算总分
        total_score = (
            structure["score"] * 0.25 +
            content["score"] * 0.15 +
            time_metrics["score"] * 0.30 +
            naming["score"] * 0.15 +
            overall["score"] * 0.15
        )

        return {
            "meta": {
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "space_id": self.space_id,
                "total_nodes": len(self.all_nodes),
                "leaf_nodes": len(self.nodes),
                "total_score": round(total_score, 1),
                "grade": calculate_grade(total_score)
            },
            "dimensions": {
                "structure": structure,
                "content": content,
                "time": time_metrics,
                "naming": naming,
                "overall": overall
            },
            "recommendations": self._generate_recommendations({
                "structure": structure,
                "content": content,
                "time": time_metrics,
                "naming": naming
            })
        }

    # ================================
    # 结构健康度评价 (25分)
    # ================================

    def _evaluate_structure(self) -> Dict[str, Any]:
        """评价结构健康度"""
        metrics = {}
        total_score = 0

        # 1. 最大深度 (5分)
        max_depth = max(node.get("level", 0) for node in self.nodes)
        if max_depth <= 2:
            score_depth = 5
        elif max_depth == 3:
            score_depth = 4
        elif max_depth == 4:
            score_depth = 2
        else:
            score_depth = 0
        metrics["max_depth"] = {"value": max_depth, "score": score_depth, "max": 5}
        total_score += score_depth

        # 2. 深度合理性 (8分)
        depths = [node.get("level", 0) for node in self.nodes]
        avg_depth = statistics.mean(depths) if depths else 0
        depth_std = statistics.stdev(depths) if len(depths) > 1 else 0

        if 2 <= avg_depth <= 3 and depth_std < 1:
            score_reasonable = 8
        elif 2 <= avg_depth <= 4:
            score_reasonable = 5
        else:
            score_reasonable = 2
        metrics["depth_reasonable"] = {
            "value": {"average": round(avg_depth, 1), "std": round(depth_std, 2)},
            "score": score_reasonable,
            "max": 8
        }
        total_score += score_reasonable

        # 3. 空分类占比 (7分)
        # 空分类 = obj_type 为 wiki 但没有叶子节点的分类
        empty_categories = 0
        for node in self.all_nodes:
            if node.get("obj_type") == "wiki":
                # 检查是否有叶子节点以这个分类为前缀
                has_children = any(
                    leaf.get("path", "").startswith(node.get("path", ""))
                    for leaf in self.nodes
                )
                if not has_children:
                    empty_categories += 1

        empty_ratio = empty_categories / len(self.all_nodes) if self.all_nodes else 0
        if empty_ratio == 0:
            score_empty = 7
        elif empty_ratio < 0.05:
            score_empty = 5
        elif empty_ratio <= 0.10:
            score_empty = 3
        else:
            score_empty = 0
        metrics["empty_categories"] = {
            "value": {"count": empty_categories, "ratio": round(empty_ratio * 100, 1)},
            "score": score_empty,
            "max": 7
        }
        total_score += score_empty

        # 4. 孤立节点占比 (5分)
        # 孤立节点 = 根目录下的叶子节点
        orphans = sum(
            1 for node in self.nodes
            if node.get("level", 0) == 0
        )
        orphan_ratio = orphans / len(self.nodes) if self.nodes else 0
        if orphan_ratio == 0:
            score_orphan = 5
        elif orphan_ratio < 0.05:
            score_orphan = 3
        elif orphan_ratio <= 0.10:
            score_orphan = 1
        else:
            score_orphan = 0
        metrics["orphan_nodes"] = {
            "value": {"count": orphans, "ratio": round(orphan_ratio * 100, 1)},
            "score": score_orphan,
            "max": 5
        }
        total_score += score_orphan

        return {
            "score": total_score,
            "max": 25,
            "metrics": metrics
        }

    # ================================
    # 内容分布评价 (15分)
    # ================================

    def _evaluate_content(self) -> Dict[str, Any]:
        """评价内容分布"""
        metrics = {}
        total_score = 0

        # 1. 类型多样性 (5分)
        obj_types = set(node.get("obj_type", "") for node in self.nodes)
        type_count = len(obj_types)
        if type_count >= 3:
            score_diversity = 5
        elif type_count == 2:
            score_diversity = 3
        else:
            score_diversity = 1
        metrics["type_diversity"] = {
            "value": {"count": type_count, "types": list(obj_types)},
            "score": score_diversity,
            "max": 5
        }
        total_score += score_diversity

        # 2. 文档占比 (5分)
        docx_count = sum(1 for node in self.nodes if node.get("obj_type") == "docx")
        docx_ratio = docx_count / len(self.nodes) if self.nodes else 0
        if docx_ratio > 0.7:
            score_docx = 5
        elif docx_ratio >= 0.5:
            score_docx = 3
        else:
            score_docx = 1
        metrics["docx_ratio"] = {
            "value": {"count": docx_count, "ratio": round(docx_ratio * 100, 1)},
            "score": score_docx,
            "max": 5
        }
        total_score += score_docx

        # 3. 分类均衡度 (5分)
        # 统计一级分类下的节点数
        level1_nodes = [node for node in self.nodes if node.get("level", 0) == 0]
        if len(level1_nodes) > 1:
            # 计算变异系数
            child_counts = [
                sum(1 for n in self.nodes if n.get("path", "").startswith(node.get("title", "")))
                for node in level1_nodes
            ]
            if child_counts:
                mean_count = statistics.mean(child_counts)
                std_count = statistics.stdev(child_counts) if len(child_counts) > 1 else 0
                cv = std_count / mean_count if mean_count > 0 else 0

                if cv < 0.5:
                    score_balance = 5
                elif cv <= 1:
                    score_balance = 3
                else:
                    score_balance = 1
            else:
                score_balance = 1
        else:
            score_balance = 1
        metrics["category_balance"] = {
            "value": {"cv": round(cv, 2) if 'cv' in locals() else 0},
            "score": score_balance,
            "max": 5
        }
        total_score += score_balance

        return {
            "score": total_score,
            "max": 15,
            "metrics": metrics
        }

    # ================================
    # 时间活跃度评价 (30分)
    # ================================

    def _evaluate_time(self) -> Dict[str, Any]:
        """评价时间活跃度"""
        metrics = {}
        total_score = 0

        # 当前时间戳（秒）
        now = self.current_time
        day_seconds = 86400

        # 1. 7天活跃度 (10分)
        active_7d = sum(
            1 for node in self.nodes
            if node.get("obj_edit_time", 0) and (now - int(node.get("obj_edit_time", 0))) <= 7 * day_seconds
        )
        active_7d_ratio = active_7d / len(self.nodes) if self.nodes else 0
        if active_7d_ratio > 0.3:
            score_7d = 10
        elif active_7d_ratio >= 0.1:
            score_7d = 6
        else:
            score_7d = 2
        metrics["active_7d"] = {
            "value": {"count": active_7d, "ratio": round(active_7d_ratio * 100, 1)},
            "score": score_7d,
            "max": 10
        }
        total_score += score_7d

        # 2. 30天活跃度 (8分)
        active_30d = sum(
            1 for node in self.nodes
            if node.get("obj_edit_time", 0) and (now - int(node.get("obj_edit_time", 0))) <= 30 * day_seconds
        )
        active_30d_ratio = active_30d / len(self.nodes) if self.nodes else 0
        if active_30d_ratio > 0.5:
            score_30d = 8
        elif active_30d_ratio >= 0.2:
            score_30d = 5
        else:
            score_30d = 2
        metrics["active_30d"] = {
            "value": {"count": active_30d, "ratio": round(active_30d_ratio * 100, 1)},
            "score": score_30d,
            "max": 8
        }
        total_score += score_30d

        # 3. 内容新鲜度 (7分)
        edit_times = [int(node.get("obj_edit_time", 0)) for node in self.nodes if node.get("obj_edit_time", 0)]
        if edit_times:
            avg_days_ago = (now - statistics.mean(edit_times)) / day_seconds
            if avg_days_ago < 30:
                score_freshness = 7
            elif avg_days_ago < 60:
                score_freshness = 4
            elif avg_days_ago < 90:
                score_freshness = 2
            else:
                score_freshness = 0
        else:
            avg_days_ago = 0
            score_freshness = 0
        metrics["freshness"] = {
            "value": {"avg_days_ago": round(avg_days_ago, 1)},
            "score": score_freshness,
            "max": 7
        }
        total_score += score_freshness

        # 4. stagnant内容 (5分)
        stagnant = sum(
            1 for node in self.nodes
            if node.get("obj_edit_time", 0) and (now - int(node.get("obj_edit_time", 0))) > 90 * day_seconds
        )
        stagnant_ratio = stagnant / len(self.nodes) if self.nodes else 0
        if stagnant_ratio < 0.1:
            score_stagnant = 5
        elif stagnant_ratio <= 0.3:
            score_stagnant = 3
        elif stagnant_ratio <= 0.5:
            score_stagnant = 1
        else:
            score_stagnant = 0
        metrics["stagnant"] = {
            "value": {"count": stagnant, "ratio": round(stagnant_ratio * 100, 1)},
            "score": score_stagnant,
            "max": 5
        }
        total_score += score_stagnant

        return {
            "score": total_score,
            "max": 30,
            "metrics": metrics
        }

    # ================================
    # 命名规范评价 (15分)
    # ================================

    def _evaluate_naming(self) -> Dict[str, Any]:
        """评价命名规范"""
        metrics = {}
        total_score = 0

        titles = [node.get("title", "") for node in self.nodes]

        # 1. 命名一致性 (6分)
        chinese_count = sum(1 for title in titles if any('\u4e00' <= c <= '\u9fff' for c in title))
        english_count = sum(1 for title in titles if any(c.isalpha() and ord(c) < 128 for c in title))
        total = len(titles)

        if total > 0:
            chinese_ratio = chinese_count / total
            english_ratio = english_count / total

            if chinese_ratio > 0.8 or english_ratio > 0.8:
                score_consistency = 6
            elif chinese_ratio > 0.6 or english_ratio > 0.6:
                score_consistency = 4
            else:
                score_consistency = 2
        else:
            score_consistency = 0

        metrics["naming_consistency"] = {
            "value": {
                "chinese_ratio": round(chinese_ratio * 100, 1) if total > 0 else 0,
                "english_ratio": round(english_ratio * 100, 1) if total > 0 else 0
            },
            "score": score_consistency,
            "max": 6
        }
        total_score += score_consistency

        # 2. 特殊字符 (5分)
        special_count = sum(
            1 for title in titles
            if any(ord(c) > 127 and not ('\u4e00' <= c <= '\u9fff') for c in title)
        )
        special_ratio = special_count / total if total > 0 else 0
        if special_ratio == 0:
            score_special = 5
        elif special_ratio < 0.05:
            score_special = 3
        elif special_ratio <= 0.10:
            score_special = 1
        else:
            score_special = 0
        metrics["special_chars"] = {
            "value": {"count": special_count, "ratio": round(special_ratio * 100, 1)},
            "score": score_special,
            "max": 5
        }
        total_score += score_special

        # 3. 标题长度合理性 (4分)
        lengths = [len(title) for title in titles]
        if lengths:
            avg_length = statistics.mean(lengths)
            if 5 <= avg_length <= 20:
                score_length = 4
            elif (3 <= avg_length < 5) or (20 < avg_length <= 30):
                score_length = 2
            else:
                score_length = 0
        else:
            avg_length = 0
            score_length = 0
        metrics["title_length"] = {
            "value": {"average": round(avg_length, 1)},
            "score": score_length,
            "max": 4
        }
        total_score += score_length

        return {
            "score": total_score,
            "max": 15,
            "metrics": metrics
        }

    # ================================
    # 综合评分 (15分)
    # ================================

    def _calculate_overall(self, structure: Dict, content: Dict, time_metrics: Dict, naming: Dict) -> Dict[str, Any]:
        """计算综合评分"""
        metrics = {}
        total_score = 0

        # 1. 整体健康度 (10分) - 基于前四个维度的加权平均
        weighted_score = (
            structure["score"] / structure["max"] * 25 +
            content["score"] / content["max"] * 15 +
            time_metrics["score"] / time_metrics["max"] * 30 +
            naming["score"] / naming["max"] * 15
        )
        # 转换为 10 分制
        overall_health = (weighted_score / 85) * 10
        metrics["overall_health"] = {
            "value": round(overall_health, 1),
            "score": round(overall_health, 1),
            "max": 10
        }
        total_score += round(overall_health, 1)

        # 2. 规模增长率 (5分) - 对比历史快照
        growth_score = self._calculate_growth_score()
        metrics["growth_rate"] = {
            "value": growth_score["value"],
            "score": growth_score["score"],
            "max": 5
        }
        total_score += growth_score["score"]

        return {
            "score": round(total_score, 1),
            "max": 15,
            "metrics": metrics
        }

    def _calculate_growth_score(self) -> Dict[str, Any]:
        """计算规模增长率得分"""
        # 尝试加载历史快照
        if not SNAPSHOT_PATH.exists():
            return {"value": "无历史数据", "score": 3}  # 默认给中等分

        try:
            with open(SNAPSHOT_PATH, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)

            prev_total = snapshot.get("meta", {}).get("total_nodes", 0)
            current_total = len(self.nodes)

            if prev_total == 0:
                growth_rate = 0
            else:
                growth_rate = (current_total - prev_total) / prev_total

            if growth_rate > 0.10:
                score = 5
            elif growth_rate > 0.05:
                score = 3
            elif growth_rate > 0:
                score = 1
            else:
                score = 0

            return {
                "value": {
                    "previous": prev_total,
                    "current": current_total,
                    "growth_rate": round(growth_rate * 100, 1)
                },
                "score": score
            }
        except Exception:
            return {"value": "快照读取失败", "score": 3}

    # ================================
    # 优化建议生成
    # ================================

    def _generate_recommendations(self, evaluation: Dict) -> List[str]:
        """根据评价结果生成优化建议"""
        recommendations = []

        structure = evaluation["structure"]["metrics"]
        content = evaluation["content"]["metrics"]
        time_metrics = evaluation["time"]["metrics"]
        naming = evaluation["naming"]["metrics"]

        # 结构建议
        if structure["orphan_nodes"]["value"]["count"] > 0:
            recommendations.append(
                f"将 {structure['orphan_nodes']['value']['count']} 个孤立节点移入合适的分类"
            )
        if structure["empty_categories"]["value"]["count"] > 0:
            recommendations.append(
                f"删除或填充 {structure['empty_categories']['value']['count']} 个空分类"
            )
        if structure["max_depth"]["value"] > 4:
            recommendations.append("优化层级结构，将深层级提升至 4 层以内")

        # 内容建议
        if content["docx_ratio"]["value"]["ratio"] < 50:
            recommendations.append("增加文档类型内容，当前文档占比过低")

        # 时间建议
        if time_metrics["stagnant"]["value"]["ratio"] > 0.10:
            recommendations.append(
                f"更新超过 90 天未编辑的 {time_metrics['stagnant']['value']['count']} 个内容"
            )
        if time_metrics["freshness"]["value"]["avg_days_ago"] > 60:
            recommendations.append("提升内容更新频率，平均内容新鲜度较低")

        # 命名建议
        if naming["special_chars"]["value"]["count"] > 0:
            recommendations.append("统一命名风格，减少特殊字符使用")
        if naming["title_length"]["value"]["average"] > 20:
            recommendations.append("优化部分过长的标题，提升可读性")

        return recommendations

    def save_snapshot(self, evaluation: Dict):
        """保存评价快照"""
        with open(SNAPSHOT_PATH, 'w', encoding='utf-8') as f:
            json.dump(evaluation, f, ensure_ascii=False, indent=2)


# ================================
# 命令行入口
# ================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="飞书知识库多维评价",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行评价
  python3 evaluator.py --evaluate

  # 输出 JSON 格式
  python3 evaluator.py --evaluate --json --output report.json

  # 保存快照
  python3 evaluator.py --evaluate --save-snapshot
        """
    )

    parser.add_argument("--evaluate", "-e", action="store_true",
                       help="执行评价")
    parser.add_argument("--json", action="store_true",
                       help="输出 JSON 格式")
    parser.add_argument("--output", "-o",
                       help="输出文件路径")
    parser.add_argument("--save-snapshot", action="store_true",
                       help="保存评价快照")

    args = parser.parse_args()

    if not args.evaluate:
        parser.print_help()
        return

    # 执行评价
    evaluator = WikiEvaluator()
    evaluation = evaluator.evaluate_all()

    # 输出结果
    if args.json:
        output = json.dumps(evaluation, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"报告已保存到: {args.output}")
        else:
            print(output)
    else:
        # 简单文本输出（详细报告由 report_generator.py 处理）
        meta = evaluation["meta"]
        print(f"\n总得分: {meta['total_score']}/100")
        print(f"评级: {meta['grade']}")
        print("\n维度得分:")
        for name, dim in evaluation["dimensions"].items():
            print(f"  {name.capitalize()}: {dim['score']}/{dim['max']}")

    # 保存快照
    if args.save_snapshot:
        evaluator.save_snapshot(evaluation)
        print(f"\n快照已保存到: {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
