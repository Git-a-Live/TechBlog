#!/usr/bin/env python3
"""把仓库根目录的笔记同步到 Quartz 的 content 目录。

只复制 Markdown 与附件，跳过版本控制、Obsidian 配置与站点工程本身。
内容目录默认位于系统临时目录，避免在笔记库内产生重复笔记。
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = Path(tempfile.gettempdir()) / "techblog-content"

SKIP_DIRS = {
    ".git",
    ".github",
    ".obsidian",
    ".workbuddy",
    "node_modules",
    "scripts",
    "site",
}
SKIP_FILES = {".DS_Store"}
ATTACHMENT_DIR = "附件"

INDEX_TEMPLATE = """---
title: TechBlog
---
Android、Kotlin、Compose、Flutter 与计算机基础的学习笔记。

- [Android 开发积累](android开发积累/)
- [跨平台开发](跨平台开发/)
- [语言基础](语言基础/)
- [计算机基础](计算机基础/)
- [程序员素养](程序员素养/)
"""


def remove_tree(path: Path) -> None:
    """删除目录；Windows 下 copytree 会保留只读属性，需先去掉再删。"""

    def handle(func, target, error):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=handle)


def iter_notes():
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if path.name in SKIP_FILES:
            continue
        yield path, rel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="内容输出目录")
    args = parser.parse_args()

    if not (ROOT / "site" / "quartz").is_dir():
        print("未找到 site/quartz，请先初始化 Quartz 工程", file=sys.stderr)
        return 1

    content = Path(args.out).expanduser().resolve()
    if content.exists():
        remove_tree(content)
    content.mkdir(parents=True)

    count = 0
    for src, rel in iter_notes():
        dst = content / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        count += 1

    asset_count = 0
    attachments = ROOT / ATTACHMENT_DIR
    if attachments.is_dir():
        dst_dir = content / ATTACHMENT_DIR
        shutil.copytree(attachments, dst_dir)
        asset_count = sum(1 for p in dst_dir.rglob("*") if p.is_file())

    index = content / "index.md"
    if not index.exists():
        index.write_text(INDEX_TEMPLATE, encoding="utf-8")

    print(f"已同步笔记 {count} 篇，附件 {asset_count} 个 -> {content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
