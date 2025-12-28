import unittest
import sys
import os

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from search_tools import CourseSearchTool, ToolManager
from models import Course, Lesson
from tests.mocks.mock_vector_store import MockVectorStore

class TestCourseSearchTool(unittest.TestCase):
    """Comprehensive tests for CourseSearchTool execute method"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock vector store
        self.mock_vector_store = MockVectorStore()

        # Create the search tool
        self.search_tool = CourseSearchTool(self.mock_vector_store)

        # Add some test courses to the vector store
        test_course = Course(
            title="Test Course",
            course_link="https://example.com/test-course",
            instructor="Test Instructor",
            lessons=[
                Lesson(
                    lesson_number=1,
                    title="Introduction",
                    lesson_link="https://example.com/test-course/lesson1"
                ),
                Lesson(
                    lesson_number=2,
                    title="Advanced Topics",
                    lesson_link="https://example.com/test-course/lesson2"
                )
            ]
        )

        self.mock_vector_store.add_course_metadata(test_course)

    def test_successful_search_with_valid_query(self):
        """Test successful search with valid query"""
        result = self.search_tool.execute(query="test query")

        # Should return formatted results
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

        # Should contain course and lesson information
        self.assertIn("[Test Course - Lesson 1]", result)
        self.assertIn("[Test Course - Lesson 2]", result)

    def test_search_with_course_name_filter(self):
        """Test search with course name filter"""
        result = self.search_tool.execute(query="test query", course_name="Test Course")

        # Should return results filtered by course
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn("[Test Course", result)

    def test_search_with_lesson_number_filter(self):
        """Test search with lesson number filter"""
        result = self.search_tool.execute(query="test query", lesson_number=1)

        # Should return results filtered by lesson
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn("Lesson 1", result)

    def test_search_with_both_course_and_lesson_filters(self):
        """Test search with both course and lesson filters"""
        result = self.search_tool.execute(
            query="test query",
            course_name="Test Course",
            lesson_number=1
        )

        # Should return results filtered by both course and lesson
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn("[Test Course - Lesson 1]", result)

    def test_search_with_no_results_found(self):
        """Test search with no results found"""
        result = self.search_tool.execute(query="no results query")

        # Should return "no results" message
        self.assertIsInstance(result, str)
        self.assertIn("No relevant content found", result)

    def test_search_with_invalid_course_name(self):
        """Test search with invalid course name"""
        result = self.search_tool.execute(
            query="test query",
            course_name="invalid course name"
        )

        # Should return error about course not found
        self.assertIsInstance(result, str)
        self.assertIn("No course found matching", result)

    def test_search_with_invalid_lesson_number(self):
        """Test search with invalid lesson number"""
        # This should still work but return no results for that specific lesson
        result = self.search_tool.execute(
            query="test query",
            lesson_number=999
        )

        # Should return formatted results (mock doesn't validate lesson numbers)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_result_formatting_with_html_links(self):
        """Test result formatting with HTML links"""
        result = self.search_tool.execute(query="test query")

        # HTML links are stored in sources, not in the main result
        self.assertIsInstance(result, str)

        # Check that sources contain HTML links
        sources = self.search_tool.last_sources
        self.assertTrue(len(sources) > 0)

        # Check first source for HTML link formatting
        first_source = sources[0]
        self.assertIn("<a href=", first_source)
        self.assertIn("target=\"_blank\"", first_source)
        self.assertIn("rel=\"noopener noreferrer\"", first_source)

    def test_source_tracking_functionality(self):
        """Test source tracking functionality"""
        # Execute a search
        self.search_tool.execute(query="test query")

        # Check that sources are tracked
        sources = self.search_tool.last_sources
        self.assertIsInstance(sources, list)
        self.assertTrue(len(sources) > 0)

        # Check that sources contain HTML links
        for source in sources:
            self.assertIn("<a href=", source)

    def test_error_handling_in_search(self):
        """Test error handling in search execution"""
        # Test with a query that should trigger an error in the mock
        result = self.search_tool.execute(query="no results query")

        # Should handle empty results gracefully
        self.assertIsInstance(result, str)
        self.assertIn("No relevant content found", result)

    def test_tool_definition_format(self):
        """Test that tool definition is in correct format"""
        tool_def = self.search_tool.get_tool_definition()

        # Should have required fields
        self.assertIn("name", tool_def)
        self.assertIn("description", tool_def)
        self.assertIn("input_schema", tool_def)

        # Should specify correct tool name
        self.assertEqual(tool_def["name"], "search_course_content")

        # Should have proper input schema
        input_schema = tool_def["input_schema"]
        self.assertEqual(input_schema["type"], "object")
        self.assertIn("properties", input_schema)
        self.assertIn("required", input_schema)

        # Query should be required
        self.assertIn("query", input_schema["required"])

    def test_empty_query_handling(self):
        """Test handling of empty query"""
        # This should still work (mock doesn't validate query)
        result = self.search_tool.execute(query="")

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_special_characters_in_query(self):
        """Test handling of special characters in query"""
        result = self.search_tool.execute(query="test query with special chars: !@#$%")

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_unicode_characters_in_query(self):
        """Test handling of unicode characters in query"""
        result = self.search_tool.execute(query="test query with unicode: 你好世界 🌍")

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_very_long_query_handling(self):
        """Test handling of very long query"""
        long_query = "a" * 1000  # 1000 character query
        result = self.search_tool.execute(query=long_query)

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_multiple_searches_in_sequence(self):
        """Test multiple searches in sequence"""
        # First search
        result1 = self.search_tool.execute(query="first query")

        # Second search
        result2 = self.search_tool.execute(query="second query")

        # Both should succeed
        self.assertIsInstance(result1, str)
        self.assertIsInstance(result2, str)
        self.assertTrue(len(result1) > 0)
        self.assertTrue(len(result2) > 0)

if __name__ == '__main__':
    unittest.main()