# 自动视频翻译工具

自动将视频中的音频转换为多语言字幕，简化多语言视频内容的传播。

## 功能特点

- ✅ 从视频文件中**提取音频**
- ✅ **语音转文本**（音频转文字）
- ✅ 文本**多语言翻译**
- ✅ 自动生成**翻译字幕**
- 🚧 **规划中：** 自动生成多语言语音配音

## 系统要求

- Python 3.8 或更高版本
- FFmpeg（用于视频和音频处理）
- 足够的磁盘空间用于临时文件（建议至少 1GB）
- 内存要求：最小 4GB，推荐 8GB 或更高
- GPU 支持（可选）：支持 CUDA 的 NVIDIA GPU 可显著提升性能

## 安装指南

### 方法一：使用安装脚本（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/Video-Speech-Translator.git
cd Video-Speech-Translator

# 运行安装脚本
chmod +x install.sh
./install.sh
```

### 方法二：手动安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/Video-Speech-Translator.git
cd Video-Speech-Translator

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # 在Windows上使用: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 以开发模式安装
pip install -e .
```

### 依赖版本要求

核心依赖：
- python-dotenv >= 1.0.0
- loguru >= 0.7.0
- typer >= 0.9.0
- rich >= 13.4.2
- pydantic >= 2.4.2

视频处理：
- ffmpeg-python >= 0.2.0
- moviepy >= 1.0.3

语音识别：
- whisper >= 1.1.10
- whisperx >= 3.1.1

翻译服务：
- googletrans >= 4.0.0-rc1
- deepltranslator >= 1.11.0

## 使用方法

### 命令行界面

```bash
# 激活虚拟环境（如果尚未激活）
source venv/bin/activate

# 基本用法
python main.py translate <视频文件路径>

# 指定目标语言（可以指定多个）
python main.py translate <视频文件路径> --lang en zh-CN ja

# 指定输出目录
python main.py translate <视频文件路径> --output ./my_subtitles

# 指定字幕格式（srt 或 vtt）
python main.py translate <视频文件路径> --format vtt

# 显示详细日志
python main.py translate <视频文件路径> --verbose

# 显示支持的语言列表
python main.py languages

# 显示版本信息
python main.py version
```

### Web界面

```bash
# 启动Web服务器
python web_app.py
```

然后在浏览器中访问：http://localhost:8000

## 配置选项

可以通过创建JSON配置文件来自定义应用行为：

```json
{
  "log_level": "INFO",
  "temp_dir": "./temp",
  "output_dir": "./output",
  "audio_format": "wav",
  "audio_sample_rate": 16000,
  "speech_recognition_model": "base",
  "speech_recognition_device": "cpu",
  "use_whisperx": true,
  "translation_service": "google",
  "target_languages": ["en", "zh-CN", "ja"],
  "subtitle_format": "srt"
}
```

### 配置说明

- `log_level`: 日志级别（DEBUG/INFO/WARNING/ERROR）
- `temp_dir`: 临时文件存储目录
- `output_dir`: 输出文件存储目录
- `audio_format`: 音频格式（wav/mp3）
- `audio_sample_rate`: 音频采样率
- `speech_recognition_model`: Whisper模型大小（tiny/base/small/medium/large）
- `speech_recognition_device`: 运行设备（cpu/cuda）
- `use_whisperx`: 是否使用WhisperX增强
- `translation_service`: 翻译服务提供商（google/deepl）
- `target_languages`: 目标语言列表
- `subtitle_format`: 字幕格式（srt/vtt）

使用配置文件：

```bash
python main.py translate <视频文件路径> --config my_config.json
```

## 性能参数

### 语音识别性能

| Whisper模型 | 内存占用 | GPU显存占用 | 处理速度 |
|------------|---------|------------|----------|
| tiny       | 1GB     | 1GB        | 16x      |
| base       | 1GB     | 1GB        | 8x       |
| small      | 2GB     | 2GB        | 4x       |
| medium     | 5GB     | 5GB        | 2x       |
| large      | 10GB    | 10GB       | 1x       |

注：处理速度为相对值，以large模型为基准（1x）。

### 支持的视频格式

- 视频：MP4, AVI, MOV, MKV, WMV
- 音频：MP3, WAV, AAC, M4A
- 字幕：SRT, VTT

## 项目结构

```
.
├── main.py                 # 命令行入口点
├── web_app.py              # Web界面入口点
├── setup.py                # 安装脚本
├── requirements.txt        # 依赖列表
├── README.md               # 项目说明
├── examples/               # 示例脚本
└── src/                    # 源代码
    ├── __init__.py         # 包初始化
    ├── cli/                # 命令行界面
    ├── core/               # 核心处理逻辑
    ├── speech_recognition/ # 语音识别模块
    ├── subtitle/           # 字幕生成模块
    ├── translation/        # 翻译模块
    ├── utils/              # 工具类
    ├── video_processor/    # 视频处理模块
    └── web/                # Web界面
```

## 常见问题

1. **Q: 为什么视频处理速度很慢？**
   A: 处理速度主要受语音识别模型大小和运行设备影响。使用更小的模型或GPU可以提升速度。

2. **Q: 如何提高字幕翻译质量？**
   A: 可以切换到DeepL翻译服务，通常能提供更好的翻译质量。

3. **Q: 支持哪些语言？**
   A: 支持Whisper和翻译服务支持的所有语言。使用`python main.py languages`查看完整列表。

4. **Q: 临时文件占用空间太大？**
   A: 可以通过配置文件调整音频格式和采样率，或定期清理temp目录。

## 示例

```bash
# 运行测试示例
python examples/test_translator.py <视频文件路径>
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献指南

欢迎贡献！请随时提交问题或拉取请求。在提交之前，请确保：

1. 代码符合项目的编码规范
2. 添加了适当的测试用例
3. 更新了相关文档
4. 提交信息清晰明了

## 致谢

- [FFmpeg](https://ffmpeg.org/) - 用于视频和音频处理
- [Whisper](https://github.com/openai/whisper) - 用于语音识别
- [WhisperX](https://github.com/m-bain/whisperX) - 用于增强语音识别
- [Google Translate](https://cloud.google.com/translate) - 用于文本翻译
- [DeepL](https://www.deepl.com/) - 用于高质量文本翻译
