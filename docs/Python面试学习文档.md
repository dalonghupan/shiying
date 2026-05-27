# Python 面试学习文档

> 基于「拾影」项目的开发实践，提炼 Python 面试高频知识点

---

## 一、Python 基础

### 1.1 类型提示（Type Hints）

```python
# 函数签名类型提示
def compress_images(
    source_paths: list[str],
    dest_dir: str,
    quality: int = 80,
    max_size_kb: int = 0,
    on_progress: Callable[[int, int], None] | None = None
) -> dict[str, int]:
    ...

# 类属性类型提示
class ImageLoader(QObject):
    _image_paths: list[Path] = []
    _processed_count: int = 0

# dict 类型提示
_scores: dict[str, float] = {}  # path -> score
```

**面试考点**：
- `list[str]` vs `List[str]`：Python 3.9+ 内置泛型，之前需 `from typing import List`
- `X | None` vs `Optional[X]`：Python 3.10+ 联合类型语法
- `Callable[[int, int], None]`：可调用对象类型，参数类型 + 返回类型

### 1.2 路径处理（pathlib）

```python
from pathlib import Path

CACHE_DIR = Path.home() / ".shiying" / "cache"
LOG_DIR = Path.home() / ".shiying" / "logs"

# 创建目录
Path(dest_dir).mkdir(parents=True, exist_ok=True)

# 遍历文件
for path in Path(directory).iterdir():
    if path.suffix.lower() in SUPPORTED_FORMATS:
        ...

# 路径属性
path.suffix       # ".jpg"
path.stem         # "photo"
path.name         # "photo.jpg"
path.parent       # 父目录
```

**面试考点**：
- `pathlib.Path` vs `os.path`：前者是面向对象的，支持 `/` 拼接，更 Pythonic
- `mkdir(parents=True, exist_ok=True)`：递归创建目录，已存在不报错
- `Path.home()`：跨平台获取用户主目录

### 1.3 枚举与常量

```python
# 常量（约定大写，无强制）
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
THUMBNAIL_SIZE = (256, 256)
COLOR_PRIMARY = "#7C4DFF"

# 集合用于快速查找
if path.suffix.lower() in SUPPORTED_FORMATS:  # O(1)
```

**面试考点**：
- `set` 的 `in` 操作是 O(1)，`list` 的 `in` 是 O(n)
- Python 没有真正的常量，靠命名约定（全大写）
- `frozenset` 用于不可变集合场景

### 1.4 字典操作

```python
# 字典推导
sorted_items = sorted(
    self.cards.items(),
    key=lambda x: x[1]._score,
    reverse=descending
)
self.cards = dict(sorted_items)

# 安全取值
score = self._scores.get(path, 0.0)

# 字典遍历
for path, card in self.cards.items():
    card.checkbox.setChecked(card._score >= threshold)

# 条件筛选
selected = [path for path, card in self.cards.items() if card.is_selected]
```

**面试考点**：
- `dict.items()` 返回键值对视图，Python 3.7+ 字典保持插入顺序
- `sorted()` 的 `key` 参数接收函数，`lambda` 是常见用法
- 字典推导 `{k: v for ...}` vs `dict()` 构造

---

## 二、面向对象编程

### 2.1 类的继承与多态

```python
# 自定义 QWidget 子类
class ImageCard(QWidget):
    toggled = pyqtSignal(str, bool)  # 类属性：信号

    def __init__(self, image_path: str, pixmap: QPixmap, index: int = 0, parent=None):
        super().__init__(parent)  # 调用父类构造
        self.image_path = image_path
        self._score = 0.0        # 实例属性

    def mouseDoubleClickEvent(self, event: QMouseEvent):  # 重写父类方法
        self.double_clicked.emit(self.image_path)

# 自定义 QSlider 子类
class JumpSlider(QSlider):
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            val = self.minimum() + (self.maximum() - self.minimum()) * event.position().x() / self.width()
            self.setValue(int(val))
        super().mousePressEvent(event)  # 必须调用 super() 保留父类行为
```

**面试考点**：
- `super().__init__(parent)` 必须调用，否则 Qt 对象未正确初始化
- 重写事件处理方法时，是否需要调用 `super()` 取决于是否要保留父类行为
- Python 的 MRO（方法解析顺序）：C3 线性化

