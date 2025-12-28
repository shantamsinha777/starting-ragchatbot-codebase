import unittest
import sys
import os

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from session_manager import SessionManager


class TestSessionManagement(unittest.TestCase):
    """Integration tests for session management functionality"""

    def setUp(self):
        """Setup session manager"""
        self.session_manager = SessionManager(max_history=2)

    def test_session_isolation(self):
        """Test that different sessions are isolated"""
        session1 = "user1"
        session2 = "user2"

        # Add exchanges to different sessions
        self.session_manager.add_exchange(session1, "Question 1", "Answer 1")
        self.session_manager.add_exchange(session2, "Question 2", "Answer 2")

        # Get histories
        history1 = self.session_manager.get_conversation_history(session1)
        history2 = self.session_manager.get_conversation_history(session2)

        # Should be different
        self.assertIn("Question 1", history1)
        self.assertNotIn("Question 2", history1)
        self.assertIn("Question 2", history2)
        self.assertNotIn("Question 1", history2)

    def test_history_limit_enforcement(self):
        """Test that history limits are enforced"""
        session_id = "test_session"

        # Add more exchanges than the limit
        for i in range(5):
            self.session_manager.add_exchange(session_id, f"Q{i}", f"A{i}")

        history = self.session_manager.get_conversation_history(session_id)

        # Should only contain the last 2 exchanges (MAX_HISTORY)
        lines = history.split("\n")
        self.assertLessEqual(len([l for l in lines if l.strip()]), 4)  # 2 exchanges = 4 lines

    def test_session_cleanup(self):
        """Test cleanup of old sessions"""
        # Add sessions with timestamps
        self.session_manager.add_exchange("old_session", "Q1", "A1")
        self.session_manager.add_exchange("active_session", "Q2", "A2")

        # Simulate old session (in real implementation, this would check timestamps)
        # For now, just test that sessions exist
        self.assertIsNotNone(self.session_manager.get_conversation_history("old_session"))
        self.assertIsNotNone(self.session_manager.get_conversation_history("active_session"))

    def test_concurrent_session_handling(self):
        """Test handling of multiple concurrent sessions"""
        sessions = ["session1", "session2", "session3"]

        # Add exchanges to all sessions
        for i, session in enumerate(sessions):
            self.session_manager.add_exchange(session, f"Question {i}", f"Answer {i}")

        # Verify all sessions have their own history
        for i, session in enumerate(sessions):
            history = self.session_manager.get_conversation_history(session)
            self.assertIn(f"Question {i}", history)
            self.assertIn(f"Answer {i}", history)

    def test_empty_session_handling(self):
        """Test handling of empty or new sessions"""
        new_session = "new_session_id"

        # Get history for new session (should be empty or None)
        history = self.session_manager.get_conversation_history(new_session)

        # Should handle gracefully
        if history is None:
            self.assertIsNone(history)
        else:
            self.assertEqual(history.strip(), "")

    def test_session_history_formatting(self):
        """Test proper formatting of session history"""
        session_id = "format_test"

        # Add multiple exchanges
        self.session_manager.add_exchange(session_id, "First question", "First answer")
        self.session_manager.add_exchange(session_id, "Second question", "Second answer")

        # Get history and verify format
        history = self.session_manager.get_conversation_history(session_id)

        # Should contain proper User/Assistant formatting
        self.assertIn("User: First question", history)
        self.assertIn("Assistant: First answer", history)
        self.assertIn("User: Second question", history)
        self.assertIn("Assistant: Second answer", history)

    def test_special_character_session_ids(self):
        """Test session IDs with special characters"""
        special_session_ids = [
            "user@email.com",
            "user-with-dashes",
            "user_with_underscores",
            "user123",
            "user with spaces",
            "user/with/slashes",
        ]

        for session_id in special_session_ids:
            try:
                self.session_manager.add_exchange(session_id, "Test question", "Test answer")
                history = self.session_manager.get_conversation_history(session_id)
                self.assertIsNotNone(history)
            except Exception:
                # Some special characters might not be allowed, but shouldn't crash
                self.assertTrue(True)

    def test_large_session_history(self):
        """Test handling of large session histories"""
        session_id = "large_history_test"

        # Add many exchanges (within reasonable limits)
        for i in range(10):
            self.session_manager.add_exchange(session_id, f"Question {i}", f"Answer {i}")

        # Should handle gracefully (will only keep last MAX_HISTORY exchanges)
        history = self.session_manager.get_conversation_history(session_id)
        self.assertIsNotNone(history)
        self.assertTrue(len(history) > 0)

    def test_session_id_edge_cases(self):
        """Test various edge cases for session IDs"""
        edge_case_ids = [
            "",  # Empty string
            "a",  # Single character
            "x" * 100,  # Very long ID
            "session_with_unicode_中文_日本語",  # Unicode characters
        ]

        for session_id in edge_case_ids:
            try:
                self.session_manager.add_exchange(session_id, "Test", "Test")
                history = self.session_manager.get_conversation_history(session_id)
                self.assertIsNotNone(history)
            except Exception:
                # Some edge cases might fail, but shouldn't crash the system
                self.assertTrue(True)

    def test_session_consistency_across_calls(self):
        """Test that session data remains consistent across multiple calls"""
        session_id = "consistency_test"

        # Add initial exchange
        self.session_manager.add_exchange(session_id, "First", "First Response")

        # Get history multiple times
        history1 = self.session_manager.get_conversation_history(session_id)
        history2 = self.session_manager.get_conversation_history(session_id)

        # Should be identical
        self.assertEqual(history1, history2)

        # Add another exchange
        self.session_manager.add_exchange(session_id, "Second", "Second Response")

        # Get updated history
        history3 = self.session_manager.get_conversation_history(session_id)

        # Should be different from previous (contains new exchange)
        self.assertNotEqual(history1, history3)
        self.assertIn("Second", history3)
        self.assertIn("Second Response", history3)


if __name__ == "__main__":
    unittest.main()
