#!/usr/bin/env python3
"""
Markdown 格式化器 - 统一和优化 Markdown 文档格式
"""

import re
from pathlib import Path
from typing import Dict, List


class MarkdownFormatter:
    """Markdown 文档格式化器"""

    # 默认格式化规则
    DEFAULT_RULES = {
        "unify_blank_lines": True,      # 统一空行（最多2个连续空行）
        "trim_trailing_spaces": True,   # 删除行尾空格
        "normalize_headers": True,      # 统一标题格式（# 后空格）
        "fix_lists": True,              # 修复列表格式
        "normalize_links": True,        # 标准化链接格式
        "preserve_code_blocks": True    # 保持代码块不变
    }

    def __init__(self, rules: Dict = None, max_file_size_kb: int = 100):
        """
        初始化格式化器

        Args:
            rules: 格式化规则字典
            max_file_size_kb: 大文件阈值（KB），超过则跳过复杂格式化
        """
        self.rules = rules or self.DEFAULT_RULES.copy()
        self.max_file_size = max_file_size_kb * 1024

        # 统计信息
        self.stats = {
            "blank_lines_removed": 0,
            "trailing_spaces_trimmed": 0,
            "headers_normalized": 0,
            "lists_fixed": 0,
            "links_normalized": 0
        }

    def format_file(self, file_path: str,
                   output_path: str = None,
                   verbose: bool = True) -> bool:
        """
        格式化 Markdown 文件

        Args:
            file_path: 输入文件路径
            output_path: 输出文件路径（默认覆盖原文件）
            verbose: 是否显示详细信息

        Returns:
            是否成功
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"✗ 文件不存在: {file_path}")
            return False

        # 检查文件大小
        file_size = file_path.stat().st_size
        if verbose:
            print(f"正在格式化: {file_path.name}")
            print(f"  文件大小: {file_size / 1024:.1f} KB")

        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"✗ 读取文件失败: {e}")
            return False

        # 格式化内容
        is_large_file = file_size > self.max_file_size
        if is_large_file:
            print(f"  ⚠️ 文件较大，跳过复杂格式化")

        formatted = self.format_content(content, skip_complex=is_large_file)

        # 确定输出路径
        if output_path is None:
            output_path = file_path
        else:
            output_path = Path(output_path)

        # 写入文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted)
        except Exception as e:
            print(f"✗ 写入文件失败: {e}")
            return False

        # 打印统计信息
        if verbose:
            self._print_stats()

        if output_path != file_path and verbose:
            print(f"  ✓ 已保存到: {output_path}")

        return True

    def format_content(self, content: str, skip_complex: bool = False) -> str:
        """
        格式化 Markdown 内容

        Args:
            content: Markdown 内容
            skip_complex: 是否跳过复杂格式化（用于大文件）

        Returns:
            格式化后的内容
        """
        lines = content.split('\n')
        formatted_lines = []
        in_code_block = False
        code_fence_char = None

        for line in lines:
            # 检测代码块
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_fence_char = '```'
                else:
                    in_code_block = False
                    code_fence_char = None
                formatted_lines.append(line)
                continue

            # 检测其他代码块标记
            if line.strip().startswith('~~~'):
                if not in_code_block:
                    in_code_block = True
                    code_fence_char = '~~~'
                else:
                    in_code_block = False
                    code_fence_char = None
                formatted_lines.append(line)
                continue

            # 代码块内不做处理
            if in_code_block:
                formatted_lines.append(line)
                continue

            # 应用格式化规则
            processed = line
            changed = False

            # 删除行尾空格
            if self.rules["trim_trailing_spaces"]:
                trimmed = processed.rstrip()
                if trimmed != processed:
                    processed = trimmed
                    self.stats["trailing_spaces_trimmed"] += 1
                    changed = True

            # 标准化标题格式
            if self.rules["normalize_headers"]:
                header_match = re.match(r'^(#{1,6})([^#\s].*)$', processed)
                if header_match:
                    level = header_match.group(1)
                    text = header_match.group(2).strip()
                    new_line = f"{level} {text}"
                    if new_line != processed:
                        processed = new_line
                        self.stats["headers_normalized"] += 1
                        changed = True

            # 修复列表格式（跳过复杂处理时仅做简单修复）
            if self.rules["fix_lists"] and not skip_complex:
                # 确保列表符号后有空格
                list_match = re.match(r'^(\s*[-*+])([^\s])', processed)
                if list_match:
                    processed = f"{list_match.group(1)} {list_match.group(2)}"
                    self.stats["lists_fixed"] += 1
                    changed = True

                # 确保有序列表后有空格
                ordered_list_match = re.match(r'^(\s*\d+)([^\s\.])', processed)
                if ordered_list_match:
                    processed = f"{ordered_list_match.group(1)}. {ordered_list_match.group(2)}"
                    self.stats["lists_fixed"] += 1
                    changed = True

            # 标准化链接格式（跳过复杂处理时跳过）
            if self.rules["normalize_links"] and not skip_complex:
                # 确保链接格式正确 [text](url)
                link_pattern = r'\[([^\]]+)\]\s*\(\s*([^\)]+)\s*\)'
                new_line = re.sub(link_pattern, r'[\1](\2)', processed)
                if new_line != processed:
                    processed = new_line
                    self.stats["links_normalized"] += 1
                    changed = True

            formatted_lines.append(processed)

        # 统一空行
        if self.rules["unify_blank_lines"]:
            formatted_lines = self._unify_blank_lines(formatted_lines)

        return '\n'.join(formatted_lines)

    def _unify_blank_lines(self, lines: List[str]) -> List[str]:
        """
        统一空行（最多2个连续空行）

        Args:
            lines: 行列表

        Returns:
            处理后的行列表
        """
        result = []
        blank_count = 0
        original_blank_count = 0

        for line in lines:
            if line == '':
                blank_count += 1
                original_blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                # 统计实际移除的空行数
                if blank_count > 2:
                    self.stats["blank_lines_removed"] += (blank_count - 2)
                blank_count = 0
                result.append(line)

        return result

    def _print_stats(self):
        """打印格式化统计信息"""
        if not any(self.stats.values()):
            print("  ✓ 格式检查完成，无需修改")
            return

        print("  格式化结果:")
        if self.stats["blank_lines_removed"] > 0:
            print(f"    ✓ 统一空行: 移除 {self.stats['blank_lines_removed']} 个多余空行")
        if self.stats["trailing_spaces_trimmed"] > 0:
            print(f"    ✓ 清理行尾空格: {self.stats['trailing_spaces_trimmed']} 行")
        if self.stats["headers_normalized"] > 0:
            print(f"    ✓ 标准化标题: {self.stats['headers_normalized']} 个")
        if self.stats["lists_fixed"] > 0:
            print(f"    ✓ 修复列表格式: {self.stats['lists_fixed']} 处")
        if self.stats["links_normalized"] > 0:
            print(f"    ✓ 标准化链接: {self.stats['links_normalized']} 处")


def main():
    """命令行入口"""
    import argparse

    # 首先检查配置
    try:
        require_config()
    except SystemExit:
        return

    parser = argparse.ArgumentParser(
        description="格式化 Markdown 文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 格式化单个文件（覆盖原文件）
  python3 formatter.py document.md

  # 格式化并保存到新文件
  python3 formatter.py document.md -o formatted.md

  # 批量格式化目录
  python3 formatter.py --dir ~/Documents/notes

  # 显示详细统计信息
  python3 formatter.py document.md -v
        """
    )

    parser.add_argument("file", nargs="?", help="要格式化的文件路径")
    parser.add_argument("--dir", "-d", help="批量格式化目录")
    parser.add_argument("--output", "-o", help="输出文件路径（默认覆盖原文件）")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="显示详细统计信息")

    args = parser.parse_args()

    formatter = MarkdownFormatter()

    # 批量格式化目录
    if args.dir:
        dir_path = Path(args.dir)
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"✗ 目录不存在: {dir_path}")
            return

        md_files = list(dir_path.rglob("*.md")) + list(dir_path.rglob("*.markdown"))
        print(f"找到 {len(md_files)} 个 Markdown 文件\n")

        for file_path in md_files:
            formatter.format_file(str(file_path), verbose=args.verbose)
            # 重置统计
            formatter.stats = {k: 0 for k in formatter.stats}

    # 格式化单个文件
    elif args.file:
        formatter.format_file(
            args.file,
            output_path=args.output,
            verbose=args.verbose
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
