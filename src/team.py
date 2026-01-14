from typing import List

from pydantic import ConfigDict, BaseModel, Field
from src.settings import settings

# Define a base Agent model using Pydantic
class Agent(BaseModel):
    name: str
    role: str
    description: str
    tools: List[str] = Field(default_factory=list)
    instructions: List[str]
    model_id: str  # Changed from Model to str to fix validation error
    add_datetime_to_instructions: bool = True
    markdown: bool = True
    debug_mode: bool = False
    model_config = ConfigDict(arbitrary_types_allowed=True)

# Define a base Model class using Pydantic
class Model(BaseModel):
    id: str
    model_config = ConfigDict(arbitrary_types_allowed=True)

# Create specific model classes for each provider
class DeepSeek(Model):
    pass

class Groq(Model):
    pass

class Ollama(Model):
    pass

class OpenRouter(Model):
    pass

def get_model_config() -> tuple[str, str]:
    """
    Determines the LLM provider, team model ID, and agent model ID based on environment variables.

    Returns:
        A tuple containing:
        - team_model_id: The model ID for the team coordinator.
        - agent_model_id: The model ID for the specialist agents.
    """
    provider = settings.LLM_PROVIDER
    settings.logger.info(f"Selected LLM Provider: {provider}")

    if provider == "deepseek":
        # Use environment variables for DeepSeek model IDs if set, otherwise use defaults
        team_model_id = settings.DEEPSEEK_TEAM_MODEL_ID
        agent_model_id = settings.DEEPSEEK_AGENT_MODEL_ID
        settings.logger.info(f"Using DeepSeek: Team Model='{team_model_id}', Agent Model='{agent_model_id}'")
    elif provider == "groq":
        team_model_id = settings.GROQ_TEAM_MODEL_ID
        agent_model_id = settings.GROQ_AGENT_MODEL_ID
        settings.logger.info(f"Using Groq: Team Model='{team_model_id}', Agent Model='{agent_model_id}'")
    elif provider == "openrouter":
        team_model_id = settings.OPENROUTER_TEAM_MODEL_ID
        agent_model_id = settings.OPENROUTER_AGENT_MODEL_ID
        settings.logger.info(f"Using OpenRouter: Team Model='{team_model_id}', Agent Model='{agent_model_id}'")
    elif provider.lower() == "ollama":
        team_model_id = settings.OLLAMA_TEAM_MODEL_ID
        agent_model_id = settings.OLLAMA_AGENT_MODEL_ID
        settings.logger.info(f"Using Ollama: Team Model='{team_model_id}', Agent Model='{agent_model_id}'")
    else:
        settings.logger.error(f"Unsupported LLM_PROVIDER: {provider}. Defaulting to Ollama.")
        team_model_id = "deepseek-r1:7b"
        agent_model_id = "deepseek-r1:7b"

    return team_model_id, agent_model_id

class Team(BaseModel):
    name: str
    mode: str
    members: List[Agent]
    model: Model
    description: str
    instructions: List[str]
    success_criteria: List[str] = Field(default_factory=list)
    enable_agentic_context: bool = False
    share_member_interactions: bool = False
    markdown: bool = True
    debug_mode: bool = False
    add_datetime_to_instructions: bool = True
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def arun(self, input_text: str) -> str:
        """
        Asynchronously processes the input text using the team's coordination logic.

        Args:
            input_text (str): The input text to process

        Returns:
            str: The processed response
        """
        # For now, we'll just return a simple response indicating that the method works
        # In a real implementation, this would coordinate with the team members and process the input
        return f"Team {self.name} has processed the input: {input_text}"

