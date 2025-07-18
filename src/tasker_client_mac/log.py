import logging
import os
from logging.handlers import RotatingFileHandler

class LoggerClient:
    """
    单例模式实现的客户端日志模块。
    提供统一的日志记录功能，支持文件和控制台输出，可配置日志级别和轮转。
    """
    _instance = None
    LOG_LEVEL = os.environ.get("CLIENT_LOG_LEVEL", "INFO").upper()
    LOG_DIR = "logs"
    LOG_FILE_NAME = "tasker_client_mac.log"
    LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerClient, cls).__new__(cls)
            cls._instance.logger = logging.getLogger("tasker_client_mac_logger")
            cls._instance.setup_logging()
        return cls._instance

    def reset_level(self, level: str, env: str = "dev"):
        """
        重置日志级别。
        :param level: 新的日志级别字符串 (e.g., "INFO", "DEBUG").
        :param env: 环境 (e.g., "dev", "prod").
        """
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"无效的日志级别: {level}")
        self.logger.setLevel(numeric_level)
        if env == "prod":
            # 在生产环境中，可能需要更严格的日志配置
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    self.logger.removeHandler(handler)
            # 确保文件处理器存在
            if not any(isinstance(h, RotatingFileHandler) for h in self.logger.handlers):
                self._add_file_handler()
        else:
            # 开发环境中，确保控制台输出
            if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
                self._add_console_handler()

    def _add_console_handler(self):
        """
        添加控制台处理器。
        """
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _add_file_handler(self):
        """
        添加文件处理器。
        """
        os.makedirs(self.LOG_DIR, exist_ok=True)
        file_handler = RotatingFileHandler(
            self.LOG_FILE_PATH,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def setup_logging(self):
        """
        设置日志配置。
        """
        self.logger.setLevel(getattr(logging, self.LOG_LEVEL, logging.INFO))
        self.logger.propagate = False  # 防止日志重复输出

        # 移除所有现有的处理器，避免重复添加
        if self.logger.handlers:
            for handler in self.logger.handlers:
                self.logger.removeHandler(handler)

        # 添加控制台处理器
        self._add_console_handler()

        # 添加文件处理器
        self._add_file_handler()

# 实例化 LoggerClient，确保单例模式生效
logger_client_instance = LoggerClient().logger