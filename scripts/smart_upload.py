#!/usr/bin/env python3
"""
智能上传助手 - 根据扩展名自动选择上传方式

扩展名支持：
  .pdf        → 创建文档 + 插入 PDF
  .md/.mdx    → 直接创建 Markdown 文档
  .txt        → 直接创建文本文档
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from lark_api import upload_pdf_to_wiki, create_document, require_config


class Uploader:
    """上传器"""

    def __init__(self):
        self.success_count = 0
        self.fail_count = 0
        self.results = []

    def upload(self, file_path: str, parent_token: str, title: str = "",
               target_path: str = "") -> Dict:
        """
        上传单个文件，根据扩展名选择上传方式

        Args:
            file_path: 文件路径
            parent_token: 目标父节点 token
            title: 文档标题（默认用文件名）
            target_path: 目标分类路径（用于结果展示）

        Returns:
            上传结果（含 target_path）
        """
        path = Path(file_path)
        if not title:
            title = path.stem

        suffix = path.suffix.lower()
        doc_url = None

        if suffix == ".pdf":
            doc_url = upload_pdf_to_wiki(str(path), title, parent_token)
        elif suffix in [".md", ".mdx"]:
            with open(path, "r", encoding="utf-8") as f:
                markdown = f.read()
            doc_url = create_document(title, parent_token, markdown)
        elif suffix == ".txt":
            with open(path, "r", encoding="utf-8") as f:
                markdown = f.read()
            doc_url = create_document(title, parent_token, markdown)
        else:
            print(f"  不支持的类型: {suffix}")

        if doc_url:
            self.success_count += 1
            return {"file": path.name, "target_path": target_path,
                    "doc_url": doc_url, "ok": True}
        else:
            self.fail_count += 1
            return {"file": path.name, "target_path": target_path,
                    "doc_url": None, "ok": False}

    def summary(self) -> str:
        """生成 Markdown 表格格式的上传结果"""
        total = self.success_count + self.fail_count
        lines = []
        lines.append("")
        lines.append("上传结果")
        lines.append("")
        lines.append("| 文件名 | 目标位置 | 链接 |")
        lines.append("|--------|---------|------|")

        for r in self.results:
            if r["doc_url"]:
                # doc_url 格式: https://my.feishu.cn/wiki/{node_token}
                node_token = r["doc_url"].rstrip("/").split("/")[-1]
                link = f"[链接](https://my.feishu.cn/wiki/{node_token})"
            else:
                link = "—"
            path_display = r["target_path"] or "—"
            lines.append(f"| {r['file']} | {path_display} | {link} |")

        lines.append("")
        lines.append(f"总计 {total} | 成功 {self.success_count} | 失败 {self.fail_count}")
        return "\n".join(lines)


def upload_batch(tasks: List[Dict], delay: float = 1.0) -> Uploader:
    """
    批量上传文件（逐文件执行）

    Args:
        tasks: 上传任务列表，每项包含 file_path, parent_token, title, target_path
        delay: 每文件间隔秒数

    Returns:
        Uploader 实例（含统计结果）
    """
    uploader = Uploader()
    total = len(tasks)

    print(f"\n开始批量上传 {total} 个文件...\n")

    for i, task in enumerate(tasks, 1):
        file_path = task["file_path"]
        parent_token = task["parent_token"]
        title = task.get("title", "")
        path = Path(file_path)

        print(f"[{i}/{total}] {path.name}...")
        target = task.get("target_path", "")
        result = uploader.upload(file_path, parent_token, title, target)
        uploader.results.append(result)

        if result["ok"]:
            print(f"  ✓ {result['doc_url']}")
        else:
            print(f"  ✗ 上传失败")

        if i < total:
            time.sleep(delay)

    print(uploader.summary())
    return uploader


def main():
    """命令行入口 - 从 stdin 或 --tasks 参数读取任务"""
    import argparse

    parser = argparse.ArgumentParser(description="飞书知识库批量上传工具")
    parser.add_argument("--tasks", help="JSON 格式的任务列表文件路径")
    parser.add_argument("--delay", type=float, default=1.0, help="每文件间隔秒数 (默认 1.0)")

    args = parser.parse_args()

    require_config()

    if args.tasks:
        with open(args.tasks, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    else:
        print("用法: python3 smart_upload.py --tasks tasks.json")
        sys.exit(1)

    upload_batch(tasks, delay=args.delay)


if __name__ == "__main__":
    main()
