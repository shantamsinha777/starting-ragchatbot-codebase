import openai
import json
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with OpenRouter API (OpenAI format) for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool **only** for questions about specific course content or detailed educational materials
- **One search per query maximum**
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        """Initialize OpenRouter client using OpenAI-compatible format"""
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = model

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build messages array - OpenRouter uses standard OpenAI message format
        messages = []

        # Add conversation history if exists
        if conversation_history:
            # Parse history string into messages
            # Format: "User: ...\nAssistant: ..."
            lines = conversation_history.split('\n')
            current_role = None
            current_content = []

            for line in lines:
                if line.startswith("User: "):
                    if current_role and current_content:
                        messages.append({
                            "role": "user",
                            "content": "\n".join(current_content)
                        })
                    current_role = "user"
                    current_content = [line[6:]]  # Remove "User: "
                elif line.startswith("Assistant: "):
                    if current_role and current_content:
                        messages.append({
                            "role": current_role,
                            "content": "\n".join(current_content)
                        })
                    current_role = "assistant"
                    current_content = [line[11:]]  # Remove "Assistant: "
                elif current_content:
                    current_content.append(line)

            # Add final message if exists
            if current_role and current_content:
                messages.append({
                    "role": current_role,
                    "content": "\n".join(current_content)
                })

        # Add current query
        messages.append({"role": "user", "content": query})

        # Add system prompt as the first message (OpenAI format)
        full_messages = [{"role": "system", "content": self.SYSTEM_PROMPT}] + messages

        # Prepare API call parameters
        api_params = {
            **self.base_params,
            "messages": full_messages,
        }

        print(f"[DEBUG] First API call - messages: {len(full_messages)}")
        for i, msg in enumerate(full_messages):
            content_preview = str(msg.get('content', ''))[:80]
            if 'tool_calls' in msg:
                content_preview = f"tool_calls: {[tc['function']['name'] for tc in msg['tool_calls']]}"
            print(f"  [{i}] {msg['role']}: {content_preview}")

        # Convert tools to OpenAI format if available
        if tools:
            openai_tools = []
            for tool in tools:
                # Convert Anthropic format to OpenAI format
                if "input_schema" in tool:
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["input_schema"]
                        }
                    })
                else:
                    # Already in correct format
                    openai_tools.append(tool)

            api_params["tools"] = openai_tools
            api_params["tool_choice"] = "auto"

        # Get response from OpenRouter
        try:
            print(f"[AI_DEBUG] Making API call to OpenRouter")
            response = self.client.chat.completions.create(**api_params)
            print(f"[AI_DEBUG] Got response, finish_reason: {response.choices[0].finish_reason}")
        except Exception as e:
            print(f"[AI_ERROR] OpenRouter API call failed: {e}")
            raise

        # Check if AI wants to use tools
        if response.choices[0].finish_reason == "tool_calls" and tool_manager:
            print(f"[AI_DEBUG] Tool call detected, handling execution")
            return self._handle_tool_execution(response, api_params, tool_manager)

        # Return direct response
        return response.choices[0].message.content

    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()

        # Add assistant's tool call message
        message = initial_response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": message.content,  # May be None
            "tool_calls": [tc.to_dict() for tc in message.tool_calls] if message.tool_calls else None
        })

        # Execute all tool calls and collect results
        tool_results = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                # Extract function name and arguments
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)  # Parse JSON string

                # Execute tool
                tool_result = tool_manager.execute_tool(function_name, **function_args)

                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_result
                })

        # Add tool results as tool messages (OpenAI format)
        if tool_results:
            messages.extend(tool_results)  # Each tool result is a separate message

        # Re-add system prompt at the beginning (OpenAI format)
        full_messages = [{"role": "system", "content": self.SYSTEM_PROMPT}] + messages

        print(f"[DEBUG] Final messages being sent: {len(full_messages)} messages")
        for i, msg in enumerate(full_messages):
            print(f"  [{i}] {msg['role']}: {str(msg.get('content', ''))[:100]}")

        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": full_messages,
        }

        # Get final response
        final_response = self.client.chat.completions.create(**final_params)
        return final_response.choices[0].message.content