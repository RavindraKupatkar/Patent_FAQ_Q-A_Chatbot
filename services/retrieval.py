from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class SuggestionEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.questions = []

    def load_questions(self, questions):
        self.questions = questions
        if questions:
            self.question_vectors = self.vectorizer.fit_transform(questions)

    def get_suggestions(self, query, top_k=3):
        if not self.questions:
            return []
        
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.question_vectors)
        top_indices = np.argsort(similarities[0])[-top_k:][::-1]
        return [self.questions[i] for i in top_indices]