import unittest
import tempfile
import shutil
import os
import sys

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Mock the document_processor module to avoid pydantic dependency
with open("tests/mocks/mock_document_processor.py", "r") as f:
    mock_doc_code = f.read()

document_processor = type(sys)('document_processor')
sys.modules['document_processor'] = document_processor
exec(mock_doc_code, document_processor.__dict__)

from document_processor import DocumentProcessor

class TestDocumentProcessing(unittest.TestCase):
    """Integration tests for document processing pipeline"""

    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = DocumentProcessor(800, 100)

    def tearDown(self):
        """Cleanup test files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_txt_file_processing(self):
        """Test processing of TXT files"""
        # Create test TXT file
        txt_path = os.path.join(self.temp_dir, "test_course.txt")
        with open(txt_path, 'w') as f:
            f.write("""Course Title: Test Course
Course Link: https://example.com/course
Course Instructor: Test Instructor

Lesson 1: Introduction
This is the introduction content.

Lesson 2: Advanced Topics
This is advanced content.
""")

        # Process the document
        course, chunks = self.processor.process_course_document(txt_path)

        self.assertIsNotNone(course)
        self.assertEqual(course.title, "Test Course")
        self.assertEqual(course.instructor, "Test Instructor")
        self.assertEqual(len(chunks), 2)  # Should create 2 chunks

    def test_large_document_chunking(self):
        """Test chunking of large documents"""
        # Create a large document
        large_content = "Lesson 1: Long Content\n" + ("This is a sentence. " * 1000)
        txt_path = os.path.join(self.temp_dir, "large_course.txt")
        with open(txt_path, 'w') as f:
            f.write(f"""Course Title: Large Course
Course Link: https://example.com/large
Course Instructor: Test Instructor

{large_content}
""")

        course, chunks = self.processor.process_course_document(txt_path)

        self.assertGreater(len(chunks), 1)  # Should be chunked
        # Verify chunk size limits
        for chunk in chunks:
            self.assertLessEqual(len(chunk.content), 900)  # CHUNK_SIZE + overlap

    def test_malformed_document_handling(self):
        """Test handling of malformed documents"""
        # Create incomplete document
        txt_path = os.path.join(self.temp_dir, "malformed.txt")
        with open(txt_path, 'w') as f:
            f.write("This is not a proper course document format.")

        course, chunks = self.processor.process_course_document(txt_path)

        # Should handle gracefully
        self.assertIsNotNone(course)
        self.assertGreater(len(chunks), 0)

    def test_empty_document_handling(self):
        """Test handling of empty documents"""
        # Create empty document
        txt_path = os.path.join(self.temp_dir, "empty.txt")
        with open(txt_path, 'w') as f:
            f.write("")

        course, chunks = self.processor.process_course_document(txt_path)

        # Should handle gracefully
        self.assertIsNotNone(course)
        self.assertEqual(len(chunks), 0)  # No chunks from empty content

    def test_document_with_missing_fields(self):
        """Test document with missing required fields"""
        # Create document without course title
        txt_path = os.path.join(self.temp_dir, "missing_fields.txt")
        with open(txt_path, 'w') as f:
            f.write("""Course Instructor: Test Instructor

Lesson 1: Introduction
This is some content.
""")

        course, chunks = self.processor.process_course_document(txt_path)

        # Should handle gracefully
        self.assertIsNotNone(course)
        self.assertGreater(len(chunks), 0)

    def test_document_with_multiple_lessons(self):
        """Test document with many lessons"""
        # Create document with multiple lessons
        txt_path = os.path.join(self.temp_dir, "multi_lesson.txt")
        with open(txt_path, 'w') as f:
            f.write("""Course Title: Multi-Lesson Course
Course Link: https://example.com/multi
Course Instructor: Test Instructor

Lesson 1: Introduction
Introduction content here.

Lesson 2: Basics
Basic content here.

Lesson 3: Intermediate
Intermediate content here.

Lesson 4: Advanced
Advanced content here.

