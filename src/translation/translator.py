#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
翻译模块 - 翻译器

负责文本的多语言翻译，支持多种翻译服务，包括Google翻译和DeepL翻译。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, Field

from src.utils.exceptions import TranslationError


class TranslationConfig(BaseModel):
    """翻译配置"""
    service: str = Field(default="google", description="翻译服务: google, deepl")
    source_lang: Optional[str] = Field(default=None, description="源语言代码，None表示自动检测")
    target_lang: str = Field(default="en", description="目标语言代码")
    api_key: Optional[str] = Field(default=None, description="API密钥，某些服务需要")
    timeout: int = Field(default=10, description="请求超时时间（秒）")
    retries: int = Field(default=3, description="失败重试次数")


class TranslationResult(BaseModel):
    """翻译结果"""
    original_text: str = Field(description="原始文本")
    translated_text: str = Field(description="翻译后的文本")
    source_lang: str = Field(description="源语言代码")
    target_lang: str = Field(description="目标语言代码")
    service: str = Field(description="使用的翻译服务")


class BaseTranslator(ABC):
    """翻译器基类"""

    def __init__(self, config: TranslationConfig):
        """初始化翻译器

        Args:
            config: 翻译配置
        """
        self.config = config
        logger.debug(f"初始化翻译器，配置: {self.config}")

    @abstractmethod
    def translate(self, text: str) -> TranslationResult:
        """翻译文本

        Args:
            text: 要翻译的文本

        Returns:
            翻译结果

        Raises:
            TranslationError: 翻译错误
        """
        pass

    @abstractmethod
    def translate_batch(self, texts: List[str]) -> List[TranslationResult]:
        """批量翻译文本

        Args:
            texts: 要翻译的文本列表

        Returns:
            翻译结果列表

        Raises:
            TranslationError: 翻译错误
        """
        pass


class GoogleTranslator(BaseTranslator):
    """Google翻译器"""

    def __init__(self, config: TranslationConfig):
        """初始化Google翻译器

        Args:
            config: 翻译配置
        """
        super().__init__(config)
        self.translator = None

    def _init_translator(self):
        """初始化翻译器实例"""
        if self.translator is not None:
            return

        try:
            from googletrans import Translator
            self.translator = Translator()
            logger.debug("Google翻译器初始化成功")
        except Exception as e:
            error_msg = f"初始化Google翻译器失败: {str(e)}"
            logger.error(error_msg)
            raise TranslationError(error_msg) from e

    def translate(self, text: str) -> TranslationResult:
        """使用Google翻译文本

        Args:
            text: 要翻译的文本

        Returns:
            翻译结果

        Raises:
            TranslationError: 翻译错误
        """
        if not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_lang=self.config.source_lang or "auto",
                target_lang=self.config.target_lang,
                service="google"
            )

        self._init_translator()

        retries = 0
        while retries <= self.config.retries:
            try:
                logger.info(f"开始翻译文本，目标语言: {self.config.target_lang}")
                result = self.translator.translate(
                    text,
                    src=self.config.source_lang,
                    dest=self.config.target_lang
                )

                translation_result = TranslationResult(
                    original_text=text,
                    translated_text=result.text,
                    source_lang=result.src,
                    target_lang=result.dest,
                    service="google"
                )

                logger.success(f"文本翻译成功: {result.src} -> {result.dest}")
                return translation_result

            except Exception as e:
                retries += 1
                if retries > self.config.retries:
                    error_msg = f"Google翻译失败，已重试{retries-1}次: {str(e)}"
                    logger.error(error_msg)
                    raise TranslationError(error_msg) from e
                logger.warning(f"Google翻译失败，正在重试({retries}/{self.config.retries}): {str(e)}")

    def translate_batch(self, texts: List[str]) -> List[TranslationResult]:
        """批量翻译文本

        Args:
            texts: 要翻译的文本列表

        Returns:
            翻译结果列表

        Raises:
            TranslationError: 翻译错误
        """
        return [self.translate(text) for text in texts]


