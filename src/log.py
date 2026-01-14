import logging
import logging.handlers
import logging.config
import sys
from pathlib import Path
# from agno.utils.log import agent_logger, team_logger

from src.models import ThoughtData
from src.settings import settings

# def init_logger():
#     # Clear any existing logging handlers
#     loggers = ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "asyncio", "starlette")
#     for logger_name in loggers:
#         logging_logger = logging.getLogger(logger_name)
#         logging_logger.handlers = []  # Clear any existing handlers
#         logging_logger.propagate = True  # Allow logs to propagate to the root logger
#     # setup logging for the fastmcp server
#     formatter = logging.Formatter(
#         '%(asctime)s hf-context7 [%(process)d]: %(message)s',
#         '%b %d %H:%M:%S')
#     formatter.converter = time.gmtime  # if you want UTC time
#     log_level = os.environ.get('LOGLEVEL', 'INFO').upper()
#     # Create a file handler to write logs to a file
#     file_handler = logging.handlers.WatchedFileHandler('hf-context7.log')
#     file_handler.setLevel(log_level)
#     file_handler.setFormatter(formatter)
#     # Create a stream handler to print logs to the console
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(log_level)  # You can set the desired log level for console output
#     console_handler.setFormatter(formatter)
#     settings.logger = logging.getLogger()
#     # in place of logger.addHandler(file_handler) to avoid appending new handler
#     settings.logger.handlers[:] = [file_handler,console_handler] 
#     settings.logger.setLevel(os.environ.get('LOGLEVEL', 'INFO').upper())

def setup_logging():
    """
    Set up application logging with both file and console handlers.
    Logs will be stored in the user's home directory under .sequential_thinking/logs.

    Returns:
        Logger instance configured with both handlers.
    """
    # logging.config.fileConfig('logging.ini')

    # Create logs directory in user's home
    log_dir = Path(settings.LOG_FOLDER)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Create logger
    settings.logger = logging.getLogger("sequential_thinking")
    settings.logger.setLevel(log_level)

    # Log format
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "sequential_thinking.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    settings.logger.addHandler(file_handler)
    settings.logger.addHandler(console_handler)

    # add submodules
    # agent_logger.propagate = True
    # agent_logger.addHandler(file_handler)
    # team_logger.propagate = True
    # team_logger.addHandler(file_handler)


# --- Utility for Formatting Thoughts (for Logging) ---
def format_thought_for_log(thought_data: ThoughtData) -> str:
    """Formats a ThoughtData object into a human-readable string for logging.

    Creates a multi-line log entry summarizing the key details of a thought,
    including its type (standard, revision, or branch), sequence number,
    content, and status flags.

    Args:
        thought_data: The ThoughtData object containing the thought details.

    Returns:
        A formatted string suitable for logging.

    Example format:
        Revision 5/10 (revising thought 3)
          Thought: Refined the analysis based on critique.
          Next Needed: True, Needs More: False
        Branch 6/10 (from thought 4, ID: alt-approach)
          Thought: Exploring an alternative approach.
          Branch Details: ID='alt-approach', originates from Thought #4
          Next Needed: True, Needs More: False
        Thought 1/5
          Thought: Initial plan for the analysis.
          Next Needed: True, Needs More: False
    """
    prefix: str
    context: str = ""
    branch_info_log: str = None # Optional line for branch-specific details

    # Determine the type of thought and associated context
    if thought_data.isRevision and thought_data.revisesThought is not None:
        prefix = 'Revision'
        context = f' (revising thought {thought_data.revisesThought})'
    elif thought_data.branchFromThought is not None and thought_data.branchId is not None:
        prefix = 'Branch'
        context = f' (from thought {thought_data.branchFromThought}, ID: {thought_data.branchId})'
        # Prepare the extra detail line for branches
        branch_info_log = f"  Branch Details: ID='{thought_data.branchId}', originates from Thought #{thought_data.branchFromThought}"
    else:
        # Standard thought
        prefix = 'Thought'
        # No extra context needed for standard thoughts

    # Construct the header line (e.g., "Thought 1/5", "Revision 3/5 (revising thought 2)")
    header = f"{prefix} {thought_data.thoughtNumber}/{thought_data.totalThoughts}{context}"

    # Assemble the log entry lines
    log_lines = [
        header,
        f"  Thought: {thought_data.thought}" # Indent thought content
    ]
    if branch_info_log:
        log_lines.append(branch_info_log) # Add branch details if applicable

    # Add status flags line
    log_lines.append(f"  Next Needed: {thought_data.nextThoughtNeeded}, Needs More: {thought_data.needsMoreThoughts}")

    return "\n".join(log_lines)

