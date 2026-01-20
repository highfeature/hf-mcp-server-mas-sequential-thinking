from src.sequential_thinking.sensitive_data_filter import SensitiveDataFilter
from src.sequential_thinking.settings import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(name)s - %(levelprefix)s %(message)s",
        },
        "formatter_simple": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(name)s:%(levelname)s:  %(message)s",
        },
        "formatter_detailed": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(name)s:%(levelname)s %(module)s:%(lineno)d:  %(message)s",
        },
    },
    "filters": {
        "sensitive_data_filter": {
            "()": SensitiveDataFilter,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "formatter_simple",
            "level": "INFO",
            "stream": "ext://sys.stdout",
            "filters": ["sensitive_data_filter"],
        },
        "file_sequential_thinking": {
            "formatter": "formatter_simple",
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG" if settings.DEBUG else "INFO",
            "filename": f"{settings.LOG_FOLDER}/sequential_thinking.log",
            "mode": "a",
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
        },
        "file_access": {
            "formatter": "formatter_simple",
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG" if settings.DEBUG else "INFO",
            "filename": f"{settings.LOG_FOLDER}/sequential_thinking_access.log",
            "mode": "a",
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
        },
        "file_errors": {
            "formatter": "formatter_detailed",
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG" if settings.DEBUG else "INFO",
            "filename": f"{settings.LOG_FOLDER}/sequential_thinking_errors.log",
            "mode": "a",
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
        },
    },
    "loggers": {
        "root": {
            "handlers": [
                "file_access",
                # "console"
            ],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": [
                "file_access",
                # "console"
            ],
            "level": "INFO",
        },
        "uvicorn.error": {
            "handlers": [
                "file_errors",
                # "console"
            ],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": [
                "file_access",
                "console"
            ],
            "level": "INFO",
        },
        "fastapi": {
            "handlers": [
                "file_sequential_thinking",
                # "console"
            ],
            "level": "INFO",
            "propagate": True,
        },
        # "FastMCP.fastmcp.server.server": {
        #     "handlers": [
        #         "file_sequential_thinking",
        #         "console"
        #     ],
        #     "level": "INFO",
        #     "propagate": False,
        # },
        # "asyncio": {
        #     "handlers": [
        #         "file_errors",
        #         "console"
        #     ],
        #     "level": "INFO",
        #     "propagate": False,
        # },
        # "starlette": {
        #     "handlers": [
        #         "file_errors",
        #         "console"
        #     ],
        #     "level": "INFO",
        #     "propagate": False,
        # },
        # "logger_agent_logger": {
        #     "handlers": [
        #         "file_sequential_thinking",
        #         "console"
        #     ],
        #     "level": "DEBUG",
        #     "propagate": True,
        # },
        "team": {
            "handlers": ["file_sequential_thinking", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