def create_sequential_thinking_team() -> Team:
    """
    Creates and configures the Pydantic-based multi-agent team for sequential thinking,
    using 'coordinate' mode. The Team object itself acts as the coordinator.

    Returns:
        An initialized Team instance.
    """
    try:
        team_model_id, agent_model_id = get_model_config()
        team_model_instance = Model(id=team_model_id)
        # agent_model_instance = Model(id=agent_model_id)

    except Exception as e:
        settings.logger.error(f"Error initializing models: {e}")
        settings.logger.error("Please ensure the necessary API keys and configurations are set for the selected provider.")
        raise

    # Agent definitions for specialists
    planner = Agent(
        name="Planner",
        role="Strategic Planner",
        description="Develops strategic plans and roadmaps based on delegated sub-tasks.",
        tools=["ThinkingTools()"],
        instructions=[
            "You are the Strategic Planner specialist.",
            "You will receive specific sub-tasks from the Team Coordinator related to planning, strategy, or process design.",
            "**When you receive a sub-task:**",
            " 1. Understand the specific planning requirement delegated to you.",
            " 2. Use the `think` tool as a scratchpad if needed to outline your steps or potential non-linear points relevant *to your sub-task*.",
            " 3. Develop the requested plan, roadmap, or sequence of steps.",
            " 4. Identify any potential revision/branching points *specifically related to your plan* and note them.",
            " 5. Consider constraints or potential roadblocks relevant to your assigned task.",
            " 6. Formulate a clear and concise response containing the requested planning output.",
            " 7. Return your response to the Team Coordinator.",
            "Focus on fulfilling the delegated planning sub-task accurately and efficiently.",
        ],
        model_id=agent_model_id, # Use the designated agent model
        add_datetime_to_instructions=True,
        markdown=True,
        debug_mode=settings.DEBUG_AGENTS,
    )

    researcher = Agent(
        name="Researcher",
        role="Information Gatherer",
        description="Gathers and validates information based on delegated research sub-tasks.",
        tools=["ThinkingTools()", "DuckDuckGoTools()" if settings.WEB_SEARCH_TOOL == "DuckDuckGoTools" else "ExaTools()"],
        instructions=[
            "You are the Information Gatherer specialist.",
            "You will receive specific sub-tasks from the Team Coordinator requiring information gathering or verification.",
            "**When you receive a sub-task:**",
            " 1. Identify the specific information requested in the delegated task.",
            " 2. Use your tools (like Exa) to find relevant facts, data, or context. Use the `think` tool to plan queries or structure findings if needed.",
            " 3. Validate information where possible.",
            " 4. Structure your findings clearly.",
            " 5. Note any significant information gaps encountered during your research for the specific sub-task.",
            " 6. Formulate a response containing the research findings relevant to the sub-task.",
            " 7. Return your response to the Team Coordinator.",
            "Focus on accuracy and relevance for the delegated research request.",
        ],
        model_id=agent_model_id, # Use the designated agent model
        add_datetime_to_instructions=True,
        markdown=True,
        debug_mode=settings.DEBUG_AGENTS,
    )

    analyzer = Agent(
        name="Analyzer",
        role="Core Analyst",
        description="Performs analysis based on delegated analytical sub-tasks.",
        tools=["ThinkingTools()"],
        instructions=[
            "You are the Core Analyst specialist.",
            "You will receive specific sub-tasks from the Team Coordinator requiring analysis, pattern identification, or logical evaluation.",
            "**When you receive a sub-task:**",
            " 1. Understand the specific analytical requirement of the delegated task.",
            " 2. Use the `think` tool as a scratchpad if needed to outline your analysis framework or draft insights related *to your sub-task*.",
            " 3. Perform the requested analysis (e.g., break down components, identify patterns, evaluate logic).",
            " 4. Generate concise insights based on your analysis of the sub-task.",
            " 5. Based on your analysis, identify any significant logical inconsistencies or invalidated premises *within the scope of your sub-task* that you should highlight in your response.",
            " 6. Formulate a response containing your analytical findings and insights.",
            " 7. Return your response to the Team Coordinator.",
            "Focus on depth and clarity for the delegated analytical task.",
        ],
        model_id=agent_model_id, # Use the designated agent model
        add_datetime_to_instructions=True,
        markdown=True,
        debug_mode=settings.DEBUG_AGENTS,
    )

    critic = Agent(
        name="Critic",
        role="Quality Controller",
        description="Critically evaluates ideas or assumptions based on delegated critique sub-tasks.",
        tools=["ThinkingTools()"],
        instructions=[
            "You are the Quality Controller specialist.",
            "You will receive specific sub-tasks from the Team Coordinator requiring critique, evaluation of assumptions, or identification of flaws.",
            "**When you receive a sub-task:**",
            " 1. Understand the specific aspect requiring critique in the delegated task.",
            " 2. Use the `think` tool as a scratchpad if needed to list assumptions or potential weaknesses related *to your sub-task*.",
            " 3. Critically evaluate the provided information or premise as requested.",
            " 4. Identify potential biases, flaws, or logical fallacies within the scope of the sub-task.",
            " 5. Suggest specific improvements or point out weaknesses constructively.",
            " 6. If your critique reveals significant flaws or outdated assumptions *within the scope of your sub-task*, highlight this clearly in your response.",
            " 7. Formulate a response containing your critical evaluation and recommendations.",
            " 8. Return your response to the Team Coordinator.",
            "Focus on rigorous and constructive critique for the delegated evaluation task.",
        ],
        model_id=agent_model_id, # Use the designated agent model
        add_datetime_to_instructions=True,
        markdown=True,
        debug_mode=settings.DEBUG_AGENTS,
    )

    synthesizer = Agent(
        name="Synthesizer",
        role="Integration Specialist",
        description="Integrates information or forms conclusions based on delegated synthesis sub-tasks.",
        tools=["ThinkingTools()"],
        instructions=[
            "You are the Integration Specialist.",
            "You will receive specific sub-tasks from the Team Coordinator requiring integration of information, synthesis of ideas, or formation of conclusions.",
            "**When you receive a sub-task:**",
            " 1. Understand the specific elements needing integration or synthesis in the delegated task.",
            " 2. Use the `think` tool as a scratchpad if needed to outline connections or draft conclusions related *to your sub-task*.",
            " 3. Connect the provided elements, identify overarching themes, or draw conclusions as requested.",
            " 4. Distill complex inputs into clear, structured insights for the sub-task.",
            " 5. Formulate a response presenting the synthesized information or conclusions.",
            " 6. Return your response to the Team Coordinator.",
            "Focus on creating clarity and coherence for the delegated synthesis task.",
            "**For the final synthesis task provided by the Coordinator:** Aim for a concise and high-level integration. Focus on the core synthesized understanding and key takeaways, rather than detailing the step-by-step process or extensive analysis of each component.",
        ],
        model_id=agent_model_id, # Use the designated agent model
        add_datetime_to_instructions=True,
        markdown=True,
        debug_mode=settings.DEBUG_AGENTS,
    )

    # Create the team with coordinate mode.
    # The Team object itself acts as the coordinator, using the instructions/description/model provided here.
    team = Team(
        name="SequentialThinkingTeam",
        mode="coordinate",
        members=[planner, researcher, analyzer, critic, synthesizer], # ONLY specialist agents
        model=team_model_instance, # Model for the Team's coordination logic
        description="You are the Coordinator of a specialist team processing sequential thoughts. Your role is to manage the flow, delegate tasks, and synthesize results.",
        instructions=[
            "You are the Coordinator managing a team of specialists (Planner, Researcher, Analyzer, Critic, Synthesizer) in 'coordinate' mode.",
            "Your core responsibilities when receiving an input thought:",
            " 1. Analyze the input thought, considering its type (e.g., initial planning, analysis, revision, branch).",
            " 2. Break the thought down into specific, actionable sub-tasks suitable for your specialist team members.",
            " 3. Determine the MINIMUM set of specialists required to address the thought comprehensively.",
            " 4. Delegate the appropriate sub-task(s) ONLY to the essential specialists identified. Provide clear instructions and necessary context (like previous thought content if revising/branching) for each sub-task.",
            " 5. Await responses from the delegated specialist(s).",
            " 6. Synthesize the responses from the specialist(s) into a single, cohesive, and comprehensive response addressing the original input thought.",
            " 7. Based on the synthesis and specialist feedback, identify potential needs for revision of previous thoughts or branching to explore alternatives.",
            " 8. Include clear recommendations in your final synthesized response if revision or branching is needed. Use formats like 'RECOMMENDATION: Revise thought #X...' or 'SUGGESTION: Consider branching from thought #Y...'.",
            " 9. Ensure the final synthesized response directly addresses the initial input thought and provides necessary guidance for the next step in the sequence.",
            "Delegation Criteria:",
            " - Choose specialists based on the primary actions implied by the thought (planning, research, analysis, critique, synthesis).",
            " - **Prioritize Efficiency:** Delegate sub-tasks only to specialists whose expertise is *strictly necessary*. Aim to minimize concurrent delegations.",
            " - Provide context: Include relevant parts of the input thought or previous context when delegating.",
            "Synthesis:",
            " - Integrate specialist responses logically.",
            " - Resolve conflicts or highlight discrepancies.",
            " - Formulate a final answer representing the combined effort.",
            "Remember: Orchestrate the team effectively and efficiently."
        ],
        success_criteria=[
            "Break down input thoughts into appropriate sub-tasks",
            "Delegate sub-tasks efficiently to the most relevant specialists",
            "Specialists execute delegated sub-tasks accurately",
            "Synthesize specialist responses into a cohesive final output addressing the original thought",
            "Identify and recommend necessary revisions or branches based on analysis"
        ],
        enable_agentic_context=False, # Allows context sharing managed by the Team (coordinator)
        share_member_interactions=False, # Allows members' interactions to be shared
        markdown=True,
        debug_mode=settings.DEBUG_AGENTS,
        add_datetime_to_instructions=True
    )

    return team