"""
Mock document processor for testing without pydantic dependency
"""

print("📄 Mock document processor loaded!")

class MockCourse:
    def __init__(self, title="Test Course", instructor="Test Instructor", course_link="https://example.com"):
        self.title = title
        self.instructor = instructor
        self.course_link = course_link
        self.lessons = []  # Add lessons attribute to match real Course interface

class MockLesson:
    def __init__(self, title="Test Lesson", content="Test content"):
        self.title = title
        self.content = content

class MockCourseChunk:
    def __init__(self, content="Test chunk content", course_title="Test Course", lesson_number=1):
        self.content = content
        self.course_title = course_title
        self.lesson_number = lesson_number

class DocumentProcessor:
    def __init__(self, chunk_size=800, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"🔧 Mock document processor created with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")

    def process_course_document(self, file_path):
        """Mock document processing that simulates the real behavior"""
        print(f"📄 Processing document: {file_path}")

        # Read the file content with UTF-8 encoding to preserve special characters
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️  Error reading file: {e}")
            return MockCourse(), []

        # Parse basic course information
        course_title = "Test Course"
        course_instructor = "Test Instructor"
        course_link = "https://example.com"

        # Extract course info if available
        lines = content.split('\n')
        for line in lines:
            if line.startswith('Course Title:'):
                course_title = line.replace('Course Title:', '').strip()
            elif line.startswith('Course Instructor:'):
                course_instructor = line.replace('Course Instructor:', '').strip()
            elif line.startswith('Course Link:'):
                course_link = line.replace('Course Link:', '').strip()

        # Create course object
        course = MockCourse(course_title, course_instructor, course_link)

        # Enhanced chunking behavior with size limits
        chunks = []

        # Find lesson content and create chunks
        lesson_content = []
        in_lesson = False
        current_lesson_title = ""

        for line in lines:
            if line.startswith('Lesson ') and ':' in line:
                # Save previous lesson content with chunking
                if lesson_content:
                    lesson_text = '\n'.join(lesson_content).strip()
                    if lesson_text:
                        # Chunk the lesson content if it's too large
                        lesson_chunks = self._chunk_text_enhanced(lesson_text, course_title)
                        chunks.extend(lesson_chunks)
                    lesson_content = []
                current_lesson_title = line.strip()
                in_lesson = True
            elif in_lesson and line.strip():
                lesson_content.append(line)
            elif in_lesson and not line.strip():
                in_lesson = False

        # Add last lesson if any
        if lesson_content:
            lesson_text = '\n'.join(lesson_content).strip()
            if lesson_text:
                lesson_chunks = self._chunk_text_enhanced(lesson_text, course_title)
                chunks.extend(lesson_chunks)

        # If no lessons found, create chunks from all content
        if not chunks and content.strip():
            content_chunks = self._chunk_text_enhanced(content, course_title)
            chunks.extend(content_chunks)

        print(f"📝 Created {len(chunks)} chunks for course: {course_title}")
        return course, chunks

    def _chunk_text_enhanced(self, text, course_title):
        """Enhanced text chunking that respects size limits and tries to preserve formatting"""
        chunks = []
        
        if len(text) <= self.chunk_size:
            # Text fits in one chunk
            chunks.append(MockCourseChunk(text, course_title, len(chunks) + 1))
        else:
            # Need to split into multiple chunks
            words = text.split(' ')
            current_chunk = ""
            chunk_index = 1
            
            for word in words:
                # Check if adding this word would exceed the limit
                test_chunk = current_chunk + (" " if current_chunk else "") + word
                
                if len(test_chunk) > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunks.append(MockCourseChunk(current_chunk.strip(), course_title, chunk_index))
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:].strip() + " " + word
                else:
                    current_chunk = test_chunk
            
            # Add final chunk if any content remains
            if current_chunk.strip():
                chunks.append(MockCourseChunk(current_chunk.strip(), course_title, chunk_index))
        
        return chunks

    def _chunk_text(self, text, chunk_size, overlap):
        """Simulate text chunking with overlap"""
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)

            if end >= len(text):
                break

            start = end - overlap

        return chunks