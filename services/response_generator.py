from openai import OpenAI

class ResponseGenerator:
    def __init__(self):
        self.client = OpenAI()
        self.system_prompt = """ 
        You are a patent and BIS regulations FAQ assistant. 
        Strictly use only the provided context to answer questions.
        If answer is not available in the context, respond with: "I don't have information about this. Here are some related questions:"
        If you have a valid answer from the context, provide it without mentioning suggested questions.
        Think step-by-step:
        step 1: Firstly understand the question.
        step 2: Now you need to find-out key-words from the questions.
        step 3: Now you need to search those key-words throughout the provided context.
        step 4: If no answer is found, you need to find-out 3 - 4 related questions from the context.
        step 5: Return the answer or suggested questions based on whether an answer was found.

        Format your response as follows:
        1. If you have an answer:
           - Provide the answer
           - At the end, add "Source: [source URL]" (only for sources that provided the answer)
        
        2. If no answer is found:
           - Say "I don't have information about this. Here are some related questions:"
           - List the related questions
           - Do not include source URLs
        """

    def generate(self, context, query, history, sources):
        messages = [
            {"role": "system", "content": self.system_prompt},
            *history,
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.2
        )

        # Get the response content
        response_content = response.choices[0].message.content

        # Only append sources if the response doesn't indicate "no information"
        if "I don't have information about this" not in response_content and sources:
            # Format sources as a single line
            source_str = ", ".join(sources)
            return f"{response_content}\n\nSource: {source_str}"
        
        return response_content