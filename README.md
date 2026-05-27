# 拾影

> 拾取人间光影，精选优质画面

一个轻量级桌面图片筛选工具，帮助你从海量照片中快速挑出适合发朋友圈的高质量图片。

## 功能特性

- **双模式筛选**
  - 基础算法模式：基于清晰度（拉普拉斯方差）和构图（三分线 + 对称度）自动评分，无需网络
  - AI 大模型模式：接入本地多模态视觉模型，从画质、光影、氛围感、朋友圈适配度多维度智能评估

- **批量处理**：支持单目录最多 5000 张图片批量加载和筛选

- **可视化预览**：卡片式网格展示，实时显示评分，支持手动勾选调整

- **智能排序**：按评分自动排序，高分图片金色边框标识

- **图片压缩**：支持按质量（10-95 滑块）或目标文件大小（KB）批量压缩，自动添加 `small_` 前缀，RGBA 自动转 RGB

- **一键导出**：批量导出精选图片到指定目录

- **隐私安全**：图片全程本地处理，不上传公网

- **跨平台**：支持 macOS 和 Windows

## 安装

### 环境要求

- Python 3.11+
- macOS / Windows

### 从源码运行

```bash
# 克隆仓库
git clone https://github.com/dalonghupan/shiying.git
cd shiying

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 使用打包版本

下载对应平台的可执行文件，双击即可运行，无需安装 Python。

## 使用说明

1. 点击「选择目录」加载图片文件夹
2. 选择筛选模式（基础算法 / AI 大模型）
3. 点击「开始筛选」，等待评分完成
4. 调整阈值滑块，手动勾选需要的图片
5. 点击「导出已选」保存精选图片，或点击「压缩导出」压缩后保存

### AI 模型配置

如需使用 AI 筛选模式，需先部署本地多模态视觉模型（兼容 OpenAI API 格式）：

1. 在侧边栏选择「AI 大模型」模式
2. 填写模型接口地址（如 `http://localhost:8080/v1/chat/completions`）
3. 填写 API Key（可选）
4. 点击「测试连接」验证配置

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.11 |
| UI 框架 | PyQt6 |
| 图像处理 | OpenCV, Pillow, NumPy |
| AI 调用 | httpx |
| 打包 | PyInstaller |

## 项目结构

```
shiying/
├── main.py                 # 程序入口
├── config.py               # 全局配置
├── ui/                     # 界面层
│   ├── main_window.py      # 主窗口
│   ├── toolbar.py          # 工具栏
│   ├── sidebar.py          # 侧边栏（含压缩设置）
│   ├── preview_panel.py    # 图片预览
│   └── status_bar.py       # 状态栏
├── core/                   # 核心逻辑
│   ├── image_loader.py     # 图片加载
│   ├── algorithm_filter.py # 基础算法筛选
│   ├── ai_agent.py         # AI 模型调用
│   ├── scorer.py           # 统一评分
│   ├── compressor.py       # 图片压缩
│   └── exporter.py         # 图片导出
├── utils/                  # 工具模块
│   ├── image_utils.py      # 图片工具
│   ├── cache.py            # 缩略图缓存
│   ├── logger.py           # 日志配置
│   └── thread_manager.py   # 线程管理
├── assets/                 # 资源文件
│   └── styles.qss          # 主题样式
└── tests/                  # 单元测试
```

## 开发

```bash
# 运行测试
./venv/bin/python -m pytest tests/ -v

# 跨平台打包
./build.sh
```

## 许可证

MIT License

## 致谢

项目名「拾影」，寓意拾取人间光影、精选优质画面。
