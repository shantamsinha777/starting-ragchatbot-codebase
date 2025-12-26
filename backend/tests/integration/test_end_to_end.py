import unittest
import tempfile
import shutil
import os
import sys

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Mock the openai module to avoid real API calls when not needed
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

class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests for complete RAG workflow"""

    def setUp(self):
        """Setup complete RAG system"""
        self.temp_dir = tempfile.mkdtemp()

        # Create test config
        class TestConfig:
            OPENROUTER_API_KEY = os.getenv('TEST_OPENROUTER_API_KEY', 'test-key')
            OPENROUTER_MODEL = 'meta-llama/llama-3.2-3b-instruct'
            CHROMA_PATH = self.temp_dir
            EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
            CHUNK_SIZE = 800
            CHUNK_OVERLAP = 100
            MAX_RESULTS = 5
            MAX_HISTORY = 2

        self.config = TestConfig()
        self.rag_system = RAGSystem(self.config)

    def tearDown(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_complete_query_workflow(self):
        """Test complete workflow from document to query response"""
        # Create test document
        doc_path = os.path.join(self.temp_dir, "test_course.txt")
        with open(doc_path, 'w') as f:
            f.write("""Course Title: E2E Test Course
Course Link: https://example.com/e2e
Course Instructor: Test Instructor

Lesson 1: Getting Started
This is the introduction to our test course.

Lesson 2: Advanced Concepts
Here we cover advanced topics in detail.
""")

        # Add document to system
        course, chunks = self.rag_system.add_course_document(doc_path)
        self.assertIsNotNone(course)

        # Test query
        response, sources = self.rag_system.query("What is the introduction about?")

        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        self.assertIsInstance(sources, list)

    def test_conversation_context_preservation(self):
        """Test that conversation context is preserved across queries"""
        session_id = "test_conversation"

        # First query
        response1, sources1 = self.rag_system.query("What courses do you have?", session_id)

        # Follow-up query that should reference previous context
        response2, sources2 = self.rag_system.query("Tell me more about the first one", session_id)

        # Both should succeed
        self.assertIsInstance(response1, str)
        self.assertIsInstance(response2, str)

        # Check session history was updated
        history = self.rag_system.session_manager.get_conversation_history(session_id)
        self.assertIn("What courses do you have?", history)
        self.assertIn("Tell me more about the first one", history)

    def test_error_recovery_workflow(self):
        """Test system recovery from various error conditions"""
        # Test with invalid session ID
        response, sources = self.rag_system.query("Test query", session_id="invalid_session_123")

        # Should handle gracefully
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)

        # Test with empty query
        response, sources = self.rag_system.query("")
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)

    def test_multiple_document_workflow(self):
        """Test workflow with multiple documents"""
        # Create multiple test documents
        for i in range(3):
            doc_path = os.path.join(self.temp_dir, f"test_course_{i}.txt")
            with open(doc_path, 'w') as f:
                f.write(f"""Course Title: E2E Test Course {i}
Course Link: https://example.com/e2e{i}
Course Instructor: Test Instructor {i}

Lesson 1: Introduction
This is the introduction to test course {i}.

Lesson 2: Advanced
Advanced content for course {i}.
""")

            # Add document to system
            course, chunks = self.rag_system.add_course_document(doc_path)
            self.assertIsNotNone(course)

        # Test query that should find content from multiple courses
        response, sources = self.rag_system.query("Tell me about the introductions")

        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        self.assertIsInstance(sources, list)

    def test_session_isolation_in_workflow(self):
        """Test that sessions remain isolated in complete workflow"""
        session1 = "user1"
        session2 = "user2"

        # Add documents and query for both sessions
        doc_path = os.path.join(self.temp_dir, "session_test_course.txt")
        with open(doc_path, 'w') as f:
            f.write("""Course Title: Session Test Course
Course Link: https://example.com/session
Course Instructor: Test Instructor

Lesson 1: Session Isolation
This lesson tests session isolation.
""")

        course, chunks = self.rag_system.add_course_document(doc_path)

        # Query from first session
        response1, sources1 = self.rag_system.query("What is session isolation?", session1)

        # Query from second session
        response2, sources2 = self.rag_system.query("What are sessions?", session2)

        # Both should succeed
        self.assertIsInstance(response1, str)
        self.assertIsInstance(response2, str)

        # Session histories should be different
        history1 = self.rag_system.session_manager.get_conversation_history(session1)
        history2 = self.rag_system.session_manager.get_conversation_history(session2)

        self.assertIn("What is session isolation?", history1)
        self.assertNotIn("What is session isolation?", history2)
        self.assertIn("What are sessions?", history2)
        self.assertNotIn("What are sessions?", history1)

    def test_workflow_with_special_queries(self):
        """Test complete workflow with special character queries"""
        # Add test document
        doc_path = os.path.join(self.temp_dir, "special_query_course.txt")
        with open(doc_path, 'w') as f:
            f.write("""Course Title: Special Query Course
Course Link: https://example.com/special
Course Instructor: Test Instructor

Lesson 1: Special Characters
This lesson covers special characters and Unicode.
""")

        course, chunks = self.rag_system.add_course_document(doc_path)

        # Test queries with special characters
        special_queries = [
            "What about Unicode? 你好世界 🌍",
            "Tell me about special chars: !@#$%^&*()",
            "Query with math: ∑∫∆∇∂∀∃∞≈≠≤≥"
        ]

        for query in special_queries:
            response, sources = self.rag_system.query(query)
            self.assertIsInstance(response, str)
            self.assertIsInstance(sources, list)

    def test_workflow_performance(self):
        """Test performance of complete workflow"""
        import time

        # Create multiple documents
        start_time = time.time()
        for i in range(5):
            doc_path = os.path.join(self.temp_dir, f"perf_course_{i}.txt")
            with open(doc_path, 'w') as f:
                f.write(f"""Course Title: Performance Course {i}
Course Link: https://example.com/perf{i}
Course Instructor: Test Instructor

Lesson 1: Performance
Performance test content for course {i}.
""")

            course, chunks = self.rag_system.add_course_document(doc_path)

        doc_creation_time = time.time() - start_time

        # Test multiple queries
        start_time = time.time()
        for i in range(10):
            response, sources = self.rag_system.query(f"Tell me about course {i % 5}")
            self.assertIsInstance(response, str)

        query_time = time.time() - start_time

        # Performance should be reasonable
        self.assertLess(doc_creation_time, 10.0)  # Should be fast with mocks
        self.assertLess(query_time, 5.0)  # Should be fast with mocks

if __name__ == '__main__':
    unittest.main()