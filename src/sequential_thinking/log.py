import logging
import logging.handlers
import logging.config
import traceback
from typing import Optional

from pydantic import BaseModel
from starlette.requests import Request

from src.sequential_thinking.log_config import LOGGING_CONFIG
from src.sequential_thinking.models import ThoughtData
from src.sequential_thinking.settings import settings


def log_request(request: Request):
    request_info = RequestInfo(request)
    request_log = RequestLog(
        req_id=request.state.req_id,
        method=request_info.method,
        route=request_info.route,
        ip=request_info.ip,
        url=request_info.url,
        host=request_info.host,
        body=request_info.body,
        headers=request_info.headers,
    )
    settings.logger_fastapi.info(request_log.dict())


def log_error(uuid: str, response_body: dict):
    error_log = ErrorLog(
        req_id=uuid,
        error_message=response_body["error_message"],
    )
    settings.logger_fastapi.error(error_log.dict())
    settings.logger_fastapi.error(traceback.format_exc())


class RequestInfo:
    def __init__(self, request) -> None:
        self.request = request

    @property
    def method(self) -> str:
        return str(self.request.method)

    @property
    def route(self) -> str:
        return self.request["path"]

    @property
    def ip(self) -> str:
        return str(self.request.client.host)

    @property
    def url(self) -> str:
        return str(self.request.url)

    @property
    def host(self) -> str:
        return str(self.request.url.hostname)

    @property
    def headers(self) -> dict:
        return {key: value for key, value in self.request.headers.items()}

    @property
    def body(self) -> dict:
        return self.request.state.body


class RequestLog(BaseModel):
    req_id: str
    method: str
    route: str
    ip: str
    url: str
    host: str
    body: dict
    headers: dict


class ErrorLog(BaseModel):
    req_id: str
    error_message: str


def setup_logging():
    """
    Set up application logging with both file and console handlers.
    Logs will be stored in the user's home directory under .sequential_thinking/logs.

    Returns:
        Logger instance configured with both handlers.
    """
    logging.config.dictConfig(LOGGING_CONFIG)

    settings.logger_fastapi = logging.getLogger("fastapi")
    settings.logger_team = logging.getLogger("team")
    # settings.logger_agent = logging.getLogger("logger_agent_logger")
    # logging.config.fileConfig('logging.ini', disable_existing_loggers=False)

    # # Create logs directory in user's home
    # log_dir = Path(settings.LOG_FOLDER)
    # log_dir.mkdir(parents=True, exist_ok=True)
    # log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # # Create logger
    # settings.logger = logging.getLogger("sequential_thinking")
    # settings.logger.setLevel(log_level)

    # # Log format
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    #     datefmt='%Y-%m-%d %H:%M:%S'
    # )

    # # File handler with rotation
    # file_handler = logging.handlers.RotatingFileHandler(
    #     log_dir / "sequential_thinking.log",
    #     maxBytes=10*1024*1024,  # 10MB
    #     backupCount=5,
    #     encoding='utf-8'
    # )
    # file_handler.setLevel(log_level)
    # file_handler.setFormatter(formatter)

    # # Console handler
    # console_handler = logging.StreamHandler(sys.stderr)
    # console_handler.setLevel(log_level)
    # console_handler.setFormatter(formatter)

    # # Add handlers to logger
    # settings.logger.addHandler(file_handler)
    # settings.logger.addHandler(console_handler)

    # # add submodules
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
    branch_info_log: Optional[str] = None  # Optional line for branch-specific details

    # Determine the type of thought and associated context
    if thought_data.isRevision and thought_data.revisesThought is not None:
        prefix = "Revision"
        context = f" (revising thought {thought_data.revisesThought})"
    elif (
        thought_data.branchFromThought is not None and thought_data.branchId is not None
    ):
        prefix = "Branch"
        context = f" (from thought {thought_data.branchFromThought}, ID: {thought_data.branchId})"
        # Prepare the extra detail line for branches
        branch_info_log = f"  Branch Details: ID='{thought_data.branchId}', originates from Thought #{thought_data.branchFromThought}"
    else:
        # Standard thought
        prefix = "Thought"
        # No extra context needed for standard thoughts

    # Construct the header line (e.g., "Thought 1/5", "Revision 3/5 (revising thought 2)")
    header = (
        f"{prefix} {thought_data.thoughtNumber}/{thought_data.totalThoughts}{context}"
    )

    # Assemble the log entry lines
    log_lines = [header, f"  Thought: {thought_data.thought}"]  # Indent thought content
    if branch_info_log:
        log_lines.append(branch_info_log)  # Add branch details if applicable

    # Add status flags line
    log_lines.append(
        f"  Next Needed: {thought_data.nextThoughtNeeded}, Needs More: {thought_data.needsMoreThoughts}"
    )

    return "\n".join(log_lines)
