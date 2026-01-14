import pytest

from fastmcp.client import Client
from src import mcp

@pytest.mark.asyncio
async def test_sequential_thinking_tool():
    # Create a client that connects directly to the server instance
    async with Client(mcp) as client:
        # Test the sequentialthinking tool with a simple input
        result = await client.call_tool(
            "sequentialthinking",
            {
                "thought": "Analyze the core assumptions of the problem.",
                "thoughtNumber": 1,
                "totalThoughts": 5,
                "nextThoughtNeeded": True
            }
        )

        # Verify that we got a response
        assert result is not None

        # Access the content from the CallToolResult object
        response_content = result.content if hasattr(result, 'content') else result

        # Verify that the response contains the expected fields
        assert isinstance(response_content[0].text, str)