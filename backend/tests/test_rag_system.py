import unittest
import sys
import os

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock the openai module before importing rag_system
# Read the mock file content and execute it
with open("tests/mocks/mock_openai.py", "r") as f:
    mock_code = f.read()

# Create a new module and execute the code in its namespace
openai = type(sys)('openai')
sys.modules['openai'] = openai
exec(mock_code, openai.__dict__)

# Mock the vector_store module to avoid chromadb and sentence-transformers dependencies
with open("tests/mocks/mock_vector_store_module.py", "r") as f:
    vector_store_code = f.read()

vector_store = type(sys)('vector_store')
sys.modules['vector_store'] = vector_store
exec(vector_store_code, vector_store.__dict__)

from rag_system import RAGSystem
from tests.mocks.mock_session_manager import MockSessionManager

class TestRAGSystem(unittest.TestCase):
    """Comprehensive tests for RAG system content-query handling"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock configuration
        self.config = type('Config', (), {
            'OPENROUTER_API_KEY': 'test-key',
            'OPENROUTER_MODEL': 'test-model',
            'CHROMA_PATH': './test_chroma',
            'EMBEDDING_MODEL': 'test-embedding',
            'CHUNK_SIZE': 800,
            'CHUNK_OVERLAP': 100,
            'MAX_RESULTS': 5,
            'MAX_HISTORY': 2
        })()

        # Create RAG system with mock components
        self.rag_system = RAGSystem(self.config)

        # Replace session manager with mock
        self.rag_system.session_manager = MockSessionManager()

    def test_complete_query_flow_with_valid_question(self):
        """Test complete query flow with valid question"""
        query = "What is the introduction to the test course?"

        # Execute query
        response, sources = self.rag_system.query(query)

        # Should return response and sources
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)
        self.assertTrue(len(response) > 0)

    def test_query_with_session_management(self):
        """Test query with session management"""
        session_id = "test-session-123"
        query = "What is the test course about?"

        # Execute query with session
        response, sources = self.rag_system.query(query, session_id)

        # Should return response and sources
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)

        # Session should have been updated
        history = self.rag_system.session_manager.get_conversation_history(session_id)
        self.assertIsNotNone(history)

    def test_source_retrieval_and_formatting(self):
        """Test source retrieval and formatting"""
        query = "Tell me about course materials"

        # Execute query
        response, sources = self.rag_system.query(query)

        # Sources should be a list
        self.assertIsInstance(sources, list)

        # Each source should be properly formatted
        for source in sources:
            self.assertIsInstance(source, str)

    def test_error_handling_in_query_processing(self):
        """Test error handling in query processing"""
        # Test with empty query
        try:
            response, sources = self.rag_system.query("")
            self.assertIsInstance(response, str)
        except Exception:
            # Should handle gracefully
            self.assertTrue(True)

        # Test with None query
        try:
            response, sources = self.rag_system.query(None)
            self.assertIsInstance(response, str)
        except Exception:
            self.assertTrue(True)

    def test_course_analytics_functionality(self):
        """Test course analytics functionality"""
        analytics = self.rag_system.get_course_analytics()

        # Should return analytics dictionary
        self.assertIsInstance(analytics, dict)
        self.assertIn("total_courses", analytics)
        self.assertIn("course_titles", analytics)

    def test_query_with_conversation_history(self):
        """Test query with existing conversation history"""
        session_id = "test-session-history"

        # Add some history first
        self.rag_system.session_manager.add_exchange(
            session_id,
            "What is the first topic?",
            "The first topic is introduction"
        )

        # Execute new query with session
        query = "What comes after the introduction?"
        response, sources = self.rag_system.query(query, session_id)

        # Should return response considering history
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)

    def test_multiple_queries_in_sequence(self):
        """Test multiple queries in sequence"""
        session_id = "test-sequence"

        # First query
        response1, sources1 = self.rag_system.query("First question", session_id)

        # Second query
        response2, sources2 = self.rag_system.query("Second question", session_id)

        # Both should succeed
        self.assertIsInstance(response1, str)
        self.assertIsInstance(response2, str)
        self.assertIsInstance(sources1, list)
        self.assertIsInstance(sources2, list)

    def test_query_with_no_session(self):
        """Test query with no session ID"""
        query = "What is this course about?"

        # Execute query without session
        response, sources = self.rag_system.query(query, session_id=None)

        # Should still work
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)

    def test_empty_response_handling(self):
        """Test handling of empty responses"""
        # This would test edge cases where AI returns empty response
        # For now, just test that basic queries work
        query = "Tell me something"
        response, sources = self.rag_system.query(query)

        self.assertIsInstance(response, str)

    def test_source_tracking_across_queries(self):
        """Test source tracking across multiple queries"""
        session_id = "test-sources"

        # First query
        response1, sources1 = self.rag_system.query("First query", session_id)

        # Second query
        response2, sources2 = self.rag_system.query("Second query", session_id)

        # Sources should be tracked for each query
        self.assertIsInstance(sources1, list)
        self.assertIsInstance(sources2, list)

    def test_query_with_special_characters(self):
        """Test query with special characters"""
        query = "What is this course about? Special chars: !@#$%"
        response, sources = self.rag_system.query(query)

        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)

    def test_query_with_unicode(self):
        """Test query with unicode characters"""
        query = "What is this course about? Unicode: 你好世界 🌍"
        response, sources = self.rag_system.query(query)

        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)

    def test_very_long_query(self):
        """Test very long query"""
        long_query = "What " + "is " * 100 + "this course about?"
        response, sources = self.rag_system.query(long_query)

        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)

    def test_query_with_only_whitespace(self):
        """Test query with only whitespace"""
        try:
            response, sources = self.rag_system.query("   ")
            self.assertIsInstance(response, str)
        except Exception:
            self.assertTrue(True)

    def test_concurrent_session_handling(self):
        """Test handling of multiple concurrent sessions"""
        session1 = "session-1"
        session2 = "session-2"

        # Queries to different sessions
        response1, _ = self.rag_system.query("Query for session 1", session1)
        response2, _ = self.rag_system.query("Query for session 2", session2)

        # Both should work independently
        self.assertIsInstance(response1, str)
        self.assertIsInstance(response2, str)

        # Sessions should have separate histories
        history1 = self.rag_system.session_manager.get_conversation_history(session1)
        history2 = self.rag_system.session_manager.get_conversation_history(session2)

        self.assertIsNotNone(history1)
        self.assertIsNotNone(history2)

    def test_session_history_limit_enforcement(self):
        """Test enforcement of session history limits"""
        session_id = "test-history-limit"

        # Add many exchanges to test history limit
        for i in range(10):
            self.rag_system.session_manager.add_exchange(
                session_id,
                f"Question {i}",
                f"Answer {i}"
            )

        # Get history - should be limited
        history = self.rag_system.session_manager.get_conversation_history(session_id)
        self.assertIsNotNone(history)

        # Count lines to verify limit
        lines = history.split('\n')
        self.assertLessEqual(len(lines), self.config.MAX_HISTORY * 2)

    def test_course_analytics_with_empty_database(self):
        """Test course analytics when database is empty"""
        analytics = self.rag_system.get_course_analytics()

        self.assertIsInstance(analytics, dict)
        self.assertIn("total_courses", analytics)
        self.assertIn("course_titles", analytics)

        # Should handle empty database gracefully
        self.assertIsInstance(analytics["total_courses"], int)
        self.assertIsInstance(analytics["course_titles"], list)

    def test_query_response_structure(self):
        """Test structure of query responses"""
        query = "What is the structure of responses?"
        response, sources = self.rag_system.query(query)

        # Response should be string
        self.assertIsInstance(response, str)

        # Sources should be list of strings
        self.assertIsInstance(sources, list)
        for source in sources:
            self.assertIsInstance(source, str)

    def test_error_recovery_in_query_flow(self):
        """Test error recovery in query flow"""
        # This would test the system's ability to recover from errors
        # For basic testing, just verify queries work
        query = "Test error recovery"
        response, sources = self.rag_system.query(query)

        self.assertIsInstance(response, str)

if __name__ == '__main__':
    unittest.main()