### 2.2 属性装饰器

```python
class ImageCard(QWidget):
    @property
    def is_selected(self) -> bool:
        return self.checkbox.isChecked()

    # 使用
    if card.is_selected:  # 像访问属性一样调用方法
        ...
```

**面试考点**：
- `@property` 将方法伪装为属性，支持 getter/setter/deleter
- 何时用 `@property`：需要计算逻辑但对外表现为属性时
- `@property` vs 直接属性：前者可加校验、缓存、日志

### 2.3 单例模式

```python
class ThreadPoolManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = QThreadPool.globalInstance()
            cls._instance.pool.setMaxThreadCount(4)
        return cls._instance
```

**面试考点**：
- `__new__` 控制对象创建，`__init__` 控制对象初始化
- 单例的线程安全问题：此处依赖 GIL，多线程场景需加锁
- 替代方案：模块级变量、装饰器 `@functools.lru_cache`

---

## 三、异常处理

### 3.1 完整的异常处理链

```python
# 网络请求异常处理
async def test_connection(self) -> bool:
    try:
        response = await self._client.post(self.config.api_url, json=payload)
        response.raise_for_status()
        return True
    except httpx.ConnectError:
        logger.error("连接失败: %s", self.config.api_url)
        return False
    except httpx.TimeoutException:
        logger.error("连接超时: %s", self.config.api_url)
        return False
    except httpx.HTTPStatusError as e:
        logger.error("HTTP 错误: %s — %s", e.response.status_code, e.response.text)
        return False
    except Exception as e:
        logger.error("未知错误: %s", e, exc_info=True)
        return False
    finally:
        await self.close()  # 资源释放
```

**面试考点**：
- 异常从具体到宽泛排列（`ConnectError` 在 `Exception` 之前）
- `finally` 无论如何都会执行，适合资源释放
- `exc_info=True` 记录完整堆栈，便于排查
- `as e` 绑定异常对象，获取详细信息

### 3.2 自定义异常与熔断

```python
# 连续失败熔断
consecutive_errors = 0
for path in self._image_paths:
    try:
        result = await agent.score_image(path)
        consecutive_errors = 0  # 成功则重置
    except Exception as e:
        consecutive_errors += 1
        if consecutive_errors >= 3:
            raise RuntimeError(f"连续 {consecutive_errors} 次评分失败，可能是模型配置错误: {e}")
```

**面试考点**：
- 熔断模式：避免无效重试，快速失败
- `raise` 重新抛出异常，保留原始堆栈
- `RuntimeError` vs `ValueError` vs `TypeError`：选择语义最接近的异常类型

### 3.3 JSON 解析容错

```python
def _parse_ai_response(text: str) -> dict:
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 markdown 代码块中的 JSON
    import re
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试从文本中提取 JSON 对象
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法解析 AI 响应: {text[:200]}")
```

**面试考点**：
- 多层 fallback 策略：每层失败后尝试下一层
- 正则 `re.DOTALL` 让 `.` 匹配换行符
- 提前返回 vs 嵌套 if：前者更清晰

---

## 四、并发编程

### 4.1 多线程（QThreadPool + QRunnable）

```python
class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()

# 提交任务
worker = self.thread_pool.submit(process_image, path)
worker.signals.result.connect(self._on_score_result)  # 跨线程信号
```

**面试考点**：
- `QRunnable` 是轻量级任务对象，由 `QThreadPool` 管理
- 跨线程通信必须通过信号槽（Qt 的线程安全机制）
- `QThreadPool.globalInstance()` 全局线程池，默认最大线程数 = CPU 核心数

### 4.2 异步编程（asyncio + httpx）

```python
import asyncio
import httpx

class AIAgent:
    def __init__(self, config: AIConfig):
        self._client = httpx.AsyncClient(timeout=config.timeout)

    async def score_image(self, image_path: str) -> dict:
        response = await self._client.post(
            self.config.api_url,
            json=payload,
            headers={"Authorization": f"Bearer {self.config.api_key}"}
        )
        response.raise_for_status()
        return self._extract_score(response.json())

    async def close(self):
        await self._client.aclose()

# 在线程中运行异步代码
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_ai_scoring())
    finally:
        loop.run_until_complete(agent.close())
        loop.close()

worker = self.thread_pool.submit(run_async)
```

