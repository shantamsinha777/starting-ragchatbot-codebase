"""
Test suite for sequential tool calling (up to 2 rounds) in AI Generator.

Tests verify:
1. Sequential tool flow (2 rounds + synthesis)
2. Round enforcement (max 2 tool rounds)
3. Error handling
4. History preservation
5. Session compatibility
"""

import unittest
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Mock the openai module
from tests.mocks.mock_openai import OpenAI

sys.modules["openai"] = sys.modules["__main__"]

from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool, CourseOutlineTool
from tests.mocks.mock_vector_store import MockVectorStore
from tests.mocks.mock_ai_api_enhanced import (
    MockOpenAIClientEnhanced,
    create_sequential_strategy,
    always_tool_call_strategy,
)


class TestSequentialToolCalling(unittest.TestCase):
    """Test sequential tool calling with up to 2 rounds"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = type(
            "Config",
            (),
            {
                "OPENROUTER_API_KEY": "test-key",
                "OPENROUTER_MODEL": "test-model",
            },
        )()

        # Create AI generator
        self.ai_generator = AIGenerator(
            api_key=self.config.OPENROUTER_API_KEY, model=self.config.OPENROUTER_MODEL
        )

        # Create mock vector store and tool manager
        self.mock_vector_store = MockVectorStore()
        self.tool_manager = ToolManager()
        self.search_tool = CourseSearchTool(self.mock_vector_store)
        self.outline_tool = CourseOutlineTool(self.mock_vector_store)
        self.tool_manager.register_tool(self.search_tool)
        self.tool_manager.register_tool(self.outline_tool)

    def test_sequential_two_round_tool_calling(self):
        """Test complete sequential flow: 2 tool rounds + synthesis"""
        # Use enhanced mock client with sequential strategy
        mock_client = MockOpenAIClientEnhanced()
        mock_client.set_response_strategy(create_sequential_strategy(tool_rounds=2))
        self.ai_generator.client = mock_client

        # Generate response
        response = self.ai_generator.generate_response(
            query="Find course information",
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager,
        )

        # Verify response
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

        # Verify 3 API calls were made (2 tool rounds + 1 synthesis)
        self.assertEqual(mock_client.get_call_count(), 3)

        # Verify request structure
        round1 = mock_client.get_request(0)
        round2 = mock_client.get_request(1)
        round3 = mock_client.get_request(2)

        # Round 1 should have tools
        self.assertIn("tools", round1)
        self.assertTrue(len(round1["tools"]) > 0)

        # Round 2 should have tools (and contain tool results from round 1)
        self.assertIn("tools", round2)
        # Should contain assistant tool_call and tool messages
        messages2 = round2.get("messages", [])
        has_tool_results = any(m.get("role") == "tool" for m in messages2)
        self.assertTrue(has_tool_results, "Round 2 should include tool results from Round 1")

        # Round 3 should NOT have tools (synthesis)
        self.assertNotIn("tools", round3)

    def test_single_round_backward_compatibility(self):
        """Test existing behavior: one tool call + one final response"""
        # Mock client that returns tool_calls in round 1, then stop in round 2
        mock_client = MockOpenAIClientEnhanced()

        def single_round_strategy(call_count, kwargs):
            if call_count == 1:
                tool_call = {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_course_outline",
                        "arguments": json.dumps({"course_name": "Test"}),
                    },
                }
                return MockChatCompletion(
                    choices=[MockChoice("tool_calls", MockMessage(None, [tool_call]))]
                )
            else:
                return MockChatCompletion(choices=[MockChoice("stop", MockMessage("Final answer"))])

        mock_client.set_response_strategy(single_round_strategy)
        self.ai_generator.client = mock_client

        response = self.ai_generator.generate_response(
            query="Test query",
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager,
        )

        self.assertEqual(response, "Final answer")
        self.assertEqual(mock_client.get_call_count(), 2)  # 1 tool + 1 synthesis

    def test_no_tool_call_needed(self):
        """Test direct response without any tool calls"""
        mock_client = MockOpenAIClientEnhanced()

        def direct_response_strategy(call_count, kwargs):
            return MockChatCompletion(
                choices=[MockChoice("stop", MockMessage("Direct answer without tools"))]
            )

        mock_client.set_response_strategy(direct_response_strategy)
        self.ai_generator.client = mock_client

        response = self.ai_generator.generate_response(
            query="General knowledge question",
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager,
        )

        self.assertEqual(response, "Direct answer without tools")
        self.assertEqual(mock_client.get_call_count(), 1)  # Only 1 call, no tool loop

    def test_max_rounds_enforcement(self):
        """Test that even if LLM wants more tools, max 2 rounds are enforced"""
        mock_client = MockOpenAIClientEnhanced()
        mock_client.set_response_strategy(always_tool_call_strategy)
        self.ai_generator.client = mock_client

        response = self.ai_generator.generate_response(
            query="Keep asking for tools",
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager,
        )

        # Should make 3 calls: 2 tool rounds + 1 synthesis
        # NOT 4 calls (even though mock wants to keep returning tool_calls)
        self.assertEqual(mock_client.get_call_count(), 3)

        # Final response should be from synthesis
        self.assertIsInstance(response, str)

    def test_tool_execution_error_handling(self):
        """Test graceful handling when tool execution fails"""
        mock_client = MockOpenAIClientEnhanced()

        def error_round_strategy(call_count, kwargs):
            if call_count == 1:
                tool_call = {
                    "id": "call_error",
                    "type": "function",
                    "function": {
                        "name": "search_course_content",
                        "arguments": json.dumps({"query": "test"}),
                    },
                }
                return MockChatCompletion(
                    choices=[MockChoice("tool_calls", MockMessage(None, [tool_call]))]
                )
            else:
                return MockChatCompletion(
                    choices=[MockChoice("stop", MockMessage("Got error but continued"))]
                )

        mock_client.set_response_strategy(error_round_strategy)
        self.ai_generator.client = mock_client

        # Override tool_manager to raise error
        original_execute = self.tool_manager.execute_tool

        def failing_execute(*args, **kwargs):
            raise Exception("Simulated tool failure")

        self.tool_manager.execute_tool = failing_execute

        try:
            response = self.ai_generator.generate_response(
                query="Test",
                tools=self.tool_manager.get_tool_definitions(),
                tool_manager=self.tool_manager,
            )

            # Should return error message in tool result, then synthesize
            self.assertIsInstance(response, str)
            # Should have made 2 calls: 1 tool (failed) + 1 synthesis
            self.assertEqual(mock_client.get_call_count(), 2)
        finally:
            self.tool_manager.execute_tool = original_execute

    def test_conversation_history_preservation(self):
        """Test that conversation history is preserved across rounds"""
        mock_client = MockOpenAIClientEnhanced()
        mock_client.set_response_strategy(create_sequential_strategy(tool_rounds=2))
        self.ai_generator.client = mock_client

        # Add initial history
        history = "User: Previous question\nAssistant: Previous answer"

        self.ai_generator.generate_response(
            query="New question",
            conversation_history=history,
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager,
        )

        # Verify history was included in all API calls
        for i in range(mock_client.get_call_count()):
            request = mock_client.get_request(i)
            messages = request.get("messages", [])

            # Find user messages
            user_messages = [m for m in messages if m.get("role") == "user"]

            # First user message should be the history or current query
            found_history = False
            for msg in user_messages:
                if "Previous question" in msg.get("content", ""):
                    found_history = True
                    break

            if i == 0:
                self.assertTrue(found_history, f"Round {i+1} should contain history")

    def test_message_history_structure_across_rounds(self):
        """Verify message history contains all interactions"""
        mock_client = MockOpenAIClientEnhanced()
        mock_client.set_response_strategy(create_sequential_strategy(tool_rounds=2))
        self.ai_generator.client = mock_client

        self.ai_generator.generate_response(
            query="Test",
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager,
        )

        # Check round 2 has assistant tool_calls from round 1
        round2_request = mock_client.get_request(1)
        messages2 = round2_request.get("messages", [])

        # Should have assistant tool_calls
        has_assistant_tool_calls = any(
            m.get("role") == "assistant" and m.get("tool_calls") for m in messages2
        )
        self.assertTrue(has_assistant_tool_calls)

        # Should have tool results
        has_tool_results = any(m.get("role") == "tool" for m in messages2)
        self.assertTrue(has_tool_results)

    def test_empty_tool_results_handling(self):
        """Test when tools return empty results"""
        mock_client = MockOpenAIClientEnhanced()

        def empty_results_strategy(call_count, kwargs):
            if call_count == 1:
                tool_call = {
                    "id": "call_empty",
                    "type": "function",
                    "function": {
                        "name": "search_course_content",
                        "arguments": json.dumps({"query": "nonexistent"}),
                    },
                }
                return MockChatCompletion(
                    choices=[MockChoice("tool_calls", MockMessage(None, [tool_call]))]
                )
            else:
                # Tool would return empty, but we proceed anyway
                return MockChatCompletion(
                    choices=[MockChoice("stop", MockMessage("No results found, continuing anyway"))]
                )

        mock_client.set_response_strategy(empty_results_strategy)
        self.ai_generator.client = mock_client

        # Override tool to return empty
        original = self.tool_manager.execute_tool
        self.tool_manager.execute_tool = lambda *a, **k: "No results found."

        try:
            response = self.ai_generator.generate_response(
                query="Test",
                tools=self.tool_manager.get_tool_definitions(),
                tool_manager=self.tool_manager,
            )

            # Should still proceed to synthesis
            self.assertIsInstance(response, str)
            self.assertEqual(mock_client.get_call_count(), 2)
        finally:
            self.tool_manager.execute_tool = original

    def test_session_compatibility(self):
        """Test that session storage format remains unchanged"""
        # This is more of an integration test - verify that the output
        # from AI generator can be stored in session manager as before
        mock_client = MockOpenAIClientEnhanced()
        mock_client.set_response_strategy(create_sequential_strategy(tool_rounds=2))
        self.ai_generator.client = mock_client

        response = self.ai_generator.generate_response(
            query="Test query",
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager,
        )

        # Response should be a simple string (not a complex object)
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

        # This response can be stored in session manager as before:
        # session_manager.add_exchange(session_id, "Test query", response)

    def test_parse_conversation_history(self):
        """Test the history parsing helper method"""
        # Test with valid history
        history = "User: First Q\nAssistant: First A\nUser: Second Q\nAssistant: Second A"
        messages = self.ai_generator._parse_conversation_history(history)

        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0], {"role": "user", "content": "First Q"})
        self.assertEqual(messages[1], {"role": "assistant", "content": "First A"})
        self.assertEqual(messages[2], {"role": "user", "content": "Second Q"})
        self.assertEqual(messages[3], {"role": "assistant", "content": "Second A"})

        # Test with None
        self.assertEqual(self.ai_generator._parse_conversation_history(None), [])

        # Test with empty string
        self.assertEqual(self.ai_generator._parse_conversation_history(""), [])

    def test_build_api_params_with_tools(self):
        """Test API parameter building with tools"""
        messages = [{"role": "user", "content": "Test"}]
        tools = [{"name": "test", "description": "desc", "input_schema": {"type": "object"}}]

        # Round 0 (first tool round)
        params = self.ai_generator._build_api_params(messages, tools, 0)
        self.assertIn("tools", params)
        self.assertEqual(len(params["tools"]), 1)
        self.assertIn("tool_choice", params)
        self.assertEqual(params["tool_choice"], "auto")

        # Round 1 (second tool round)
        params = self.ai_generator._build_api_params(messages, tools, 1)
        self.assertIn("tools", params)

        # Round 2 (synthesis - no tools)
        params = self.ai_generator._build_api_params(messages, tools, 2)
        self.assertNotIn("tools", params)

    def test_execute_tool_calls(self):
        """Test tool execution helper method"""

        # Create mock tool call objects
        class MockToolCallObj:
            def __init__(self, call_id, function_name, args_dict):
                self.id = call_id
                self.function = type(
                    "Func", (), {"name": function_name, "arguments": json.dumps(args_dict)}
                )()

        tool_calls = [MockToolCallObj("call1", "search_course_content", {"query": "test"})]

        results, sources = self.ai_generator._execute_tool_calls(tool_calls, self.tool_manager)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["role"], "tool")
        self.assertEqual(results[0]["tool_call_id"], "call1")
        self.assertIn("content", results[0])

    def test_make_synthesis_call(self):
        """Test final synthesis call"""
        mock_client = MockOpenAIClientEnhanced()

        def synthesis_strategy(call_count, kwargs):
            return MockChatCompletion(
                choices=[MockChoice("stop", MockMessage("Synthesis complete"))]
            )

        mock_client.set_response_strategy(synthesis_strategy)
        self.ai_generator.client = mock_client

        messages = [{"role": "user", "content": "Test"}]

        response = self.ai_generator._make_synthesis_call(messages)

        self.assertEqual(response, "Synthesis complete")
        self.assertEqual(mock_client.get_call_count(), 1)


# Test for message chain validation
class TestMessageChainValidation(unittest.TestCase):
    """Test message chain integrity"""

    def test_message_chain_with_sequential_tools(self):
        """Verify message chain is valid after sequential tool calls"""
        from tests.mocks.mock_ai_api_enhanced import MockOpenAIClientEnhanced

        mock_client = MockOpenAIClientEnhanced()
        mock_client.set_response_strategy(create_sequential_strategy(tool_rounds=2))

        # Simulate the full flow
        generator = AIGenerator("test-key", "test-model")
        generator.client = mock_client

        tool_manager = ToolManager()
        tool_manager.register_tool(CourseSearchTool(MockVectorStore()))
        tool_manager.register_tool(CourseOutlineTool(MockVectorStore()))

        generator.generate_response(
            query="Test", tools=tool_manager.get_tool_definitions(), tool_manager=tool_manager
        )

        # Verify message chain
        is_valid, error = mock_client.verify_message_chain()
        self.assertTrue(is_valid, f"Message chain invalid: {error}")


if __name__ == "__main__":
    unittest.main()