class DeepLTranslator(BaseTranslator):
    """DeepL翻译器"""

    def __init__(self, config: TranslationConfig):
        """初始化DeepL翻译器

        Args:
            config: 翻译配置
        """
        super().__init__(config)
        if not config.api_key:
            logger.warning("未提供DeepL API密钥，将无法使用DeepL翻译服务")
        self.translator = None

    def _init_translator(self):
        """初始化翻译器实例"""
        if self.translator is not None:
            return

        if not self.config.api_key:
            error_msg = "使用DeepL翻译服务需要提供API密钥"
            logger.error(error_msg)
            raise TranslationError(error_msg)

        try:
            from deepl import Translator
            self.translator = Translator(self.config.api_key)
            logger.debug("DeepL翻译器初始化成功")
        except Exception as e:
            error_msg = f"初始化DeepL翻译器失败: {str(e)}"
            logger.error(error_msg)
            raise TranslationError(error_msg) from e

    def translate(self, text: str) -> TranslationResult:
        """使用DeepL翻译文本

        Args:
            text: 要翻译的文本

        Returns:
            翻译结果

        Raises:
            TranslationError: 翻译错误
        """
        if not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_lang=self.config.source_lang or "auto",
                target_lang=self.config.target_lang,
                service="deepl"
            )

        self._init_translator()

        retries = 0
        while retries <= self.config.retries:
            try:
                logger.info(f"开始使用DeepL翻译文本，目标语言: {self.config.target_lang}")
                result = self.translator.translate_text(
                    text,
                    source_lang=self.config.source_lang,
                    target_lang=self.config.target_lang
                )

                translation_result = TranslationResult(
                    original_text=text,
                    translated_text=result.text,
                    source_lang=result.detected_source_lang.lower(),
                    target_lang=self.config.target_lang.lower(),
                    service="deepl"
                )

                logger.success(f"DeepL文本翻译成功: {result.detected_source_lang} -> {self.config.target_lang}")
                return translation_result

            except Exception as e:
                retries += 1
                if retries > self.config.retries:
                    error_msg = f"DeepL翻译失败，已重试{retries-1}次: {str(e)}"
                    logger.error(error_msg)
                    raise TranslationError(error_msg) from e
                logger.warning(f"DeepL翻译失败，正在重试({retries}/{self.config.retries}): {str(e)}")

    def translate_batch(self, texts: List[str]) -> List[TranslationResult]:
        """批量翻译文本

        Args:
            texts: 要翻译的文本列表

        Returns:
            翻译结果列表

        Raises:
            TranslationError: 翻译错误
        """
        if not texts:
            return []

        self._init_translator()

        retries = 0
        while retries <= self.config.retries:
            try:
                logger.info(f"开始批量使用DeepL翻译{len(texts)}条文本，目标语言: {self.config.target_lang}")
                results = self.translator.translate_text(
                    texts,
                    source_lang=self.config.source_lang,
                    target_lang=self.config.target_lang
                )

                translation_results = [
                    TranslationResult(
                        original_text=texts[i],
                        translated_text=result.text,
                        source_lang=result.detected_source_lang.lower(),
                        target_lang=self.config.target_lang.lower(),
                        service="deepl"
                    )
                    for i, result in enumerate(results)
                ]

                logger.success(f"DeepL批量文本翻译成功: {len(texts)}条")
                return translation_results

            except Exception as e:
                retries += 1
                if retries > self.config.retries:
                    error_msg = f"DeepL批量翻译失败，已重试{retries-1}次: {str(e)}"
                    logger.error(error_msg)
                    raise TranslationError(error_msg) from e
                logger.warning(f"DeepL批量翻译失败，正在重试({retries}/{self.config.retries}): {str(e)}")


class TranslatorFactory:
    """翻译器工厂，用于创建不同的翻译器实例"""

    @staticmethod
    def create_translator(config: TranslationConfig) -> BaseTranslator:
        """创建翻译器

        Args:
            config: 翻译配置

        Returns:
            翻译器实例

        Raises:
            ValueError: 不支持的翻译服务
        """
        if config.service.lower() == "google":
            return GoogleTranslator(config)
        elif config.service.lower() == "deepl":
            return DeepLTranslator(config)
        else:
            error_msg = f"不支持的翻译服务: {config.service}"
            logger.error(error_msg)
            raise ValueError(error_msg)