import json
from typing import List, Dict, Any, Optional


class MockOpenAIClient:
    """Mock implementation of OpenAI client for testing"""

    def __init__(
        self, base_url: str = "https://test.openrouter.ai/api/v1", api_key: str = "test-key"
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.call_count = 0
        self.last_request = None

    def chat(self):
        """Return the chat completions mock"""
        return MockChatCompletions(self)


class MockChatCompletions:
    """Mock implementation of chat completions API"""

    def __init__(self, client):
        self.client = client

    def create(self, **kwargs) -> "MockChatCompletion":
        """Mock create method for chat completions"""
        self.client.call_count += 1
        self.client.last_request = kwargs

        # Check if this should be a tool call based on messages
        messages = kwargs.get("messages", [])
        tools = kwargs.get("tools", [])

        # If tools are available and user asks for search, simulate tool call
        if tools and any(
            "search" in msg.get("content", "").lower()
            for msg in messages
            if msg.get("role") == "user"
        ):
            return self._create_tool_call_response(kwargs)
        else:
            return self._create_regular_response(kwargs)

    def _create_tool_call_response(self, kwargs) -> "MockChatCompletion":
        """Create a response that includes tool calls"""
        messages = kwargs.get("messages", [])
        tools = kwargs.get("tools", [])

        # Find the search tool
        search_tool = None
        for tool in tools:
            if tool.get("function", {}).get("name") == "search_course_content":
                search_tool = tool
                break

        if search_tool:
            # Extract query from user message
            query = "test query"
            for msg in messages:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if "search_course_content" in content:
                        # Extract query from the content
                        import re

                        match = re.search(
                            r'search_course_content.*?query.*?["\'](.*?)["\']', content
                        )
                        if match:
                            query = match.group(1)
                    else:
                        query = content
                    break

            # Create mock tool call
            tool_call = {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "search_course_content",
                    "arguments": json.dumps({"query": query}),
                },
            }

            return MockChatCompletion(
                choices=[
                    MockChoice(
                        finish_reason="tool_calls",
                        message=MockMessage(content="", tool_calls=[tool_call]),
                    )
                ]
            )

        return self._create_regular_response(kwargs)

    def _create_regular_response(self, kwargs) -> "MockChatCompletion":
        """Create a regular (non-tool) response"""
        messages = kwargs.get("messages", [])

        # Generate a response based on the last user message
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
                break

        if "test query" in user_content:
            response_content = "This is a test response to the query about course materials."
        elif "course structure" in user_content:
            response_content = "Here is the course structure and outline information."
        else:
            response_content = "I'm an AI assistant here to help with course materials."

        return MockChatCompletion(
            choices=[
                MockChoice(finish_reason="stop", message=MockMessage(content=response_content))
            ]
        )


class MockChatCompletion:
    """Mock chat completion response"""

    def __init__(self, choices: List["MockChoice"]):
        self.choices = choices


class MockChoice:
    """Mock choice in chat completion"""

    def __init__(self, finish_reason: str, message: "MockMessage"):
        self.finish_reason = finish_reason
        self.message = message


class MockMessage:
    """Mock message in chat completion"""

    def __init__(self, content: str, tool_calls: Optional[List] = None):
        self.content = content
        self.tool_calls = tool_calls or []

    def to_dict(self):
        """Convert to dictionary for compatibility"""
        return {"content": self.content, "tool_calls": self.tool_calls}


class MockToolCall:
    """Mock tool call"""

    def __init__(self, call_id: str, function_name: str, function_args: Dict):
        self.id = call_id
        self.function = MockFunction(name=function_name, arguments=function_args)


class MockFunction:
    """Mock function call"""

    def __init__(self, name: str, arguments: Dict):
        self.name = name
        self.arguments = json.dumps(arguments)
