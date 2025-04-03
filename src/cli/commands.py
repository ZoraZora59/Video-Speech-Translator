#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命令行接口模块 - 命令定义

定义命令行工具的各种命令和参数，使用Typer库构建友好的命令行界面。
"""

import os
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table

from src.core.processor import VideoTranslator
from src.utils.config import AppConfig, load_config, ensure_directories
from src.utils.logger import setup_logger

# 创建Typer应用
app = typer.Typer(
    name="video-translator",
    help="自动视频翻译工具 - 将视频中的语音转换为多语言字幕",
    add_completion=False,
)

# 创建Rich控制台
console = Console()


def get_app_header():
    """获取应用标题"""
    return Panel.fit(
        "[bold blue]自动视频翻译工具[/bold blue]\n[italic]将视频中的语音转换为多语言字幕[/italic]",
        border_style="blue",
    )


@app.callback()
def callback():
    """自动视频翻译工具 - 将视频中的语音转换为多语言字幕"""
    console.print(get_app_header())


@app.command("translate")
def translate(
    video_path: str = typer.Argument(..., help="视频文件路径"),
    target_languages: Optional[List[str]] = typer.Option(
        None, "--lang", "-l", help="目标语言代码，可指定多个，如 en zh-CN fr"
    ),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="输出目录"),
    subtitle_format: Optional[str] = typer.Option(None, "--format", "-f", help="字幕格式: srt 或 vtt"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="配置文件路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
):
    """将视频中的语音转换为多语言字幕"""
    try:
        # 加载配置
        config = load_config(config_file)
        
        # 设置日志级别
        log_level = "DEBUG" if verbose else config.log_level
        setup_logger(config.log_dir, log_level)
        
        # 确保必要的目录存在
        ensure_directories(config)
        
        # 更新配置
        if output_dir:
            config.output_dir = output_dir
        if subtitle_format:
            config.subtitle_format = subtitle_format
        
        # 检查视频文件是否存在
        video_path = Path(video_path)
        if not video_path.exists():
            console.print(f"[bold red]错误: 视频文件不存在: {video_path}[/bold red]")
            raise typer.Exit(1)
        
        # 检查视频格式
        if video_path.suffix.lower() not in [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]:
            console.print(f"[bold yellow]警告: 不支持的视频格式: {video_path.suffix}[/bold yellow]")
            if not typer.confirm("是否继续处理?"):
                raise typer.Exit(0)
        
        # 设置目标语言
        if target_languages:
            config.target_languages = target_languages
        elif not config.target_languages:
            config.target_languages = ["en"]  # 默认英语
        
        # 创建进度显示
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # 创建视频翻译器
            translator = VideoTranslator(config)
            
            # 设置进度回调
            def progress_callback(stage, message, percent=None):
                nonlocal task
                task.description = f"{stage}: {message}"
                if percent is not None:
                    progress.update(task, completed=int(percent * 100))
            
            # 创建总进度任务
            task = progress.add_task("准备处理视频...", total=100)
            
            # 执行翻译
            result = translator.process_video(
                video_path=str(video_path),
                progress_callback=progress_callback
            )
            
            # 更新进度
            progress.update(task, completed=100)
        
        # 显示结果
        console.print("\n[bold green]处理完成![/bold green]")
        
        # 创建结果表格
        table = Table(title="生成的字幕文件")
        table.add_column("语言", style="cyan")
        table.add_column("文件路径", style="green")
        
        for lang, subtitle_path in result.items():
            table.add_row(lang, str(subtitle_path))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]错误: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command("version")
def version():
    """显示版本信息"""
    from src import __version__
    console.print(f"自动视频翻译工具 v{__version__}")


@app.command("languages")
def languages():
    """显示支持的语言列表"""
    # 支持的语言列表
    langs = {
        "en": "英语 (English)",
        "zh-CN": "简体中文 (Chinese Simplified)",
        "zh-TW": "繁体中文 (Chinese Traditional)",
        "ja": "日语 (Japanese)",
        "ko": "韩语 (Korean)",
        "fr": "法语 (French)",
        "de": "德语 (German)",
        "es": "西班牙语 (Spanish)",
        "it": "意大利语 (Italian)",
        "ru": "俄语 (Russian)",
        "pt": "葡萄牙语 (Portuguese)",
        "ar": "阿拉伯语 (Arabic)",
        "hi": "印地语 (Hindi)",
        "th": "泰语 (Thai)",
        "vi": "越南语 (Vietnamese)",
    }
    
    # 创建语言表格
    table = Table(title="支持的语言列表")
    table.add_column("代码", style="cyan")
    table.add_column("语言", style="green")
    
    for code, name in sorted(langs.items()):
        table.add_row(code, name)
    
    console.print(table)


if __name__ == "__main__":
    app()