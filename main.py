#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动视频翻译工具 - 主程序入口点

提供命令行界面，用于将视频中的语音转换为多语言字幕。
"""

import os
import sys
from pathlib import Path

# 确保src包在Python路径中
src_path = Path(__file__).resolve().parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.cli.commands import app
from src.utils.logger import setup_logger
from src.utils.config import load_config, ensure_directories


def main():
    """主程序入口点"""
    # 应用程序由Typer接管命令行参数处理
    app()


if __name__ == "__main__":
    main()