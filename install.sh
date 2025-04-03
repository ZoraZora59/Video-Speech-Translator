#!/bin/bash

# 自动视频翻译工具 - 安装脚本
# 用于安装依赖并设置环境

set -e

echo "=================================================="
echo "      自动视频翻译工具 - 安装脚本"
echo "=================================================="
echo ""

# 检查Python版本
echo "检查Python版本..."
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d "." -f 1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d "." -f 2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "错误: 需要Python 3.8或更高版本，当前版本为 $PYTHON_VERSION"
    exit 1
fi

echo "Python版本检查通过: $PYTHON_VERSION"
echo ""

# 检查FFmpeg
echo "检查FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "警告: 未找到FFmpeg，这是处理视频所必需的"
    echo "请安装FFmpeg后再继续"
    echo "  - macOS: brew install ffmpeg"
    echo "  - Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  - CentOS/RHEL: sudo yum install ffmpeg"
    exit 1
fi
echo "FFmpeg检查通过"
echo ""

# 创建虚拟环境
echo "创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 安装开发模式
echo "以开发模式安装应用..."
pip install -e .

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p temp output logs

echo ""
echo "=================================================="
echo "安装完成！"
echo "=================================================="
echo ""
echo "使用方法:"
echo "1. 激活虚拟环境:"
echo "   source venv/bin/activate"
echo ""
echo "2. 命令行使用:"
echo "   python main.py translate <视频文件路径> --lang en zh-CN"
echo ""
echo "3. 启动Web界面:"
echo "   python web_app.py"
echo "   然后在浏览器中访问: http://localhost:8000"
echo ""
echo "4. 运行测试示例:"
echo "   python examples/test_translator.py <视频文件路径>"
echo ""
echo "详细文档请参阅README.md"
echo ""