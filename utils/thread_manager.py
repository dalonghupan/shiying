"""线程池管理"""
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


class WorkerSignals(QObject):
    """工作线程信号"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)


class Worker(QRunnable):
    """通用工作线程"""
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


class ThreadPoolManager:
    """线程池管理器（单例）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = QThreadPool.globalInstance()
            cls._instance.pool.setMaxThreadCount(4)
        return cls._instance

    def submit(self, fn, *args, **kwargs) -> Worker:
        """提交任务到线程池"""
        worker = Worker(fn, *args, **kwargs)
        self.pool.start(worker)
        return worker
