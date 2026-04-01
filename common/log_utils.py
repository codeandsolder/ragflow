#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any

from common.file_utils import get_project_base_directory

_initialized_root_logger = False


def init_root_logger(logfile_basename: str, log_format: str = "%(asctime)-15s %(levelname)-8s %(process)d %(message)s") -> None:
    """Initialize the root logger with file and console handlers.

    Args:
        logfile_basename: Base name for the log file (without extension)
        log_format: Log message format string
    """
    global _initialized_root_logger
    if _initialized_root_logger:
        return
    _initialized_root_logger = True

    logger = logging.getLogger()
    logger.handlers.clear()
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(get_project_base_directory(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{logfile_basename}.log")

    # Configure formatter
    formatter = logging.Formatter(log_format)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Capture warnings
    logging.captureWarnings(True)

    # Configure log levels from environment
    _configure_log_levels()

    # Log initialization
    logger.info(f"{logfile_basename} log path: {log_path}, log levels: {dict(_get_log_levels())}")


def _configure_log_levels() -> None:
    """Configure log levels from LOG_LEVELS environment variable."""
    LOG_LEVELS = os.environ.get("LOG_LEVELS", "")
    pkg_levels = {}

    for pkg_name_level in LOG_LEVELS.split(","):
        terms = pkg_name_level.split("=")
        if len(terms) != 2:
            continue
        pkg_name, pkg_level = terms[0].strip(), terms[1].strip()
        
        try:
            level = logging.getLevelName(pkg_level.upper())
            if not isinstance(level, int):
                level = logging.INFO
            pkg_levels[pkg_name] = level
        except Exception:
            continue

    # Set default levels for common libraries
    default_levels = {
        "peewee": logging.WARNING,
        "pdfminer": logging.WARNING,
        "root": logging.INFO
    }

    for pkg_name, default_level in default_levels.items():
        if pkg_name not in pkg_levels:
            pkg_levels[pkg_name] = default_level

    # Apply log levels
    for pkg_name, pkg_level in pkg_levels.items():
        pkg_logger = logging.getLogger(pkg_name)
        pkg_logger.setLevel(pkg_level)


def _get_log_levels() -> dict[str, int]:
    """Get current log levels for all loggers."""
    loggers = {}
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        loggers[name] = logger.level
    return loggers


def log_exception(e: Exception, *args: Any) -> None:
    """Log an exception and any additional arguments, then re-raise the exception.

    Args:
        e: The exception to log
        *args: Additional arguments to log
    """
    logging.exception(e)

    for arg in args:
        try:
            text = getattr(arg, "text", None)
            if text is not None:
                logging.error(text)
                raise Exception(text)
        except Exception:
            pass
        logging.error(str(arg))

    raise e
