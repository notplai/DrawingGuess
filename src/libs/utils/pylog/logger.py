import os
import sys
import traceback
import threading
import inspect

from typing import Optional, Union, Literal, List, Callable, Dict, Any
from .interfaces import LogLevel

# Defines a custom Logger class.
class Logger:
    """
    A custom logger class for formatted and level-based logging.
    It can capture context like file, line, and function name.
    """
    
    def __init__(self, name: str, level: Union[LogLevel, Literal['DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL'], int] = LogLevel.INFO):
        """
        Initializes the Logger.

        Args:
            name: The name of the logger (e.g., __name__).
            level: The minimum LogLevel to output. Can be a LogLevel enum,
                   a string, or an integer.
        """
        self.name: str = name
        # Set the log level, converting from string or int if necessary
        self.level: LogLevel = level if isinstance(level, LogLevel) else LogLevel[level] if isinstance(level, str) else LogLevel(level)
        self.handlers: List[Callable[[Dict[str, Any]], None]] = []
        self.filters: List[Callable[[Dict[str, Any]], bool]] = []
        self.propagate: bool = True
        self.disabled: bool = False
        self.parent: Optional[Logger] = None

    # The core logging method.
    def log(self, level: LogLevel, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Logs a message at a specific level.
        This is the internal method called by debug, info, warning, etc.

        Args:
            level: The LogLevel of the message.
            msg: The message string (can be a format string).
            *args: Arguments for the format string.
            **kwargs: Keyword arguments for the format string.
        """
        # Check if logger is disabled or message level is below logger's level
        if self.disabled or level.value < self.level.value:
            return

        # Format the message
        msg_formatted: str = msg.format(*args, **kwargs) if args else msg

        record: Dict[str, Any]
        try:
            # --- Inspect the call stack to get context ---
            frame = inspect.currentframe()
            # Go back two frames to get the caller of debug(), info(), etc.
            f_back = frame.f_back.f_back if (frame and frame.f_back) else None
            if f_back:
                info = inspect.getframeinfo(f_back)
                record = {
                    'logger': self.name,
                    'level': level,
                    'message': msg_formatted,
                    'thread': threading.current_thread().name,
                    'thread_id': threading.get_ident(),
                    'process_id': os.getpid(),
                    'file': info.filename,
                    'line': info.lineno,
                    'function': info.function,
                }
            else:
                raise Exception("Could not get frame info")
        except Exception:
            # Fallback if inspection fails
            record = {
                'logger': self.name,
                'level': level,
                'message': msg_formatted,
                'thread': threading.current_thread().name,
                'thread_id': threading.get_ident(),
                'process_id': os.getpid(),
            }

        # Apply filters
        for f in self.filters:
            if not f(record):
                return # Filter blocked this message

        # Process message with handlers or default print
        if self.handlers:
            for h in self.handlers:
                h(record)
        elif self.propagate and self.parent:
            self.parent.log(level, msg, *args, **kwargs)
        else:
            # Default output if no handlers
            print(f"[{level.name}] {self.name} ({record.get('thread', '?')}/{record.get('process_id', '?')}): {record['message']}")

    # Logs a DEBUG level message.
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level DEBUG."""
        self.log(LogLevel.DEBUG, msg, *args, **kwargs)

    # Logs an INFO level message.
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level INFO."""
        self.log(LogLevel.INFO, msg, *args, **kwargs)

    # Logs a WARNING level message.
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level WARNING."""
        self.log(LogLevel.WARNING, msg, *args, **kwargs)

    # Logs an ERROR level message.
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level ERROR."""
        self.log(LogLevel.ERROR, msg, *args, **kwargs)

    # Logs a CRITICAL level message.
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level CRITICAL."""
        self.log(LogLevel.CRITICAL, msg, *args, **kwargs)

    # Logs an ERROR level message with exception info.
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs a message with level ERROR and appends exception traceback."""
        exc_info: str = traceback.format_exc()
        self.error(f"{msg}\n{exc_info}", *args, **kwargs)

    # Adds a handler function.
    def add_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Adds a handler function that will be called with the log record."""
        self.handlers.append(handler)

    # Removes a handler function.
    def remove_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Removes a previously added handler function."""
        self.handlers.remove(handler)

    # Adds a filter function.
    def add_filter(self, filter_func: Callable[[Dict[str, Any]], bool]) -> None:
        """Adds a filter function. If it returns False, the log is dropped."""
        self.filters.append(filter_func)

    # Removes a filter function.
    def remove_filter(self, filter_func: Callable[[Dict[str, Any]], bool]) -> None:
        """Removes a previously added filter function."""
        self.filters.remove(filter_func)

    # Sets the logger's minimum output level.
    def set_level(self, level: LogLevel) -> None:
        """Changes the logger's minimum output level."""
        if isinstance(level, LogLevel):
            self.level = level

    # Checks if a given level will be logged.
    def is_enabled_for(self, level: LogLevel) -> bool:
        """Returns True if the logger is enabled for the given level."""
        return not self.disabled and level.value >= self.level.value

    # Gets the effective log level.
    def get_effective_level(self) -> LogLevel:
        """
        Gets the effective log level.
        If self.level is not set, it checks the parent.
        """
        if self.level:
            return self.level
        if self.parent:
            return self.parent.get_effective_level()
        return LogLevel.INFO