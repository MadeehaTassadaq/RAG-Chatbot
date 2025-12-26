# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot system that allows users to ask questions about documentation content and receive contextually relevant answers.

## Features

- **RAG System**: Uses vector embeddings to retrieve relevant content from documentation
- **FastAPI Backend**: Robust API server with Cohere integration for embeddings
- **Docusaurus Frontend**: Modern documentation site with integrated chatbot
- **Qdrant Vector Database**: Efficient similarity search for content retrieval
- **Text Selection**: Ability to ask questions about selected text

## Architecture

- **Frontend**: Docusaurus-based documentation site with React chatbot component
- **Backend**: FastAPI server handling RAG queries and vector database operations
- **Storage**: Qdrant vector database for document embeddings
- **AI**: Cohere for text embeddings and generation

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Run the backend server:
```bash
python run_server.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your backend URL
```

4. Start the development server:
```bash
npm start
```

## Configuration

The system requires the following environment variables:

### Backend (.env)
- `COHERE_API_KEY`: Your Cohere API key
- `QDRANT_URL`: URL for your Qdrant instance
- `QDRANT_API_KEY`: API key for Qdrant
- `OPENAI_API_KEY`: Your OpenAI API key (optional, if using OpenAI)

### Frontend (.env)
- `REACT_APP_BACKEND_URL`: URL of the backend API server

## Content Ingestion

To ingest content into the RAG system:

1. Ensure your backend is running with proper environment variables
2. Run the ingestion script:
```bash
cd backend
python ingest.py
```

The script will crawl the specified documentation site, chunk the content based on headers, generate embeddings, and store them in Qdrant.

## API Endpoints

- `POST /query` - Query the RAG system with a question
- `GET /health` - Check the health status of the API

## Deployment

### Backend
- Deploy to Render.com using the provided `render.yaml`
- Ensure environment variables are configured in the deployment

### Frontend
- Deploy to Azure Static Web Apps
- Configure the backend URL in environment variables

## Technologies Used

- Python 3.11+
- FastAPI
- Cohere
- Qdrant
- Docusaurus
- React
- Node.js 18+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Specify your license here]