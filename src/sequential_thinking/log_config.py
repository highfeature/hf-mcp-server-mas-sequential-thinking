from src.sequential_thinking.sensitive_data_filter import SensitiveDataFilter

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
            "level": "DEBUG",
            "filename": "sequential_thinking.log",
            "mode": "a",
        },
        "file_access": {
            "formatter": "formatter_simple",
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "filename": "sequential_thinking_access.log",
            "mode": "a",
        },
        "file_errors": {
            "formatter": "formatter_detailed",
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "filename": "sequential_thinking_errors.log",
            "mode": "a",
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
            "propagate": True,
        },
        "uvicorn.error": {
            "handlers": [
                "file_errors",
                # "console"
            ],
            "level": "INFO",
            # "propagate": True,
        },
        "uvicorn.access": {
            "handlers": [
                "file_access",
                # "console"
            ],
            "level": "INFO",
            # "propagate": True,
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
