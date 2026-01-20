import os


class Settings:
    PORT = int(os.getenv("PORT", 8090))
    logger_fastapi = None
    logger_team = None
    DEBUG=True if os.environ.get("DEBUG", "False") == "True" else False
    DEBUG_AGENTS=True if os.environ.get("DEBUG_AGENTS", "False") == "True" else False
    LOG_FOLDER = os.environ.get("LOG_FOLDER", "./hf-mcp-sequential-thinking/logs")
    WEB_SEARCH_TOOL = os.environ.get("WEB_SEARCH_TOOL", "DuckDuckGoTools")
    # provider
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama").lower()
    # models
    DEEPSEEK_TEAM_MODEL_ID = os.environ.get("DEEPSEEK_TEAM_MODEL_ID", "deepseek-chat")
    DEEPSEEK_AGENT_MODEL_ID = os.environ.get("DEEPSEEK_AGENT_MODEL_ID", "deepseek-chat")
    GROQ_TEAM_MODEL_ID = os.environ.get(
        "GROQ_TEAM_MODEL_ID", "deepseek-r1-distill-llama-70b"
    )
    GROQ_AGENT_MODEL_ID = os.environ.get("GROQ_AGENT_MODEL_ID", "qwen-2.5-32b")
    OPENROUTER_TEAM_MODEL_ID = os.environ.get(
        "OPENROUTER_TEAM_MODEL_ID", "deepseek/deepseek-chat-v3-0324"
    )
    OPENROUTER_AGENT_MODEL_ID = os.environ.get(
        "OPENROUTER_AGENT_MODEL_ID", "deepseek/deepseek-r1"
    )
    OLLAMA_TEAM_MODEL_ID = os.environ.get(
        "OLLAMA_TEAM_MODEL_ID", "hf-tool-thinking-qween3-14b-32k:latest"
    )
    OLLAMA_AGENT_MODEL_ID = os.environ.get(
        "OLLAMA_AGENT_MODEL_ID", "hf-tool-thinking-qween3-14b-32k:latest"
    )


settings = Settings()
