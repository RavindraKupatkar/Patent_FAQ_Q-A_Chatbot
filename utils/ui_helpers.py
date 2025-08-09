"""
UI Helper Functions

This module contains utility functions for UI operations and state management.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import time
from datetime import datetime

class UIHelpers:
    """Collection of UI helper functions."""
    
    @staticmethod
    def initialize_session_state():
        """Initialize all session state variables."""
        defaults = {
            'initialized': True,
            'chat_history': None,
            'selected_question': None,
            'db_manager': None,
            'response_generator': None,
            'suggestion_engine': None,
            'embedder': None,
            'show_welcome': True,
            'current_tab': 'chat',
            'user_preferences': {
                'theme': 'light',
                'language': 'en',
                'response_length': 'medium'
            },
            'system_stats': {
                'total_queries': 0,
                'successful_responses': 0,
                'last_query_time': None
            }
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def update_system_stats(success: bool = True):
        """Update system statistics."""
        if 'system_stats' not in st.session_state:
            st.session_state.system_stats = {
                'total_queries': 0,
                'successful_responses': 0,
                'last_query_time': None
            }
        
        st.session_state.system_stats['total_queries'] += 1
        if success:
            st.session_state.system_stats['successful_responses'] += 1
        st.session_state.system_stats['last_query_time'] = datetime.now()
    
    @staticmethod
    def get_success_rate() -> float:
        """Calculate the success rate of queries."""
        stats = st.session_state.get('system_stats', {})
        total = stats.get('total_queries', 0)
        successful = stats.get('successful_responses', 0)
        
        if total == 0:
            return 0.0
        return (successful / total) * 100
    
    @staticmethod
    def format_timestamp(timestamp: datetime) -> str:
        """Format timestamp for display."""
        if not timestamp:
            return "Never"
        
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    @staticmethod
    def show_toast(message: str, type: str = "info", duration: int = 3):
        """Show a toast notification."""
        toast_colors = {
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6'
        }
        
        color = toast_colors.get(type, toast_colors['info'])
        
        toast_placeholder = st.empty()
        toast_placeholder.markdown(f"""
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: {color};
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                z-index: 1000;
                animation: slideInRight 0.3s ease-out;
            ">
                {message}
            </div>
            <style>
            @keyframes slideInRight {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            </style>
        """, unsafe_allow_html=True)
        
        time.sleep(duration)
        toast_placeholder.empty()
    
    @staticmethod
    def create_download_link(data: str, filename: str, text: str) -> str:
        """Create a download link for data."""
        import base64
        
        b64 = base64.b64encode(data.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">{text}</a>'
        return href
    
    @staticmethod
    def validate_input(text: str, min_length: int = 1, max_length: int = 1000) -> tuple[bool, str]:
        """Validate user input."""
        if not text or not text.strip():
            return False, "Please enter a question."
        
        if len(text.strip()) < min_length:
            return False, f"Question must be at least {min_length} characters long."
        
        if len(text.strip()) > max_length:
            return False, f"Question must be less than {max_length} characters long."
        
        return True, ""
    
    @staticmethod
    def get_question_suggestions(query: str, category: str = "all") -> List[str]:
        """Get question suggestions based on input."""
        patent_suggestions = [
            "What is the patent application process?",
            "How long does patent protection last?",
            "What are the costs involved in patent filing?",
            "What are the requirements for patentability?",
            "How do I check if my invention is patentable?",
            "What is the difference between a patent and a trademark?",
            "Can I file a patent internationally?",
            "What happens after I file a patent application?"
        ]
        
        bis_suggestions = [
            "What is the BIS certification process?",
            "How long does BIS certification take?",
            "What are the costs of BIS certification?",
            "Which products need BIS certification?",
            "How do I apply for BIS certification?",
            "What are BIS quality standards?",
            "How to renew BIS certification?",
            "What documents are required for BIS certification?"
        ]
        
        if category == "patent":
            return patent_suggestions
        elif category == "bis":
            return bis_suggestions
        else:
            # Return mixed suggestions based on query content
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ['patent', 'invention', 'ip']):
                return patent_suggestions[:4] + bis_suggestions[:2]
            elif any(keyword in query_lower for keyword in ['bis', 'certification', 'standard']):
                return bis_suggestions[:4] + patent_suggestions[:2]
            else:
                return patent_suggestions[:3] + bis_suggestions[:3]
    
    @staticmethod
    def export_chat_history(chat_history: List[Dict[str, Any]]) -> str:
        """Export chat history as formatted text."""
        export_text = "# Chat History Export\n\n"
        export_text += f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, message in enumerate(chat_history):
            role = "You" if message['role'] == 'user' else "Assistant"
            timestamp = message.get('timestamp', '')
            content = message['content']
            
            export_text += f"## {role} ({timestamp})\n"
            export_text += f"{content}\n\n"
            
            if message.get('source'):
                export_text += f"*Source: {message['source']}*\n\n"
            
            export_text += "---\n\n"
        
        return export_text
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information for display."""
        import platform
        import psutil
        
        try:
            return {
                'platform': platform.system(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': f"{psutil.virtual_memory().total // (1024**3)} GB",
                'memory_available': f"{psutil.virtual_memory().available // (1024**3)} GB"
            }
        except:
            return {
                'platform': 'Unknown',
                'python_version': platform.python_version(),
                'cpu_count': 'Unknown',
                'memory_total': 'Unknown',
                'memory_available': 'Unknown'
            }
    
    @staticmethod
    def create_feedback_form():
        """Create a feedback form."""
        with st.expander("📝 Feedback"):
            st.write("Help us improve the assistant!")
            
            rating = st.select_slider(
                "How would you rate your experience?",
                options=["😞 Poor", "😐 Fair", "😊 Good", "😍 Excellent"],
                value="😊 Good"
            )
            
            feedback_text = st.text_area(
                "Additional comments (optional):",
                placeholder="Tell us what you liked or what could be improved..."
            )
            
            if st.button("Submit Feedback"):
                # In a real application, you would save this feedback
                st.success("Thank you for your feedback!")
                return {
                    'rating': rating,
                    'comment': feedback_text,
                    'timestamp': datetime.now()
                }
        
        return None