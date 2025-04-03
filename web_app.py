#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动视频翻译工具 - Web应用入口点

提供Web界面，用于将视频中的语音转换为多语言字幕。
"""

import os
import sys
from pathlib import Path

# 确保src包在Python路径中
src_path = Path(__file__).resolve().parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 创建必要的目录
from src.utils.config import load_config, ensure_directories
from src.utils.logger import setup_logger

# 加载配置
config = load_config()

# 设置日志
setup_logger(config.log_dir, config.log_level)

# 确保必要的目录存在
ensure_directories(config)


def main():
    """启动Web应用"""
    import uvicorn
    from src.web.app import app
    
    # 打印启动信息
    print("\n自动视频翻译工具 - Web界面")
    print("将视频中的语音转换为多语言字幕\n")
    print("正在启动Web服务器...")
    print("启动后，请在浏览器中访问: http://localhost:8000\n")
    
    # 启动Web服务器
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()