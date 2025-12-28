"""
API endpoint tests for the RAG system

Tests the FastAPI endpoints (/api/query, /api/courses, /) for proper request/response handling.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock dependencies
openai_mock = type(sys)("openai")
sys.modules["openai"] = openai_mock

vector_store_mock = type(sys)("vector_store")
sys.modules["vector_store"] = vector_store_mock

document_processor_mock = type(sys)("document_processor")
sys.modules["document_processor"] = document_processor_mock


@pytest.mark.api
@pytest.mark.integration
class TestQueryEndpoint:
    """Tests for the /api/query endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        # Create mock components
        self.mock_rag_system = Mock()
        self.mock_rag_system.query.return_value = (
            "Test answer about Python programming",
            ["Python 101, Lesson 1"],
        )
        self.mock_rag_system.session_manager = Mock()
        self.mock_rag_system.session_manager.create_session.return_value = "mock-session-123"

        self.mock_config = Mock()
        self.mock_config.OPENROUTER_API_KEY = "test-key"

    @pytest.fixture
    def client_with_mocks(self):
        """Create test client with mocked RAG system"""
        with patch("backend.app.rag_system", self.mock_rag_system):
            with patch("backend.app.config", self.mock_config):
                from backend.app import app

                return TestClient(app)

    def test_query_endpoint_success_with_session(self, client_with_mocks):
        """Test successful query with existing session"""
        response = client_with_mocks.post(
            "/api/query", json={"query": "What is Python?", "session_id": "existing-session-456"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["answer"] == "Test answer about Python programming"
        assert data["session_id"] == "existing-session-456"

    def test_query_endpoint_success_without_session(self, client_with_mocks):
        """Test successful query without session (creates new one)"""
        response = client_with_mocks.post("/api/query", json={"query": "Tell me about Python"})

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "mock-session-123"

    def test_query_endpoint_empty_query(self, client_with_mocks):
        """Test query endpoint with empty query"""
        response = client_with_mocks.post(
            "/api/query", json={"query": "", "session_id": "test-session"}
        )

        # Should handle gracefully
        assert response.status_code in [200, 422]  # Either success or validation error

    def test_query_endpoint_missing_query(self, client_with_mocks):
        """Test query endpoint with missing query field"""
        response = client_with_mocks.post("/api/query", json={"session_id": "test-session"})

        # Should return 422 validation error
        assert response.status_code == 422

    def test_query_endpoint_error_handling(self, client_with_mocks):
        """Test query endpoint error handling"""
        # Make RAG system raise an exception
        self.mock_rag_system.query.side_effect = Exception("Database connection failed")

        response = client_with_mocks.post(
            "/api/query", json={"query": "Test query", "session_id": "test-session"}
        )

        # Should return 500 error
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    def test_query_endpoint_with_unicode(self, client_with_mocks):
        """Test query endpoint with unicode characters"""
        response = client_with_mocks.post(
            "/api/query", json={"query": "What is 你好 in Python? 🐍", "session_id": "test-session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_query_endpoint_with_special_characters(self, client_with_mocks):
        """Test query endpoint with special characters"""
        response = client_with_mocks.post(
            "/api/query",
            json={
                "query": "How to use $variable and @decorator in Python?",
                "session_id": "test-session",
            },
        )

        assert response.status_code == 200

    def test_query_endpoint_preserves_session_history(self, client_with_mocks):
        """Test that session history is preserved between queries"""
        # First query
        response1 = client_with_mocks.post(
            "/api/query", json={"query": "First question", "session_id": "history-test"}
        )
        assert response1.status_code == 200

        # Second query with same session
        response2 = client_with_mocks.post(
            "/api/query", json={"query": "Second question", "session_id": "history-test"}
        )
        assert response2.status_code == 200

        # Verify session manager was called with correct session
        self.mock_rag_system.session_manager.add_exchange.assert_called()


@pytest.mark.api
@pytest.mark.integration
class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        self.mock_rag_system = Mock()
        self.mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": ["Python 101", "Advanced Python", "Data Science Basics"],
        }

        self.mock_config = Mock()

    @pytest.fixture
    def client_with_mocks(self):
        """Create test client with mocked RAG system"""
        with patch("backend.app.rag_system", self.mock_rag_system):
            with patch("backend.app.config", self.mock_config):
                from backend.app import app

                return TestClient(app)

    def test_courses_endpoint_success(self, client_with_mocks):
        """Test successful course statistics retrieval"""
        response = client_with_mocks.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3
        assert "Python 101" in data["course_titles"]

    def test_courses_endpoint_empty_catalog(self, client_with_mocks):
        """Test courses endpoint with empty catalog"""
        self.mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        response = client_with_mocks.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_courses_endpoint_error(self, client_with_mocks):
        """Test courses endpoint error handling"""
        self.mock_rag_system.get_course_analytics.side_effect = Exception("Analytics error")

        response = client_with_mocks.get("/api/courses")

        assert response.status_code == 500
        assert "Analytics error" in response.json()["detail"]

    def test_courses_endpoint_response_structure(self, client_with_mocks):
        """Test that response has correct structure"""
        response = client_with_mocks.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # Verify response matches CourseStats model
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        for title in data["course_titles"]:
            assert isinstance(title, str)


@pytest.mark.api
@pytest.mark.integration
class TestRootEndpoint:
    """Tests for the root endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        # Mock the dependencies to avoid issues with static files
        with patch("backend.app.rag_system", Mock()):
            with patch("backend.app.config", Mock()):
                from backend.app import app

                return TestClient(app)

    def test_root_endpoint_redirect(self, client):
        """Test root endpoint serves static files"""
        response = client.get("/")

        # Should either serve the frontend or redirect
        assert response.status_code in [200, 307, 302]
        if response.status_code == 200:
            # If it serves content, should be HTML
            assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.api
@pytest.mark.integration
class TestAPIValidation:
    """Test API validation and edge cases"""

    def setup_method(self):
        """Setup for validation tests"""
        self.mock_rag_system = Mock()
        self.mock_rag_system.query.return_value = ("Response", ["Source"])
        self.mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Test"],
        }
        self.mock_config = Mock()

    @pytest.fixture
    def client(self):
        """Create test client"""
        with patch("backend.app.rag_system", self.mock_rag_system):
            with patch("backend.app.config", self.mock_config):
                from backend.app import app

                return TestClient(app)

    def test_content_type_json(self, client):
        """Test that endpoints require JSON content type"""
        response = client.post(
            "/api/query", data="not json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    def test_missing_content_type(self, client):
        """Test missing content type header"""
        response = client.post("/api/query", json={"query": "test"})
        # FastAPI should handle this automatically
        assert response.status_code in [200, 422]

    def test_malformed_json(self, client):
        """Test malformed JSON payload"""
        response = client.post(
            "/api/query", data="{'invalid': json}", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    def test_extra_fields_in_request(self, client):
        """Test request with extra fields"""
        response = client.post(
            "/api/query",
            json={"query": "test", "session_id": "test", "extra_field": "should be ignored"},
        )
        # Should be lenient and ignore extra fields
        assert response.status_code == 200

    def test_very_long_query(self, client):
        """Test very long query string"""
        long_query = "What is Python? " * 1000
        response = client.post("/api/query", json={"query": long_query, "session_id": "test"})
        assert response.status_code == 200

    def test_special_headers_preserved(self, client):
        """Test that custom headers are handled"""
        response = client.post(
            "/api/query",
            json={"query": "test"},
            headers={"X-Custom-Header": "test-value", "User-Agent": "test-agent"},
        )
        # Should work regardless of headers
        assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestAPIPerformance:
    """Performance-related tests"""

    def setup_method(self):
        """Setup for performance tests"""
        self.mock_rag_system = Mock()
        self.mock_rag_system.query.return_value = ("Response", ["Source"])
        self.mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Test"],
        }
        self.mock_config = Mock()

    @pytest.fixture
    def client(self):
        """Create test client"""
        with patch("backend.app.rag_system", self.mock_rag_system):
            with patch("backend.app.config", self.mock_config):
                from backend.app import app

                return TestClient(app)

    @pytest.mark.slow
    def test_multiple_concurrent_queries(self, client):
        """Test handling multiple concurrent queries"""
        import time

        def make_query(session_id):
            start = time.time()
            response = client.post("/api/query", json={"query": "test", "session_id": session_id})
            duration = time.time() - start
            return response.status_code, duration

        # Simulate concurrent requests
        results = []
        for i in range(10):
            results.append(make_query(f"session-{i}"))

        # All should succeed
        for status, duration in results:
            assert status == 200


# Integration test with real-ish mock data
@pytest.mark.api
@pytest.mark.integration
class TestAPIIntegrationFlow:
    """Integration test for complete API flow"""

    def test_complete_user_flow(self):
        """Test a complete user interaction flow"""
        # Mock the RAG system with realistic behavior
        mock_rag = Mock()

        # First call: query without session
        mock_rag.session_manager.create_session.return_value = "user-123"
        mock_rag.query.return_value = (
            "Python is a high-level programming language created by Guido van Rossum.",
            ["Python 101, Lesson 0: Introduction"],
        )

        # Second call: get courses
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["Python 101", "Advanced Python"],
        }

        with patch("backend.app.rag_system", mock_rag):
            with patch("backend.app.config", Mock()):
                from backend.app import app

                client = TestClient(app)

                # Step 1: User sends first query
                response1 = client.post("/api/query", json={"query": "What is Python?"})
                assert response1.status_code == 200
                data1 = response1.json()
                assert "user-123" in data1["session_id"]
                assert "Python" in data1["answer"]

                # Step 2: User asks for course list
                response2 = client.get("/api/courses")
                assert response2.status_code == 200
                data2 = response2.json()
                assert data2["total_courses"] == 2

                # Step 3: User asks follow-up in same session
                response3 = client.post(
                    "/api/query", json={"query": "Tell me more", "session_id": data1["session_id"]}
                )
                assert response3.status_code == 200
                # Session should be preserved
                assert response3.json()["session_id"] == data1["session_id"]


# Test the actual error scenarios
@pytest.mark.api
class TestAPIErrorScenarios:
    """Test various error scenarios"""

    def setup_method(self):
        """Setup for error scenario tests"""
        self.mock_config = Mock()

    @pytest.fixture
    def client(self):
        """Create test client"""
        with patch("backend.app.config", self.mock_config):
            from backend.app import app

            return TestClient(app)

    def test_rag_system_not_initialized(self, client):
        """Test behavior when RAG system fails to initialize"""
        with patch("backend.app.rag_system", side_effect=Exception("Init failed")):
            # This would happen during app startup, so we test query endpoint
            with patch("backend.app.rag_system.query", side_effect=Exception("System unavailable")):
                response = client.post("/api/query", json={"query": "test", "session_id": "test"})
                assert response.status_code == 500

    def test_concurrent_session_conflicts(self, client):
        """Test potential session ID conflicts"""
        mock_rag = Mock()
        mock_rag.query.return_value = ("Response", ["Source"])
        mock_rag.session_manager.create_session.return_value = "session-1"

        with patch("backend.app.rag_system", mock_rag):
            # Create multiple sessions rapidly
            sessions = []
            for _ in range(5):
                response = client.post("/api/query", json={"query": "test"})
                if response.status_code == 200:
                    sessions.append(response.json()["session_id"])

            # All should be created
            assert len(sessions) == 5


# Async support for FastAPI endpoints
@pytest.mark.api
@pytest.mark.asyncio
class TestAsyncAPI:
    """Test async capabilities of the API"""

    @pytest.fixture
    def client(self):
        """Create async test client"""
        with patch("backend.app.rag_system", Mock()):
            with patch("backend.app.config", Mock()):
                from backend.app import app

                return TestClient(app)

    async def test_async_query_response(self, client):
        """Test that query endpoint can handle async processing"""
        mock_rag = Mock()
        mock_rag.query.return_value = ("Async response", ["Source"])
        mock_rag.session_manager.create_session.return_value = "async-session"

        with patch("backend.app.rag_system", mock_rag):
            # This tests the async nature of the FastAPI endpoint
            response = client.post("/api/query", json={"query": "async test", "session_id": "test"})
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
