import pytest

from fastmcp.client import Client
from fastapi.testclient import TestClient

from src.main import app, mcp


# for fastAPI tests
tclient = TestClient(app)


# for fastMCP tests
@pytest.fixture
def mcp_server():
    app.run(
        transport="streamable-http", host="127.0.0.1", port=19050
    )  # , path="/mcp-server/mcp/")


# fastAPI tests
@pytest.mark.asyncio
async def test_fastapi_root():
    response = tclient.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "service": "Highfeature Sequential Thinking MCP Service",
        "version": "1.0.0",
        "status": "running",
    }


@pytest.mark.asyncio
async def test_fastapi_health():
    response = tclient.get("/health-check")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# fastAPI tests
@pytest.mark.asyncio
async def test_fastapi_openapi_json_get():
    response = tclient.get("/mcp/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "openapi" in response.json()


async def test_sequential_thinking_tool() -> None:
    """Tests the sequentialthinking tool with a simple input."""
    # Create a client that connects directly to the server instance
    async with Client(mcp) as client:
        result = await client.call_tool(
            "sequentialthinking",
            {
                "thought": "Analyze the core assumptions of the problem.",
                "thoughtNumber": 1,
                "totalThoughts": 5,
                "nextThoughtNeeded": True,
            },
        )

        print("\nTest: sequentialthinking")
        print(f"Response type: {type(result)}")
        if isinstance(result, str):
            print(f"Response (truncated): {result[:200]}...")
