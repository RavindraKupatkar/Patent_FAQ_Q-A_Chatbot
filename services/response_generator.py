import openai
from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

class ResponseGenerator:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # Try Streamlit secrets first, then environment variables
        api_key = st.secrets.get("OPENAI_API_KEY", os.getenv('OPENAI_API_KEY'))
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate_response(self, query):
        """Generate a response based on the user's query."""
        try:
            # Search for relevant documents
            patent_results = self.db_manager.search("patent_faqs", query, limit=2)
            bis_results = self.db_manager.search("bis_faqs", query, limit=2)
            
            # Combine and format the context
            context = ""
            if patent_results:
                context += "Patent Information:\n" + "\n".join([doc.page_content for doc in patent_results]) + "\n\n"
            if bis_results:
                context += "BIS Information:\n" + "\n".join([doc.page_content for doc in bis_results])
            
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides information about patents and BIS standards. Use the provided context to answer questions accurately."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Get the source document if available
            source = None
            if patent_results:
                source = patent_results[0].metadata.get('source')
            elif bis_results:
                source = bis_results[0].metadata.get('source')
            
            return {
                "answer": response.choices[0].message.content.strip(),
                "source": source
            }
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error while processing your request. Please try again.",
                "source": None
            }