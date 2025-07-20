from typing import List, Dict, Optional
import json
import os
from datetime import datetime

class ChatHistory:
    def __init__(self, max_history: int = 10):
        self.history: List[Dict] = []
        self.max_history = max_history
        self.history_file = "chat_history.json"
        self._load_history()

    def add_message(self, role: str, content: str, source: Optional[str] = None) -> None:
        """Add a message to the chat history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if source:
            message["source"] = source
            
        self.history.append(message)
        
        # Keep only the last max_history messages
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        self._save_history()

    def get_history(self) -> List[Dict]:
        """Get the current chat history."""
        return self.history

    def clear(self) -> None:
        """Clear the chat history."""
        self.history = []
        self._save_history()

    def save(self) -> None:
        """Save the current chat history."""
        self._save_history()

    def _save_history(self) -> None:
        """Save chat history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving chat history: {e}")

    def _load_history(self) -> None:
        """Load chat history from file if it exists."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            self.history = []