**面试考点**：
- `async/await` 是协程语法，`await` 挂起当前协程，让出控制权
- `httpx.AsyncClient` 是异步 HTTP 客户端，需配合 `await` 使用
- `asyncio.new_event_loop()` 在子线程中创建新事件循环（主线程已有）
- `aclose()` 关闭异步客户端，释放连接池

### 4.3 线程 vs 协程 vs 进程

| 维度 | 线程 (threading) | 协程 (asyncio) | 进程 (multiprocessing) |
|------|-----------------|----------------|----------------------|
| 切换方式 | OS 调度，抢占式 | 程序控制，协作式 | OS 调度，独立进程 |
| GIL 影响 | 受限（CPU 密集不行） | 不受影响 | 不受影响 |
| 适用场景 | I/O 密集 | I/O 密集 | CPU 密集 |
| 通信方式 | 共享内存（需锁） | 事件循环 | Pipe/Queue |
| 开销 | 中等 | 最小 | 最大 |

**本项目选择**：
- 图片加载（I/O）→ `QThreadPool` + `QRunnable`
- AI 请求（网络 I/O）→ `asyncio` + `httpx`（在子线程中运行事件循环）
- 图片评分（CPU）→ 也在 `QThreadPool` 中运行（利用多核）

---

## 五、图像处理

### 5.1 PIL/Pillow 基础操作

```python
from PIL import Image

# 打开与转换
img = Image.open(image_path)
img = img.convert("RGB")           # 转为 RGB（丢弃 alpha）
img = img.convert("L")             # 转为灰度

# 缩放
img.thumbnail((256, 256), Image.Resampling.LANCZOS)  # 等比缩放，不放大

# 保存
img.save(output_path, "JPEG", quality=80, optimize=True)

# 获取像素数据
data = img.tobytes("raw", "RGB")   # 原始字节，用于创建 QImage
```

**面试考点**：
- `thumbnail()` vs `resize()`：前者保持比例且不放大，后者强制目标尺寸
- `convert("RGB")` 是 RGBA→RGB 的标准方法
- `LANCZOS` 是最高质量的下采样算法
- `optimize=True` 启用 Huffman 编码优化，文件更小但保存更慢

### 5.2 OpenCV 基础操作

```python
import cv2
import numpy as np

# 读取（BGR 格式）
img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)  # 灰度读取

# 清晰度评分（拉普拉斯方差）
def score_sharpness(gray_img: np.ndarray) -> float:
    laplacian = cv2.Laplacian(gray_img, cv2.CV_64F)
    return laplacian.var()  # 方差越大越清晰
```

**面试考点**：
- OpenCV 默认 BGR，PIL 默认 RGB，混用时需转换
- `cv2.IMREAD_GRAYSCALE` 直接读灰度，避免内存浪费
- 拉普拉斯方差是清晰度评价的经典算法

---

## 六、测试（pytest）

### 6.1 基本测试结构

```python
import pytest
from pathlib import Path
from PIL import Image

def _create_test_image(path: Path, size=(100, 100), mode="RGB"):
    """测试辅助函数"""
    img = Image.new(mode, size, color="red")
    img.save(path, "PNG")

def test_compress_images_basic(tmp_path):
    """tmp_path 是 pytest 内置 fixture，自动创建临时目录"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"

    _create_test_image(src_dir / "photo.png")

    result = compress_images([str(src_dir / "photo.png")], str(dst_dir), quality=50)

    assert result["success"] == 1
    assert result["failed"] == 0
    assert (dst_dir / "small_photo.png").exists()
    assert (dst_dir / "small_photo.png").stat().st_size > 0
```

### 6.2 参数化测试

```python
@pytest.mark.parametrize("mode", ["RGB", "RGBA", "L"])
def test_convert_mode(tmp_path, mode):
    """测试不同颜色模式都能正确处理"""
    img = Image.new(mode, (100, 100), color="red")
    path = tmp_path / f"test_{mode}.png"
    img.save(path, "PNG")
    result = compress_images([str(path)], str(tmp_path / "out"))
    assert result["success"] == 1
```

### 6.3 异常测试

