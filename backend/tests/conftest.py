"""
Pytest configuration and fixtures for the RAG system API tests
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from typing import Generator, Dict, List, Any

# Add the backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ==================== MOCK IMPORTS ====================
# These mock imports prevent dependency issues during testing

# Mock OpenAI client
openai_mock = type(sys)("openai")
sys.modules["openai"] = openai_mock

# Mock vector_store module
vector_store_mock = type(sys)("vector_store")
sys.modules["vector_store"] = vector_store_mock

# Mock document_processor module
document_processor_mock = type(sys)("document_processor")
sys.modules["document_processor"] = document_processor_mock


# ==================== FIXTURES ====================


@pytest.fixture
def mock_config():
    """Mock configuration object"""

    class MockConfig:
        OPENROUTER_API_KEY = "test-api-key"
        OPENROUTER_MODEL = "test-model"
        CHROMA_PATH = "./test_chroma"
        EMBEDDING_MODEL = "test-embedding"
        CHUNK_SIZE = 800
        CHUNK_OVERLAP = 100
        MAX_RESULTS = 5
        MAX_HISTORY = 2

    return MockConfig()


@pytest.fixture
def mock_vector_store():
    """Mock vector store with basic functionality"""
    mock_store = Mock()
    mock_store.course_catalog = Mock()
    mock_store.course_content = Mock()

    # Mock search behavior
    mock_store.course_content.search.return_value = [
        {
            "content": "Test content about Python basics",
            "course_title": "Python 101",
            "lesson_number": 1,
            "chunk_index": 0,
            "distance": 0.1,
        }
    ]

    # Mock course listing
    mock_store.course_catalog.get.return_value = {
        "metadatas": [
            {
                "course_title": "Python 101",
                "instructor": "Test Instructor",
                "course_link": "http://test.com",
            }
        ]
    }

    # Mock course resolution
    mock_store.resolve_course_name.return_value = "Python 101"

    return mock_store


@pytest.fixture
def mock_session_manager():
    """Mock session manager"""
    mock_manager = Mock()
    mock_manager.create_session.return_value = "test-session-123"
    mock_manager.get_conversation_history.return_value = ""
    mock_manager.add_exchange = Mock()
    return mock_manager


@pytest.fixture
def mock_ai_generator():
    """Mock AI generator"""
    mock_gen = Mock()
    mock_gen.generate_response.return_value = "This is a test response from the AI"
    return mock_gen


@pytest.fixture
def mock_search_tool():
    """Mock search tool"""
    mock_tool = Mock()
    mock_tool.name = "search_course_content"
    mock_tool.description = "Mock search tool"
    mock_tool.execute.return_value = (
        "Mock search results: Python basics content found in Python 101, Lesson 1"
    )
    return mock_tool


@pytest.fixture
def mock_tool_manager():
    """Mock tool manager"""
    mock_manager = Mock()
    mock_manager.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search for course content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "course_name": {"type": "string", "description": "Course name filter"},
                    "lesson_number": {"type": "integer", "description": "Lesson number filter"},
                },
                "required": ["query"],
            },
        }
    ]
    mock_manager.execute_tool.return_value = "Mock tool execution result"
    return mock_manager


@pytest.fixture
def sample_query_request():
    """Sample query request data"""
    return {"query": "What is Python?", "session_id": "test-session-456"}


@pytest.fixture
def sample_courses_response():
    """Sample courses response data"""
    return {"total_courses": 2, "course_titles": ["Python 101", "Advanced Python"]}


@pytest.fixture
def mock_rag_system():
    """Mock RAG system"""
    mock_system = Mock()
    mock_system.query.return_value = ("This is a test answer", ["Python 101, Lesson 1"])
    mock_system.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Python 101", "Advanced Python"],
    }
    mock_system.add_course_folder.return_value = (2, 15)  # courses, chunks
    mock_system.session_manager = Mock()
    mock_system.session_manager.create_session.return_value = "new-session-789"
    return mock_system


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for API testing"""
    mock_client = Mock()

    # Mock chat completions
    mock_completion = Mock()
    mock_completion.choices = [Mock()]
    mock_completion.choices[0].message.content = "Mock AI response"
    mock_completion.choices[0].finish_reason = "stop"

    mock_client.chat.completions.create.return_value = mock_completion

    return mock_client


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing"""
    return [
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
        {"role": "user", "content": "Tell me more about it"},
    ]


@pytest.fixture
def mock_docs_data():
    """Mock document processing data"""
    return {
        "courses": [
            {
                "title": "Python 101",
                "instructor": "Test Instructor",
                "link": "http://test.com",
                "lessons": [
                    {
                        "number": 0,
                        "title": "Introduction",
                        "content": "Introduction to Python basics",
                    },
                    {
                        "number": 1,
                        "title": "Variables",
                        "content": "Python variables and data types",
                    },
                ],
            }
        ],
        "chunks": [
            {
                "content": "Introduction to Python basics",
                "course_title": "Python 101",
                "lesson_number": 0,
                "chunk_index": 0,
            },
            {
                "content": "Python variables and data types",
                "course_title": "Python 101",
                "lesson_number": 1,
                "chunk_index": 0,
            },
        ],
    }


# ==================== API TEST FIXTURES ====================


@pytest.fixture
def test_client():
    """FastAPI TestClient with mocked dependencies"""
    # Mock the imports before creating the app
    with patch.dict(
        sys.modules,
        {
            "openai": openai_mock,
            "vector_store": vector_store_mock,
            "document_processor": document_processor_mock,
            "config": Mock(),
            "rag_system": Mock(),
            "ai_generator": Mock(),
            "search_tools": Mock(),
            "session_manager": Mock(),
        },
    ):
        # Import app and components
        from backend.app import app

        return TestClient(app)


@pytest.fixture
def test_client_with_mocks(mock_rag_system, mock_config, mock_vector_store):
    """Test client with fully mocked RAG system"""
    with patch("backend.app.rag_system", mock_rag_system):
        with patch("backend.app.config", mock_config):
            from backend.app import app

            return TestClient(app)


# ==================== UTILITY FUNCTIONS ====================


def create_mock_response(content: str, finish_reason: str = "stop"):
    """Create a mock OpenAI response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = content
    mock_response.choices[0].finish_reason = finish_reason
    mock_response.choices[0].message.tool_calls = None
    return mock_response


