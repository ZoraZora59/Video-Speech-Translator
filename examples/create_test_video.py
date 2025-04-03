#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动视频翻译工具 - 测试视频生成脚本

用于生成一个简单的测试视频，包含音频轨道，用于测试视频翻译流程。
"""

import os
import sys
from pathlib import Path

try:
    from moviepy.editor import ColorClip, AudioClip, CompositeAudioClip
    import numpy as np
except ImportError:
    print("请先安装依赖: pip install moviepy numpy")
    sys.exit(1)


def create_test_video(output_path, duration=5, size=(640, 480), fps=24):
    """创建测试视频
    
    Args:
        output_path: 输出文件路径
        duration: 视频时长（秒）
        size: 视频尺寸
        fps: 帧率
    """
    # 创建一个蓝色背景视频
    color_clip = ColorClip(size=size, color=(0, 0, 255), duration=duration)
    
    # 创建一个1000Hz的正弦波音频
    def make_frame(t):
        return 0.5 * np.sin(2 * np.pi * 1000 * t)
    
    audio_clip = AudioClip(make_frame=make_frame, duration=duration)
    audio_clip = audio_clip.set_fps(44100)
    
    # 将音频添加到视频
    color_clip = color_clip.set_audio(audio_clip)
    
    # 设置视频编解码器
    color_clip = color_clip.set_fps(fps)
    
    # 确保输出目录存在
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 写入视频文件
    print(f"正在生成测试视频: {output_path}")
    color_clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        fps=fps
    )
    print(f"测试视频生成完成: {output_path}")


def main():
    """主函数"""
    # 设置输出路径
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    output_path = project_dir / "temp" / "test_video.mp4"
    
    # 创建temp目录
    (project_dir / "temp").mkdir(exist_ok=True)
    
    # 生成测试视频
    create_test_video(output_path)
    
    print(f"\n可以使用以下命令测试视频翻译流程:")
    print(f"python examples/test_translator.py {output_path}\n")


if __name__ == "__main__":
    main()