#!/bin/bash
# 拾影·跨平台打包脚本

set -e

echo "=== 拾影 打包开始 ==="

# 确保依赖已安装
pip install pyinstaller

# 使用 spec 文件打包
pyinstaller 拾影.spec --clean

echo "=== 打包完成 ==="
echo "输出目录: dist/"
echo "可执行文件: dist/拾影"
