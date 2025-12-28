"""
Mock models module to replace the real models.py
This prevents the need to load pydantic
"""

print("🚀 Mock models module loaded!")

from typing import List, Dict, Optional


class Lesson:
    """Mock Lesson class"""

    def __init__(self, lesson_number: int, title: str, lesson_link: Optional[str] = None):
        self.lesson_number = lesson_number
        self.title = title
        self.lesson_link = lesson_link


class Course:
    """Mock Course class"""

    def __init__(
        self,
        title: str,
        course_link: Optional[str] = None,
        instructor: Optional[str] = None,
        lessons: Optional[List] = None,
    ):
        self.title = title
        self.course_link = course_link
        self.instructor = instructor
        self.lessons = lessons or []


class CourseChunk:
    """Mock CourseChunk class"""

    def __init__(
        self,
        content: str,
        course_title: str,
        lesson_number: Optional[int] = None,
        chunk_index: int = 0,
    ):
        self.content = content
        self.course_title = course_title
        self.lesson_number = lesson_number
        self.chunk_index = chunk_index