def create_mock_tool_call_response(tool_name: str, tool_args: Dict):
    """Create a mock OpenAI response with tool calls"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = None
    mock_response.choices[0].finish_reason = "tool_calls"

    mock_tool_call = Mock()
    mock_tool_call.id = "call_test_123"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = tool_name
    mock_tool_call.function.arguments = str(tool_args)

    mock_response.choices[0].message.tool_calls = [mock_tool_call]
    return mock_response


# ==================== MARKERS AND CONFIGURATION ====================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "api: marks tests as API endpoint tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")


# ==================== TEST DATA GENERATORS ====================


class TestDataGenerator:
    """Utility class for generating test data"""

    @staticmethod
    def get_sample_course_data():
        """Return sample course data structure"""
        return {
            "course_title": "Python Programming",
            "instructor": "Jane Doe",
            "course_link": "https://example.com/python",
            "lessons": [
                {"number": 0, "title": "Introduction", "content": "Welcome to Python Programming!"},
                {
                    "number": 1,
                    "title": "Basic Syntax",
                    "content": "Python syntax and basic constructs",
                },
            ],
        }

    @staticmethod
    def get_sample_chunks():
        """Return sample chunks for vector search"""
        return [
            {
                "content": "Python is a high-level programming language",
                "course_title": "Python Programming",
                "lesson_number": 0,
                "chunk_index": 0,
                "distance": 0.05,
            },
            {
                "content": "Variables in Python are dynamically typed",
                "course_title": "Python Programming",
                "lesson_number": 1,
                "chunk_index": 0,
                "distance": 0.1,
            },
        ]

    @staticmethod
    def get_error_responses():
        """Return common error response patterns"""
        return {
            "api_error": "Error: API request failed",
            "no_results": "No relevant course content found",
            "invalid_session": "Invalid session ID",
            "malformed_query": "Query cannot be empty",
        }


# Export everything
__all__ = [
    "mock_config",
    "mock_vector_store",
    "mock_session_manager",
    "mock_ai_generator",
    "mock_search_tool",
    "mock_tool_manager",
    "sample_query_request",
    "sample_courses_response",
    "mock_rag_system",
    "mock_openai_client",
    "sample_conversation_history",
    "mock_docs_data",
    "test_client",
    "test_client_with_mocks",
    "create_mock_response",
    "create_mock_tool_call_response",
    "TestDataGenerator",
]
