from utils.document_loader import load_pdf
from utils.db_manager import VectorDBManager
from services.response_generator import ResponseGenerator
from services.retrieval import SuggestionEngine
from utils.chat_history import ChatHistory
import os

# Initialize vector database manager
db_manager = VectorDBManager()

# Create Collections
patent_collection = db_manager.create_collection("patent_faqs")
bis_collection = db_manager.create_collection("bis_faqs")

# Define file paths
PATENT_FAQ_PATH = "D:\\BuzzBoard_Assessment\\BB_assessment\\data\\Final_FREQUENTLY_ASKED_QUESTIONS_-PATENT.pdf"
BIS_FAQ_PATH = "D:\\BuzzBoard_Assessment\\BB_assessment\\data\\FINAL_FAQs_June_2018.pdf"

# Load and index documents
patent_text = load_pdf(PATENT_FAQ_PATH)
db_manager.index_document(
    "patent_faqs",
    patent_text,
    {"source": PATENT_FAQ_PATH}
)

bis_text = load_pdf(BIS_FAQ_PATH)
db_manager.index_document(
    "bis_faqs",
    bis_text,
    {"source": BIS_FAQ_PATH}
)

# Save the vector database
db_manager.save()

# Initialize other components
response_generator = ResponseGenerator()
chat_history = ChatHistory()
suggestion_engine = SuggestionEngine()

def determine_collection(query: str) -> str:
    """Determine which collection to query based on the question content."""
    query = query.lower()
    patent_keywords = ['patent', 'intellectual property', 'ip', 'invention', 'patent application']
    bis_keywords = ['bis', 'bureau of indian standards', 'standard', 'certification', 'quality']
    
    patent_score = sum(1 for keyword in patent_keywords if keyword in query)
    bis_score = sum(1 for keyword in bis_keywords if keyword in query)
    
    if patent_score > bis_score:
        return "patent_faqs"
    elif bis_score > patent_score:
        return "bis_faqs"
    else:
        return None  # If scores are equal or no keywords found

#main chat loop
while True:
    query = input("\nAsk Your Question: ")
    if query.lower() in ["exit", "quit"]:
        break

    # Determine which collection to query
    collection = determine_collection(query)
    
    #Retrieve relevant context
    context = ""
    sources = set()
    
    if collection == "patent_faqs":
        results = db_manager.query(patent_collection, query)
        for result in results:
            context += f"{result['text']}\n\n"
            sources.add(result['metadata'].get("source", ""))
    elif collection == "bis_faqs":
        results = db_manager.query(bis_collection, query)
        for result in results:
            context += f"{result['text']}\n\n"
            sources.add(result['metadata'].get("source", ""))
    else:
        # If no specific collection is determined, try both but with lower confidence
        patent_results = db_manager.query(patent_collection, query)
        bis_results = db_manager.query(bis_collection, query)
        
        # Combine results but with a note about uncertainty
        context = "Note: This question might be related to both Patent and BIS topics. Here are the most relevant answers:\n\n"
        for result in patent_results:
            context += f"{result['text']}\n\n"
            sources.add(result['metadata'].get("source", ""))
        for result in bis_results:
            context += f"{result['text']}\n\n"
            sources.add(result['metadata'].get("source", ""))

    #Generate Response
    response = response_generator.generate(
        context,
        query,
        chat_history.get(),
        list(sources)  # Pass sources to include in response
    )

    # Print the response (which already includes suggestions if no answer was found)
    print(f"\nAssistant: {response}")

    chat_history.add("user", query)
    chat_history.add("assistant", response)
    