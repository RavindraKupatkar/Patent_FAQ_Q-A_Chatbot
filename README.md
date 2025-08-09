# Patent & BIS FAQ Assistant

An intelligent FAQ assistant with a modern, user-friendly interface that provides comprehensive information about Patents and BIS (Bureau of Indian Standards) regulations.

## Features

### 🎨 Enhanced User Interface
- **Modern Design**: Clean, professional interface with gradient backgrounds and smooth animations
- **Responsive Layout**: Optimized for both desktop and mobile devices
- **Interactive Elements**: Hover effects, smooth transitions, and visual feedback
- **Accessibility**: High contrast ratios and readable typography
- **Dark/Light Theme**: Customizable theme preferences

### 🤖 AI-Powered Features
- **Real-time Chat**: Instant responses with typing indicators
- **Smart Suggestions**: Context-aware question recommendations
- **Source Attribution**: Clear references to source documents
- **Multi-topic Support**: Handles both Patent and BIS queries intelligently

### 📊 Advanced Functionality
- **System Statistics**: Real-time performance metrics and usage analytics
- **Chat Export**: Download conversation history
- **Settings Panel**: Customizable response parameters
- **Feedback System**: User rating and comment collection
- **Status Indicators**: Real-time system health monitoring

### 🔍 Technical Features
- **Vector Search**: Semantic similarity matching with Pinecone
- **Intelligent Document Retrieval**: PDF processing and chunking
- **Embedding Flexibility**: Groq + open-source fallback architecture
- **Caching**: Optimized performance with intelligent caching
- **Error Handling**: Graceful error recovery and user feedback

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
   GROQ_API_KEY = "your-groq-api-key-here"
   PINECONE_API_KEY = "your-pinecone-api-key-here"
   PINECONE_ENV = "your-pinecone-environment"
   PINECONE_INDEX_NAME = "your-pinecone-index-name"
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## New UI Features

### Welcome Screen
- **Interactive Welcome**: Engaging welcome screen with feature highlights
- **Feature Cards**: Visual representation of system capabilities
- **Quick Start**: Easy navigation to get started immediately

### Enhanced Chat Interface
- **Message Bubbles**: Distinct styling for user and assistant messages
- **Typing Indicators**: Visual feedback during response generation
- **Source Links**: Clickable references to source documents
- **Empty State**: Helpful guidance when no messages exist

### Improved Sidebar
- **System Status**: Real-time status indicators
- **Quick Actions**: One-click access to common functions
- **Categorized Questions**: Organized suggestions by topic
- **Settings Panel**: Expandable configuration options

### Statistics Dashboard
- **Usage Metrics**: Total messages, success rates, and performance data
- **System Information**: Embedding provider and configuration details
- **Real-time Updates**: Live statistics and status monitoring

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
     GROQ_API_KEY = "your-actual-groq-api-key-here"
     PINECONE_API_KEY = "your-actual-pinecone-api-key-here"
     PINECONE_ENV = "your-pinecone-environment"
     PINECONE_INDEX_NAME = "your-pinecone-index-name"
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
├── components/              # Reusable UI components
│   └── ui_components.py     # UI component library
├── styles/                  # Theme and styling
│   └── theme.py            # Theme configuration
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
│   ├── embedder.py          # Enhanced embedding system
│   ├── ui_helpers.py        # UI utility functions
│   └── chat_history.py
└── README.md               # This file
```

## Technologies Used

- **Frontend**: Streamlit with custom CSS and modern UI components
- **AI/ML**: Groq API for responses, Groq/Sentence-transformers for embeddings
- **Vector Database**: Pinecone cloud vector database
- **PDF Processing**: PyPDF2
- **Styling**: Modern CSS with gradient themes, animations, and responsive design
- **Architecture**: Modular component-based design

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key | Yes |
| `PINECONE_API_KEY` | Your Pinecone API key | Yes |
| `PINECONE_ENV` | Pinecone environment | Yes |
| `PINECONE_INDEX_NAME` | Pinecone index name | Yes |

## Troubleshooting

### Common Issues

1. **"GROQ API key not found"**
   - Ensure your API key is set in `.streamlit/secrets.toml`
   - For Streamlit Cloud, add it in the Secrets section

2. **"Pinecone connection failed"**
   - Verify your Pinecone API key and environment settings
   - Check that your Pinecone index exists and is accessible

2. **"PDF files not found"**
   - Ensure PDF files are in the `data/` directory
   - Check file paths in the code

3. **"Slow initial loading"**
   - First run processes PDFs and creates embeddings
   - Subsequent runs use cached data

4. **"Streamlit Cloud build fails"**
   - Check requirements.txt for compatibility
   - Review deployment logs for specific errors
   - Ensure all environment variables are properly configured

## UI Customization

The new UI is highly customizable through the theme system:

### Theme Configuration
- Colors, fonts, and spacing are defined in `styles/theme.py`
- Easy to modify for different branding or preferences
- CSS custom properties for consistent styling

### Component System
- Reusable UI components in `components/ui_components.py`
- Consistent styling and behavior across the application
- Easy to extend with new components

### Responsive Design
- Mobile-first approach with responsive breakpoints
- Optimized for various screen sizes and devices
- Touch-friendly interface elements
## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is licensed under the MIT License.
