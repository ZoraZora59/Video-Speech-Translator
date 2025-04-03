#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具类模块 - 配置管理

负责加载和管理应用的配置信息，包括默认设置和用户自定义配置。
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from loguru import logger
from pydantic import BaseModel, Field

from src.utils.exceptions import ConfigurationError


class AppConfig(BaseModel):
    """应用配置类"""
    # 基本配置
    app_name: str = Field(default="Video-Speech-Translator", description="应用名称")
    log_level: str = Field(default="INFO", description="日志级别")
    temp_dir: str = Field(default="./temp", description="临时文件目录")
    output_dir: str = Field(default="./output", description="输出文件目录")
    log_dir: str = Field(default="./logs", description="日志文件目录")
    
    # 视频处理配置
    video_extensions: List[str] = Field(
        default=[".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"],
        description="支持的视频文件扩展名"
    )
    
    # 音频提取配置
    audio_format: str = Field(default="wav", description="音频格式")
    audio_sample_rate: int = Field(default=16000, description="音频采样率")
    audio_channels: int = Field(default=1, description="音频声道数")
    
    # 语音识别配置
    speech_recognition_model: str = Field(default="base", description="语音识别模型")
    speech_recognition_device: str = Field(default="cpu", description="语音识别设备")
    use_whisperx: bool = Field(default=True, description="是否使用WhisperX增强识别")
    
    # 翻译配置
    translation_service: str = Field(default="google", description="翻译服务")
    translation_api_key: Optional[str] = Field(default=None, description="翻译API密钥")
    target_languages: List[str] = Field(default=["en"], description="目标语言列表")
    
    # 字幕配置
    subtitle_format: str = Field(default="srt", description="字幕格式")
    subtitle_filename_suffix: str = Field(default="_subtitles", description="字幕文件名后缀")
    language_code_in_filename: bool = Field(default=True, description="是否在文件名中包含语言代码")


def get_default_config() -> AppConfig:
    """获取默认配置

    Returns:
        默认配置对象
    """
    return AppConfig()


def load_config(config_path: Optional[Union[str, Path]] = None) -> AppConfig:
    """加载配置

    Args:
        config_path: 配置文件路径，如果为None则使用默认配置

    Returns:
        配置对象

    Raises:
        ConfigurationError: 配置加载错误
    """
    # 如果未指定配置文件，则使用默认配置
    if not config_path:
        return get_default_config()
    
    config_path = Path(config_path)
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}，将使用默认配置")
        return get_default_config()
    
    try:
        # 读取配置文件
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # 创建配置对象
        config = AppConfig(**config_data)
        logger.info(f"成功加载配置文件: {config_path}")
        return config
        
    except json.JSONDecodeError as e:
        error_msg = f"配置文件格式错误: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e
    except Exception as e:
        error_msg = f"加载配置文件失败: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e


def save_config(config: AppConfig, config_path: Union[str, Path]) -> None:
    """保存配置到文件

    Args:
        config: 配置对象
        config_path: 配置文件路径

    Raises:
        ConfigurationError: 配置保存错误
    """
    config_path = Path(config_path)
    
    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 将配置对象转换为字典
        config_dict = config.model_dump()
        
        # 写入配置文件
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"成功保存配置文件: {config_path}")
        
    except Exception as e:
        error_msg = f"保存配置文件失败: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e


def ensure_directories(config: AppConfig) -> None:
    """确保必要的目录存在

    Args:
        config: 配置对象
    """
    directories = [
        config.temp_dir,
        config.output_dir,
        config.log_dir
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"创建目录: {dir_path}")