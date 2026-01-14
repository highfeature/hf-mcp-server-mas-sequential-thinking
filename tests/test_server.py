import asyncio

from fastmcp.client import Client

from src import mcp

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
                "nextThoughtNeeded": True
            }
        )

        print("\nTest: sequentialthinking")
        print(f"Response type: {type(result)}")
        if isinstance(result, str):
            print(f"Response (truncated): {result[:200]}...")

async def main() -> None:
    """Runs tests against the MCP server."""
    # Test individual functions
    await test_sequential_thinking_tool()

    # Start a simple stdio server for manual testing
    print("\nStarting MCP server on stdio...")
    try:
        await mcp.run_stdio_async()
        print("MCP server running with stdio transport")
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error starting server: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())