import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pydantic import ValidationError
from starlette.concurrency import iterate_in_threadpool

from src.sequential_thinking.models import ThoughtData
from src.sequential_thinking.team import create_sequential_thinking_team, Team
from src.sequential_thinking.settings import settings
from src.sequential_thinking.log import (
    setup_logging,
    format_thought_for_log,
    log_request,
)

load_dotenv()
setup_logging()

# --- To debug AsyncIO Cancellation ---
# def log_cancellation(f):
#     async def wrapper(*args, **kwargs):
#         try:
#             return await f(*args, **kwargs)
#         except asyncio.CancelledError:
#             print(f"Cancelled {f}")
#             raise
#     return wrapper


@dataclass
class AppContext:
    """Holds shared application resources, like the Pydantic team."""

    team: Team
    thought_history: List[ThoughtData] = field(default_factory=list)
    branches: Dict[str, List[ThoughtData]] = field(default_factory=dict)

    def add_thought(self, thought: ThoughtData) -> None:
        """Add a thought to history and manage branches"""
        self.thought_history.append(thought)

        # Handle branching
        if thought.branchFromThought is not None and thought.branchId is not None:
            if thought.branchId not in self.branches:
                self.branches[thought.branchId] = []
            self.branches[thought.branchId].append(thought)

    def get_branch_thoughts(self, branch_id: str) -> List[ThoughtData]:
        """Get all thoughts in a specific branch"""
        return self.branches.get(branch_id, [])

    def get_all_branches(self) -> Dict[str, int]:
        """Get all branch IDs and their thought counts"""
        return {
            branch_id: len(thoughts) for branch_id, thoughts in self.branches.items()
        }


app_context: Optional[AppContext] = None


# Initialize FastMCP =========================================
mcp = FastMCP("HighfeatureMcpServerSequentialThinking")
# --- MCP Handlers ---


@mcp.prompt("sequential-thinking")
def sequential_thinking_prompt(problem: str, context: str = ""):
    """
    Starter prompt for sequential thinking that ENCOURAGES non-linear exploration
    using coordinate mode. Returns separate user and assistant messages.
    """
    min_thoughts = 5  # Set a reasonable minimum number of initial thoughts

    user_prompt_text = f"""Initiate a comprehensive sequential thinking process for the following problem:

    Problem: {problem}
    {f'Context: {context}' if context else ''}"""

    assistant_guidelines = f"""Okay, let's start the sequential thinking process. Here are the guidelines and the process we'll follow using the 'coordinate' mode team:

    **Sequential Thinking Goals & Guidelines (Coordinate Mode)**:

    1.  **Estimate Steps:** Analyze the problem complexity. Your initial `totalThoughts` estimate should be at least {min_thoughts}.
    2.  **First Thought:** Call the 'sequentialthinking' tool with `thoughtNumber: 1`, your estimated `totalThoughts` (at least {min_thoughts}), and `nextThoughtNeeded: True`. Structure your first thought as: "Plan a comprehensive analysis approach for: {problem}"
    3.  **Encouraged Revision:** Actively look for opportunities to revise previous thoughts if you identify flaws, oversights, or necessary refinements based on later analysis (especially from the Coordinator synthesizing Critic/Analyzer outputs). Use `isRevision: True` and `revisesThought: <thought_number>` when performing a revision. Robust thinking often involves self-correction. Look for 'RECOMMENDATION: Revise thought #X...' in the Coordinator's response.
    4.  **Encouraged Branching:** Explore alternative paths, perspectives, or solutions where appropriate. Use `branchFromThought: <thought_number>` and `branchId: <unique_branch_name>` to initiate branches. Exploring alternatives is key to thorough analysis. Consider suggestions for branching proposed by the Coordinator (e.g., 'SUGGESTION: Consider branching...').
    5.  **Extension:** If the analysis requires more steps than initially estimated, use `needsMoreThoughts: True` on the thought *before* you need the extension.
    6.  **Thought Content:** Each thought must:
        *   Be detailed and specific to the current stage (planning, analysis, critique, synthesis, revision, branching).
        *   Clearly explain the *reasoning* behind the thought, especially for revisions and branches.
        *   Conclude by outlining what the *next* thought needs to address to fulfill the overall plan, considering the Coordinator's synthesis and suggestions.

    **Process:**

    *   The `sequentialthinking` tool will track your progress. The Pydantic team operates in 'coordinate' mode. The Coordinator agent receives your thought, delegates sub-tasks to specialists (like Analyzer, Critic), and synthesizes their outputs, potentially including recommendations for revision or branching.
    *   Focus on insightful analysis, constructive critique (leading to potential revisions), and creative exploration (leading to potential branching).
    *   Actively reflect on the process. Linear thinking might be insufficient for complex problems.

    Proceed with the first thought based on these guidelines."""

    return [
        {
            "description": "Starter prompt for non-linear sequential thinking (coordinate mode), providing problem and guidelines separately.",
            "messages": [
                {"role": "user", "content": {"type": "text", "text": user_prompt_text}},
                {
                    "role": "assistant",
                    "content": {"type": "text", "text": assistant_guidelines},
                },
            ],
        }
    ]


