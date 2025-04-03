#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动视频翻译工具 - 测试脚本

用于测试视频翻译流程的完整性，包括视频处理、语音识别、翻译和字幕生成。
"""

import os
import sys
from pathlib import Path
import argparse

# 确保src包在Python路径中
src_path = Path(__file__).resolve().parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.core.processor import VideoTranslator
from src.utils.config import load_config, ensure_directories
from src.utils.logger import setup_logger


def progress_callback(stage, message, percent=None):
    """进度回调函数
    
    Args:
        stage: 当前阶段名称
        message: 进度消息
        percent: 进度百分比（0-1）
    """
    if percent is not None:
        print(f"[{stage}] {message} - {percent*100:.1f}%")
    else:
        print(f"[{stage}] {message}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试视频翻译流程")
    parser.add_argument(
        "video_path", 
        help="视频文件路径"
    )
    parser.add_argument(
        "-l", "--languages", 
        nargs="+", 
        default=["en", "zh-CN"], 
        help="目标语言代码，默认为英语和简体中文"
    )
    parser.add_argument(
        "-f", "--format", 
        choices=["srt", "vtt"], 
        default="srt", 
        help="字幕格式，默认为SRT"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="显示详细日志"
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 设置日志级别
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger(config.log_dir, log_level)
    
    # 确保必要的目录存在
    ensure_directories(config)
    
    # 更新配置
    config.target_languages = args.languages
    config.subtitle_format = args.format
    
    # 检查视频文件是否存在
    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"错误: 视频文件不存在: {video_path}")
        return 1
    
    print("\n自动视频翻译工具 - 测试脚本")
    print("将视频中的语音转换为多语言字幕\n")
    print(f"处理视频: {video_path}")
    print(f"目标语言: {', '.join(config.target_languages)}")
    print(f"字幕格式: {config.subtitle_format}\n")
    
    try:
        # 创建视频翻译器
        translator = VideoTranslator(config)
        
        # 执行翻译
        result = translator.process_video(
            video_path=str(video_path),
            progress_callback=progress_callback
        )
        
        # 显示结果
        print("\n处理完成!")
        print("生成的字幕文件:")
        for lang, subtitle_path in result.items():
            print(f"  - {lang}: {subtitle_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())