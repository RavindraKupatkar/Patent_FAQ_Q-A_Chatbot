import asyncio
import sys
import warnings
import logging
import os

def initialize_app():
    # Configure logging
    logging.basicConfig(level=logging.ERROR)
    logging.getLogger('streamlit').setLevel(logging.ERROR)
    logging.getLogger('torch').setLevel(logging.ERROR)
    logging.getLogger('asyncio').setLevel(logging.ERROR)

    # Suppress all warnings
    warnings.filterwarnings("ignore")
    
    # Set environment variable to disable torch warnings
    os.environ['PYTHONWARNINGS'] = 'ignore'
    
    # Handle asyncio event loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception:
        pass

if __name__ == "__main__":
    initialize_app() 