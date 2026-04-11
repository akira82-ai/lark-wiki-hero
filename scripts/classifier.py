#!/usr/bin/env python3
"""
智能分类器 - 分析文档内容并匹配知识库最佳分类目录
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from lark_api import require_config, build_node_tree, flatten_node_tree, load_config


class WikiClassifier:
    """知识库智能分类器"""

    # 预定义分类关键词库
    CATEGORY_KEYWORDS = {
        "技术": ["代码", "开发", "编程", "算法", "API", "框架", "接口", "数据库",
                "后端", "前端", "全栈", "测试", "部署", "运维", "服务器",
                "Python", "JavaScript", "Java", "Go", "TypeScript", "Rust",
                "React", "Vue", "Angular", "Node.js", "Django", "Flask"],
        "产品": ["需求", "功能", "用户", "体验", "设计", "原型", "交互",
                "PRD", "产品文档", "产品需求", "用户故事"],
        "运营": ["数据", "增长", "活动", "用户", "渠道", "推广", "营销",
                "分析", "报告", "KPI", "ROI", "转化率"],
        "管理": ["流程", "规范", "制度", "计划", "总结", "会议", "项目",
                "OKR", "KPI", "周报", "月报", "复盘"],
        "文档": ["手册", "指南", "教程", "入门", "快速开始", "FAQ",
                "说明", "帮助", "文档"],
        "设计": ["UI", "UX", "界面", "视觉", "交互", "图标", "色彩",
                "Figma", "Sketch", "设计系统"],
    }

    def __init__(self):
        self.category_tree = None
        self.flat_categories = None
        self._load_categories()

    def _load_categories(self):
        """加载知识库分类结构"""
        print("正在加载知识库分类结构...")
        self.category_tree = build_node_tree(max_depth=5)
        self.flat_categories = flatten_node_tree(self.category_tree)
        print(f"✓ 已加载 {len(self.flat_categories)} 个分类节点")

    def _extract_keywords(self, text: str, max_chars: int = 200) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 输入文本
            max_chars: 最大分析字符数

        Returns:
            关键词列表
        """
        # 限制分析长度
        text = text[:max_chars]

        # 中文分词（简单实现：按字符分割，过滤非中文字符）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        chinese_text = ''.join(chinese_chars)

        # 英文单词提取
        english_words = re.findall(r'\b[A-Za-z]{2,}\b', text)

        # 合并关键词
        keywords = []

        # 提取中文关键词（2-4字的连续词组）
        for i in range(len(chinese_text) - 1):
            for length in [2, 3, 4]:
                if i + length <= len(chinese_text):
                    word = chinese_text[i:i + length]
                    if len(word) == length:
                        keywords.append(word)

        # 添加英文单词
        keywords.extend([w.capitalize() for w in english_words])

        # 去重并返回
        return list(set(keywords))

    def _calculate_similarity(self, keywords: List[str],
                            category_title: str) -> float:
        """
        计算关键词与分类标题的相似度

        Args:
            keywords: 关键词列表
            category_title: 分类标题

        Returns:
            相似度分数 (0-1)
        """
        if not keywords:
            return 0.0

        score = 0.0
        total_keywords = len(keywords)

        # 直接匹配
        for keyword in keywords:
            if keyword.lower() in category_title.lower():
                score += 1.0

        # 部分匹配（子串）
        for keyword in keywords:
            if len(keyword) >= 2 and keyword.lower() in category_title.lower():
                score += 0.5

        return score / total_keywords if total_keywords > 0 else 0.0

    def _classify_by_keywords(self, title: str, content: str = "") -> List[Tuple[str, float]]:
        """
        基于关键词进行分类

        Args:
            title: 文档标题
            content: 文档内容

        Returns:
            [(node_token, score)] 列表，按分数排序
        """
        # 提取关键词
        title_keywords = self._extract_keywords(title, max_chars=100)
        content_keywords = self._extract_keywords(content, max_chars=200)

        # 标题关键词权重更高
        all_keywords = title_keywords * 3 + content_keywords

        # 计算每个分类的分数
        scores = []
        for token, info in self.flat_categories.items():
            # 只考虑文件夹类型的节点
            if info["obj_type"] != "wiki":
                continue

            # 计算相似度
            similarity = self._calculate_similarity(all_keywords, info["title"])

            # 路径匹配（完整路径的相似度）
            path_similarity = self._calculate_similarity(
                all_keywords, info["path"]
            )

            # 综合分数
            total_score = similarity * 0.7 + path_similarity * 0.3

            if total_score > 0:
                scores.append((token, total_score, info))

        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)

        return [(token, score) for token, score, _ in scores[:10]]

    def classify(self, file_path: str) -> Optional[Dict]:
        """
        分类单个文件

        Args:
            file_path: 文件路径

        Returns:
            分类结果 {best_token, best_path, confidence, alternatives}
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"文件不存在: {file_path}")
            return None

        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None

        # 提取标题（文件名）
        title = file_path.stem

        # 进行分类
        print(f"正在分析文档: {title}")
        print(f"  提取关键词...")

        scores = self._classify_by_keywords(title, content)

        if not scores:
            print("  ⚠️ 未找到匹配的分类，将使用根目录")
            config = load_config()
            return {
                "best_token": config.get("default_parent_token", ""),
                "best_path": "根目录",
                "confidence": 0.0,
                "alternatives": []
            }

        best_token, best_score = scores[0]
        best_info = self.flat_categories[best_token]

        print(f"  检测到关键词: {', '.join(self._extract_keywords(title + content[:200]))[:10]}")
        print(f"  匹配目录: {best_info['path']}")
        print(f"  置信度: {best_score:.2%}")

        # 返回前 3 个备选
        alternatives = []
        for token, score in scores[1:4]:
            info = self.flat_categories[token]
            alternatives.append({
                "token": token,
                "path": info["path"],
                "score": score
            })

        return {
            "best_token": best_token,
            "best_path": best_info["path"],
            "confidence": best_score,
            "alternatives": alternatives
        }


def main():
    # 首先检查配置
    try:
        require_config()
    except SystemExit:
        return
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="智能分类文档到知识库")
    parser.add_argument("file", help="要分类的文件路径")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="显示详细分类信息")

    args = parser.parse_args()

    classifier = WikiClassifier()
    result = classifier.classify(args.file)

    if result:
        print(f"\n最佳匹配: {result['best_path']}")
        print(f"节点 Token: {result['best_token']}")

        if args.verbose and result['alternatives']:
            print("\n备选分类:")
            for alt in result['alternatives']:
                print(f"  - {alt['path']} ({alt['score']:.2%})")


if __name__ == "__main__":
    main()
