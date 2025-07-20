# Streamlit Cloud Deployment Checklist

## ✅ Pre-Deployment Checklist

### Code Preparation
- [x] Main Streamlit app is in `app.py`
- [x] `requirements.txt` is updated with all dependencies
- [x] `.streamlit/config.toml` is configured with theme settings
- [x] Code handles both local `.env` and Streamlit Cloud secrets
- [x] Sensitive files are in `.gitignore`

### File Structure
- [x] All necessary files are present:
  - `app.py` (main application)
  - `requirements.txt` 
  - `.streamlit/config.toml`
  - `services/` directory
  - `utils/` directory
  - `README.md`

### Dependencies
- [x] All imports can be resolved from `requirements.txt`
- [x] No local-only dependencies
- [x] Compatible versions for Streamlit Cloud

## 🚀 Deployment Steps

### 1. GitHub Setup
- [ ] Push all code to GitHub repository
- [ ] Ensure repository is public or accessible to Streamlit Cloud
- [ ] Check that `.gitignore` excludes sensitive files

### 2. Streamlit Cloud Setup
- [ ] Go to [share.streamlit.io](https://share.streamlit.io)
- [ ] Sign in with GitHub account
- [ ] Click "New app"
- [ ] Select your repository
- [ ] Set main file: `app.py`
- [ ] Click "Deploy!"

### 3. Environment Configuration
- [ ] In Streamlit Cloud dashboard, go to app settings
- [ ] Navigate to "Secrets" tab
- [ ] Add OpenAI API key:
  ```toml
  OPENAI_API_KEY = "your-actual-api-key-here"
  ```
- [ ] Save secrets

### 4. Monitoring
- [ ] Watch deployment logs for errors
- [ ] Test the deployed application
- [ ] Verify all functionality works
- [ ] Check that PDFs load properly
- [ ] Test chat functionality

## 🔧 Post-Deployment

### Testing
- [ ] Ask a patent-related question
- [ ] Ask a BIS-related question
- [ ] Test suggested questions
- [ ] Verify source attribution
- [ ] Check chat history functionality
- [ ] Test clear chat feature

### Performance
- [ ] Monitor initial load times
- [ ] Check for any memory issues
- [ ] Verify caching works properly

### Maintenance
- [ ] Set up monitoring for API usage
- [ ] Plan for regular updates
- [ ] Document any issues encountered

## 🚨 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Import errors | Check `requirements.txt` versions |
| API key not found | Verify secrets configuration |
| PDF loading fails | Check file paths and permissions |
| Slow loading | Optimize caching and chunk sizes |
| Memory errors | Reduce batch sizes or implement pagination |

## 📝 Notes

- First deployment may take 5-10 minutes
- Initial app load will be slower due to PDF processing
- Vector database is cached for subsequent requests
- Monitor OpenAI API usage to avoid rate limits

## 🔗 Useful Links

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)
- [Streamlit Cloud Community](https://discuss.streamlit.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Your App URL](https://[your-app-name].streamlit.app) (replace after deployment)
