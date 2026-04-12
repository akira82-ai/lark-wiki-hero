#!/usr/bin/env python3
"""
批量上传器 - 智能分类并上传文档到知识库
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
from lark_api import create_document, load_config, require_config


class WikiUploader:
    """知识库批量上传器"""

    def __init__(self, delay_ms: int = 1000):
        """
        初始化上传器

        Args:
            delay_ms: 批量上传时的延迟（毫秒）
        """
        self.delay = delay_ms / 1000.0

    def upload_single_file(self, file_path: str,
                          parent_token: Optional[str] = None) -> Optional[Dict]:
        """
        上传单个文件

        Args:
            file_path: 文件路径
            parent_token: 父节点 token（未指定时使用默认父节点）

        Returns:
            上传结果
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"✗ 文件不存在: {file_path}")
            return None

        # 只处理 markdown 文件
        if file_path.suffix.lower() not in ['.md', '.markdown']:
            print(f"✗ 跳过非 Markdown 文件: {file_path}")
            return None

        # 确定目标节点
        target_token = parent_token
        if target_token is None:
            config = load_config()
            target_token = config.get("default_parent_token", "")

        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"✗ 读取文件失败: {e}")
            return None

        # 提取标题（使用文件名）
        title = file_path.stem

        # 创建文档
        print(f"正在上传: {title}")
        result = create_document(
            title=title,
            parent_node_token=target_token,
            markdown=content
        )

        if result:
            print(f"✓ 上传成功")
            print(f"  文档: {result}")
            return {
                "file": str(file_path),
                "status": "success",
                "url": result,
                "target": target_token
            }
        else:
            print(f"✗ 上传失败")
            return {
                "file": str(file_path),
                "status": "failed"
            }

    def upload_directory(self, directory: str,
                        parent_token: Optional[str] = None) -> List[Dict]:
        """
        批量上传目录中的所有 Markdown 文件

        Args:
            directory: 目录路径
            parent_token: 父节点 token（未指定时使用默认父节点）

        Returns:
            上传结果列表
        """
        directory = Path(directory)

        if not directory.exists() or not directory.is_dir():
            print(f"✗ 目录不存在: {directory}")
            return []

        # 查找所有 markdown 文件
        md_files = list(directory.rglob("*.md")) + list(directory.rglob("*.markdown"))

        if not md_files:
            print(f"✗ 目录中没有找到 Markdown 文件: {directory}")
            return []

        print(f"\n{'='*50}")
        print(f"批量上传模式")
        print(f"{'='*50}")
        print(f"扫描目录: {directory}")
        print(f"找到 {len(md_files)} 个 Markdown 文件\n")

        # 批量上传
        results = []
        for i, file_path in enumerate(md_files, 1):
            print(f"\n[{i}/{len(md_files)}]", end=" ")

            result = self.upload_single_file(
                file_path,
                parent_token
            )

            if result:
                results.append(result)

            # 添加延迟避免 API 限流
            if i < len(md_files):
                time.sleep(self.delay)

        # 打印总结
        self._print_summary(results)

        return results

    def _print_summary(self, results: List[Dict]):
        """打印上传总结"""
        if not results:
            print(f"\n{'='*50}")
            print("没有文件被上传")
            return

        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = len(results) - success_count

        print(f"\n{'='*50}")
        print("上传总结")
        print(f"{'='*50}")
        print(f"总数: {len(results)}")
        print(f"成功: {success_count} ✓")
        print(f"失败: {failed_count} ✗")

        if failed_count > 0:
            print("\n失败的文件:")
            for r in results:
                if r["status"] == "failed":
                    print(f"  - {r['file']}")


def main():
    """命令行入口"""
    import argparse

    # 首先检查配置
    try:
        require_config()
    except SystemExit:
        return

    parser = argparse.ArgumentParser(
        description="智能上传文档到飞书知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 上传单个文件
  python3 uploader.py document.md

  # 上传到指定目录
  python3 uploader.py document.md --parent <node_token>

  # 批量上传目录
  python3 uploader.py --dir ~/Documents/notes

  # 批量上传到指定目录
  python3 uploader.py --dir ~/Documents/notes --parent <node_token>
        """
    )

    parser.add_argument("file", nargs="?", help="要上传的文件路径")
    parser.add_argument("--dir", "-d", help="批量上传目录")
    parser.add_argument("--parent", "-p", help="父节点 token（未指定时使用默认父节点）")

    args = parser.parse_args()

    uploader = WikiUploader()

    # 批量上传目录
    if args.dir:
        uploader.upload_directory(
            args.dir,
            parent_token=args.parent
        )
    # 上传单个文件
    elif args.file:
        uploader.upload_single_file(
            args.file,
            parent_token=args.parent
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