```python
def test_compress_images_invalid_file(tmp_path):
    """无效文件应计入 failed，不抛异常"""
    result = compress_images(["/nonexistent/photo.jpg"], str(tmp_path / "out"))
    assert result["failed"] == 1
    assert result["success"] == 0

def test_raises_value_error():
    with pytest.raises(ValueError, match="不支持图片"):
        agent.score_image("/path/to/image.jpg")
```

**面试考点**：
- `tmp_path` 是 pytest 内置 fixture，自动清理临时目录
- `pytest.raises` 用于断言抛出特定异常
- `match` 参数支持正则匹配异常信息
- 测试文件命名 `test_*.py`，函数命名 `test_*`

---

## 七、日志系统

### 7.1 logging 模块配置

```python
import logging
from logging.handlers import RotatingFileHandler
from config import LOG_DIR

def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "shiying.log"

    handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    ))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)

# 各模块获取 logger
logger = get_logger(__name__)
logger.info("加载完成，共 %d 张", count)
logger.error("AI 评分失败: %s — %s", path, e, exc_info=True)
```

**面试考点**：
- `RotatingFileHandler`：文件达到 `maxBytes` 后自动轮转，保留 `backupCount` 个备份
- `%(name)s` 通常是模块名 `__name__`，便于定位日志来源
- `%s` 占位符 vs f-string：logging 推荐用 `%s`，因为只有实际输出时才格式化（性能）
- `exc_info=True` 记录完整异常堆栈

---

## 八、GUI 开发（PyQt6）

### 8.1 信号槽机制

```python
from PyQt6.QtCore import pyqtSignal

class Toolbar(QWidget):
    filter_clicked = pyqtSignal()           # 无参数信号
    directory_selected = pyqtSignal(str)     # 带参数信号

# 连接信号
self.toolbar.filter_clicked.connect(self._on_filter_clicked)
self.toolbar.directory_selected.connect(self._on_directory_selected)

# 发射信号
self.filter_clicked.emit()
self.directory_selected.emit(dir_path)

# Lambda 连接
self.test_btn.clicked.connect(lambda: self.test_connection_clicked.emit())
```

### 8.2 布局系统

```python
# 垂直布局
layout = QVBoxLayout()
layout.addWidget(widget1)
layout.addWidget(widget2)
layout.addStretch()  # 弹性空间，把组件推到顶部

# 水平布局
h_layout = QHBoxLayout()
h_layout.addWidget(slider)
h_layout.addWidget(label)

# 表单布局
form = QFormLayout()
form.addRow("名称:", input_field)
form.addRow(button)

# 手动定位（替代布局）
widget.setGeometry(x, y, width, height)  # 相对于父组件的坐标
```

### 8.3 事件循环与 UI 刷新

```python
# 正确做法：依赖事件循环自然刷新
card.show()
self._relayout_grid()  # 更新几何信息
# Qt 会在下一个 paint 事件中自动重绘

# 错误做法：强制处理事件（可能导致重入崩溃）
card.show()
QApplication.processEvents()  # macOS 上可能崩溃
```

**面试考点**：
- Qt 的事件循环是单线程的，UI 操作必须在主线程
- 跨线程信号通过 `QueuedConnection` 安全传递
- `processEvents()` 会递归处理事件，可能导致重入

---

## 九、项目架构设计

### 9.1 目录结构

```
shiying/
├── main.py              # 入口
├── config.py            # 全局配置常量
├── core/                # 核心业务逻辑
│   ├── ai_agent.py      # AI 模型调用
│   ├── algorithm_filter.py  # 基础算法
│   ├── compressor.py    # 图片压缩
│   ├── exporter.py      # 图片导出
│   ├── image_loader.py  # 图片加载
│   └── scorer.py        # 评分逻辑
├── ui/                  # 界面层
│   ├── main_window.py   # 主窗口
│   ├── preview_panel.py # 预览面板
│   ├── sidebar.py       # 侧边栏
│   ├── status_bar.py    # 状态栏
│   └── toolbar.py       # 工具栏
├── utils/               # 工具类
│   ├── cache.py         # 缓存管理
│   ├── image_utils.py   # 图片工具
│   ├── logger.py        # 日志配置
│   └── thread_manager.py # 线程池管理
└── tests/               # 测试
    ├── test_algorithm_filter.py
    ├── test_compressor.py
    ├── test_exporter.py
    ├── test_image_utils.py
    └── test_scorer.py
```

