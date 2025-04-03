#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具类模块 - 异常定义

定义应用中可能出现的各种异常类型，便于统一异常处理。
"""


class VideoTranslatorError(Exception):
    """视频翻译工具基础异常类"""
    pass


class VideoProcessingError(VideoTranslatorError):
    """视频处理错误"""
    pass


class AudioExtractionError(VideoProcessingError):
    """音频提取错误"""
    pass


class SpeechRecognitionError(VideoTranslatorError):
    """语音识别错误"""
    pass


class TranslationError(VideoTranslatorError):
    """翻译错误"""
    pass


class SubtitleGenerationError(VideoTranslatorError):
    """字幕生成错误"""
    pass


class ConfigurationError(VideoTranslatorError):
    """配置错误"""
    pass


class APIError(VideoTranslatorError):
    """API调用错误"""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ResourceNotFoundError(VideoTranslatorError):
    """资源未找到错误"""
    pass


class ValidationError(VideoTranslatorError):
    """数据验证错误"""
    pass


class DependencyError(VideoTranslatorError):
    """依赖项错误，如缺少必要的库或工具"""
    pass