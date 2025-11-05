import enum

# Defines the standard logging levels as an Enum.
LogLevel = enum.Enum('LogLevel', {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'WARN': 30, 'ERROR': 40, 'CRITICAL': 50})