# Patent & BIS FAQ Assistant

An intelligent FAQ assistant that provides information about Patents and BIS (Bureau of Indian Standards) regulations.

## Features
- Real-time chat interface
- Intelligent source selection
- Accurate answers based on official documentation
- Source attribution
- Example questions

## Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key in `.streamlit/secrets.toml`
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Deployment
This application is deployed on Streamlit Cloud. Visit the live application at: [Your Streamlit Cloud URL]

## Project Structure
```
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/           # Streamlit configuration
│   └── secrets.toml      # API keys and secrets
├── data/                 # PDF documents
├── services/            # Business logic
├── utils/               # Utility functions
└── README.md            # Project documentation
``` 