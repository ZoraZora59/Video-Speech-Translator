#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
核心处理模块 - 视频翻译器

负责协调各个功能模块完成视频翻译的完整流程，包括视频处理、语音识别、翻译和字幕生成。
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable

from loguru import logger

from src.utils.config import AppConfig
from src.utils.exceptions import VideoTranslatorError
from src.video_processor.extractor import VideoAudioExtractor, AudioExtractionConfig
from src.speech_recognition.recognizer import WhisperRecognizer, WhisperXRecognizer, RecognizerConfig, RecognitionResult
from src.translation.translator import TranslatorFactory, TranslationConfig, TranslationResult
from src.subtitle.generator import SubtitleGeneratorFactory, SubtitleConfig, SubtitleSegment, BaseSubtitleGenerator


class VideoTranslator:
    """视频翻译器，协调各个功能模块完成视频翻译的完整流程"""

    def __init__(self, config: AppConfig):
        """初始化视频翻译器

        Args:
            config: 应用配置
        """
        self.config = config
        logger.debug(f"初始化视频翻译器，配置: {config}")

    def process_video(
        self, 
        video_path: Union[str, Path],
        progress_callback: Optional[Callable[[str, str, Optional[float]], None]] = None
    ) -> Dict[str, Path]:
        """处理视频，完成从视频到多语言字幕的完整流程

        Args:
            video_path: 视频文件路径
            progress_callback: 进度回调函数，接收三个参数：阶段名称、消息、进度百分比（0-1）

        Returns:
            字典，键为语言代码，值为对应的字幕文件路径

        Raises:
            VideoTranslatorError: 视频处理错误
            FileNotFoundError: 视频文件不存在
        """
        video_path = Path(video_path)
        if not video_path.exists():
            error_msg = f"视频文件不存在: {video_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # 1. 提取音频
            audio_path = self._extract_audio(video_path, progress_callback)
            
            # 2. 语音识别
            recognition_result = self._recognize_speech(audio_path, progress_callback)
            
            # 3. 翻译文本
            translation_results = self._translate_text(recognition_result, progress_callback)
            
            # 4. 生成字幕
            subtitle_paths = self._generate_subtitles(
                video_path, recognition_result, translation_results, progress_callback
            )
            
            return subtitle_paths
            
        except Exception as e:
            error_msg = f"处理视频失败: {str(e)}"
            logger.error(error_msg)
            if isinstance(e, VideoTranslatorError):
                raise
            else:
                raise VideoTranslatorError(error_msg) from e

    def _extract_audio(self, video_path: Path, progress_callback: Optional[Callable] = None) -> Path:
        """从视频中提取音频

        Args:
            video_path: 视频文件路径
            progress_callback: 进度回调函数

        Returns:
            音频文件路径
        """
        if progress_callback:
            progress_callback("音频提取", "正在从视频中提取音频...", 0.1)
        
        # 配置音频提取器
        audio_config = AudioExtractionConfig(
            output_format=self.config.audio_format,
            sample_rate=self.config.audio_sample_rate,
            channels=self.config.audio_channels,
            output_dir=self.config.temp_dir
        )
        
        # 创建音频提取器
        extractor = VideoAudioExtractor(audio_config)
        
        # 提取音频
        logger.info(f"开始从视频提取音频: {video_path}")
        audio_path = extractor.extract_audio(video_path)
        logger.success(f"音频提取完成: {audio_path}")
        
        if progress_callback:
            progress_callback("音频提取", f"音频提取完成: {audio_path.name}", 0.2)
        
        return audio_path

    def _recognize_speech(self, audio_path: Path, progress_callback: Optional[Callable] = None) -> RecognitionResult:
        """识别音频中的语音

        Args:
            audio_path: 音频文件路径
            progress_callback: 进度回调函数

        Returns:
            语音识别结果
        """
        if progress_callback:
            progress_callback("语音识别", "正在识别音频中的语音...", 0.3)
        
        # 配置语音识别器
        recognizer_config = RecognizerConfig(
            model_name=self.config.speech_recognition_model,
            device=self.config.speech_recognition_device,
            language=None,  # 自动检测
            task="transcribe"
        )
        
        # 创建语音识别器
        if self.config.use_whisperx:
            recognizer = WhisperXRecognizer(recognizer_config)
        else:
            recognizer = WhisperRecognizer(recognizer_config)
        
        # 识别语音
        logger.info(f"开始识别音频: {audio_path}")
        result = recognizer.recognize(audio_path)
        logger.success(f"语音识别完成，检测语言: {result.language}")
        
        if progress_callback:
            progress_callback("语音识别", f"语音识别完成，检测语言: {result.language}", 0.4)
        
        return result

    def _translate_text(self, recognition_result: RecognitionResult, progress_callback: Optional[Callable] = None) -> Dict[str, TranslationResult]:
        """翻译识别出的文本

        Args:
            recognition_result: 语音识别结果
            progress_callback: 进度回调函数

        Returns:
            翻译结果字典，键为语言代码，值为翻译结果
        """
        if progress_callback:
            progress_callback("文本翻译", "正在翻译文本...", 0.5)
        
        # 如果目标语言包含源语言，则不需要翻译
        source_lang = recognition_result.language
        target_langs = [lang for lang in self.config.target_languages if lang != source_lang]
        
        # 如果没有需要翻译的目标语言，则返回空字典
        if not target_langs:
            logger.info(f"没有需要翻译的目标语言，源语言: {source_lang}")
            if progress_callback:
                progress_callback("文本翻译", "无需翻译，源语言已在目标语言列表中", 0.6)
            return {}
        
        # 配置翻译器
        translation_config = TranslationConfig(
            service=self.config.translation_service,
            source_lang=source_lang,
            api_key=self.config.translation_api_key
        )
        
        # 创建翻译器
        translator_factory = TranslatorFactory()
        
        # 翻译结果字典
        translation_results = {}
        
        # 对每种目标语言进行翻译
        total_langs = len(target_langs)
        for i, target_lang in enumerate(target_langs):
            if progress_callback:
                progress_callback("文本翻译", f"正在翻译为 {target_lang}...", 0.5 + 0.1 * (i / total_langs))
            
            # 更新目标语言
            translation_config.target_lang = target_lang
            
            # 创建翻译器
            translator = translator_factory.create_translator(translation_config)
            
            # 翻译文本
            logger.info(f"开始翻译文本，目标语言: {target_lang}")
            result = translator.translate(recognition_result.text)
            logger.success(f"文本翻译完成: {source_lang} -> {target_lang}")
            
            # 保存翻译结果
            translation_results[target_lang] = result
        
        if progress_callback:
            progress_callback("文本翻译", f"文本翻译完成，共 {len(translation_results)} 种语言", 0.6)
        
        return translation_results

    def _generate_subtitles(
        self, 
        video_path: Path, 
        recognition_result: RecognitionResult,
        translation_results: Dict[str, TranslationResult],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Path]:
        """生成字幕文件

        Args:
            video_path: 视频文件路径
            recognition_result: 语音识别结果
            translation_results: 翻译结果字典
            progress_callback: 进度回调函数

        Returns:
            字幕文件路径字典，键为语言代码，值为字幕文件路径
        """
        if progress_callback:
            progress_callback("字幕生成", "正在生成字幕文件...", 0.7)
        
        # 配置字幕生成器
        subtitle_config = SubtitleConfig(
            format=self.config.subtitle_format,
            output_dir=self.config.output_dir,
            filename_suffix=self.config.subtitle_filename_suffix,
            language_code_in_filename=self.config.language_code_in_filename
        )
        
        # 创建字幕生成器
        generator_factory = SubtitleGeneratorFactory()
        generator = generator_factory.create_generator(subtitle_config)
        
        # 字幕文件路径字典
        subtitle_paths = {}
        
        # 源语言字幕
        source_lang = recognition_result.language
        if source_lang in self.config.target_languages:
            if progress_callback:
                progress_callback("字幕生成", f"正在生成源语言({source_lang})字幕...", 0.75)
            
            # 准备字幕片段
            segments = BaseSubtitleGenerator.prepare_segments(recognition_result)
            
            # 生成字幕文件
            output_path = self._get_subtitle_path(video_path, source_lang)
            subtitle_path = generator.generate(segments, output_path)
            
            # 保存字幕路径
            subtitle_paths[source_lang] = subtitle_path
        
        # 翻译语言字幕
        total_langs = len(translation_results)
        for i, (target_lang, translation_result) in enumerate(translation_results.items()):
            if progress_callback:
                progress_callback("字幕生成", f"正在生成{target_lang}字幕...", 0.8 + 0.1 * (i / total_langs))
            
            # 准备字幕片段
            segments = BaseSubtitleGenerator.prepare_segments(recognition_result, translation_result)
            
            # 生成字幕文件
            output_path = self._get_subtitle_path(video_path, target_lang)
            subtitle_path = generator.generate(segments, output_path)
            
            # 保存字幕路径
            subtitle_paths[target_lang] = subtitle_path
        
        if progress_callback:
            progress_callback("字幕生成", f"字幕生成完成，共 {len(subtitle_paths)} 个文件", 0.95)
        
        return subtitle_paths

    def _get_subtitle_path(self, video_path: Path, language_code: str) -> Path:
        """获取字幕文件路径

        Args:
            video_path: 视频文件路径
            language_code: 语言代码

        Returns:
            字幕文件路径
        """
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建文件名
        if self.config.language_code_in_filename:
            filename = f"{video_path.stem}{self.config.subtitle_filename_suffix}_{language_code}.{self.config.subtitle_format}"
        else:
            filename = f"{video_path.stem}{self.config.subtitle_filename_suffix}.{self.config.subtitle_format}"
        
        return output_dir / filename