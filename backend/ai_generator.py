import openai
import json
from typing import List, Optional, Dict, Any, Tuple


class AIGenerator:
    """Handles interactions with OpenRouter API (OpenAI format) for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools.

## Sequential Tool Usage (Up to 2 Rounds)

You can use tools up to 2 times per user query to gather information iteratively:

**Round 1**: Initial information gathering
- Use tools to get first layer of information
- Think about what additional information you need based on results

**Round 2**: Deeper research or synthesis
- Use different tools/parameters based on Round 1 results, OR
- Synthesize answer if you have enough information

**Maximum**: 2 tool-calling rounds per query

**Stop Early When**:
- You have sufficient information to answer the question
- Tools return no useful results
- You've reached 2 rounds

## Tool Definitions

**get_course_outline(course_name)**: Get course structure, lessons, instructor, links
- Use for: Course overview, lesson lists, course information

**search_course_content(query, course_name?, lesson_number?)**: Search within course content
- Use for: Specific topics, concepts, detailed content
- course_name: Optional filter by course (partial matching works)
- lesson_number: Optional filter by lesson number

## Response Guidelines

- **Direct answers only** - no meta-commentary about the search process
- **Synthesize** search results into fact-based responses
- **Include all links** from course/lesson information
- **No reasoning process explanations**
- If no results found, state this clearly

## Sequential Example

Query: "Find a course discussing the same topic as lesson 4 of Python Basics"

Round 1:
- Call: get_course_outline("Python Basics")
- Learn: Lesson 4 is about "Advanced Lists"

Round 2:
- Call: search_course_content("Advanced Lists")
- Find: "Data Structures Mastery" covers similar topics

Final Answer:
- Synthesize both results with complete course information
"""

    def __init__(self, api_key: str, model: str):
        """Initialize OpenRouter client using OpenAI-compatible format"""
        self.client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with sequential tool calling support (up to 2 rounds).

        Flow:
        1. Build initial message history from conversation_history
        2. Add current query
        3. Loop with tool calls (up to 2 rounds)
        4. If tools were used, make final synthesis call

        Args:
            query: The user's question or request
            conversation_history: Previous messages in "User: ...\nAssistant: ..." format
            tools: Available tools the AI can use (converted to OpenAI format)
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """
        # 1. Parse conversation history and add current query
        messages = self._parse_conversation_history(conversation_history)
        messages.append({"role": "user", "content": query})

        # Track tool usage for sequencing
        full_message_history = messages.copy()
        tool_rounds = 0
        tools_used = False

        # 2. Sequential tool calling loop
        while True:
            # Build API parameters
            api_params = self._build_api_params(full_message_history, tools, tool_rounds)

            # Debug logging
            print(f"[DEBUG] Round {tool_rounds + 1} - {len(full_message_history)} messages")
            for i, msg in enumerate(full_message_history[-5:]):  # Show last 5
                preview = str(msg.get("content", ""))[:60]
                if "tool_calls" in msg:
                    preview = f"tool_calls: {[tc['function']['name'] for tc in msg['tool_calls']]}"
                print(f"  [{i}] {msg['role']}: {preview}")

            # Make API call
            try:
                print(f"[AI_DEBUG] Making API call (Round {tool_rounds + 1})")
                response = self.client.chat.completions.create(**api_params)
                finish_reason = response.choices[0].finish_reason
                print(f"[AI_DEBUG] Got response, finish_reason: {finish_reason}")
            except Exception as e:
                print(f"[AI_ERROR] OpenRouter API call failed: {e}")
                raise

            # 3. Check response type
            if finish_reason == "tool_calls" and tool_manager:
                tools_used = True

                # Add assistant's tool call message
                message = response.choices[0].message
                full_message_history.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": (
                            [tc.to_dict() for tc in message.tool_calls]
                            if message.tool_calls
                            else None
                        ),
                    }
                )

                # Execute tools and add results
                tool_results, sources = self._execute_tool_calls(message.tool_calls, tool_manager)
                full_message_history.extend(tool_results)

                # Increment tool round counter
                tool_rounds += 1

                # Check termination conditions
                if tool_rounds >= 2:
                    print(f"[AI_DEBUG] Max rounds (2) reached, breaking to synthesis")
                    break

                # Continue to next round (tools still available)
                continue

            else:
                # No tool calls - return direct response
                return response.choices[0].message.content

        # 4. If tools were used, make final synthesis call (no tools)
        if tools_used:
            print(f"[AI_DEBUG] Making final synthesis call")
            return self._make_synthesis_call(full_message_history)

        # Fallback (shouldn't reach here)
        return "I've completed my analysis."

    def _parse_conversation_history(self, history_str: Optional[str]) -> List[Dict]:
        """
        Parse "User: ...\nAssistant: ..." format into message array.

        Args:
            history_str: Formatted conversation history

        Returns:
            List of message dicts
        """
        if not history_str:
            return []

        messages = []
        lines = history_str.split("\n")
        current_role = None
        current_content = []

        for line in lines:
            if line.startswith("User: "):
                if current_role and current_content:
                    messages.append({"role": current_role, "content": "\n".join(current_content)})
                current_role = "user"
                current_content = [line[6:]]
            elif line.startswith("Assistant: "):
                if current_role and current_content:
                    messages.append({"role": current_role, "content": "\n".join(current_content)})
                current_role = "assistant"
                current_content = [line[11:]]
            elif current_content:
                current_content.append(line)

        if current_role and current_content:
            messages.append({"role": current_role, "content": "\n".join(current_content)})

        return messages

    def _build_api_params(
        self, messages: List[Dict], tools: Optional[List], tool_rounds: int
    ) -> Dict[str, Any]:
        """
        Build API parameters including system prompt and optional tools.

        Args:
            messages: Conversation history including current query
            tools: Tool definitions
            tool_rounds: Current tool round count (0 or 1 means tools available)

        Returns:
            API parameters dict
        """
        # Add system prompt
        full_messages = [{"role": "system", "content": self.SYSTEM_PROMPT}] + messages

        # Build base params
        api_params = {
            **self.base_params,
            "messages": full_messages,
        }

        # Add tools only for first 2 rounds
        if tools and tool_rounds < 2:
            openai_tools = []
            for tool in tools:
                if "input_schema" in tool:
                    openai_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool["name"],
                                "description": tool["description"],
                                "parameters": tool["input_schema"],
                            },
                        }
                    )
                else:
                    openai_tools.append(tool)

            api_params["tools"] = openai_tools
            api_params["tool_choice"] = "auto"

        return api_params

    def _execute_tool_calls(self, tool_calls, tool_manager) -> Tuple[List[Dict], List[str]]:
        """
        Execute all tool calls and format results.

        Args:
            tool_calls: List of tool call objects from API response
            tool_manager: Manager to execute tools

        Returns:
            Tuple of (tool_result_messages, sources_list)
        """
        if not tool_calls:
            return [], []

        tool_results = []
        all_sources = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"[AI_DEBUG] Executing tool: {function_name} with args: {function_args}")

            # Execute tool
            try:
                tool_result = tool_manager.execute_tool(function_name, **function_args)

                # Track sources if available
                if hasattr(tool_manager, "get_last_sources"):
                    sources = tool_manager.get_last_sources()
                    if sources:
                        all_sources.extend(sources)
            except Exception as e:
                tool_result = f"Tool execution error: {str(e)}"

            tool_results.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_result,
                }
            )

            print(f"[AI_DEBUG] Tool result length: {len(tool_result)} chars")

        return tool_results, all_sources

    def _make_synthesis_call(self, messages: List[Dict]) -> str:
        """
        Make final API call without tools to synthesize results.

        Args:
            messages: Complete message history with tool interactions

        Returns:
            Final synthesized response
        """
        # Build API params without tools
        api_params = {
            **self.base_params,
            "messages": [{"role": "system", "content": self.SYSTEM_PROMPT}] + messages,
        }

        # Make final call
        final_response = self.client.chat.completions.create(**api_params)
        return final_response.choices[0].message.content
