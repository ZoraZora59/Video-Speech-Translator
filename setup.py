#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动视频翻译工具 - 安装脚本

用于安装依赖并设置环境。
"""

from setuptools import setup, find_packages
from src import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="video-speech-translator",
    version=__version__,
    author="Video Speech Translator Team",
    author_email="example@example.com",
    description="自动将视频中的语音转换为多语言字幕",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Video-Speech-Translator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "video-translator=main:main",
            "video-translator-web=web_app:main",
        ],
    },
)