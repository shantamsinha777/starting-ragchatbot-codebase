
"""Mock OpenAI module for testing AI Generator without actual API calls."""

print("🚀 OpenAI mock module loaded!")


class OpenAI:
    """Mock OpenAI client for testing."""

    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.chat = ChatCompletions()
        print(f"🔧 OpenAI client created with base_url={base_url}")


class ChatCompletions:
    """Mock chat completions property."""

    @property
    def completions(self):
        return Completions()


class Completions:
    """Mock completions API."""

    def __init__(self):
        self.call_count = 0

    def create(self, **kwargs):
        """Mock create method - responds based on tools and messages."""
        self.call_count += 1

        # Return a mock response that matches OpenAI API format
        # Check if tools are requested and if we should simulate tool calls
        use_tools = kwargs.get('tools') is not None
        messages = kwargs.get('messages', [])
        has_search = 'search' in str(messages).lower()
        has_outline = 'outline' in str(messages).lower()

        # Tool call trigger: if tools present and specific keywords in messages
        if use_tools and (has_search or has_outline):
            if has_outline:
                return self._create_outline_tool_call_response()
            else:
                return self._create_search_tool_call_response()
        else:
            # Normal response
            return self._create_normal_response()

    def _create_normal_response(self):
        """Create a normal (non-tool) response."""
        return type('Response', (), {
            'choices': [
                type('Choice', (), {
                    'finish_reason': 'stop',
                    'message': type('Message', (), {
                        'content': 'Mock AI response',
                        'tool_calls': []
                    })()
                })()
            ]
        })()

    def _create_search_tool_call_response(self):
        """Create a search_course_content tool call response."""
        return self._create_tool_call_response('search_course_content', '{"query": "test query"}')

    def _create_outline_tool_call_response(self):
        """Create a get_course_outline tool call response."""
        return self._create_tool_call_response('get_course_outline', '{"course_name": "Test Course"}')

    def _create_tool_call_response(self, function_name, arguments):
        """Create a generic tool call response."""
        # Create tool call object with proper structure
        tool_call = MockToolCall(
            call_id=f'call_{self.call_count}',
            function_name=function_name,
            function_args=arguments
        )

        message = type('Message', (), {
            'content': None,
            'tool_calls': [tool_call]
        })()

        choice = type('Choice', (), {
            'finish_reason': 'tool_calls',
            'message': message
        })()

        return type('Response', (), {
            'choices': [choice]
        })()


class MockToolCall:
    """Mock tool call with proper to_dict method."""

    def __init__(self, call_id, function_name, function_args):
        self.id = call_id
        self.type = 'function'
        self.function = MockFunction(function_name, function_args)

    def to_dict(self):
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'type': self.type,
            'function': {
                'name': self.function.name,
                'arguments': self.function.arguments
            }
        }


class MockFunction:
    """Mock function object."""

    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
