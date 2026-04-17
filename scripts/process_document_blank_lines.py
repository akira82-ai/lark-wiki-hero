#!/usr/bin/env python3
"""移除飞书文档中的多余空行，保留段落间的单个空行"""

import subprocess
import sys
import json

def fetch_document(doc_token):
    """获取文档内容"""
    result = subprocess.run(
        ['lark-cli', 'docs', '+fetch', '--doc', doc_token, '--format', 'pretty'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"获取文档失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout

def remove_extra_blank_lines(content):
    """
    移除多余的空行，保留段落间的一个空行以维持阅读体验

    规则：
    1. 连续的多个空行（2个或更多）替换为单个空行
    2. 保留段落间的单个空行
    3. 代码块内部保持不变
    """
    lines = content.split('\n')
    result = []
    consecutive_blank = 0
    in_code_block = False

    for line in lines:
        # 检测代码块
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
            else:
                in_code_block = False
            result.append(line)
            consecutive_blank = 0
            continue

        # 在代码块内，保持原样
        if in_code_block:
            result.append(line)
            consecutive_blank = 0
            continue

        # 检测空行
        if line.strip() == '':
            consecutive_blank += 1
            # 只保留连续空行的第一个
            if consecutive_blank == 1:
                result.append(line)
        else:
            # 非空行，重置计数器
            consecutive_blank = 0
            result.append(line)

    return '\n'.join(result)

def update_document(doc_token, content):
    """更新文档内容"""
    result = subprocess.run(
        ['lark-cli', 'docs', '+update', '--doc', doc_token,
         '--mode', 'overwrite', '--markdown', '-'],
        input=content,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"更新文档失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout

def main():
    if len(sys.argv) < 2:
        print("用法: python3 process_document_blank_lines.py <doc_token>", file=sys.stderr)
        sys.exit(1)

    doc_token = sys.argv[1]

    print(f"📥 正在获取文档: {doc_token}")
    original_content = fetch_document(doc_token)

    print("🔧 正在处理空行...")
    processed_content = remove_extra_blank_lines(original_content)

    # 统计移除的空行数
    original_lines = original_content.split('\n')
    processed_lines = processed_content.split('\n')
    removed_lines = len(original_lines) - len(processed_lines)

    print(f"✂️  移除了 {removed_lines} 行")

    print(f"📤 正在更新文档...")
    update_document(doc_token, processed_content)

    print("✅ 文档更新完成！")

if __name__ == '__main__':
    main()