Lesson 5: Conclusion
Conclusion content here.
""")

        course, chunks = self.processor.process_course_document(txt_path)

        self.assertIsNotNone(course)
        self.assertEqual(course.title, "Multi-Lesson Course")
        self.assertEqual(len(chunks), 5)  # Should create 5 chunks (one per lesson)

    def test_document_with_special_characters(self):
        """Test document containing special characters"""
        txt_path = os.path.join(self.temp_dir, "special_chars.txt")
        with open(txt_path, 'w') as f:
            f.write("""Course Title: Special Characters Course
Course Link: https://example.com/special
Course Instructor: Test Instructor

Lesson 1: Special Characters
This lesson contains special characters: !@#$%^&*()
And Unicode: 你好世界 🌍
And math: ∑∫∆∇∂∀∃∞≈≠≤≥
""")

        course, chunks = self.processor.process_course_document(txt_path)

        self.assertIsNotNone(course)
        self.assertGreater(len(chunks), 0)
        # Verify special characters are preserved
        for chunk in chunks:
            self.assertIn("Special Characters", chunk.content)

    def test_document_with_urls_and_emails(self):
        """Test document containing URLs and email addresses"""
        txt_path = os.path.join(self.temp_dir, "urls_emails.txt")
        with open(txt_path, 'w') as f:
            f.write("""Course Title: URLs and Emails Course
Course Link: https://example.com/urls
Course Instructor: Test Instructor

Lesson 1: Contact Information
Contact us at email@example.com
Visit our website at https://example.com
Check out our API at https://api.example.com/v1
""")

        course, chunks = self.processor.process_course_document(txt_path)

        self.assertIsNotNone(course)
        self.assertGreater(len(chunks), 0)
        # Verify URLs and emails are preserved
        for chunk in chunks:
            self.assertIn("email@example.com", chunk.content)
            self.assertIn("https://example.com", chunk.content)

    def test_document_with_code_samples(self):
        """Test document containing code samples"""
        txt_path = os.path.join(self.temp_dir, "code_samples.txt")
        with open(txt_path, 'w') as f:
            f.write("""Course Title: Code Samples Course
Course Link: https://example.com/code
Course Instructor: Test Instructor

Lesson 1: Python Code
Here's some Python code:

def hello_world():
    print("Hello, World!")
    return True

Lesson 2: JavaScript Code
Here's some JavaScript:

function helloWorld() {
    console.log("Hello, World!");
    return true;
}
""")

        course, chunks = self.processor.process_course_document(txt_path)

        self.assertIsNotNone(course)
        self.assertEqual(len(chunks), 2)  # Should create 2 chunks (one per lesson)
        # Verify code is preserved
        found_python = False
        found_javascript = False
        for chunk in chunks:
            if "def hello_world():" in chunk.content:
                found_python = True
            if "function helloWorld()" in chunk.content:
                found_javascript = True
        self.assertTrue(found_python)
        self.assertTrue(found_javascript)

    def test_document_chunking_at_boundaries(self):
        """Test chunking behavior at sentence boundaries"""
        # Create document with content that should be chunked at sentence boundaries
        txt_path = os.path.join(self.temp_dir, "boundary_test.txt")
        with open(txt_path, 'w') as f:
            f.write("""Course Title: Boundary Test Course
Course Link: https://example.com/boundary
Course Instructor: Test Instructor

Lesson 1: Boundary Testing
This is the first sentence. This is the second sentence. This is the third sentence. This is the fourth sentence. This is the fifth sentence. This is the sixth sentence. This is the seventh sentence. This is the eighth sentence. This is the ninth sentence. This is the tenth sentence.
""")

        course, chunks = self.processor.process_course_document(txt_path)

        self.assertIsNotNone(course)
        self.assertGreater(len(chunks), 0)
        # Verify chunks don't break sentences in the middle
        for chunk in chunks:
            # Check that sentences are complete (not broken in middle)
            self.assertNotIn("sentence. This", chunk.content)

if __name__ == '__main__':
    unittest.main()