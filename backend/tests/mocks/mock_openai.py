
print("🚀 OpenAI mock module loaded!")

class OpenAI:
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.chat = ChatCompletions()
        print(f"🔧 OpenAI client created with base_url={base_url}")

class ChatCompletions:
    @property
    def completions(self):
        return Completions()

class Completions:
    def create(self, **kwargs):
        # Return a mock response that matches OpenAI API format
        # Check if tools are requested and if we should simulate tool calls
        use_tools = kwargs.get('tools') is not None

        if use_tools and 'search' in str(kwargs.get('messages', '')).lower():
            # Simulate AI deciding to use a tool
            return self._create_tool_call_response()
        else:
            # Normal response
            return self._create_normal_response()

    def _create_normal_response(self):
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

    def _create_tool_call_response(self):
        # Create a mock tool call response
        def to_dict(self):
            return {
                'id': self.id,
                'type': self.type,
                'function': {
                    'name': self.function.name,
                    'arguments': self.function.arguments
                }
            }

        tool_call = type('ToolCall', (), {
            'id': 'call_123',
            'type': 'function',
            'function': type('Function', (), {
                'name': 'search_course_content',
                'arguments': '{"query": "test query"}'
            })(),
            'to_dict': to_dict
        })()

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
