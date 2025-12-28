import unittest
import tempfile
import shutil
import os
import sys

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

# Mock the openai module to avoid real API calls
with open("tests/mocks/mock_openai.py", "r") as f:
    mock_code = f.read()

# Create a new module and execute the code in its namespace
openai = type(sys)("openai")
sys.modules["openai"] = openai
exec(mock_code, openai.__dict__)

# Try to import real vector store, but use mock if not available
try:
    from vector_store import VectorStore
    from models import Course

    REAL_CHROMADB_AVAILABLE = True
except ImportError:
    # Use mock vector store if real ChromaDB not available
    with open("tests/mocks/mock_vector_store_module.py", "r") as f:
        vector_store_code = f.read()

    vector_store = type(sys)("vector_store")
    sys.modules["vector_store"] = vector_store
    exec(vector_store_code, vector_store.__dict__)

    from vector_store import VectorStore
    from models import Course

    REAL_CHROMADB_AVAILABLE = False


class TestChromaIntegration(unittest.TestCase):
    """Integration tests using real ChromaDB operations or mocks"""

    @classmethod
    def setUpClass(cls):
        """Setup with real ChromaDB if available, otherwise use mock"""
        if not REAL_CHROMADB_AVAILABLE:
            print(
                "ℹ️  Using mock ChromaDB - install chromadb and sentence-transformers for real tests"
            )

    def setUp(self):
        """Setup temporary ChromaDB instance"""
        self.temp_dir = tempfile.mkdtemp()
        self.vector_store = VectorStore(self.temp_dir, "all-MiniLM-L6-v2")

    def tearDown(self):
        """Cleanup temporary database"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_real_vector_search(self):
        """Test actual vector similarity search"""
        # Add a test document
        test_content = "This is a test document for vector search."
        metadata = {"course_title": "Test Course", "lesson_number": 1}

        # Add content to vector store
        from models import CourseChunk

        chunk = CourseChunk(content=test_content, course_title="Test Course", lesson_number=1)
        self.vector_store.add_course_content([chunk])

        # Test search
        results = self.vector_store.search("test document")
        self.assertFalse(results.is_empty())
        self.assertIn(test_content, results.documents[0])

    def test_course_metadata_storage(self):
        """Test storing and retrieving course metadata"""
        course = Course(
            title="Integration Test Course",
            course_link="https://example.com/course",
            instructor="Test Instructor",
            lessons=[],
        )

        self.vector_store.add_course_metadata(course)

        # Verify storage
        titles = self.vector_store.get_existing_course_titles()
        self.assertIn("Integration Test Course", titles)

    def test_multiple_course_handling(self):
        """Test handling multiple courses in database"""
        courses = [
            Course(title="Course 1", instructor="Instructor 1"),
            Course(title="Course 2", instructor="Instructor 2"),
            Course(title="Course 3", instructor="Instructor 3"),
        ]

        for course in courses:
            self.vector_store.add_course_metadata(course)

        # Verify all courses stored
        stored_titles = self.vector_store.get_existing_course_titles()
        self.assertEqual(len(stored_titles), 3)
        self.assertIn("Course 1", stored_titles)
        self.assertIn("Course 2", stored_titles)
        self.assertIn("Course 3", stored_titles)

    def test_vector_store_persistence(self):
        """Test that vector store persists data"""
        # Add test data
        from models import CourseChunk

        chunk = CourseChunk(
            content="Persistence test content", course_title="Persistence Course", lesson_number=1
        )
        self.vector_store.add_course_content([chunk])

        # Create new vector store instance pointing to same directory
        vector_store2 = VectorStore(self.temp_dir, "all-MiniLM-L6-v2")

        # Should find the same data
        results = vector_store2.search("Persistence test")
        self.assertFalse(results.is_empty())

    def test_course_name_resolution(self):
        """Test course name resolution via vector similarity"""
        # Add courses with similar names
        courses = [
            Course(title="Advanced Python Programming", instructor="Instructor A"),
            Course(title="Python Programming Basics", instructor="Instructor B"),
            Course(title="Python for Data Science", instructor="Instructor C"),
        ]

        for course in courses:
            self.vector_store.add_course_metadata(course)

        # Test resolution
        resolved_title = self.vector_store.resolve_course_name("Python Programming")
        self.assertIsNotNone(resolved_title)
        self.assertIn("Python", resolved_title)

    def test_large_dataset_performance(self):
        """Test performance with larger dataset"""
        import time
        from models import CourseChunk

        # Add multiple chunks
        chunks = []
        for i in range(10):
            chunk = CourseChunk(
                content=f"Test content for document {i}",
                course_title="Performance Test Course",
                lesson_number=i + 1,
            )
            chunks.append(chunk)

        start_time = time.time()
        self.vector_store.add_course_content(chunks)
        add_time = time.time() - start_time

        # Test search performance
        start_time = time.time()
        results = self.vector_store.search("Test content")
        search_time = time.time() - start_time

        self.assertFalse(results.is_empty())
        self.assertLess(add_time, 5.0)  # Should be reasonably fast
        self.assertLess(search_time, 2.0)  # Should be reasonably fast


if __name__ == "__main__":
    unittest.main()
