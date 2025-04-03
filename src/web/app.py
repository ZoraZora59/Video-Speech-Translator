#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动视频翻译工具 - Web界面

提供基于FastAPI的Web界面，用于将视频中的语音转换为多语言字幕。
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from pydantic import BaseModel

from src.core.processor import VideoTranslator
from src.utils.config import AppConfig, load_config, ensure_directories
from src.utils.logger import setup_logger

# 创建FastAPI应用
app = FastAPI(
    title="自动视频翻译工具",
    description="将视频中的语音转换为多语言字幕",
    version="0.1.0",
)

# 配置模板和静态文件
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 确保目录存在
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# 设置模板
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 加载配置
config = load_config()

# 设置日志
setup_logger(config.log_dir, config.log_level)

# 确保必要的目录存在
ensure_directories(config)

# 创建上传目录
UPLOAD_DIR = Path(config.temp_dir) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 进度存储
progress_store = {}


class TranslationRequest(BaseModel):
    """翻译请求模型"""
    target_languages: List[str]
    subtitle_format: str


class ProgressResponse(BaseModel):
    """进度响应模型"""
    task_id: str
    stage: str
    message: str
    percent: float


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """首页"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_languages: str = Form("en"),
    subtitle_format: str = Form("srt"),
):
    """上传视频文件并开始处理"""
    # 检查文件类型
    if not file.filename.lower().endswith(tuple(config.video_extensions)):
        raise HTTPException(status_code=400, detail="不支持的视频格式")
    
    # 生成任务ID
    import uuid
    task_id = str(uuid.uuid4())
    
    # 保存上传的文件
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 解析目标语言
    langs = [lang.strip() for lang in target_languages.split(",") if lang.strip()]
    
    # 更新配置
    task_config = AppConfig(**config.dict())
    task_config.target_languages = langs
    task_config.subtitle_format = subtitle_format
    
    # 初始化进度
    progress_store[task_id] = {
        "stage": "准备",
        "message": "正在准备处理视频...",
        "percent": 0.0
    }
    
    # 在后台处理视频
    background_tasks.add_task(
        process_video_task,
        task_id=task_id,
        file_path=file_path,
        config=task_config
    )
    
    return {"task_id": task_id}


async def process_video_task(task_id: str, file_path: Path, config: AppConfig):
    """后台处理视频任务"""
    try:
        # 创建视频翻译器
        translator = VideoTranslator(config)
        
        # 设置进度回调
        def progress_callback(stage, message, percent=None):
            progress_store[task_id] = {
                "stage": stage,
                "message": message,
                "percent": percent or 0.0
            }
        
        # 执行翻译
        result = translator.process_video(
            video_path=str(file_path),
            progress_callback=progress_callback
        )
        
        # 更新进度为完成
        progress_store[task_id] = {
            "stage": "完成",
            "message": f"处理完成，生成了 {len(result)} 个字幕文件",
            "percent": 1.0,
            "result": {lang: str(path) for lang, path in result.items()}
        }
        
    except Exception as e:
        # 更新进度为错误
        progress_store[task_id] = {
            "stage": "错误",
            "message": f"处理失败: {str(e)}",
            "percent": 0.0,
            "error": str(e)
        }


@app.get("/progress/{task_id}")
def get_progress(task_id: str):
    """获取处理进度"""
    if task_id not in progress_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    progress = progress_store[task_id]
    response = {
        "task_id": task_id,
        "stage": progress["stage"],
        "message": progress["message"],
        "percent": progress["percent"]
    }
    
    # 如果处理完成，添加结果
    if "result" in progress:
        response["result"] = progress["result"]
    
    # 如果处理失败，添加错误信息
    if "error" in progress:
        response["error"] = progress["error"]
    
    return response


@app.get("/download/{task_id}/{lang}")
def download_subtitle(task_id: str, lang: str):
    """下载字幕文件"""
    if task_id not in progress_store or "result" not in progress_store[task_id]:
        raise HTTPException(status_code=404, detail="字幕文件不存在")
    
    result = progress_store[task_id]["result"]
    if lang not in result:
        raise HTTPException(status_code=404, detail=f"语言 {lang} 的字幕文件不存在")
    
    subtitle_path = result[lang]
    return FileResponse(
        path=subtitle_path,
        filename=Path(subtitle_path).name,
        media_type="application/octet-stream"
    )


@app.get("/languages")
def get_languages():
    """获取支持的语言列表"""
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
    
    return {"languages": [{"code": code, "name": name} for code, name in langs.items()]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)