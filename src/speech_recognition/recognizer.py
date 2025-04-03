#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
语音识别模块 - 识别器

负责将音频文件转换为文本，支持多种语音识别引擎，主要使用Whisper模型。
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from loguru import logger
from pydantic import BaseModel, Field

from src.utils.exceptions import SpeechRecognitionError


class RecognitionResult(BaseModel):
    """语音识别结果"""
    text: str = Field(description="识别出的文本")
    language: str = Field(description="识别出的语言代码")
    segments: List[Dict[str, Any]] = Field(default_factory=list, description="时间轴分段信息")
    confidence: Optional[float] = Field(default=None, description="识别置信度")


class RecognizerConfig(BaseModel):
    """语音识别配置"""
    model_name: str = Field(default="base", description="Whisper模型名称: tiny, base, small, medium, large")
    device: str = Field(default="cpu", description="运行设备: cpu, cuda")
    language: Optional[str] = Field(default=None, description="语言代码，None表示自动检测")
    task: str = Field(default="transcribe", description="任务类型: transcribe, translate")
    beam_size: int = Field(default=5, description="束搜索大小")
    temperature: float = Field(default=0, description="采样温度")
    verbose: bool = Field(default=False, description="是否显示详细日志")


class WhisperRecognizer:
    """基于Whisper的语音识别器"""

    def __init__(self, config: Optional[RecognizerConfig] = None):
        """初始化Whisper语音识别器

        Args:
            config: 识别配置，如果为None则使用默认配置
        """
        self.config = config or RecognizerConfig()
        self.model = None
        logger.debug(f"初始化Whisper语音识别器，配置: {self.config}")

    def _load_model(self):
        """加载Whisper模型"""
        if self.model is not None:
            return

        try:
            import whisper
            logger.info(f"加载Whisper模型: {self.config.model_name} 到 {self.config.device}")
            self.model = whisper.load_model(self.config.model_name, device=self.config.device)
            logger.success(f"Whisper模型加载成功: {self.config.model_name}")
        except Exception as e:
            error_msg = f"加载Whisper模型失败: {str(e)}"
            logger.error(error_msg)
            raise SpeechRecognitionError(error_msg) from e

    def recognize(self, audio_path: Union[str, Path]) -> RecognitionResult:
        """识别音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            识别结果

        Raises:
            SpeechRecognitionError: 语音识别错误
            FileNotFoundError: 音频文件不存在
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            error_msg = f"音频文件不存在: {audio_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # 加载模型
        self._load_model()

        try:
            logger.info(f"开始识别音频: {audio_path}")
            
            # 执行识别
            result = self.model.transcribe(
                str(audio_path),
                language=self.config.language,
                task=self.config.task,
                beam_size=self.config.beam_size,
                temperature=self.config.temperature,
                verbose=self.config.verbose
            )
            
            # 构建识别结果
            recognition_result = RecognitionResult(
                text=result["text"],
                language=result["language"],
                segments=result["segments"]
            )
            
            logger.success(f"音频识别成功，检测语言: {recognition_result.language}")
            return recognition_result
            
        except Exception as e:
            error_msg = f"音频识别失败: {str(e)}"
            logger.error(error_msg)
            raise SpeechRecognitionError(error_msg) from e


class WhisperXRecognizer(WhisperRecognizer):
    """基于WhisperX的增强语音识别器，提供更精确的时间戳"""

    def _load_model(self):
        """加载WhisperX模型"""
        if self.model is not None:
            return

        try:
            import whisperx
            logger.info(f"加载WhisperX模型: {self.config.model_name} 到 {self.config.device}")
            self.model = whisperx.load_model(self.config.model_name, device=self.config.device)
            logger.success(f"WhisperX模型加载成功: {self.config.model_name}")
        except Exception as e:
            error_msg = f"加载WhisperX模型失败: {str(e)}"
            logger.error(error_msg)
            raise SpeechRecognitionError(error_msg) from e

    def recognize(self, audio_path: Union[str, Path]) -> RecognitionResult:
        """使用WhisperX识别音频文件，提供更精确的时间戳

        Args:
            audio_path: 音频文件路径

        Returns:
            识别结果

        Raises:
            SpeechRecognitionError: 语音识别错误
            FileNotFoundError: 音频文件不存在
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            error_msg = f"音频文件不存在: {audio_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # 加载模型
        self._load_model()

        try:
            import whisperx
            logger.info(f"开始使用WhisperX识别音频: {audio_path}")
            
            # 加载音频
            audio = whisperx.load_audio(str(audio_path))
            
            # 执行识别
            result = self.model.transcribe(
                audio,
                language=self.config.language,
                task=self.config.task,
                beam_size=self.config.beam_size,
                temperature=self.config.temperature,
            )
            
            # 加载对齐模型并对齐时间戳
            model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=self.config.device)
            result = whisperx.align(result["segments"], model_a, metadata, audio, self.config.device)
            
            # 构建识别结果
            recognition_result = RecognitionResult(
                text=" ".join([segment["text"] for segment in result["segments"]]),
                language=result["language"],
                segments=result["segments"]
            )
            
            logger.success(f"WhisperX音频识别成功，检测语言: {recognition_result.language}")
            return recognition_result
            
        except Exception as e:
            error_msg = f"WhisperX音频识别失败: {str(e)}"
            logger.error(error_msg)
            raise SpeechRecognitionError(error_msg) from e