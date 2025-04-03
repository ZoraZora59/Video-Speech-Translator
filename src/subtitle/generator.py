#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
字幕模块 - 生成器

负责生成和处理字幕文件，支持多种字幕格式，如SRT和WebVTT。
"""

import os
from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import pysrt
from loguru import logger
from pydantic import BaseModel, Field
from webvtt import WebVTT, Caption

from src.speech_recognition.recognizer import RecognitionResult
from src.translation.translator import TranslationResult
from src.utils.exceptions import SubtitleGenerationError


class SubtitleConfig(BaseModel):
    """字幕配置"""
    format: str = Field(default="srt", description="字幕格式: srt, vtt")
    output_dir: Optional[str] = Field(default=None, description="输出目录，默认与视频文件相同目录")
    filename_suffix: str = Field(default="_subtitles", description="文件名后缀")
    language_code_in_filename: bool = Field(default=True, description="是否在文件名中包含语言代码")


class SubtitleSegment(BaseModel):
    """字幕片段"""
    index: int = Field(description="字幕索引")
    start_time: float = Field(description="开始时间（秒）")
    end_time: float = Field(description="结束时间（秒）")
    text: str = Field(description="字幕文本")


class BaseSubtitleGenerator(ABC):
    """字幕生成器基类"""

    def __init__(self, config: SubtitleConfig):
        """初始化字幕生成器

        Args:
            config: 字幕配置
        """
        self.config = config
        logger.debug(f"初始化字幕生成器，配置: {self.config}")

    @abstractmethod
    def generate(self, segments: List[SubtitleSegment], output_path: Union[str, Path]) -> Path:
        """生成字幕文件

        Args:
            segments: 字幕片段列表
            output_path: 输出文件路径

        Returns:
            输出文件路径

        Raises:
            SubtitleGenerationError: 字幕生成错误
        """
        pass

    @staticmethod
    def prepare_segments(recognition_result: RecognitionResult, translation_result: Optional[TranslationResult] = None) -> List[SubtitleSegment]:
        """从识别结果和翻译结果准备字幕片段

        Args:
            recognition_result: 语音识别结果
            translation_result: 翻译结果，如果为None则使用原始文本

        Returns:
            字幕片段列表
        """
        segments = []
        translated_text = translation_result.translated_text if translation_result else recognition_result.text
        
        # 如果没有分段信息，则创建一个完整的字幕
        if not recognition_result.segments:
            segments.append(SubtitleSegment(
                index=1,
                start_time=0.0,
                end_time=60.0,  # 默认1分钟
                text=translated_text
            ))
            return segments
        
        # 如果有翻译结果但没有分段翻译，则尝试简单分配翻译文本
        if translation_result and len(recognition_result.segments) > 1:
            # 这里使用一个简单的方法分配翻译文本，实际应用中可能需要更复杂的对齐算法
            logger.warning("翻译结果没有分段信息，使用简单文本分配方法")
            
            # 计算原始文本中每个分段的比例
            total_length = len(recognition_result.text)
            translated_length = len(translated_text)
            
            current_pos = 0
            for i, segment in enumerate(recognition_result.segments):
                segment_text = segment.get("text", "")
                segment_ratio = len(segment_text) / total_length if total_length > 0 else 0
                
                # 根据比例计算翻译文本的对应部分
                segment_trans_length = int(translated_length * segment_ratio)
                segment_trans_text = translated_text[current_pos:current_pos + segment_trans_length]
                current_pos += segment_trans_length
                
                # 添加字幕片段
                segments.append(SubtitleSegment(
                    index=i + 1,
                    start_time=segment.get("start", 0.0),
                    end_time=segment.get("end", 0.0),
                    text=segment_trans_text.strip()
                ))
            
            # 确保所有翻译文本都被使用
            if current_pos < translated_length and segments:
                segments[-1].text += translated_text[current_pos:]
        else:
            # 直接使用分段信息
            for i, segment in enumerate(recognition_result.segments):
                segments.append(SubtitleSegment(
                    index=i + 1,
                    start_time=segment.get("start", 0.0),
                    end_time=segment.get("end", 0.0),
                    text=segment.get("text", "") if not translation_result else segment.get("text", "")
                ))
        
        return segments


class SRTGenerator(BaseSubtitleGenerator):
    """SRT字幕生成器"""

    def generate(self, segments: List[SubtitleSegment], output_path: Union[str, Path]) -> Path:
        """生成SRT字幕文件

        Args:
            segments: 字幕片段列表
            output_path: 输出文件路径

        Returns:
            输出文件路径

        Raises:
            SubtitleGenerationError: 字幕生成错误
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"开始生成SRT字幕文件: {output_path}")
            
            # 创建SRT字幕对象
            subs = pysrt.SubRipFile()
            
            for segment in segments:
                # 转换时间格式
                start_time = self._seconds_to_time(segment.start_time)
                end_time = self._seconds_to_time(segment.end_time)
                
                # 创建字幕项
                item = pysrt.SubRipItem(
                    index=segment.index,
                    start=start_time,
                    end=end_time,
                    text=segment.text
                )
                subs.append(item)
            
            # 保存字幕文件
            subs.save(str(output_path), encoding='utf-8')
            
            logger.success(f"SRT字幕文件生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"生成SRT字幕文件失败: {str(e)}"
            logger.error(error_msg)
            raise SubtitleGenerationError(error_msg) from e
    
    @staticmethod
    def _seconds_to_time(seconds: float) -> pysrt.SubRipTime:
        """将秒转换为SRT时间格式

        Args:
            seconds: 秒数

        Returns:
            SRT时间对象
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return pysrt.SubRipTime(hours, minutes, seconds, milliseconds)


class VTTGenerator(BaseSubtitleGenerator):
    """WebVTT字幕生成器"""

    def generate(self, segments: List[SubtitleSegment], output_path: Union[str, Path]) -> Path:
        """生成WebVTT字幕文件

        Args:
            segments: 字幕片段列表
            output_path: 输出文件路径

        Returns:
            输出文件路径

        Raises:
            SubtitleGenerationError: 字幕生成错误
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"开始生成WebVTT字幕文件: {output_path}")
            
            # 创建WebVTT字幕对象
            vtt = WebVTT()
            
            for segment in segments:
                # 转换时间格式
                start_time = self._format_timestamp(segment.start_time)
                end_time = self._format_timestamp(segment.end_time)
                
                # 创建字幕项
                caption = Caption(
                    start=start_time,
                    end=end_time,
                    text=segment.text
                )
                vtt.captions.append(caption)
            
            # 保存字幕文件
            vtt.save(str(output_path))
            
            logger.success(f"WebVTT字幕文件生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"生成WebVTT字幕文件失败: {str(e)}"
            logger.error(error_msg)
            raise SubtitleGenerationError(error_msg) from e
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """将秒转换为WebVTT时间格式

        Args:
            seconds: 秒数

        Returns:
            WebVTT时间字符串
        """
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = td.microseconds // 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


class SubtitleGeneratorFactory:
    """字幕生成器工厂，用于创建不同的字幕生成器实例"""

    @staticmethod
    def create_generator(config: SubtitleConfig) -> BaseSubtitleGenerator:
        """创建字幕生成器

        Args:
            config: 字幕配置

        Returns:
            字幕生成器实例

        Raises:
            ValueError: 不支持的字幕格式
        """
        if config.format.lower() == "srt":
            return SRTGenerator(config)
        elif config.format.lower() == "vtt":
            return VTTGenerator(config)
        else:
            error_msg = f"不支持的字幕格式: {config.format}"
            logger.error(error_msg)
            raise ValueError(error_msg)