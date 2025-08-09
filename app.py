import streamlit as st
import os
from dotenv import load_dotenv
from utils.db_manager import VectorDBManager
from services.response_generator import ResponseGenerator
from services.suggestion_engine import SuggestionEngine
from utils.chat_history import ChatHistory
from utils.embedder import get_embedder
import time

# Load environment variables
load_dotenv()

# Validate required environment variables
required_env_vars = [
    'GROQ_API_KEY',
    'PINECONE_API_KEY', 
    'PINECONE_ENV',
    'PINECONE_INDEX_NAME'
]

missing_vars = []
for var in required_env_vars:
    if not (st.secrets.get(var) or os.getenv(var)):
        missing_vars.append(var)

if missing_vars:
    st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    st.info("Please check your .env file or Streamlit secrets configuration.")
    st.stop()

# Page config with enhanced settings
st.set_page_config(
    page_title="Patent & BIS FAQ Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/help',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': "# Patent & BIS FAQ Assistant\nYour intelligent assistant for patent and BIS-related queries."
    }
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.chat_history = ChatHistory()
    st.session_state.chat_history.clear()
    st.session_state.selected_question = None
    st.session_state.db_manager = None
    st.session_state.response_generator = None
    st.session_state.suggestion_engine = None
    st.session_state.embedder = None
    st.session_state.show_welcome = True
    st.session_state.current_tab = "chat"

