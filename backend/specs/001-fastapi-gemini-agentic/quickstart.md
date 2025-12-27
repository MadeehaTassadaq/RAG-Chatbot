# Quickstart Guide

## Prerequisites

- Python 3.11+
- uv package manager
- Access to the following APIs:
  - Google Gemini API (with valid API key)
  - Cohere API (for embeddings)
  - Qdrant vector database (with URL and API key)
  - Neon Postgres database (with connection URL)

## Setup

### 1. Clone and Navigate to Project
```bash
git clone <your-repo-url>
cd <project-directory>
```

### 2. Install Dependencies with uv
```bash
# Install uv if not already installed
pip install uv

# Install project dependencies
uv pip install -r requirements.txt
# Or if using pyproject.toml
uv sync
```

### 3. Environment Configuration
Create a `.env` file with the following variables:
```env
GEMINI_API_KEY=your_gemini_api_key
COHERE_API_KEY=your_cohere_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=your_collection_name
NEON_DATABASE_URL=your_neon_database_url
```

## Running the Application

### Development
```bash
# Run with auto-reload for development
uv run python main.py
# Or using uvicorn directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
# Run with uvicorn in production mode
uv run uvicorn main:app --host 0.0.0.0 --port $PORT
```

## API Usage

### 1. Start a New Conversation
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key principles of humanoid robotics?"
  }'
```

### 2. Continue a Conversation
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you elaborate on the control systems?",
    "session_id": "your-session-id-from-previous-response"
  }'
```

### 3. Add Selection Context
```bash
curl -X POST http://localhost:8000/api/chat/selection \
  -H "Content-Type: application/json" \
  -d '{
    "selected_text": "The primary control system uses inverse kinematics to determine joint angles.",
    "session_id": "your-session-id"
  }'
```

### 4. Check Health
```bash
curl http://localhost:8000/health
```

## Deployment

### Render Setup
1. Create a new Web Service on Render
2. Connect to your GitHub repository
3. Set the build command to: `pip install uv && uv pip install -r requirements.txt`
4. Set the start command to: `uv run uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all required environment variables in the Render dashboard

### Environment Variables for Deployment
Make sure to set these in your deployment environment:
- `GEMINI_API_KEY`
- `COHERE_API_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION`
- `NEON_DATABASE_URL`

## Testing

### Run Unit Tests
```bash
uv run pytest tests/
```

### Run Integration Tests
```bash
uv run pytest tests/integration/
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Verify all API keys are correctly set in environment variables
2. **Database Connection**: Ensure NEON_DATABASE_URL is properly formatted
3. **Qdrant Connection**: Check QDRANT_URL and QDRANT_API_KEY are correct
4. **CORS Issues**: If using from a different domain, ensure your frontend URL is in the CORS middleware

### Enable Logging
Add the following to your environment for debugging:
```env
LOG_LEVEL=DEBUG
```