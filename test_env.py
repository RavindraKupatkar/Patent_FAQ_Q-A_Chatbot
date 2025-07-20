from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get and print the API key (partially masked for security)
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    # Show first 4 and last 4 characters of the API key
    masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
    print(f"API Key found: {masked_key}")
    print(f"API Key length: {len(api_key)}")
else:
    print("No API key found in environment variables!") 