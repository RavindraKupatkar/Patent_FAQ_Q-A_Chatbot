"""
UI Components for Patent & BIS FAQ Assistant

This module contains reusable UI components for the Streamlit application.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
import time

class UIComponents:
    """Collection of reusable UI components."""
    
    @staticmethod
    def render_status_card(title: str, status: str, icon: str = "✅", color: str = "success"):
        """Render a status card with icon and colored background."""
        color_classes = {
            "success": "status-success",
            "info": "status-info",
            "warning": "status-warning",
            "error": "status-error"
        }
        
        st.markdown(f"""
            <div class="status-indicator {color_classes.get(color, 'status-info')}">
                {icon} {title}: {status}
            </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_feature_grid(features: List[Dict[str, str]]):
        """Render a grid of feature cards."""
        feature_html = ""
        for feature in features:
            feature_html += f"""
                <div class="feature-item">
                    <div class="feature-icon">{feature['icon']}</div>
                    <div class="feature-title">{feature['title']}</div>
                    <div class="feature-desc">{feature['description']}</div>
                </div>
            """
        
        st.markdown(f"""
            <div class="feature-grid">
                {feature_html}
            </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_question_card(question: str, category: str, key: str):
        """Render a clickable question card."""
        if st.button(question, key=key, use_container_width=True):
            return True
        return False
    
    @staticmethod
    def render_chat_message(content: str, role: str, source: Optional[str] = None):
        """Render a chat message with proper styling."""
        if role == "user":
            st.markdown(f"""
                <div class="chat-message">
                    <div class="user-message">
                        <div class="message-content">{content}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            source_html = ""
            if source:
                source_text = source.split('/')[-1]  # Get filename only
                source_html = f"""
                    <div class="message-source">
                        <a href="{source}" target="_blank" class="source-link">
                            📄 Source: {source_text}
                        </a>
                    </div>
                """
            
            st.markdown(f"""
                <div class="chat-message">
                    <div class="assistant-message">
                        <div class="message-content">{content}</div>
                        {source_html}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_loading_indicator(message: str = "Processing..."):
        """Render a loading indicator with animated dots."""
        st.markdown(f"""
            <div style="text-align: center; padding: 2rem;">
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
                <div style="margin-top: 1rem; color: #6b7280;">{message}</div>
            </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_welcome_screen():
        """Render the welcome screen with features."""
        features = [
            {
                "icon": "📋",
                "title": "Patent Expertise",
                "description": "Comprehensive patent information and guidance"
            },
            {
                "icon": "🏛️",
                "title": "BIS Standards",
                "description": "Bureau of Indian Standards regulations and processes"
            },
            {
                "icon": "🤖",
                "title": "AI-Powered",
                "description": "Advanced AI for accurate and helpful responses"
            },
            {
                "icon": "⚡",
                "title": "Instant Answers",
                "description": "Get quick, reliable answers to your questions"
            }
        ]
        
        st.markdown("""
            <div class="welcome-card">
                <div class="welcome-icon">🎯</div>
                <div class="welcome-title">Welcome to Your AI Assistant!</div>
                <div class="welcome-text">
                    I'm here to help you with questions about patents and Bureau of Indian Standards (BIS) regulations. 
                    Ask me anything or choose from the suggested questions in the sidebar.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        UIComponents.render_feature_grid(features)
    
    @staticmethod
    def render_sidebar_header(title: str, subtitle: str):
        """Render the sidebar header."""
        st.markdown(f"""
            <div class="sidebar-header">
                <div class="sidebar-title">{title}</div>
                <div class="sidebar-subtitle">{subtitle}</div>
            </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_metrics_row(metrics: List[Dict[str, Any]]):
        """Render a row of metrics."""
        cols = st.columns(len(metrics))
        for i, metric in enumerate(metrics):
            with cols[i]:
                st.metric(
                    label=metric['label'],
                    value=metric['value'],
                    delta=metric.get('delta')
                )
    
    @staticmethod
    def render_empty_chat_state():
        """Render empty chat state."""
        st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #6b7280;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
                <div style="font-size: 1.2rem; font-weight: 500;">Start a conversation!</div>
                <div>Ask me anything about patents or BIS standards.</div>
            </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_typing_indicator():
        """Render typing indicator for AI responses."""
        st.markdown("""
            <div class="chat-message">
                <div class="assistant-message" style="padding: 1rem;">
                    <div class="loading-dots">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                    <span style="margin-left: 1rem; color: #6b7280;">AI is thinking...</span>
                </div>
            </div>
        """, unsafe_allow_html=True)