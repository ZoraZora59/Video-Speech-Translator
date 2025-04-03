#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频处理模块 - 音频提取器

负责从视频文件中提取音频内容，支持多种视频格式，并处理可能出现的异常情况。
"""

import os
from pathlib import Path
from typing import Optional, Union

import ffmpeg
from loguru import logger
from pydantic import BaseModel, Field

from src.utils.exceptions import VideoProcessingError


class AudioExtractionConfig(BaseModel):
    """音频提取配置"""
    output_format: str = Field(default="wav", description="输出音频格式")
    sample_rate: int = Field(default=16000, description="采样率")
    channels: int = Field(default=1, description="声道数")
    output_dir: Optional[str] = Field(default=None, description="输出目录，默认与视频文件相同目录")


class VideoAudioExtractor:
    """视频音频提取器"""

    def __init__(self, config: Optional[AudioExtractionConfig] = None):
        """初始化视频音频提取器

        Args:
            config: 音频提取配置，如果为None则使用默认配置
        """
        self.config = config or AudioExtractionConfig()
        logger.debug(f"初始化视频音频提取器，配置: {self.config}")

    def extract_audio(self, video_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
        """从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频文件路径，如果为None则自动生成

        Returns:
            输出音频文件路径

        Raises:
            VideoProcessingError: 视频处理错误
            FileNotFoundError: 视频文件不存在
        """
        video_path = Path(video_path)
        if not video_path.exists():
            error_msg = f"视频文件不存在: {video_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # 如果未指定输出路径，则自动生成
        if output_path is None:
            output_dir = Path(self.config.output_dir) if self.config.output_dir else video_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{video_path.stem}.{self.config.output_format}"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"开始从视频提取音频: {video_path} -> {output_path}")

        try:
            # 使用ffmpeg提取音频
            (ffmpeg
             .input(str(video_path))
             .output(str(output_path),
                     acodec='pcm_s16le',
                     ar=self.config.sample_rate,
                     ac=self.config.channels)
             .run(quiet=True, overwrite_output=True))

            logger.success(f"音频提取成功: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            error_msg = f"音频提取失败: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e
        except Exception as e:
            error_msg = f"音频提取过程中发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e