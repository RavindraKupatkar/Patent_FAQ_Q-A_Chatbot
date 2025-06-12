import streamlit as st
from utils.document_loader import load_pdf
from utils.db_manager import VectorDBManager
from services.response_generator import ResponseGenerator
from services.retrieval import SuggestionEngine
from utils.chat_history import ChatHistory
import os

# Set page config
st.set_page_config(
    page_title="Patent & BIS FAQ Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stTextInput>div>div>input {
        background-color: white;
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
        color: white;
    }
    .chat-message.assistant {
        background-color: #f0f2f6;
    }
    .chat-message .content {
        display: flex;
        flex-direction: column;
    }
    .chat-message .source {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = VectorDBManager()
    st.session_state.response_generator = ResponseGenerator()
    st.session_state.chat_history = ChatHistory()
    st.session_state.suggestion_engine = SuggestionEngine()
    
    # Create Collections
    st.session_state.patent_collection = st.session_state.db_manager.create_collection("patent_faqs")
    st.session_state.bis_collection = st.session_state.db_manager.create_collection("bis_faqs")
    
    # Define file paths
    PATENT_FAQ_PATH = os.path.join("data", "Final_FREQUENTLY_ASKED_QUESTIONS_-PATENT.pdf")
    BIS_FAQ_PATH = os.path.join("data", "FINAL_FAQs_June_2018.pdf")
    
    # Load and index documents
    with st.spinner("Loading Patent FAQs..."):
        patent_text = load_pdf(PATENT_FAQ_PATH)
        st.session_state.db_manager.index_document(
            "patent_faqs",
            patent_text,
            {"source": PATENT_FAQ_PATH}
        )
    
    with st.spinner("Loading BIS FAQs..."):
        bis_text = load_pdf(BIS_FAQ_PATH)
        st.session_state.db_manager.index_document(
            "bis_faqs",
            bis_text,
            {"source": BIS_FAQ_PATH}
        )
    
    # Save the vector database
    st.session_state.db_manager.save()

# Header
st.title("🤖 Patent & BIS FAQ Assistant")
st.markdown("""
    Ask questions about Patents and BIS (Bureau of Indian Standards) regulations. 
    The assistant will provide accurate answers based on official documentation.
""")

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
        This assistant can help you with:
        - Patent application process
        - BIS certification requirements
        - Patent fees and timelines
        - BIS standards and compliance
    """)
    
    st.header("Example Questions")
    st.markdown("""
        - What is the process of applying for a patent?
        - How long does it take to get a patent granted?
        - What is the validity period of a BIS certificate?
        - How can I get BIS certification for my product?
    """)

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your question here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Determine which collection to query
    query = prompt.lower()
    patent_keywords = ['patent', 'intellectual property', 'ip', 'invention', 'patent application']
    bis_keywords = ['bis', 'bureau of indian standards', 'standard', 'certification', 'quality']
    
    patent_score = sum(1 for keyword in patent_keywords if keyword in query)
    bis_score = sum(1 for keyword in bis_keywords if keyword in query)
    
    # Get response
    with st.spinner("Thinking..."):
        if patent_score > bis_score:
            results = st.session_state.db_manager.query(st.session_state.patent_collection, prompt)
        elif bis_score > patent_score:
            results = st.session_state.db_manager.query(st.session_state.bis_collection, prompt)
        else:
            patent_results = st.session_state.db_manager.query(st.session_state.patent_collection, prompt)
            bis_results = st.session_state.db_manager.query(st.session_state.bis_collection, prompt)
            results = patent_results + bis_results
        
        context = ""
        sources = set()
        for result in results:
            context += f"{result['text']}\n\n"
            sources.add(result['metadata'].get("source", ""))
        
        response = st.session_state.response_generator.generate(
            context,
            prompt,
            st.session_state.chat_history.get(),
            list(sources)
        )
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
    
    # Update chat history
    st.session_state.chat_history.add("user", prompt)
    st.session_state.chat_history.add("assistant", response) 