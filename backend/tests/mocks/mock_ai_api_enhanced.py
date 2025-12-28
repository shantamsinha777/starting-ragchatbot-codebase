"""
Enhanced Mock AI API for Sequential Tool Calling Tests

This mock supports round-aware responses and can simulate the full sequential
tool calling flow for testing purposes.
"""

import json
from typing import List, Dict, Any, Optional, Callable


class MockOpenAIClientEnhanced:
    """
    Enhanced mock client that supports sequential round testing.

    Features:
    - Track API call count and history
    - Configurable responses per round
    - Simulate sequential tool calls
    - Verify message history
    """

    def __init__(self, base_url: str = "https://test.openrouter.ai/api/v1", api_key: str = "test-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.call_count = 0
        self.request_history: List[Dict] = []
        self.response_strategy = None  # Function that determines response per call

    def completions(self):
        """Return the chat completions mock"""
        return MockChatCompletionsEnhanced(self)

    @property
    def chat(self):
        """Property for chat.completions.create() access pattern"""
        return type('Chat', (), {'completions': self.completions()})()

    def set_response_strategy(self, strategy: Callable[[int, Dict], 'MockChatCompletion']):
        """
        Set a response strategy function.

        Args:
            strategy: Function that takes (call_count, request_kwargs) and returns a response
        """
        self.response_strategy = strategy

    def get_call_count(self) -> int:
        """Get total API call count"""
        return self.call_count

    def get_request(self, n: int) -> Optional[Dict]:
        """Get the nth request (0-indexed)"""
        if 0 <= n < len(self.request_history):
            return self.request_history[n]
        return None

    def verify_message_chain(self) -> tuple[bool, str]:
        """
        Verify that the message chain is valid for sequential tool calling.

        Returns:
            (is_valid, error_message)
        """
        if not self.request_history:
            return False, "No requests made"

        for i, request in enumerate(self.request_history):
            messages = request.get('messages', [])

            # Check that tool messages follow their corresponding tool_calls
            tool_messages = [m for m in messages if m.get('role') == 'tool']
            assistant_tool_calls = []

            for msg in messages:
                if msg.get('role') == 'assistant' and 'tool_calls' in msg and msg['tool_calls']:
                    assistant_tool_calls.extend(msg['tool_calls'])

            # Verify tool_messages have corresponding tool_calls
            for tool_msg in tool_messages:
                tool_call_id = tool_msg.get('tool_call_id')
                if tool_call_id:
                    found = any(tc.get('id') == tool_call_id for tc in assistant_tool_calls)
                    if not found:
                        return False, f"Request {i}: Tool message {tool_call_id} has no matching tool call"

        return True, "Valid message chain"


class MockChatCompletionsEnhanced:
    """Enhanced mock for chat completions with round-aware responses"""

    def __init__(self, client: MockOpenAIClientEnhanced):
        self.client = client

    def create(self, **kwargs) -> 'MockChatCompletion':
        """Create method that uses response strategy or defaults"""
        self.client.call_count += 1
        self.client.request_history.append(kwargs)

        # Use custom strategy if set
        if self.client.response_strategy:
            return self.client.response_strategy(self.client.call_count, kwargs)

        # Default strategy: check if tools present and decide based on messages
        messages = kwargs.get('messages', [])
        tools = kwargs.get('tools', [])

        # Look for tool call trigger phrases
        has_tools = bool(tools)
        user_content = ' '.join([m.get('content', '') for m in messages if m.get('role') == 'user'])

        # Round 1: If tools present and user asks for search/outline
        if has_tools and self.client.call_count == 1:
            if 'outline' in user_content.lower():
                return self._create_outline_tool_response()
            elif 'search' in user_content.lower():
                return self._create_search_tool_response()
            else:
                # Default to outline if tools requested
                return self._create_outline_tool_response()

        # Round 2: Check message history to determine next action
        elif has_tools and self.client.call_count == 2:
            # Check if Round 1 result is in history
            if any('Lesson 4' in str(m.get('content', '')) for m in messages):
                # Second round: search based on lesson info
                return self._create_search_tool_response()
            else:
                # Synthesize final response
                return self._create_final_response()

        # Round 3+: Always synthesize
        else:
            return self._create_final_response()

    def _create_outline_tool_response(self) -> 'MockChatCompletion':
        """Simulate get_course_outline tool call"""
        tool_call = {
            'id': 'call_outline_123',
            'type': 'function',
            'function': {
                'name': 'get_course_outline',
                'arguments': json.dumps({'course_name': 'Python Basics'})
            }
        }

        return MockChatCompletion(
            choices=[
                MockChoice(
                    finish_reason='tool_calls',
                    message=MockMessage(content=None, tool_calls=[tool_call])
                )
            ]
        )

    def _create_search_tool_response(self) -> 'MockChatCompletion':
        """Simulate search_course_content tool call"""
        tool_call = {
            'id': 'call_search_456',
            'type': 'function',
            'function': {
                'name': 'search_course_content',
                'arguments': json.dumps({'query': 'Advanced Python topics', 'course_name': None})
            }
        }

        return MockChatCompletion(
            choices=[
                MockChoice(
                    finish_reason='tool_calls',
                    message=MockMessage(content=None, tool_calls=[tool_call])
                )
            ]
        )

    def _create_final_response(self) -> 'MockChatCompletion':
        """Simulate final synthesis response"""
        return MockChatCompletion(
            choices=[
                MockChoice(
                    finish_reason='stop',
                    message=MockMessage(
                        content="Based on the course outline and content search, Python Basics Lesson 4 covers Advanced Python topics. The Data Structures Mastery course also discusses similar concepts."
                    )
                )
            ]
        )


class MockChatCompletion:
    """Mock chat completion response"""

    def __init__(self, choices: List['MockChoice']):
        self.choices = choices


class MockChoice:
    """Mock choice in chat completion"""

    def __init__(self, finish_reason: str, message: 'MockMessage'):
        self.finish_reason = finish_reason
        self.message = message


class MockMessage:
    """Mock message in chat completion"""

    def __init__(self, content: str, tool_calls: Optional[List[Dict]] = None):
        self.content = content
        self.tool_calls = tool_calls or []
        # Convert dict tool_calls to proper objects
        self._tool_call_objects = None
        if tool_calls:
            self._tool_call_objects = [MockToolCall.from_dict(tc) for tc in tool_calls]

    @property
    def tool_calls(self):
        """Property to return tool call objects"""
        return self._tool_call_objects

    def to_dict(self):
        """Convert to dictionary for compatibility"""
        return {
            'content': self.content,
            'tool_calls': self.tool_calls
        }


class MockToolCall:
    """Mock tool call"""

    def __init__(self, call_id: str, function_name: str, function_args: Dict):
        self.id = call_id
        self.function = MockFunction(name=function_name, arguments=function_args)

    @classmethod
    def from_dict(cls, data: Dict) -> 'MockToolCall':
        """Create from dictionary"""
        return cls(
            call_id=data['id'],
            function_name=data['function']['name'],
            function_args=json.loads(data['function']['arguments'])
        )


class MockFunction:
    """Mock function call"""

    def __init__(self, name: str, arguments: Dict):
        self.name = name
        self.arguments = json.dumps(arguments)


# Helper function for common response strategies
def create_sequential_strategy(tool_rounds: int = 2):
    """
    Create a strategy that simulates sequential tool calling.

    Args:
        tool_rounds: Number of tool-calling rounds before synthesis (default 2)

    Returns:
        Response strategy function
    """
    def strategy(call_count: int, request_kwargs: Dict) -> MockChatCompletion:
        # Round 1: get_course_outline
        if call_count == 1:
            tool_call = {
                'id': 'call_round1',
                'type': 'function',
                'function': {
                    'name': 'get_course_outline',
                    'arguments': json.dumps({'course_name': 'Test Course'})
                }
            }
            return MockChatCompletion(
                choices=[MockChoice('tool_calls', MockMessage(None, [tool_call]))]
            )

        # Round 2: search_course_content (if tool_rounds >= 2)
        elif call_count == 2 and tool_rounds >= 2:
            tool_call = {
                'id': 'call_round2',
                'type': 'function',
                'function': {
                    'name': 'search_course_content',
                    'arguments': json.dumps({'query': 'test topic'})
                }
            }
            return MockChatCompletion(
                choices=[MockChoice('tool_calls', MockMessage(None, [tool_call]))]
            )

        # Round 3: Final synthesis
        else:
            return MockChatCompletion(
                choices=[MockChoice('stop', MockMessage("Final synthesized answer after tool calls"))]
            )

    return strategy


# Strategy for testing max rounds enforcement
def always_tool_call_strategy(call_count: int, request_kwargs: Dict) -> MockChatCompletion:
    """Always returns tool_calls, even beyond round 2 (for testing enforcement)"""
    if call_count <= 3:
        tool_call = {
            'id': f'call_{call_count}',
            'type': 'function',
            'function': {
                'name': 'search_course_content',
                'arguments': json.dumps({'query': f'test_{call_count}'})
            }
        }
        return MockChatCompletion(
            choices=[MockChoice('tool_calls', MockMessage(None, [tool_call]))]
        )
    return MockChatCompletion(
        choices=[MockChoice('stop', MockMessage("Should never reach here"))]
    )
