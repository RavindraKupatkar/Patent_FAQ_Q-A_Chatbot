from groq import Groq
from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

class ResponseGenerator:
    def __init__(self, db_manager, temperature=0.7, max_tokens=500, model="deepseek-r1-distill-llama-70b"):
        self.db_manager = db_manager
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model
        
        # Try Streamlit secrets first, then environment variables
        api_key = st.secrets.get("GROQ_API_KEY", os.getenv('GROQ_API_KEY'))
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables or Streamlit secrets")
        
        self.client = Groq(api_key=api_key)
    
    def update_config(self, temperature=None, max_tokens=None, model=None):
        """Update configuration parameters."""
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if model is not None:
            self.model = model
    
    def get_config(self):
        """Get current configuration."""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model": self.model
        }
    
    def generate_response(self, query, temperature=None, max_tokens=None):
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
            
            # Use per-call parameters if provided, otherwise use instance defaults
            call_temperature = temperature if temperature is not None else self.temperature
            call_max_tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # Generate response using Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides information about patents and BIS standards. Use the provided context to answer questions accurately."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                temperature=call_temperature,
                max_tokens=call_max_tokens
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