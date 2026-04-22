# -*- coding: utf-8 -*-
"""
@author Jan
@date 2023-05-22
@packageName 
@className LogComponent
@describe Shared logging helpers
"""

import logging.config
import os
import sys
import colorlog
from logging.handlers import TimedRotatingFileHandler
from loguru import logger
from packages.shared.settings.runtime import LOG_DIR




class Logger(object):

    level_relations = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    def __init__(self, app_name, log_level="INFO", file_path="logs"):
        """
        Logger 类构造方法
        :param app_name: 应用程序名称
        :param log_level: 日志级别，默认为 INFO
        :param file_path: 日志文件路径，默认为 logs
        """
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        self.logger = logging.getLogger(app_name)
        # 设置日志级别
        self.logger.setLevel(self.level_relations.get(log_level))

        # 控制台日志处理程序
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # 文件日志处理程序
        file_handler = TimedRotatingFileHandler(
            os.path.join(str(LOG_DIR), f"{app_name}"), when='D', backupCount=7)
        file_handler.setLevel(log_level)

        self.log_colors_config = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        }
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s %(levelname)s [%(filename)s:%(lineno)d %(process)d: - %(funcName)s]: %(message)s',
            log_colors=self.log_colors_config)

        # 日志格式化程序
        # formatter = logging.Formatter(
        #     '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 往屏幕上输出
        sh = logging.StreamHandler()
        # 设置屏幕上显示的格式
        sh.setFormatter(formatter)

        # 将日志处理程序添加到 logger 对象中
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)



class Loguro:
    def __init__(self, level="INFO", rotation="500 MB"):
        # logger.add(level=level)
        # Don't configure loguru here - it's initialized by the app entrypoint.
        self.logger = logger



    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def exception(self, message):
        self.logger.exception(message)

    def debug(self, message):
        self.logger.debug(message)

    def success(self, message):
        self.logger.success(message)



#
#
# LOGGER_ERROR = Loguro(Config.ERROR_LOG_PATH,level = "ERROR",rotation="1 week")
#
# LOGGER_WARNING = Loguro(Config.WARNING_LOG_PATH,level="WARNING", rotation="1 week")

class LoggerFactory:
    def __init__(self):
        pass

    @staticmethod
    def get_logger(level):
        info_log_path = str(LOG_DIR / "info.logs")
        error_log_path = str(LOG_DIR / "error.logs")
        warning_log_path = str(LOG_DIR / "warning.logs")
        if level == "INFO":
            return Loguro(info_log_path, level=level, rotation="1 week")
        elif level == "ERROR":
            return Loguro(error_log_path, level=level, rotation="1 week")
        elif level == "WARNING":
            return Loguro(warning_log_path, level=level, rotation="1 week")
        else:
            raise ValueError("unsupported logging level")


def add_endpoint_logger(endpoint: str):
    """
    添加端点日志处理器
    
    Args:
        endpoint: 端点标识符（如tracerId）
        
    Returns:
        handler_id: 日志处理器ID，用于后续移除
    """
    try:
        handler_id = LOGGER.logger.add(
            str(LOG_DIR / f"{endpoint}.log"),
            level="DEBUG",
            encoding="utf-8",
            rotation="1 day", 
            retention="1 days",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
        )
        return handler_id
    except Exception as e:
        LOGGER.error(f"添加日志文件失败：{e}")
        return None


LOGGER = Loguro(level="INFO", rotation="1 week")

# LOGGER.info("Logging")
# LoggerFactory.get_logger("INFO")
# if __name__ == '__main__':
#     pass
#     LOGGER_INFO.info('Debug information')
# LOGGER.info('Debug information')
