#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具类模块 - 日志配置

配置应用的日志系统，使用loguru库实现统一的日志记录。
"""

import os
import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir=None, log_level="INFO"):
    """配置日志系统

    Args:
        log_dir: 日志文件目录，如果为None则只输出到控制台
        log_level: 日志级别，默认为INFO
    """
    # 移除默认处理器
    logger.remove()

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # 如果指定了日志目录，添加文件处理器
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 添加日志文件处理器，按天轮转
        logger.add(
            log_dir / "video_translator_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="00:00",  # 每天午夜轮转
            retention="30 days",  # 保留30天
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
        )

        # 添加错误日志文件处理器
        logger.add(
            log_dir / "video_translator_error_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            level="ERROR",
            rotation="00:00",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=True,
        )

    logger.debug(f"日志系统初始化完成，级别: {log_level}")
    return logger