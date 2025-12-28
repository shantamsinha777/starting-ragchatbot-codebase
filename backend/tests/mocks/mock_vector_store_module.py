"""
Mock vector store module to replace the real vector_store.py
This prevents the need to load chromadb and sentence-transformers
"""

print("🚀 Mock vector store module loaded!")

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import mock models instead of real ones
import sys

with open("tests/mocks/mock_models.py", "r") as f:
    models_code = f.read()

models = type(sys)("models")
sys.modules["models"] = models
exec(models_code, models.__dict__)

Course = models.Course
CourseChunk = models.CourseChunk


@dataclass
class SearchResults:
    """Container for search results with metadata"""

    documents: List[str]
    metadata: List[Dict[str, Any]]
    distances: List[float]
    error: Optional[str] = None

    @classmethod
    def from_chroma(cls, chroma_results: Dict) -> "SearchResults":
        """Create SearchResults from ChromaDB query results"""
        return cls(
            documents=chroma_results["documents"][0] if chroma_results["documents"] else [],
            metadata=chroma_results["metadatas"][0] if chroma_results["metadatas"] else [],
            distances=chroma_results["distances"][0] if chroma_results["distances"] else [],
        )

    @classmethod
    def empty(cls, error_msg: str) -> "SearchResults":
        """Create empty results with error message"""
        return cls(documents=[], metadata=[], distances=[], error=error_msg)

    def is_empty(self) -> bool:
        """Check if results are empty"""
        return len(self.documents) == 0


class VectorStore:
    """Mock VectorStore that doesn't require chromadb or sentence-transformers"""

    def __init__(self, chroma_path: str, embedding_model: str, max_results: int = 5):
        print(f"🔧 Mock VectorStore created with path={chroma_path}, model={embedding_model}")
        self.max_results = max_results
        self.courses = {}
        self.content_chunks = []

    def search(
        self,
        query: str,
        course_name: Optional[str] = None,
        lesson_number: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> SearchResults:
        """Mock search implementation that returns added content when possible"""
        # Check if we should return empty results based on query
        if "no results" in query.lower():
            return SearchResults.empty("No relevant content found")

        # Check if course name is invalid
        if course_name and "invalid course" in course_name.lower():
            return SearchResults.empty(f"No course found matching '{course_name}'")

        # If we have actual content, try to return relevant results
        if self.content_chunks:
            # Simple mock similarity - return chunks that contain query words
            matching_chunks = []
            query_words = query.lower().split()

            for chunk in self.content_chunks:
                chunk_words = chunk.content.lower().split()
                # Check if any query words appear in the chunk
                if any(word in chunk_words for word in query_words):
                    matching_chunks.append(chunk)

            if matching_chunks:
                # Return the matching chunks
                documents = [chunk.content for chunk in matching_chunks[: self.max_results]]
                metadata = [
                    {
                        "course_title": chunk.course_title,
                        "lesson_number": chunk.lesson_number or 1,
                        "lesson_link": f"https://example.com/{chunk.course_title}/lesson{chunk.lesson_number or 1}",
                    }
                    for chunk in matching_chunks[: self.max_results]
                ]
                distances = [0.1] * len(documents)

                return SearchResults(documents=documents, metadata=metadata, distances=distances)

        # Return mock search results if no matching content found
        mock_documents = [
            "This is a test document about course content and search functionality.",
            "Another relevant document that matches the search query.",
        ]

        mock_metadata = [
            {
                "course_title": course_name or "Test Course",
                "lesson_number": lesson_number if lesson_number is not None else 1,
                "lesson_link": "https://example.com/test-course/lesson1",
            },
            {
                "course_title": course_name or "Test Course",
                "lesson_number": lesson_number if lesson_number is not None else 2,
                "lesson_link": "https://example.com/test-course/lesson2",
            },
        ]

        return SearchResults(documents=mock_documents, metadata=mock_metadata, distances=[0.1, 0.2])

    def _resolve_course_name(self, course_name: str) -> Optional[str]:
        """Mock course name resolution"""
        if "invalid course" in course_name.lower():
            return None
        return course_name or "Test Course"

    def resolve_course_name(self, partial_name: str) -> Optional[str]:
        """Public method for course name resolution via vector similarity"""
        # Simple string matching for mock - find courses containing the partial name
        existing_titles = self.get_existing_course_titles()
        for title in existing_titles:
            if partial_name.lower() in title.lower():
                return title
        return None

    def _build_filter(
        self, course_title: Optional[str], lesson_number: Optional[int]
    ) -> Optional[Dict]:
        """Mock filter building"""
        return {}

    def add_course_metadata(self, course: Course):
        """Mock course metadata addition"""
        self.courses[course.title] = course

    def add_course_content(self, chunks: List[CourseChunk]):
        """Mock course content addition"""
        self.content_chunks.extend(chunks)

    def clear_all_data(self):
        """Mock data clearing"""
        self.courses.clear()
        self.content_chunks.clear()

    def get_existing_course_titles(self) -> List[str]:
        """Mock getting existing course titles"""
        return list(self.courses.keys())

    def get_course_count(self) -> int:
        """Mock getting course count"""
        return len(self.courses)

    def get_all_courses_metadata(self) -> List[Dict[str, Any]]:
        """Mock getting all courses metadata"""
        return [
            {
                "title": "Test Course",
                "course_link": "https://example.com/test-course",
                "instructor": "Test Instructor",
                "lessons": [
                    {
                        "lesson_number": 1,
                        "lesson_title": "Introduction",
                        "lesson_link": "https://example.com/test-course/lesson1",
                    },
                    {
                        "lesson_number": 2,
                        "lesson_title": "Advanced Topics",
                        "lesson_link": "https://example.com/test-course/lesson2",
                    },
                ],
            }
        ]

    def get_course_link(self, course_title: str) -> Optional[str]:
        """Mock getting course link"""
        if course_title in self.courses:
            return self.courses[course_title].course_link
        return None

    def get_lesson_link(self, course_title: str, lesson_number: int) -> Optional[str]:
        """Mock getting lesson link"""
        if course_title in self.courses:
            course = self.courses[course_title]
            for lesson in course.lessons:
                if lesson.lesson_number == lesson_number:
                    return lesson.lesson_link
        return None
