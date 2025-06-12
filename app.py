import streamlit as st
import os
from dotenv import load_dotenv
from utils.db_manager import VectorDBManager
from services.response_generator import ResponseGenerator
from services.suggestion_engine import SuggestionEngine
from utils.chat_history import ChatHistory

# Load environment variables
load_dotenv()

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = ChatHistory()

# Page config
st.set_page_config(
    page_title="Patent & BIS FAQ Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #1a1a1a;
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
    }
    .source-link {
        color: #00ff00;
        text-decoration: none;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    .source-link:hover {
        text-decoration: underline;
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

# Title
st.title("Patent & BIS FAQ Assistant 🤖")

# Description
st.markdown("""
    This AI assistant can help you with questions about:
    - Patent-related queries
    - Bureau of Indian Standards (BIS) related queries
    
    Simply type your question below and get instant answers with source references!
""")

# Chat input
user_input = st.chat_input("Ask your question here...")

# Display chat history
for message in st.session_state.chat_history.get_history():
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "source" in message:
            st.markdown(f'<a href="{message["source"]}" target="_blank" class="source-link">Source: {message["source"]}</a>', 
                       unsafe_allow_html=True)

# Process user input
if user_input:
    # Add user message to chat
    st.session_state.chat_history.add_message("user", user_input)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Get response from the generator
                response = response_generator.generate_response(user_input)
                
                # Display response
                st.markdown(response["answer"])
                
                # Display source if available
                if response["source"]:
                    st.markdown(f'<a href="{response["source"]}" target="_blank" class="source-link">Source: {response["source"]}</a>', 
                               unsafe_allow_html=True)
                
                # Add assistant message to chat history
                st.session_state.chat_history.add_message("assistant", response["answer"], response["source"])
                
                # Generate and display suggestions
                suggestions = suggestion_engine.generate_suggestions(user_input, response["answer"])
                if suggestions:
                    st.markdown("---")
                    st.markdown("**You might also want to know:**")
                    for suggestion in suggestions:
                        if st.button(suggestion, key=suggestion):
                            st.session_state.chat_history.add_message("user", suggestion)
                            st.experimental_rerun()
            
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

# Save chat history
st.session_state.chat_history.save() 