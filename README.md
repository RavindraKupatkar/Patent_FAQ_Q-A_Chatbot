# Patent & BIS FAQ Assistant

An intelligent FAQ assistant that provides information about Patents and BIS (Bureau of Indian Standards) regulations.

## Features
- 🤖 Real-time chat interface with AI-powered responses
- 📄 Intelligent document retrieval from PDF sources
- 🔍 Vector search with semantic similarity matching
- 💬 Clean, modern UI with suggested questions
- 📝 Chat history with source attribution
- 🎨 Customized dark theme optimized for readability

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone [your-repo-url]
   cd BB_assessment
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file or add your OpenAI API key to `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Streamlit Cloud Deployment

### Prerequisites
- GitHub repository with your code
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- OpenAI API key

### Deployment Steps

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Set main file path: `app.py`
   - Click "Deploy!"

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to your app settings
   - Navigate to "Secrets" section
   - Add your secrets in TOML format:
     ```toml
     OPENAI_API_KEY = "your-actual-api-key-here"
     ```

4. **Monitor Deployment**
   - Watch the deployment logs for any issues
   - Your app will be available at `https://[your-app-name].streamlit.app`

### Deployment Considerations

- **Data Persistence**: Vector database is cached using `@st.cache_resource`
- **API Rate Limits**: Consider OpenAI API usage limits
- **File Size**: Keep PDF files under Streamlit's file size limits
- **Performance**: First load may take time due to PDF processing

## Alternative Deployment Options

### Heroku
Add these files for Heroku deployment:
```bash
# Procfile
web: streamlit run app.py --server.port $PORT

# setup.sh
mkdir -p ~/.streamlit/
echo "[server]\nheadless = true\nport = $PORT\nenableCORS = false\n" > ~/.streamlit/config.toml
```

### Docker
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

## Project Structure
```
├── app.py                    # Main Streamlit application
├── main.py                   # CLI version (for testing)
├── requirements.txt          # Python dependencies
├── .streamlit/              # Streamlit configuration
│   ├── config.toml          # App configuration
│   └── secrets.toml         # API keys and secrets
├── data/                    # PDF documents
│   ├── Final_FREQUENTLY_ASKED_QUESTIONS_-PATENT.pdf
│   └── FINAL_FAQs_June_2018.pdf
├── services/               # Business logic
│   ├── response_generator.py
│   ├── suggestion_engine.py
│   └── retrieval.py
├── utils/                  # Utility functions
│   ├── db_manager.py
│   ├── document_loader.py
│   └── chat_history.py
└── README.md               # This file
```

## Technologies Used

- **Frontend**: Streamlit
- **AI/ML**: OpenAI GPT-3.5-turbo, OpenAI Embeddings
- **Vector Database**: Custom implementation with cosine similarity
- **PDF Processing**: PyPDF2
- **Styling**: Custom CSS with dark theme

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |

## Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Ensure your API key is set in `.streamlit/secrets.toml`
   - For Streamlit Cloud, add it in the Secrets section

2. **"PDF files not found"**
   - Ensure PDF files are in the `data/` directory
   - Check file paths in the code

3. **"Slow initial loading"**
   - First run processes PDFs and creates embeddings
   - Subsequent runs use cached data

4. **"Streamlit Cloud build fails"**
   - Check requirements.txt for compatibility
   - Review deployment logs for specific errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is licensed under the MIT License.