# @log_cancellation
@mcp.tool()
async def sequentialthinking(
    thought: str,
    thoughtNumber: int,
    totalThoughts: int,
    nextThoughtNeeded: bool,
    isRevision: bool = False,
    revisesThought: Optional[int] = None,
    branchFromThought: Optional[int] = None,
    branchId: Optional[str] = None,
    needsMoreThoughts: bool = False,
) -> str:
    """
    A detailed tool for dynamic and reflective problem-solving through thoughts.

    This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
    Each thought can build on, question, or revise previous insights as understanding deepens.
    It uses an Pydantic-based multi-agent team (in coordinate mode) to process each thought, where a
    Coordinator delegates sub-tasks to specialists (Planner, Researcher, Analyzer, Critic, Synthesizer)
    and synthesizes their outputs.

    When to use this tool:
    - Breaking down complex problems into manageable steps.
    - Planning and design processes requiring iterative refinement and revision.
    - Complex analysis where the approach might need course correction based on findings.
    - Problems where the full scope or optimal path is not clear initially.
    - Situations requiring a multi-step solution with context maintained across steps.
    - Tasks where focusing on relevant information and filtering out noise is crucial.
    - Developing and verifying solution hypotheses through a chain of reasoning.

    Key features & usage guidelines:
    - The process is driven by the caller (e.g., an LLM) making sequential calls to this tool.
    - Start with an initial estimate for `totalThoughts`, but adjust it dynamically via subsequent calls if needed.
    - Use `isRevision=True` and `revisesThought` to explicitly revisit and correct previous steps.
    - Use `branchFromThought` and `branchId` to explore alternative paths or perspectives.
    - If the estimated `totalThoughts` is reached but more steps are needed, set `needsMoreThoughts=True` on the *last* thought within the current estimate to signal the need for extension.
    - Express uncertainty and explore alternatives within the `thought` content.
    - Generate solution hypotheses within the `thought` content when appropriate.
    - Verify hypotheses in subsequent `thought` steps based on the reasoning chain.
    - The caller should repeat the process, calling this tool for each step, until a satisfactory solution is reached.
    - Set `nextThoughtNeeded=False` only when the caller determines the process is complete and a final answer is ready.

    Parameters:
        thought (str): The content of the current thinking step. This can be an analytical step,
                       a plan, a question, a critique, a revision, a hypothesis, or verification.
                       Make it specific enough to imply the desired action.
        thoughtNumber (int): The sequence number of this thought (>=1). Can exceed initial `totalThoughts`
                             if the process is extended.
        totalThoughts (int): The current *estimate* of the total thoughts required for the process.
                             This can be adjusted by the caller in subsequent calls. Minimum 5 suggested.
        nextThoughtNeeded (bool): Indicates if the caller intends to make another call to this tool
                                  after the current one. Set to False only when the entire process is deemed complete.
        isRevision (bool, optional): True if this thought revises or corrects a previous thought. Defaults to False.
        revisesThought (int, optional): The `thoughtNumber` of the thought being revised, required if `isRevision` is True.
                                        Must be less than the current `thoughtNumber`.
        branchFromThought (int, optional): The `thoughtNumber` from which this thought branches to explore an alternative path.
                                           Defaults to None.
        branchId (str, optional): A unique identifier for the branch being explored, required if `branchFromThought` is set.
                                 Defaults to None.
        needsMoreThoughts (bool, optional): Set to True on a thought if the caller anticipates needing more
                                             steps beyond the current `totalThoughts` estimate *after* this thought.
                                             Defaults to False.

    Returns:
        str: The Coordinator agent's synthesized response based on specialist contributions for the current `thought`.
             Includes guidance for the caller on potential next steps (e.g., suggestions for revision or branching
             based on the specialists' analysis). The caller uses this response to formulate the *next* thought.
    """
    global app_context

    # Initialize application context if not already initialized
    if not app_context:
        settings.logger_team.info(
            "Initializing application resources directly (Coordinate Mode)..."
        )
        try:
            team = create_sequential_thinking_team()
            app_context = AppContext(team=team)
            provider = settings.LLM_PROVIDER
            settings.logger_team.info(
                f"Pydantic team initialized directly in coordinate mode using provider: {provider}."
            )
        except Exception as e:
            settings.logger_team.critical(
                f"Failed to initialize Pydantic team during tool call: {e}",
                exc_info=True,
            )
            return f"Critical Error: Application context not available and re-initialization failed: {e}"

    try:
        # --- Initial Validation and Adjustments ---
        current_input_thought = ThoughtData(
            thought=thought,
            thoughtNumber=thoughtNumber,
            totalThoughts=totalThoughts,  # Pydantic validator handles minimum now
            nextThoughtNeeded=nextThoughtNeeded,
            isRevision=isRevision,
            revisesThought=revisesThought,
            branchFromThought=branchFromThought,
            branchId=branchId,
            needsMoreThoughts=needsMoreThoughts,
        )

        # Use the validated/adjusted value from the instance
        adjusted_total_thoughts = current_input_thought.totalThoughts

        # Adjust nextThoughtNeeded based on validated totalThoughts
        adjusted_next_thought_needed = current_input_thought.nextThoughtNeeded
        if (
            current_input_thought.thoughtNumber >= adjusted_total_thoughts
            and not current_input_thought.needsMoreThoughts
        ):
            adjusted_next_thought_needed = False

        # --- Logging and History Update ---
        log_prefix = "--- Received Thought ---"
        if current_input_thought.isRevision:
            log_prefix = f"--- Received REVISION Thought (revising #{current_input_thought.revisesThought}) ---"
        elif current_input_thought.branchFromThought is not None:
            log_prefix = f"--- Received BRANCH Thought (from #{current_input_thought.branchFromThought}, ID: {current_input_thought.branchId}) ---"

        formatted_log_thought = format_thought_for_log(current_input_thought)
        settings.logger_team.info(f"\n{log_prefix}\n{formatted_log_thought}\n")

        # Add the *validated* thought to history
        app_context.add_thought(current_input_thought)

        # --- Process Thought with Team (Coordinate Mode) ---
        settings.logger_team.info(
            f"Passing thought #{current_input_thought.thoughtNumber} to the Coordinator..."
        )

        input_prompt = f"Process Thought #{current_input_thought.thoughtNumber}:\n"
        if (
            current_input_thought.isRevision
            and current_input_thought.revisesThought is not None
        ):
            # Find the original thought text
            original_thought_text = "Unknown Original Thought"
            for hist_thought in app_context.thought_history[:-1]:  # Exclude current one
                if hist_thought.thoughtNumber == current_input_thought.revisesThought:
                    original_thought_text = hist_thought.thought
                    break
            input_prompt += f'**This is a REVISION of Thought #{current_input_thought.revisesThought}** (Original: "{original_thought_text}").\n'
        elif (
            current_input_thought.branchFromThought is not None
            and current_input_thought.branchId is not None
        ):
            # Find the branching point thought text
            branch_point_text = "Unknown Branch Point"
            for hist_thought in app_context.thought_history[:-1]:
                if (
                    hist_thought.thoughtNumber
                    == current_input_thought.branchFromThought
                ):
                    branch_point_text = hist_thought.thought
                    break
            input_prompt += f'**This is a BRANCH (ID: {current_input_thought.branchId}) from Thought #{current_input_thought.branchFromThought}** (Origin: "{branch_point_text}").\n'

        input_prompt += f'\nThought Content: "{current_input_thought.thought}"'

        # Call the team's arun method. The coordinator agent will handle it.
        try:
            team_response = await app_context.team.arun(input_prompt)
        except asyncio.CancelledError as ce:
            print(f"Cancelled {ce}")
            raise

        # Ensure coordinator_response is a string, default to empty string if None
        coordinator_response_content = (
            team_response.content if hasattr(team_response, "content") else None
        )
        coordinator_response = (
            str(coordinator_response_content)
            if coordinator_response_content is not None
            else ""
        )

        settings.logger_team.info(
            f"Coordinator finished processing thought #{current_input_thought.thoughtNumber}."
        )
        settings.logger_team.debug(f"Coordinator Raw Response:\n{coordinator_response}")

        # --- Guidance for Next Step (Coordinate Mode) ---
        additional_guidance = "\n\nGuidance for next step:"  # Initialize

        if not adjusted_next_thought_needed:
            additional_guidance = "\n\nThis is the final thought. Review the Coordinator's final synthesis."
        else:
            additional_guidance += "\n- **Revision/Branching:** Look for 'RECOMMENDATION: Revise thought #X...' or 'SUGGESTION: Consider branching...' in the response."
            additional_guidance += " Use `isRevision=True`/`revisesThought=X` for revisions or `branchFromThought=Y`/`branchId='...'` for branching accordingly."
            additional_guidance += "\n- **Next Thought:** Based on the Coordinator's response, formulate the next logical thought, addressing any points raised."

        # --- Build Result ---
        result_data = {
            "processedThoughtNumber": current_input_thought.thoughtNumber,
            "estimatedTotalThoughts": current_input_thought.totalThoughts,
            "nextThoughtNeeded": adjusted_next_thought_needed,
            "coordinatorResponse": coordinator_response + str(additional_guidance),
            "branches": list(app_context.branches.keys()),
            "thoughtHistoryLength": len(app_context.thought_history),
            "branchDetails": {
                "currentBranchId": (
                    current_input_thought.branchId
                    if current_input_thought.branchFromThought is not None
                    else "main"
                ),
                "branchOriginThought": current_input_thought.branchFromThought,
                "allBranches": app_context.get_all_branches(),
            },
            "isRevision": current_input_thought.isRevision,
            "revisesThought": (
                current_input_thought.revisesThought
                if current_input_thought.isRevision
                else None
            ),
            "isBranch": current_input_thought.branchFromThought is not None,
            "status": "success",
        }

        # Return only the coordinatorResponse as a string
        return result_data["coordinatorResponse"]

    except ValidationError as e:
        settings.logger_team.error(f"Validation Error processing tool call: {e}")
        return f"Input validation failed: {e}"
    except Exception as e:
        settings.logger_team.exception("Error processing tool call")
        return f"An unexpected error occurred: {str(e)}"


