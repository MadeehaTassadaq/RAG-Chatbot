#!/usr/bin/env python3
"""
Script to run the RAG chatbot server without immediate database initialization.
"""

import os
# Load environment variables from .env file
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"\'')

import uvicorn

if __name__ == "__main__":
    # Get port from environment variable for Render deployment, default to 8000
    port = int(os.getenv("PORT", 8000))
    # Run the FastAPI server
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)