from typing import List
import openai
from dotenv import load_dotenv
import os

load_dotenv()

class SuggestionEngine:
    def __init__(self):
        self.patent_suggestions = [
            "What is the patent application process?",
            "How long does patent protection last?",
            "What are the costs involved in patent filing?",
            "What are the requirements for patentability?",
            "How do I check if my invention is patentable?"
        ]
        
        self.bis_suggestions = [
            "What is the BIS certification process?",
            "How long does BIS certification take?",
            "What are the costs of BIS certification?",
            "Which products need BIS certification?",
            "How do I apply for BIS certification?"
        ]

    def generate_suggestions(self, user_input, response):
        """Generate relevant follow-up questions based on user input and response."""
        suggestions = []
        
        # Add patent-related suggestions if the input contains patent-related keywords
        if any(keyword in user_input.lower() for keyword in ['patent', 'invention', 'intellectual property']):
            suggestions.extend(self.patent_suggestions[:2])
        
        # Add BIS-related suggestions if the input contains BIS-related keywords
        if any(keyword in user_input.lower() for keyword in ['bis', 'certification', 'standard']):
            suggestions.extend(self.bis_suggestions[:2])
        
        # If no specific suggestions were added, add one from each category
        if not suggestions:
            suggestions.extend([self.patent_suggestions[0], self.bis_suggestions[0]])
        
        return suggestions[:3]  # Return at most 3 suggestions 