# Mount the MCP app as a sub-application
mcp_app = mcp.streamable_http_app()


# Initialize FastAPI =========================================
@asynccontextmanager
# @log_cancellation
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manages the application lifecycle."""
    global app_context
    settings.logger_fastapi.info(f"Application starting on port {settings.PORT}")
    settings.logger_fastapi.info(
        "Initializing application resources (Coordinate Mode)..."
    )
    try:
        team = create_sequential_thinking_team()
        app_context = AppContext(team=team)
        provider = settings.LLM_PROVIDER
        settings.logger_fastapi.info(
            f"Pydantic team initialized in coordinate mode using provider: {provider}."
        )
    except Exception as e:
        settings.logger_fastapi.critical(
            f"Failed to initialize Pydantic team during lifespan setup: {e}",
            exc_info=True,
        )
        raise e

    try:
        # Start the MCP server
        async with mcp.session_manager.run():
            yield

        # yield
    finally:
        settings.logger_fastapi.info("Shutting down application resources...")
        app_context = None


app = FastAPI(
    title="hf-mcp-sequential-thinking",
    version="1.0.0",
    description="Leverages an LLM to sequential thinking",
    lifespan=app_lifespan,
    openapi_url="/mcp/openapi.json",
)

# Add CORS middleware to the main FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
    allow_headers=[
        "mcp-protocol-version",
        "mcp-session-id",
        "Authorization",
        "Content-Type",
    ],
    expose_headers=["Mcp-Session-Id"],  # Critical for session handling
)


# Mount the FastMCP app to the FastAPI app
app.mount("/mcp-server", mcp_app, "mcp")

# This automatically handles OPTIONS for all routes, including /mcp.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# add a log middleware
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    try:
        #### request ####
        request.state.req_id = req_id
        request.state.body = json.loads(await request.body() or "{}")
        log_request(request)

        #### response ####
        response = await call_next(request)
        response_body = []
        if response.headers.get("content-type") == "application/json":
            response_body = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))
        return response
    except Exception:
        # Unexpected error handling
        settings.logger_fastapi.error(req_id, {"error_message": "ERR_UNEXPECTED"})
        raise HTTPException(status_code=500, detail="ERR_UNEXPECTED")


# Add response on OPTIONS for openapi_url, workaround for support openwebui
@app.options("/mcp-server/openapi.json")
# @log_cancellation
async def options_openapi(request: Request):
    # Customize the response for the OPTIONS method
    response = {
        "method": "OPTIONS",
        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        "description": "Custom OPTIONS response for /openapi.json",
    }
    return JSONResponse(content=response)


# Define FastAPI routes
@app.get("/")
# @log_cancellation
async def root() -> dict[str, str]:
    """Root endpoint showing service information."""
    return {
        "service": "Highfeature Sequential Thinking MCP Service",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health-check")
# @log_cancellation
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
