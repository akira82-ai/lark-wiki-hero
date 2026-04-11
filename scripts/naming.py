#!/usr/bin/env python3
"""
命名规则学习器 - 分析知识库文件命名规范并重命名本地文件
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from lark_api import require_config, build_node_tree, flatten_node_tree, load_config


class NamingPatternLearner:
    """命名规则学习器"""

    # 常见命名模式
    COMMON_PATTERNS = {
        "date_prefix": r"^(\d{4}[-_]?\d{2}[-_]?\d{2})[-_]?(.+)",  # 20240101_标题
        "category_prefix": r"^([A-Za-z\u4e00-\u9fff]+)[-_:](.+)",    # 技术_标题
        "number_prefix": r"^(\d+)[-.](.+)",                          # 01.标题
        "bracket_suffix": r"^(.+)\[([^\]]+)\]$",                    # 标题[标签]
    }

    def __init__(self):
        self.patterns = {}
        self._learn_patterns()

    def _learn_patterns(self):
        """从知识库学习命名模式"""
        print("正在分析知识库命名规范...")

        # 获取知识库节点
        tree = build_node_tree(max_depth=3)
        flat_nodes = flatten_node_tree(tree)

        # 收集文档名称
        doc_names = []
        for token, info in flat_nodes.items():
            if info["obj_type"] in ["docx", "doc"]:
                doc_names.append(info["title"])

        if not doc_names:
            print("⚠️ 知识库中没有找到文档，无法学习命名规范")
            return

        print(f"分析了 {len(doc_names)} 个文档")

        # 分析日期前缀模式
        date_count = 0
        category_count = 0
        number_count = 0

        for name in doc_names:
            # 检测日期前缀
            if re.match(r"^\d{4}[-_]?\d{2}[-_]?\d{2}", name):
                date_count += 1

            # 检测分类前缀
            if re.match(r"^[A-Za-z\u4e00-\u9fff]+[-_:]", name):
                category_count += 1

            # 检测数字前缀
            if re.match(r"^\d+[-.]", name):
                number_count += 1

        # 确定主要模式（占比超过 30%）
        total = len(doc_names)

        if date_count / total > 0.3:
            self.patterns["date_prefix"] = True
            print(f"✓ 检测到日期前缀模式 ({date_count}/{total})")

        if category_count / total > 0.3:
            self.patterns["category_prefix"] = True
            print(f"✓ 检测到分类前缀模式 ({category_count}/{total})")

        if number_count / total > 0.3:
            self.patterns["number_prefix"] = True
            print(f"✓ 检测到数字前缀模式 ({number_count}/{total})")

        if not self.patterns:
            print("⚠️ 未检测到明显的命名模式")

    def generate_name(self, file_path: str, category: str = "") -> str:
        """
        根据学习的规则生成新文件名

        Args:
            file_path: 原始文件路径
            category: 分类（可选）

        Returns:
            新文件名（不含扩展名）
        """
        file_path = Path(file_path)
        original_name = file_path.stem

        # 如果没有学习到模式，返回原始名称
        if not self.patterns:
            return original_name

        new_name = original_name

        # 应用日期前缀
        if "date_prefix" in self.patterns:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y%m%d")
            if not re.match(r"^\d{8}", new_name):
                new_name = f"{date_str}_{new_name}"

        # 应用分类前缀
        if "category_prefix" in self.patterns and category:
            if not new_name.startswith(f"{category}_") and not new_name.startswith(f"{category}-"):
                new_name = f"{category}_{new_name}"

        return new_name

    def rename_file(self, file_path: str, category: str = "",
                   dry_run: bool = False) -> Optional[str]:
        """
        重命名文件

        Args:
            file_path: 文件路径
            category: 分类（可选）
            dry_run: 是否仅预览不执行

        Returns:
            新文件路径，如果不需重命名返回 None
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"✗ 文件不存在: {file_path}")
            return None

        # 生成新名称
        new_name = self.generate_name(str(file_path), category)
        new_path = file_path.parent / f"{new_name}{file_path.suffix}"

        # 检查是否需要重命名
        if new_path == file_path:
            print(f"✓ 文件名已符合规范: {file_path.name}")
            return None

        # 显示变更
        print(f"{'预览' if dry_run else '重命名'}: {file_path.name}")
        print(f"  → {new_path.name}")

        # 执行重命名
        if not dry_run:
            try:
                file_path.rename(new_path)
                print(f"  ✓ 已重命名")
            except Exception as e:
                print(f"  ✗ 重命名失败: {e}")
                return None

        return str(new_path)


def main():
    """命令行入口"""
    import argparse

    # 首先检查配置
    try:
        require_config()
    except SystemExit:
        return

    parser = argparse.ArgumentParser(
        description="学习知识库命名规范并重命名文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 仅学习命名规范（不执行重命名）
  python3 naming.py --learn-only

  # 学习并重命名单个文件
  python3 naming.py --learn-and-rename document.md

  # 重命名时指定分类
  python3 naming.py --learn-and-rename document.md --category 技术

  # 批量重命名目录
  python3 naming.py --rename-dir ~/Documents/notes
        """
    )

    parser.add_argument("--learn-only", action="store_true",
                       help="仅学习命名规范，不执行重命名")
    parser.add_argument("--learn-and-rename", metavar="FILE",
                       help="学习并重命名文件")
    parser.add_argument("--rename-dir", metavar="DIR",
                       help="批量重命名目录中的文件")
    parser.add_argument("--category", "-c", default="",
                       help="指定分类前缀")
    parser.add_argument("--dry-run", "-n", action="store_true",
                       help="预览模式，不实际重命名")

    args = parser.parse_args()

    learner = NamingPatternLearner()

    # 仅学习模式
    if args.learn_only:
        print("\n学习的命名模式:")
        if learner.patterns:
            for pattern, enabled in learner.patterns.items():
                print(f"  - {pattern}: {'✓' if enabled else '✗'}")
        else:
            print("  (无)")
        return

    # 重命名单个文件
    if args.learn_and_rename:
        learner.rename_file(
            args.learn_and_rename,
            category=args.category,
            dry_run=args.dry_run
        )
        return

    # 批量重命名目录
    if args.rename_dir:
        dir_path = Path(args.rename_dir)
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"✗ 目录不存在: {dir_path}")
            return

        md_files = list(dir_path.rglob("*.md")) + list(dir_path.rglob("*.markdown"))
        print(f"\n找到 {len(md_files)} 个 Markdown 文件\n")

        for file_path in md_files:
            learner.rename_file(
                str(file_path),
                category=args.category,
                dry_run=args.dry_run
            )
        return

    # 没有指定操作
    parser.print_help()


if __name__ == "__main__":
    main()
