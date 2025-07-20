import streamlit as st
import os
from dotenv import load_dotenv
from utils.db_manager import VectorDBManager
from services.response_generator import ResponseGenerator
from services.suggestion_engine import SuggestionEngine
from utils.chat_history import ChatHistory

# Load environment variables
load_dotenv()

# Page config with custom theme
st.set_page_config(
    page_title="Patent & BIS FAQ Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for fresh start
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.chat_history = ChatHistory()
    st.session_state.chat_history.clear()
    st.session_state.selected_question = None

# Custom CSS for modern and clean look
st.markdown("""
    <style>
    /* Main container */
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        background-color: #0E1117;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1E1E1E;
    }
    
    .sidebar-header {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 2rem;
        color: #00FF9D;
        text-align: center;
        padding: 1rem;
        border-bottom: 2px solid #00FF9D;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .chat-message.user {
        background-color: #2B313E;
        border-left: 4px solid #00FF9D;
    }
    
    .chat-message.assistant {
        background-color: #1E1E1E;
        border-left: 4px solid #FF4B4B;
    }
    
    .chat-message .content {
        display: flex;
        margin-top: 0.5rem;
    }
    
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1rem;
    }
    
    .chat-message .message {
        flex: 1;
        font-size: 1.1rem;
        line-height: 1.5;
    }
    
    /* Source link styling */
    .source-link {
        color: #00FF9D;
        text-decoration: none;
        font-size: 0.9rem;
        margin-top: 0.8rem;
        padding: 0.5rem;
        background-color: rgba(0, 255, 157, 0.1);
        border-radius: 0.5rem;
        display: inline-block;
    }
    
    .source-link:hover {
        background-color: rgba(0, 255, 157, 0.2);
    }
    
    /* Suggested questions styling */
    .suggested-question {
        padding: 1rem;
        margin: 0.8rem 0;
        border-radius: 0.8rem;
        background-color: #2B313E;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid #3B414E;
    }
    
    .suggested-question:hover {
        background-color: #3B414E;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Button styling */
    .stButton button {
        width: 100%;
        border-radius: 0.8rem;
        padding: 0.8rem;
        font-size: 1rem;
        background-color: #2B313E;
        color: white;
        border: 1px solid #3B414E;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #3B414E;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Clear chat button */
    .clear-chat {
        background-color: #FF4B4B !important;
        color: white !important;
        margin-top: 2rem;
    }
    
    .clear-chat:hover {
        background-color: #FF6B6B !important;
    }
    
    /* Section headers */
    .section-header {
        color: #00FF9D;
        font-size: 1.4rem;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #3B414E;
    }
    
    /* Welcome message */
    .welcome-message {
        background-color: #2B313E;
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        border: 1px solid #3B414E;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize components
@st.cache_resource
def initialize_components():
    try:
        # Initialize vector database manager
        db_manager = VectorDBManager()
        
        # Try to load existing vector database
        if os.path.exists('vector_db'):
            db_manager.load('vector_db')
        else:
            # If no existing database, create and index documents
            st.warning("Vector database not found. Creating new database...")
            
            # Create collections
            db_manager.create_collection("patent_faqs")
            db_manager.create_collection("bis_faqs")
            
            # Load and index documents
            patent_pdf = os.path.join('data', 'Final_FREQUENTLY_ASKED_QUESTIONS_-PATENT.pdf')
            bis_pdf = os.path.join('data', 'FINAL_FAQs_June_2018.pdf')
            
            if os.path.exists(patent_pdf):
                patent_docs = db_manager.load_pdf(patent_pdf)
                db_manager.index_document("patent_faqs", patent_docs, {"source": patent_pdf})
            else:
                st.error(f"Patent FAQ PDF not found at {patent_pdf}")
            
            if os.path.exists(bis_pdf):
                bis_docs = db_manager.load_pdf(bis_pdf)
                db_manager.index_document("bis_faqs", bis_docs, {"source": bis_pdf})
            else:
                st.error(f"BIS FAQ PDF not found at {bis_pdf}")
            
            # Save the vector database
            db_manager.save('vector_db')
        
        # Initialize other components
        response_generator = ResponseGenerator(db_manager)
        suggestion_engine = SuggestionEngine()
        
        return db_manager, response_generator, suggestion_engine
    
    except Exception as e:
        st.error(f"Error initializing components: {str(e)}")
        return None, None, None

# Initialize components
db_manager, response_generator, suggestion_engine = initialize_components()

if db_manager is None or response_generator is None or suggestion_engine is None:
    st.error("Failed to initialize the application. Please check the error messages above.")
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-header">Patent & BIS FAQ Assistant</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="welcome-message">
    👋 Welcome to the Patent & BIS FAQ Assistant!
    
    This AI-powered assistant can help you with questions about:
    - Patent-related queries
    - Bureau of Indian Standards (BIS) related queries
    
    Simply type your question or click on a suggested question below to get started!
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Suggested Questions</div>', unsafe_allow_html=True)
    
    # Patent-related questions
    st.markdown('<div class="section-header">Patent Questions</div>', unsafe_allow_html=True)
    patent_questions = [
        "What is a patent?",
        "How do I apply for a patent?",
        "What is the duration of a patent?",
        "What are the requirements for patentability?",
        "What is the patent application process?",
        "How much does it cost to file a patent?"
    ]
    
    # Store selected question in session state
    if 'selected_question' not in st.session_state:
        st.session_state.selected_question = None
    
    for question in patent_questions:
        if st.button(question, key=f"patent_{question}"):
            st.session_state.selected_question = question
            st.session_state.chat_history.add_message("user", question)
            st.rerun()
    
    # BIS-related questions
    st.markdown('<div class="section-header">BIS Questions</div>', unsafe_allow_html=True)
    bis_questions = [
        "What is BIS certification?",
        "How do I get BIS certification?",
        "What are BIS standards?",
        "What products require BIS certification?",
        "What is the BIS certification process?",
        "How long does BIS certification take?"
    ]
    
    for question in bis_questions:
        if st.button(question, key=f"bis_{question}"):
            st.session_state.selected_question = question
            st.session_state.chat_history.add_message("user", question)
            st.rerun()
    
    # Clear chat history button
    if st.button("Clear Chat History", key="clear_chat"):
        st.session_state.chat_history.clear()
        st.session_state.selected_question = None
        st.rerun()

# Main content area
st.title("💬 Chat with Patent & BIS Assistant")

# Chat input with custom styling
user_input = st.chat_input("Type your question here...", key="chat_input")

# Process user input (either from chat or sidebar)
current_question = user_input if user_input else st.session_state.selected_question

# Process new question if any
if current_question:
    # Add user question to chat history
    st.session_state.chat_history.add_message("user", current_question)
    
    # Generate response
    with st.spinner("Thinking..."):
        try:
            # Get response from the generator
            response = response_generator.generate_response(current_question)
            
            if response and response["answer"]:
                # Add assistant response to chat history
                st.session_state.chat_history.add_message("assistant", response["answer"], response["source"])
            else:
                # Add no answer message to chat history
                no_answer_msg = "Sorry, I don't have an answer for that. Here are some related questions you might want to ask:"
                st.session_state.chat_history.add_message("assistant", no_answer_msg)
        
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            st.session_state.chat_history.add_message("assistant", error_msg)
    
    # Clear the selected question after processing
    st.session_state.selected_question = None

# Display chat history in clean Q&A format
chat_history = st.session_state.chat_history.get_history()
for i in range(0, len(chat_history), 2):
    if i + 1 < len(chat_history):
        # Display question
        with st.chat_message("user"):
            st.markdown(f"**{chat_history[i]['content']}**")
        
        # Display answer
        with st.chat_message("assistant"):
            st.markdown(chat_history[i + 1]['content'])
            if "source" in chat_history[i + 1] and chat_history[i + 1]["source"]:
                source_text = chat_history[i + 1]["source"]
                if source_text.startswith("file:///"):
                    source_text = source_text.replace("file:///", "")
                st.markdown(f'<a href="{chat_history[i + 1]["source"]}" target="_blank" class="source-link">📄 Source Document</a>', 
                           unsafe_allow_html=True)
    else:
        # Handle case where there's only a question without an answer
        with st.chat_message("user"):
            st.markdown(f"**{chat_history[i]['content']}**")

# Save chat history
st.session_state.chat_history.save() 