# Enhanced CSS with modern design principles
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Main container */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Header */
    .app-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .app-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .app-subtitle {
        font-size: 1.2rem;
        color: #6b7280;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        border-right: 1px solid #e2e8f0;
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    .sidebar-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .sidebar-subtitle {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #0ea5e9;
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 25px rgba(14, 165, 233, 0.1);
    }
    
    .welcome-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .welcome-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #0c4a6e;
        margin-bottom: 1rem;
    }
    
    .welcome-text {
        color: #0369a1;
        font-size: 1.1rem;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 1.5rem;
    }
    
    .feature-item {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .feature-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .feature-title {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    
    .feature-desc {
        font-size: 0.9rem;
        color: #64748b;
    }
    
    /* Chat interface */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        min-height: 500px;
        max-height: 600px;
        overflow-y: auto;
    }
    
    /* Chat messages */
    .chat-message {
        margin-bottom: 1.5rem;
        animation: fadeInUp 0.3s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin-left: 20%;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin-right: 20%;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .message-content {
        line-height: 1.6;
        font-size: 1rem;
    }
    
    .message-source {
        margin-top: 1rem;
        padding: 0.75rem;
        background: rgba(14, 165, 233, 0.1);
        border-radius: 10px;
        border-left: 4px solid #0ea5e9;
    }
    
    .source-link {
        color: #0ea5e9;
        text-decoration: none;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .source-link:hover {
        color: #0284c7;
        text-decoration: underline;
    }
    
    /* Question suggestions */
    .suggestions-container {
        margin-top: 2rem;
    }
    
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .question-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .question-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        transform: translateY(-1px);
    }
    
    .question-text {
        font-weight: 500;
        color: #374151;
        margin-bottom: 0.25rem;
    }
    
    .question-category {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Input area */
    .chat-input-container {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 1.5rem;
        border-top: 1px solid #e2e8f0;
        border-radius: 0 0 15px 15px;
        margin: 0 -1.5rem -1.5rem -1.5rem;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .clear-button {
        background: linear-gradient(135deg, #ef4444, #dc2626) !important;
        margin-top: 1rem;
    }
    
    .clear-button:hover {
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4) !important;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    
    .status-success {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    
    .status-info {
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-container {
            margin: 0.5rem;
            padding: 1rem;
        }
        
        .app-title {
            font-size: 2rem;
        }
        
        .user-message, .assistant-message {
            margin-left: 0;
            margin-right: 0;
        }
        
        .feature-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Loading animation */
    .loading-dots {
        display: inline-flex;
        gap: 4px;
    }
    
    .loading-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        animation: loading 1.4s infinite ease-in-out both;
    }
    
    .loading-dot:nth-child(1) { animation-delay: -0.32s; }
    .loading-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes loading {
        0%, 80%, 100% {
            transform: scale(0);
        }
        40% {
            transform: scale(1);
        }
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize components once and cache them."""
    try:
        # Initialize database manager
        db_manager = VectorDBManager()
        
        # Check if we need to index documents
        if not _check_pinecone_data(db_manager):
            st.info("🔄 Setting up document index for the first time...")
            _index_documents(db_manager)
        
        # Initialize other components
        embedder = get_embedder()
        response_generator = ResponseGenerator(db_manager)
        suggestion_engine = SuggestionEngine()
        
        return db_manager, embedder, response_generator, suggestion_engine
        
    except Exception as e:
        st.error(f"❌ Error initializing components: {str(e)}")
        st.stop()

def _check_pinecone_data(db_manager):
    """Check if Pinecone index has data in both collections."""
    try:
        patent_results = db_manager.search("patent_faqs", "test", limit=1)
        bis_results = db_manager.search("bis_faqs", "test", limit=1)
        return len(patent_results) > 0 and len(bis_results) > 0
    except:
        return False

def _index_documents(db_manager):
    """Index PDF documents into Pinecone collections."""
    try:
        # Create collections
        db_manager.create_collection("patent_faqs")
        db_manager.create_collection("bis_faqs")
        
        # Load and index documents
        patent_pdf = os.path.join('data', 'Final_FREQUENTLY_ASKED_QUESTIONS_-PATENT.pdf')
        bis_pdf = os.path.join('data', 'FINAL_FAQs_June_2018.pdf')
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        if os.path.exists(patent_pdf):
            status_text.text("📄 Loading Patent FAQ document...")
            progress_bar.progress(25)
            patent_docs = db_manager.load_pdf(patent_pdf)
            
            status_text.text("🔄 Indexing Patent FAQ embeddings...")
            progress_bar.progress(50)
            db_manager.index_document("patent_faqs", patent_docs, {"source": patent_pdf})
        
        if os.path.exists(bis_pdf):
            status_text.text("📄 Loading BIS FAQ document...")
            progress_bar.progress(75)
            bis_docs = db_manager.load_pdf(bis_pdf)
            
            status_text.text("🔄 Indexing BIS FAQ embeddings...")
            progress_bar.progress(100)
            db_manager.index_document("bis_faqs", bis_docs, {"source": bis_pdf})
        
        status_text.success("✅ Documents indexed successfully!")
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Error indexing documents: {str(e)}")
        raise

# Initialize components
if not all([st.session_state.db_manager, st.session_state.embedder, 
           st.session_state.response_generator, st.session_state.suggestion_engine]):
    
    with st.spinner("🚀 Initializing AI Assistant..."):
        components = initialize_components()
        (st.session_state.db_manager, st.session_state.embedder, 
         st.session_state.response_generator, st.session_state.suggestion_engine) = components

# Sidebar
with st.sidebar:
    st.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-title">🤖 AI Assistant</div>
            <div class="sidebar-subtitle">Patent & BIS Expert</div>
        </div>
    """, unsafe_allow_html=True)
    
    # System status
    embedder_info = st.session_state.embedder.get_provider_info()
    st.markdown(f"""
        <div class="status-indicator status-success">
            ✅ System Ready
        </div>
        <div class="status-indicator status-info">
            🧠 {embedder_info['provider'].replace('_', ' ').title()}
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 New Chat", use_container_width=True):
            st.session_state.chat_history.clear()
            st.session_state.show_welcome = True
            st.rerun()
    
    with col2:
        if st.button("📊 Stats", use_container_width=True):
            st.session_state.current_tab = "stats"
            st.rerun()
    
    st.markdown("---")
    
    # Suggested questions
    st.markdown("### 💡 Suggested Questions")
    
    # Patent questions
    st.markdown("**📋 Patent Questions**")
    patent_questions = [
        "What is a patent?",
        "How do I apply for a patent?",
        "What is the duration of a patent?",
        "What are the requirements for patentability?",
        "How much does it cost to file a patent?"
    ]
    
    for i, question in enumerate(patent_questions):
        if st.button(question, key=f"patent_{i}", use_container_width=True):
            st.session_state.selected_question = question
            st.session_state.show_welcome = False
            st.rerun()
    
    st.markdown("**🏛️ BIS Questions**")
    bis_questions = [
        "What is BIS certification?",
        "How do I get BIS certification?",
        "What are BIS standards?",
        "What products require BIS certification?",
        "How long does BIS certification take?"
    ]
    
    for i, question in enumerate(bis_questions):
        if st.button(question, key=f"bis_{i}", use_container_width=True):
            st.session_state.selected_question = question
            st.session_state.show_welcome = False
            st.rerun()
    
    st.markdown("---")
    
    # Settings
    with st.expander("⚙️ Settings"):
        st.markdown("**Response Settings**")
        temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.1)
        max_tokens = st.slider("Response Length", 100, 1000, 500, 50)
        
        if st.button("Apply Settings"):
            st.session_state.response_generator.update_config(
                temperature=temperature,
                max_tokens=max_tokens
            )
            st.success("Settings updated!")

# Main content area
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="app-header">
        <div class="app-title">Patent & BIS FAQ Assistant</div>
        <div class="app-subtitle">Your intelligent companion for patent and BIS-related queries</div>
    </div>
""", unsafe_allow_html=True)

# Welcome screen
if st.session_state.show_welcome:
    st.markdown("""
        <div class="welcome-card">
            <div class="welcome-icon">🎯</div>
            <div class="welcome-title">Welcome to Your AI Assistant!</div>
            <div class="welcome-text">
                I'm here to help you with questions about patents and Bureau of Indian Standards (BIS) regulations. 
                Ask me anything or choose from the suggested questions in the sidebar.
            </div>
            
            <div class="feature-grid">
                <div class="feature-item">
                    <div class="feature-icon">📋</div>
                    <div class="feature-title">Patent Expertise</div>
                    <div class="feature-desc">Comprehensive patent information and guidance</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🏛️</div>
                    <div class="feature-title">BIS Standards</div>
                    <div class="feature-desc">Bureau of Indian Standards regulations and processes</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">AI-Powered</div>
                    <div class="feature-desc">Advanced AI for accurate and helpful responses</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-title">Instant Answers</div>
                    <div class="feature-desc">Get quick, reliable answers to your questions</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Chat interface
if st.session_state.current_tab == "chat" or not st.session_state.show_welcome:
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        chat_history = st.session_state.chat_history.get_history()
        
        if not chat_history and not st.session_state.show_welcome:
            st.markdown("""
                <div style="text-align: center; padding: 2rem; color: #6b7280;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
                    <div style="font-size: 1.2rem; font-weight: 500;">Start a conversation!</div>
                    <div>Ask me anything about patents or BIS standards.</div>
                </div>
            """, unsafe_allow_html=True)
        
        for i in range(0, len(chat_history), 2):
            if i + 1 < len(chat_history):
                # User message
                st.markdown(f"""
                    <div class="chat-message">
                        <div class="user-message">
                            <div class="message-content">{chat_history[i]['content']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Assistant message
                assistant_msg = chat_history[i + 1]
                source_html = ""
                if "source" in assistant_msg and assistant_msg["source"]:
                    source_text = os.path.basename(assistant_msg["source"])
                    source_html = f"""
                        <div class="message-source">
                            <a href="{assistant_msg['source']}" target="_blank" class="source-link">
                                📄 Source: {source_text}
                            </a>
                        </div>
                    """
                
                st.markdown(f"""
                    <div class="chat-message">
                        <div class="assistant-message">
                            <div class="message-content">{assistant_msg['content']}</div>
                            {source_html}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("💬 Ask me anything about patents or BIS standards...", key="chat_input")

# Process user input
current_question = user_input if user_input else st.session_state.selected_question

if current_question:
    st.session_state.show_welcome = False
    st.session_state.chat_history.add_message("user", current_question)
    
    # Show typing indicator
    with st.spinner("🤔 Thinking..."):
        try:
            response = st.session_state.response_generator.generate_response(current_question)
            
            if response and response["answer"]:
                st.session_state.chat_history.add_message("assistant", response["answer"], response["source"])
            else:
                no_answer_msg = "I apologize, but I don't have specific information about that topic. Please try asking about patents or BIS standards."
                st.session_state.chat_history.add_message("assistant", no_answer_msg)
        
        except Exception as e:
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            st.session_state.chat_history.add_message("assistant", error_msg)
    
    st.session_state.selected_question = None
    st.rerun()

# Statistics tab
if st.session_state.current_tab == "stats":
    st.markdown("### 📊 System Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💬 Total Messages", len(st.session_state.chat_history.get_history()))
    
    with col2:
        embedder_info = st.session_state.embedder.get_provider_info()
        st.metric("🧠 Embedding Provider", embedder_info['provider'].replace('_', ' ').title())
    
    with col3:
        st.metric("📐 Embedding Dimension", embedder_info['dimension'])
    
    with col4:
        config = st.session_state.response_generator.get_config()
        st.metric("🎛️ Temperature", f"{config['temperature']:.1f}")
    
    # Reset to chat tab
    if st.button("← Back to Chat"):
        st.session_state.current_tab = "chat"
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Save chat history
st.session_state.chat_history.save()