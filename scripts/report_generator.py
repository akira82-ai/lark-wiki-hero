#!/usr/bin/env python3
"""
知识库评价报告生成器

支持多种输出格式：
- 可视化文本报告（默认）
- HTML 可视化报告
- Markdown 格式报告
"""

import json
from typing import Dict, Any
from pathlib import Path


# ================================
# 报告生成器类
# ================================

class EvaluationReportGenerator:
    """评价报告生成器"""

    def __init__(self, evaluation: Dict[str, Any]):
        """
        初始化报告生成器

        Args:
            evaluation: 评价结果字典
        """
        self.evaluation = evaluation
        self.meta = evaluation["meta"]
        self.dimensions = evaluation["dimensions"]
        self.recommendations = evaluation["recommendations"]

    # ================================
    # 文本报告生成
    # ================================

    def generate_text_report(self) -> str:
        """生成可视化文本报告"""
        lines = []

        # 标题
        lines.append("═" * 60)
        lines.append("           飞书知识库多维评价报告")
        lines.append("═" * 60)
        lines.append(f"评价时间: {self._format_timestamp(self.meta['evaluated_at'])}")
        lines.append(f"知识空间: {self.meta['space_id']}")
        if 'leaf_nodes' in self.meta:
            lines.append(f"节点总数: {self.meta['total_nodes']} 个（叶子节点: {self.meta['leaf_nodes']} 个）")
        else:
            lines.append(f"节点总数: {self.meta['total_nodes']}")
        lines.append("")
        lines.append("─" * 60)
        lines.append(f"                    总得分: {self.meta['total_score']}/100")
        lines.append(f"                    评级: {self.meta['grade']} ({self._grade_name(self.meta['grade'])})")
        lines.append("─" * 60)
        lines.append("")

        # 维度得分条形图
        lines.append("┌─ 维度得分 ─────────────────────────────────────────────┐")
        for name, dim in self.dimensions.items():
            display_name = self._dimension_display_name(name)
            score = dim['score']
            max_score = dim['max']
            percentage = (score / max_score) * 100
            bar = self._generate_bar(percentage)
            warning = "  ⚠️" if percentage < 60 else ""
            lines.append(f"│ {display_name}: {bar} {score}/{max_score}  ({percentage:.0f}%){warning.ljust(4)}│")
        lines.append("└────────────────────────────────────────────────────────┘")
        lines.append("")

        # 详细分析
        lines.append("🔍 详细分析")
        lines.append("─" * 60)
        lines.append("")

        # 结构健康度
        lines.extend(self._generate_structure_detail())

        # 内容分布
        lines.extend(self._generate_content_detail())

        # 时间活跃度
        lines.extend(self._generate_time_detail())

        # 命名规范
        lines.extend(self._generate_naming_detail())

        # 综合评分
        lines.extend(self._generate_overall_detail())

        # 优化建议
        if self.recommendations:
            lines.append("─" * 60)
            lines.append("💡 优化建议")
            lines.append("─" * 60)
            lines.append("")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        lines.append("═" * 60)

        return "\n".join(lines)

    def _generate_structure_detail(self) -> list:
        """生成结构健康度详情"""
        lines = []
        metrics = self.dimensions["structure"]["metrics"]

        lines.append("【结构健康度】{}/{}".format(
            self.dimensions["structure"]["score"],
            self.dimensions["structure"]["max"]
        ))

        # 最大深度
        depth = metrics["max_depth"]["value"]
        score = metrics["max_depth"]["score"]
        status = self._status_icon(score)
        lines.append(f"  {status} 最大深度: {depth} 层 ({self._depth_comment(depth)})")

        # 深度合理性
        avg = metrics["depth_reasonable"]["value"]["average"]
        std = metrics["depth_reasonable"]["value"]["std"]
        score = metrics["depth_reasonable"]["score"]
        status = self._status_icon(score)
        lines.append(f"  {status} 深度分布: 平均 {avg} 层，标准差 {std}")

        # 空分类
        empty = metrics["empty_categories"]["value"]["count"]
        ratio = metrics["empty_categories"]["value"]["ratio"]
        score = metrics["empty_categories"]["score"]
        status = self._status_icon(score, reverse=True)
        msg = f"{status} 空分类: {empty} 个 ({ratio}%)"
        if score < 7:
            msg += "  ← 需要处理"
        lines.append(msg)

        # 孤立节点
        orphans = metrics["orphan_nodes"]["value"]["count"]
        ratio = metrics["orphan_nodes"]["value"]["ratio"]
        score = metrics["orphan_nodes"]["score"]
        status = self._status_icon(score, reverse=True)
        msg = f"{status} 孤立节点: {orphans} 个 ({ratio}%)"
        if score < 5:
            msg += "  ← 需要处理"
        lines.append(msg)

        lines.append("")
        return lines

    def _generate_content_detail(self) -> list:
        """生成内容分布详情"""
        lines = []
        metrics = self.dimensions["content"]["metrics"]

        lines.append("【内容分布】{}/{}".format(
            self.dimensions["content"]["score"],
            self.dimensions["content"]["max"]
        ))

        # 类型多样性
        types = metrics["type_diversity"]["value"]["types"]
        count = metrics["type_diversity"]["value"]["count"]
        score = metrics["type_diversity"]["score"]
        status = self._status_icon(score)
        lines.append(f"  {status} 文档类型: {count} 种 ({', '.join(types)})")

        # 文档占比
        ratio = metrics["docx_ratio"]["value"]["ratio"]
        score = metrics["docx_ratio"]["score"]
        status = self._status_icon(score)
        lines.append(f"  {status} 文档占比: {ratio}%")

        # 分类均衡
        cv = metrics["category_balance"]["value"]["cv"]
        score = metrics["category_balance"]["score"]
        status = self._status_icon(score)
        balance_comment = "良好" if cv < 0.5 else "一般" if cv <= 1 else "不均衡"
        lines.append(f"  {status} 分类均衡: {balance_comment} (CV={cv})")

        lines.append("")
        return lines

    def _generate_time_detail(self) -> list:
        """生成时间活跃度详情"""
        lines = []
        metrics = self.dimensions["time"]["metrics"]

        score = self.dimensions["time"]["score"]
        max_score = self.dimensions["time"]["max"]
        warning = "  ⚠️" if score < max_score * 0.6 else ""

        lines.append(f"【时间活跃度】{score}/{max_score}{warning}")

        # 7天活跃
        count = metrics["active_7d"]["value"]["count"]
        ratio = metrics["active_7d"]["value"]["ratio"]
        score = metrics["active_7d"]["score"]
        status = self._status_icon(score)
        total = self.meta.get('leaf_nodes', self.meta['total_nodes'])
        msg = f"  {status} 7天活跃: {ratio}% ({count}/{total})"
        if score < 6:
            msg += "  ← 需要提升"
        lines.append(msg)

        # 30天活跃
        count = metrics["active_30d"]["value"]["count"]
        ratio = metrics["active_30d"]["value"]["ratio"]
        score = metrics["active_30d"]["score"]
        status = self._status_icon(score)
        total = self.meta.get('leaf_nodes', self.meta['total_nodes'])
        lines.append(f"  {status} 30天活跃: {ratio}% ({count}/{total})")

        # 内容新鲜度
        days = metrics["freshness"]["value"]["avg_days_ago"]
        score = metrics["freshness"]["score"]
        status = self._status_icon(score)
        msg = f"  {status} 内容新鲜度: 平均 {days:.0f} 天"
        if score < 4:
            msg += "  ← 需要更新"
        lines.append(msg)

        # stagnant内容
        count = metrics["stagnant"]["value"]["count"]
        ratio = metrics["stagnant"]["value"]["ratio"]
        score = metrics["stagnant"]["score"]
        status = self._status_icon(score, reverse=True)
        lines.append(f"  {status} stale内容: {ratio}% ({count} 个)")

        lines.append("")
        return lines

    def _generate_naming_detail(self) -> list:
        """生成命名规范详情"""
        lines = []
        metrics = self.dimensions["naming"]["metrics"]

        lines.append("【命名规范】{}/{}".format(
            self.dimensions["naming"]["score"],
            self.dimensions["naming"]["max"]
        ))

        # 命名一致性
        cn_ratio = metrics["naming_consistency"]["value"]["chinese_ratio"]
        en_ratio = metrics["naming_consistency"]["value"]["english_ratio"]
        score = metrics["naming_consistency"]["score"]
        status = self._status_icon(score)
        dominant = "中文" if cn_ratio > en_ratio else "英文"
        lines.append(f"  {status} 命名风格: {dominant}主导 {max(cn_ratio, en_ratio)}%")

        # 特殊字符
        count = metrics["special_chars"]["value"]["count"]
        ratio = metrics["special_chars"]["value"]["ratio"]
        score = metrics["special_chars"]["score"]
        status = self._status_icon(score, reverse=True)
        lines.append(f"  {status} 特殊字符: {count} 个 ({ratio}%)")

        # 标题长度
        avg_len = metrics["title_length"]["value"]["average"]
        score = metrics["title_length"]["score"]
        status = self._status_icon(score)
        length_comment = "合理" if 5 <= avg_len <= 20 else "略长" if avg_len > 20 else "偏短"
        msg = f"  {status} 标题长度: 平均 {avg_len:.0f} 字 ({length_comment})"
        if score < 4:
            msg += "  ← 需要优化"
        lines.append(msg)

        lines.append("")
        return lines

    def _generate_overall_detail(self) -> list:
        """生成综合评分详情"""
        lines = []
        metrics = self.dimensions["overall"]["metrics"]

        lines.append("【综合评分】{}/{}".format(
            self.dimensions["overall"]["score"],
            self.dimensions["overall"]["max"]
        ))

        # 整体健康度
        health = metrics["overall_health"]["value"]
        score = metrics["overall_health"]["score"]
        status = self._status_icon(score)
        lines.append(f"  {status} 整体健康度: {health}/10")

        # 规模增长
        growth = metrics["growth_rate"]["value"]
        if isinstance(growth, dict):
            growth_rate = growth["growth_rate"]
            score = metrics["growth_rate"]["score"]
            status = self._status_icon(score)
            growth_comment = "快速增长" if growth_rate > 10 else "稳定增长" if growth_rate > 5 else "缓慢增长" if growth_rate > 0 else "负增长"
            lines.append(f"  {status} 规模增长: +{growth_rate}% ({growth_comment})")
        else:
            lines.append(f"  ⊘ 规模增长: {growth}")

        lines.append("")
        return lines

    # ================================
    # Markdown 报告生成
    # ================================

    def generate_markdown_report(self) -> str:
        """生成 Markdown 格式报告"""
        lines = []

        # 标题
        lines.append("# 飞书知识库多维评价报告")
        lines.append("")
        lines.append(f"- **评价时间**: {self._format_timestamp(self.meta['evaluated_at'])}")
        lines.append(f"- **知识空间**: {self.meta['space_id']}")
        if 'leaf_nodes' in self.meta:
            lines.append(f"- **节点总数**: {self.meta['total_nodes']} 个（叶子节点: {self.meta['leaf_nodes']} 个）")
        else:
            lines.append(f"- **节点总数**: {self.meta['total_nodes']}")
        lines.append("")
        lines.append("## 总体评价")
        lines.append("")
        lines.append(f"- **总得分**: **{self.meta['total_score']}/100**")
        lines.append(f"- **评级**: **{self.meta['grade']} ({self._grade_name(self.meta['grade'])})**")
        lines.append("")

        # 维度得分
        lines.append("## 维度得分")
        lines.append("")
        lines.append("| 维度 | 得分 | 满分 | 占比 |")
        lines.append("|------|------|------|------|")
        for name, dim in self.dimensions.items():
            display_name = self._dimension_display_name(name)
            score = dim['score']
            max_score = dim['max']
            percentage = (score / max_score) * 100
            warning = " ⚠️" if percentage < 60 else ""
            lines.append(f"| {display_name} | {score} | {max_score} | {percentage:.0f}%{warning} |")
        lines.append("")

        # 详细分析
        lines.append("## 详细分析")
        lines.append("")

        # 结构健康度
        lines.append("### 结构健康度")
        lines.extend(self._generate_structure_md())

        # 内容分布
        lines.append("### 内容分布")
        lines.extend(self._generate_content_md())

        # 时间活跃度
        lines.append("### 时间活跃度")
        lines.extend(self._generate_time_md())

        # 命名规范
        lines.append("### 命名规范")
        lines.extend(self._generate_naming_md())

        # 综合评分
        lines.append("### 综合评分")
        lines.extend(self._generate_overall_md())

        # 优化建议
        if self.recommendations:
            lines.append("## 优化建议")
            lines.append("")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        return "\n".join(lines)

    def _generate_structure_md(self) -> list:
        """生成结构健康度 Markdown"""
        lines = []
        metrics = self.dimensions["structure"]["metrics"]
        lines.append(f"**得分**: {self.dimensions['structure']['score']}/{self.dimensions['structure']['max']}")
        lines.append("")
        lines.append("| 指标 | 数值 | 得分 |")
        lines.append("|------|------|------|")

        # 指标名映射
        metric_names = {
            "max_depth": "最大深度",
            "depth_reasonable": "深度合理性",
            "empty_categories": "空分类",
            "orphan_nodes": "孤立节点"
        }

        for metric_name, metric in metrics.items():
            display_name = metric_names.get(metric_name, metric_name)
            value = self._format_metric_value(metric["value"])
            lines.append(f"| {display_name} | {value} | {metric['score']}/{metric['max']} |")

        lines.append("")
        return lines

    def _generate_content_md(self) -> list:
        """生成内容分布 Markdown"""
        lines = []
        metrics = self.dimensions["content"]["metrics"]
        lines.append(f"**得分**: {self.dimensions['content']['score']}/{self.dimensions['content']['max']}")
        lines.append("")
        lines.append("| 指标 | 数值 | 得分 |")
        lines.append("|------|------|------|")

        # 指标名映射
        metric_names = {
            "type_diversity": "类型多样性",
            "docx_ratio": "文档占比",
            "category_balance": "分类均衡度"
        }

        for metric_name, metric in metrics.items():
            display_name = metric_names.get(metric_name, metric_name)
            value = self._format_metric_value(metric["value"])
            lines.append(f"| {display_name} | {value} | {metric['score']}/{metric['max']} |")

        lines.append("")
        return lines

    def _generate_time_md(self) -> list:
        """生成时间活跃度 Markdown"""
        lines = []
        metrics = self.dimensions["time"]["metrics"]
        lines.append(f"**得分**: {self.dimensions['time']['score']}/{self.dimensions['time']['max']}")
        lines.append("")
        lines.append("| 指标 | 数值 | 得分 |")
        lines.append("|------|------|------|")

        # 指标名映射
        metric_names = {
            "active_7d": "7天活跃度",
            "active_30d": "30天活跃度",
            "freshness": "内容新鲜度",
            "stagnant": "stale内容"
        }

        for metric_name, metric in metrics.items():
            display_name = metric_names.get(metric_name, metric_name)
            value = self._format_metric_value(metric["value"])
            lines.append(f"| {display_name} | {value} | {metric['score']}/{metric['max']} |")

        lines.append("")
        return lines

    def _generate_naming_md(self) -> list:
        """生成命名规范 Markdown"""
        lines = []
        metrics = self.dimensions["naming"]["metrics"]
        lines.append(f"**得分**: {self.dimensions['naming']['score']}/{self.dimensions['naming']['max']}")
        lines.append("")
        lines.append("| 指标 | 数值 | 得分 |")
        lines.append("|------|------|------|")

        # 指标名映射
        metric_names = {
            "naming_consistency": "命名一致性",
            "special_chars": "特殊字符",
            "title_length": "标题长度"
        }

        for metric_name, metric in metrics.items():
            display_name = metric_names.get(metric_name, metric_name)
            value = self._format_metric_value(metric["value"])
            lines.append(f"| {display_name} | {value} | {metric['score']}/{metric['max']} |")

        lines.append("")
        return lines

    def _generate_overall_md(self) -> list:
        """生成综合评分 Markdown"""
        lines = []
        metrics = self.dimensions["overall"]["metrics"]
        lines.append(f"**得分**: {self.dimensions['overall']['score']}/{self.dimensions['overall']['max']}")
        lines.append("")
        lines.append("| 指标 | 数值 | 得分 |")
        lines.append("|------|------|------|")

        # 指标名映射
        metric_names = {
            "overall_health": "整体健康度",
            "growth_rate": "规模增长率"
        }

        for metric_name, metric in metrics.items():
            display_name = metric_names.get(metric_name, metric_name)
            value = self._format_metric_value(metric["value"])
            lines.append(f"| {display_name} | {value} | {metric['score']}/{metric['max']} |")

        lines.append("")
        return lines

    # ================================
    # HTML 报告生成
    # ================================

    def generate_html_report(self) -> str:
        """生成 HTML 可视化报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>飞书知识库多维评价报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .meta {{
            display: flex;
            justify-content: center;
            gap: 20px;
            font-size: 14px;
            opacity: 0.9;
            flex-wrap: wrap;
        }}
        .score-card {{
            text-align: center;
            padding: 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        .score {{
            font-size: 72px;
            font-weight: bold;
            color: {self._grade_color(self.meta['grade'])};
            line-height: 1;
        }}
        .grade {{
            font-size: 24px;
            color: {self._grade_color(self.meta['grade'])};
            margin-top: 10px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px;
        }}
        .dimension {{
            margin-bottom: 30px;
        }}
        .dimension-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }}
        .progress-bar {{
            height: 24px;
            background: #e9ecef;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-size: 12px;
            font-weight: 600;
            transition: width 0.5s ease;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .metric-name {{
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }}
        .metric-score {{
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }}
        .recommendations {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
        }}
        .recommendations h3 {{
            color: #856404;
            margin-bottom: 15px;
        }}
        .recommendations ul {{
            list-style: none;
        }}
        .recommendations li {{
            padding: 10px 0;
            padding-left: 25px;
            position: relative;
        }}
        .recommendations li:before {{
            content: "💡";
            position: absolute;
            left: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>飞书知识库多维评价报告</h1>
            <div class="meta">
                <span>评价时间: {self._format_timestamp(self.meta['evaluated_at'])}</span>
                <span>知识空间: {self.meta['space_id']}</span>
                <span>节点总数: {self.meta['total_nodes']} 个</span>
                {f'<span>叶子节点: {self.meta["leaf_nodes"]} 个</span>' if 'leaf_nodes' in self.meta else ''}
            </div>
        </div>

        <div class="score-card">
            <div class="score">{self.meta['total_score']}</div>
            <div class="grade">{self.meta['grade']} - {self._grade_name(self.meta['grade'])}</div>
        </div>

        <div class="content">
"""

        # 维度得分
        for name, dim in self.dimensions.items():
            display_name = self._dimension_display_name(name)
            score = dim['score']
            max_score = dim['max']
            percentage = (score / max_score) * 100

            html += f"""
            <div class="dimension">
                <div class="dimension-title">{display_name}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {percentage}%">
                        {score}/{max_score} ({percentage:.0f}%)
                    </div>
                </div>
                <div class="metrics">
"""

            for metric_name, metric in dim['metrics'].items():
                value = self._format_metric_value(metric['value'])
                html += f"""
                    <div class="metric">
                        <div class="metric-name">{metric_name}</div>
                        <div class="metric-value">{value}</div>
                        <div class="metric-score">{metric['score']}/{metric['max']}</div>
                    </div>
"""

            html += """
                </div>
            </div>
"""

        # 优化建议
        if self.recommendations:
            html += """
            <div class="recommendations">
                <h3>优化建议</h3>
                <ul>
"""
            for rec in self.recommendations:
                html += f"                    <li>{rec}</li>\n"
            html += """
                </ul>
            </div>
"""

        html += """
        </div>
    </div>
</body>
</html>
"""
        return html

    # ================================
    # 工具方法
    # ================================

    def _format_timestamp(self, timestamp: str) -> str:
        """格式化时间戳"""
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def _grade_name(self, grade: str) -> str:
        """获取等级名称"""
        names = {
            "S": "优秀",
            "A": "良好",
            "B": "中等",
            "C": "较差",
            "D": "不健康"
        }
        return names.get(grade, "未知")

    def _grade_color(self, grade: str) -> str:
        """获取等级颜色"""
        colors = {
            "S": "#28a745",
            "A": "#17a2b8",
            "B": "#ffc107",
            "C": "#fd7e14",
            "D": "#dc3545"
        }
        return colors.get(grade, "#6c757d")

    def _dimension_display_name(self, name: str) -> str:
        """维度显示名称"""
        names = {
            "structure": "结构健康度",
            "content": "内容分布",
            "time": "时间活跃度",
            "naming": "命名规范",
            "overall": "综合评分"
        }
        return names.get(name, name)

    def _generate_bar(self, percentage: float, width: int = 20) -> str:
        """生成进度条"""
        filled = int(percentage / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def _status_icon(self, score: int, reverse: bool = False) -> str:
        """生成状态图标"""
        if reverse:
            if score >= 4:
                return "✓"
            elif score >= 2:
                return "⚠️"
            else:
                return "✗"
        else:
            if score >= 4:
                return "✓"
            elif score >= 2:
                return "⚠️"
            else:
                return "✗"

    def _depth_comment(self, depth: int) -> str:
        """深度评价"""
        if depth <= 2:
            return "合理"
        elif depth == 3:
            return "适中"
        elif depth == 4:
            return "略深"
        else:
            return "过深"

    def _format_metric_value(self, value: Any) -> str:
        """格式化指标值"""
        if isinstance(value, dict):
            if "ratio" in value and "count" in value:
                return f"{value['count']} 个 ({value['ratio']}%)"
            elif "average" in value and "std" in value:
                return f"平均 {value['average']} 层，标准差 {value['std']}"
            elif "count" in value and "types" in value:
                return f"{value['count']} 种 ({', '.join(value['types'])})"
            elif "count" in value:
                return f"{value['count']} 个"
            elif "ratio" in value:
                return f"{value['ratio']}%"
            elif "growth_rate" in value:
                return f"+{value['growth_rate']}%"
            elif "cv" in value:
                return f"CV={value['cv']}"
            elif "avg_days_ago" in value:
                return f"{value['avg_days_ago']:.0f} 天"
            elif "chinese_ratio" in value and "english_ratio" in value:
                return f"中文 {value['chinese_ratio']}%，英文 {value['english_ratio']}%"
            elif "previous" in value and "current" in value:
                return f"{value['previous']} → {value['current']} (+{value['growth_rate']}%)"
            elif "average" in value:
                return f"平均 {value['average']:.0f} 字"
            else:
                return str(value)
        else:
            return str(value)

    def save_report(self, content: str, output_path: str):
        """保存报告到文件"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(output_file.absolute())


# ================================
# 命令行入口
# ================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="生成知识库评价报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成文本报告
  python3 report_generator.py --text

  # 生成 HTML 报告
  python3 report_generator.py --html --output report.html

  # 生成 Markdown 报告
  python3 report_generator.py --markdown --output report.md

  # 生成所有格式
  python3 report_generator.py --all --output-dir ./reports
        """
    )

    parser.add_argument("--input", "-i",
                       help="评价结果 JSON 文件路径")
    parser.add_argument("--text", "-t", action="store_true",
                       help="生成文本报告")
    parser.add_argument("--html", action="store_true",
                       help="生成 HTML 报告")
    parser.add_argument("--markdown", "-m", action="store_true",
                       help="生成 Markdown 报告")
    parser.add_argument("--all", "-a", action="store_true",
                       help="生成所有格式")
    parser.add_argument("--output", "-o",
                       help="输出文件路径")
    parser.add_argument("--output-dir",
                       help="输出目录（用于 --all）")

    args = parser.parse_args()

    # 加载评价结果
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            evaluation = json.load(f)
    else:
        # 从 evaluator 导入
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from evaluator import WikiEvaluator

        evaluator = WikiEvaluator()
        evaluation = evaluator.evaluate_all()

    generator = EvaluationReportGenerator(evaluation)

    # 生成报告
    if args.all:
        # 生成所有格式
        output_dir = Path(args.output_dir or "./reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 文本报告
        text_content = generator.generate_text_report()
        text_path = generator.save_report(text_content, output_dir / "report.txt")
        print(f"✓ 文本报告已保存: {text_path}")

        # HTML 报告
        html_content = generator.generate_html_report()
        html_path = generator.save_report(html_content, output_dir / "report.html")
        print(f"✓ HTML 报告已保存: {html_path}")

        # Markdown 报告
        md_content = generator.generate_markdown_report()
        md_path = generator.save_report(md_content, output_dir / "report.md")
        print(f"✓ Markdown 报告已保存: {md_path}")

    else:
        # 生成指定格式
        if args.text:
            content = generator.generate_text_report()
            output = args.output or "report.txt"
            path = generator.save_report(content, output)
            print(f"✓ 文本报告已保存: {path}")

        if args.html:
            content = generator.generate_html_report()
            output = args.output or "report.html"
            path = generator.save_report(content, output)
            print(f"✓ HTML 报告已保存: {path}")

        if args.markdown:
            content = generator.generate_markdown_report()
            output = args.output or "report.md"
            path = generator.save_report(content, output)
            print(f"✓ Markdown 报告已保存: {path}")

        # 如果没有指定任何格式，显示帮助
        if not (args.text or args.html or args.markdown):
            parser.print_help()


if __name__ == "__main__":
    main()