**面试考点**：
- 分层架构：UI 层 → 业务层（core）→ 工具层（utils）
- 单向依赖：UI → core → utils，不反向引用
- 配置集中管理：`config.py` 存放所有常量

### 9.2 模块间通信

```
用户操作 → Toolbar (信号) → MainWindow (槽函数)
                              ↓
                         ImageLoader (线程池)
                              ↓ (信号)
                         MainWindow._on_thumbnail_ready
                              ↓
                         PreviewPanel.add_image
```

**面试考点**：
- 信号槽实现松耦合：Toolbar 不知道 MainWindow 的存在
- 单向数据流：UI 发起 → 业务处理 → UI 更新
- 避免循环依赖：通过信号通信而非直接调用

---

## 十、常见面试问题

### Q: `list` vs `tuple` vs `set` vs `dict` 的区别？

| 类型 | 有序 | 可变 | 重复 | 查找 | 用途 |
|------|------|------|------|------|------|
| list | 是 | 是 | 是 | O(n) | 有序集合 |
| tuple | 是 | 否 | 是 | O(n) | 不可变数据 |
| dict | 是* | 是 | key 不可 | O(1) | 键值映射 |
| set | 否 | 是 | 否 | O(1) | 去重、集合运算 |

*Python 3.7+ dict 保持插入顺序

### Q: 深拷贝 vs 浅拷贝？

```python
import copy

a = [[1, 2], [3, 4]]
b = copy.copy(a)       # 浅拷贝：外层新对象，内层引用同一对象
c = copy.deepcopy(a)   # 深拷贝：完全独立的新对象

a[0][0] = 99
print(b[0][0])  # 99（浅拷贝受影响）
print(c[0][0])  # 1（深拷贝不受影响）
```

### Q: GIL 是什么？如何绕过？

GIL（Global Interpreter Lock）是 CPython 的全局解释器锁，同一时刻只有一个线程执行 Python 字节码。

绕过方式：
- **多进程**：`multiprocessing`，每个进程独立 GIL
- **C 扩展**：NumPy/Pandas 等计算密集操作在 C 层释放 GIL
- **异步 I/O**：`asyncio`，I/O 等待时释放 GIL

### Q: `*args` 和 `**kwargs` 的区别？

```python
def fn(*args, **kwargs):
    print(args)    # tuple: (1, 2, 3)
    print(kwargs)  # dict: {'a': 1, 'b': 2}

fn(1, 2, 3, a=1, b=2)
```

### Q: 装饰器是什么？写一个计时装饰器。

```python
import time
import functools

def timer(func):
    @functools.wraps(func)  # 保留原函数元信息
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

@timer
def heavy_computation():
    time.sleep(1)
```

### Q: 上下文管理器是什么？

```python
# 方式一：类实现
class DatabaseConnection:
    def __enter__(self):
        self.conn = create_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        return False  # 不吞掉异常

with DatabaseConnection() as conn:
    conn.execute("SELECT ...")

# 方式二：contextmanager 装饰器
from contextlib import contextmanager

@contextmanager
def timer():
    start = time.perf_counter()
    yield
    print(f"Elapsed: {time.perf_counter() - start:.3f}s")
```

### Q: 什么是鸭子类型（Duck Typing）？

Python 不检查对象类型，只检查对象是否有需要的方法/属性：

```python
# 不关心是不是 QSlider 的子类，只要有 setValue/width/minimum/maximum 就行
class JumpSlider(QSlider):
    def mousePressEvent(self, event):
        val = self.minimum() + (self.maximum() - self.minimum()) * event.position().x() / self.width()
        self.setValue(int(val))
        super().mousePressEvent(event)
```

### Q: `is` vs `==` 的区别？

```python
a = [1, 2, 3]
b = [1, 2, 3]
a == b   # True（值相等）
a is b   # False（不是同一对象）

c = a
a is c   # True（同一对象）
```

- `==` 调用 `__eq__`，比较值
- `is` 比较对象 id（内存地址）
- `None` 比较始终用 `is`：`if x is None`

### Q: 什么是 `__slots__`？

```python
class Point:
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
p.z = 3  # AttributeError: 'Point' object has no attribute 'z'
```

- 限制实例只能拥有指定属性
- 节省内存（不用 `__dict__`）
- 适用于大量实例的场景
