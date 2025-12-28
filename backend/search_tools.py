from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
from vector_store import VectorStore, SearchResults


class Tool(ABC):
    """Abstract base class for all tools"""

    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters"""
        pass


class CourseSearchTool(Tool):
    """Tool for searching course content with semantic course name matching"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # Track sources from last search

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition - format that can be converted to either provider"""
        return {
            "name": "search_course_content",
            "description": "Search course materials with smart course name matching "
            "and lesson filtering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in the course content",
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. "
                        "'MCP', 'Introduction')",
                    },
                    "lesson_number": {
                        "type": "integer",
                        "description": "Specific lesson number to search within (e.g. 1, 2, 3)",
                    },
                },
                "required": ["query"],
            },
        }

    def execute(
        self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None
    ) -> str:
        """
        Execute the search tool with given parameters.

        Args:
            query: What to search for
            course_name: Optional course filter
            lesson_number: Optional lesson filter

        Returns:
            Formatted search results or error message
        """

        # Use the vector store's unified search interface
        results = self.store.search(
            query=query, course_name=course_name, lesson_number=lesson_number
        )

        # Handle errors
        if results.error:
            return results.error

        # Handle empty results
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."

        # Format and return results
        return self._format_results(results)

    def _format_results(self, results: SearchResults) -> str:
        """Format search results with course and lesson context"""
        formatted = []
        sources = []  # Track sources for the UI

        for doc, meta in zip(results.documents, results.metadata):
            course_title = meta.get("course_title", "unknown")
            lesson_num = meta.get("lesson_number")

            # Build context header
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"

            # Build source with optional link
            source_display = f"{course_title}"
            if lesson_num is not None:
                source_display += f" - Lesson {lesson_num}"

                # Try to get lesson link from vector store
                lesson_link = self.store.get_lesson_link(course_title, lesson_num)
                if lesson_link:
                    # Format as HTML link with display text
                    source = (
                        f'<a href="{lesson_link}" target="_blank" '
                        f'rel="noopener noreferrer">{source_display}</a>'
                    )
                else:
                    source = source_display
            else:
                source = source_display

            sources.append(source)

            formatted.append(f"{header}\n{doc}")

        # Store sources for retrieval
        self.last_sources = sources

        return "\n\n".join(formatted)


class CourseOutlineTool(Tool):
    """Tool for retrieving course outline information including title, link, and lesson list"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition - format that can be converted to either provider"""
        return {
            "name": "get_course_outline",
            "description": (
                "Retrieve course outline information including course title, "
                "course link, and complete lesson list. Use this when users ask "
                "for course structure, table of contents, lesson listings, "
                "or course overviews."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. "
                        "'MCP', 'Introduction')",
                    }
                },
                "required": ["course_name"],
            },
        }

    def execute(self, course_name: str) -> str:
        """
        Execute the course outline tool to retrieve course information.

        Args:
            course_name: Course title to search for

        Returns:
            Formatted course outline information or error message
        """
        # Use vector store's course resolution to find the exact course title
        course_title = self.store._resolve_course_name(course_name)
        if not course_title:
            return f"No course found matching '{course_name}'"

        # Get all course metadata
        courses_metadata = self.store.get_all_courses_metadata()
        if not courses_metadata:
            return "No course metadata available"

        # Find the specific course
        target_course = None
        for course in courses_metadata:
            if course.get("title") == course_title:
                target_course = course
                break

        if not target_course:
            return f"No detailed information found for course: {course_title}"

        # Format the course outline response
        return self._format_course_outline(target_course)

    def _format_course_outline(self, course_metadata: Dict[str, Any]) -> str:
        """Format course outline information for the AI response"""
        course_title = course_metadata.get("title", "Unknown Course")
        course_link = course_metadata.get("course_link", "")
        lessons = course_metadata.get("lessons", [])
        instructor = course_metadata.get("instructor", "")

        # Build the response
        response_parts = [f"Course: {course_title}"]

        if instructor:
            response_parts.append(f"Instructor: {instructor}")

        if course_link:
            response_parts.append(f"Course Link: {course_link}")

        # Add lesson list
        if lessons:
            response_parts.append("Lessons:")
            for lesson in lessons:
                lesson_title = lesson.get("lesson_title", "Untitled Lesson")
                lesson_number = lesson.get("lesson_number", "?")
                lesson_link = lesson.get("lesson_link", "")

                lesson_line = f"  Lesson {lesson_number}: {lesson_title}"
                if lesson_link:
                    lesson_line += f" ({lesson_link})"
                response_parts.append(lesson_line)
        else:
            response_parts.append("No lessons available for this course")

        return "\n".join(response_parts)


class ToolManager:
    """Manages available tools for the AI"""

    def __init__(self):
        self.tools = {}

    def register_tool(self, tool: Tool):
        """Register any tool that implements the Tool interface"""
        tool_def = tool.get_tool_definition()
        tool_name = tool_def.get("name")
        if not tool_name:
            raise ValueError("Tool must have a 'name' in its definition")
        self.tools[tool_name] = tool

    def get_tool_definitions(self) -> list:
        """Get all tool definitions for Anthropic tool calling"""
        return [tool.get_tool_definition() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given parameters"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"

        return self.tools[tool_name].execute(**kwargs)

    def get_last_sources(self) -> list:
        """Get sources from the last search operation"""
        # Check all tools for last_sources attribute
        for tool in self.tools.values():
            if hasattr(tool, "last_sources") and tool.last_sources:
                return tool.last_sources
        return []

    def reset_sources(self):
        """Reset sources from all tools that track sources"""
        for tool in self.tools.values():
            if hasattr(tool, "last_sources"):
                tool.last_sources = []
