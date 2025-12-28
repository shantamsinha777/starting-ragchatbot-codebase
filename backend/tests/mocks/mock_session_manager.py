from typing import Dict, List, Optional


class MockSessionManager:
    """Mock implementation of SessionManager for testing"""

    def __init__(self, max_history: int = 2):
        self.max_history = max_history
        self.sessions: Dict[str, List[str]] = {}

    def get_conversation_history(self, session_id: str) -> Optional[str]:
        """Mock getting conversation history"""
        if session_id in self.sessions:
            history = self.sessions[session_id]
            # Format as: "User: ...\nAssistant: ..."
            formatted = []
            for i, exchange in enumerate(history):
                if i % 2 == 0:  # User message
                    formatted.append(f"User: {exchange}")
                else:  # Assistant message
                    formatted.append(f"Assistant: {exchange}")
            return "\n".join(formatted)
        return None

    def add_exchange(self, session_id: str, user_query: str, assistant_response: str):
        """Mock adding conversation exchange"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        # Add user query
        self.sessions[session_id].append(user_query)
        # Add assistant response
        self.sessions[session_id].append(assistant_response)

        # Enforce max history limit
        if len(self.sessions[session_id]) > self.max_history * 2:
            self.sessions[session_id] = self.sessions[session_id][-self.max_history * 2 :]

    def clear_session(self, session_id: str):
        """Mock clearing session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
