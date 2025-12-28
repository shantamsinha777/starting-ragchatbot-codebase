import unittest
import os
import sys

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

# Mock the openai module to avoid real API calls when not needed
with open("tests/mocks/mock_openai.py", "r") as f:
    mock_code = f.read()

# Create a new module and execute the code in its namespace
openai = type(sys)("openai")
sys.modules["openai"] = openai
exec(mock_code, openai.__dict__)

# Mock the vector_store module to avoid chromadb and sentence-transformers dependencies
with open("tests/mocks/mock_vector_store_module.py", "r") as f:
    vector_store_code = f.read()

vector_store = type(sys)("vector_store")
sys.modules["vector_store"] = vector_store
exec(vector_store_code, vector_store.__dict__)

from ai_generator import AIGenerator
from rag_system import RAGSystem


class TestRealAPIIntegration(unittest.TestCase):
    """Integration tests using actual OpenRouter API calls"""

    @classmethod
    def setUpClass(cls):
        """Setup with test API key from environment"""
        cls.api_key = os.getenv("TEST_OPENROUTER_API_KEY")
        if not cls.api_key:
            raise unittest.SkipTest("No test API key available - set TEST_OPENROUTER_API_KEY")

    def test_real_ai_response_generation(self):
        """Test actual AI response generation without tools"""
        ai_gen = AIGenerator(self.api_key, "meta-llama/llama-3.2-3b-instruct")
        response = ai_gen.generate_response("What is 2+2?")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_real_tool_calling_flow(self):
        """Test actual tool calling with real AI"""
        from search_tools import ToolManager, CourseSearchTool
        from vector_store import VectorStore

        # Create real components
        vector_store = VectorStore("./test_chroma", "all-MiniLM-L6-v2")
        search_tool = CourseSearchTool(vector_store)
        tool_manager = ToolManager()
        tool_manager.register_tool(search_tool)

        ai_gen = AIGenerator(self.api_key, "meta-llama/llama-3.2-3b-instruct")

        # Test tool calling decision
        response = ai_gen.generate_response(
            query="search for information about course materials",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_api_error_handling(self):
        """Test handling of API errors with real calls"""
        ai_gen = AIGenerator("invalid-key", "meta-llama/llama-3.2-3b-instruct")

        with self.assertRaises(Exception):
            ai_gen.generate_response("Test query")

    def test_real_rag_system_integration(self):
        """Test complete RAG system with real API"""

        # Create test config
        class TestConfig:
            OPENROUTER_API_KEY = self.api_key
            OPENROUTER_MODEL = "meta-llama/llama-3.2-3b-instruct"
            CHROMA_PATH = "./test_chroma"
            EMBEDDING_MODEL = "all-MiniLM-L6-v2"
            CHUNK_SIZE = 800
            CHUNK_OVERLAP = 100
            MAX_RESULTS = 5
            MAX_HISTORY = 2

        config = TestConfig()
        rag_system = RAGSystem(config)

        # Test basic query
        response, sources = rag_system.query("What is the capital of France?")
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)
        self.assertTrue(len(response) > 0)

    def test_real_api_with_session_management(self):
        """Test real API with session management"""

        # Create test config
        class TestConfig:
            OPENROUTER_API_KEY = self.api_key
            OPENROUTER_MODEL = "meta-llama/llama-3.2-3b-instruct"
            CHROMA_PATH = "./test_chroma"
            EMBEDDING_MODEL = "all-MiniLM-L6-v2"
            CHUNK_SIZE = 800
            CHUNK_OVERLAP = 100
            MAX_RESULTS = 5
            MAX_HISTORY = 2

        config = TestConfig()
        rag_system = RAGSystem(config)

        session_id = "test_api_session"

        # First query
        response1, sources1 = rag_system.query("What is Python?", session_id)

        # Follow-up query that should reference previous context
        response2, sources2 = rag_system.query("Tell me more about it", session_id)

        # Both should succeed
        self.assertIsInstance(response1, str)
        self.assertIsInstance(response2, str)

        # Check session history was updated
        history = rag_system.session_manager.get_conversation_history(session_id)
        self.assertIn("What is Python?", history)
        self.assertIn("Tell me more about it", history)


if __name__ == "__main__":
    unittest.main()
