# Agent Context for 1-fastapi-gemini-agentic

## Current Implementation Plan

# Implementation Plan

## Feature
FastAPI Backend Refactor with OpenAI Agent SDK for Gemini API Integration

## Technical Context
The current implementation uses the OpenAI SDK with a custom base URL to interface with the Gemini API. The system already has:
- API endpoints at /api/chat and /api/chat/selection
- Neon Postgres database for persistence
- Qdrant vector database for document retrieval
- Cohere for embeddings
- Session management with UUID-based identifiers

The refactoring will enhance the agentic reasoning capabilities while maintaining existing API contracts and persistence mechanisms. The main changes involve:
- Updating to use AsyncOpenAI client for better performance
- Potentially updating dependency management with uv
- Enhancing the RAG agent logic for better agentic behavior

## Architecture Decision Summary
- Continue using OpenAI SDK with custom Gemini endpoint (already implemented)
- Maintain existing API endpoints (/api/chat, /api/chat/selection)
- Keep Neon Postgres for persistence
- Enhance RAG logic for better context handling
- Use AsyncOpenAI for improved performance

## Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│  FastAPI Server  │───▶│  External APIs  │
│ (Azure Static   │    │                  │    │                 │
│  Web App)       │    │ • /api/chat      │    │ • Gemini API    │
│                 │    │ • /api/chat/     │    │ • Cohere API    │
│                 │    │   selection      │    │ • Qdrant        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Neon Postgres   │
                    │  (Persistence)   │
                    └──────────────────┘
```

Components:
- **API Layer**: FastAPI with CORS middleware for Azure frontend compatibility
- **Agent Layer**: RAGAgent class handling retrieval and response generation
- **Persistence Layer**: Neon Postgres for session and chat history
- **Vector Layer**: Qdrant for document retrieval
- **Embedding Layer**: Cohere for generating document embeddings
- **AI Layer**: Gemini API via OpenAI SDK format

## Implementation Phases

### Phase 1: Dependency and Setup Updates
1. Update requirements.txt with proper versions
2. Configure uv for package management if not already used
3. Add/remove dependencies as needed (add openai if not present, remove google-generativeai if present)

### Phase 2: Code Refactoring
1. Update main.py to use AsyncOpenAI client
2. Enhance RAGAgent class with improved agentic reasoning patterns
3. Ensure all endpoints maintain existing contracts (/api/chat, /api/chat/selection)

### Phase 3: Testing and Validation
1. Unit tests for updated components
2. Integration tests for API endpoints
3. Performance validation

## Data Model
### Session
- session_id (VARCHAR): Unique identifier for the session
- user_id (VARCHAR): Optional user identifier
- created_at (TIMESTAMP): Session creation time
- last_active (TIMESTAMP): Last activity timestamp
- context (TEXT): JSON string containing session context

### ChatHistory
- id (SERIAL): Auto-incrementing primary key
- session_id (VARCHAR): Foreign key to sessions table
- role (VARCHAR): Message role (user/assistant)
- content (TEXT): Message content
- timestamp (TIMESTAMP): Message creation time

## API Contracts

### POST /api/chat
Request:
```json
{
  "message": "string",
  "session_id": "string (optional)"
}
```

Response:
```json
{
  "response": "string",
  "session_id": "string",
  "citations": ["string"]
}
```

### POST /api/chat/selection
Request:
```json
{
  "selected_text": "string",
  "session_id": "string"
}
```

Response:
```json
{
  "status": "string",
  "session_id": "string"
}
```

### GET /health
Response:
```json
{
  "status": "string"
}
```

## Infrastructure
- Python 3.11+ runtime
- uv package manager
- Neon Postgres database
- Qdrant vector database
- Cohere API for embeddings
- Google Gemini API
- Deployment on Render

## Testing Strategy
- Unit tests for RAGAgent functionality (retrieval, response generation, citation extraction)
- Integration tests for API endpoints with mocked external services
- End-to-end tests for complete conversation flow
- Performance tests to validate response times under load
- Error condition tests for API failures and edge cases

## Risk Analysis
- **API Key Issues**: Implement proper error handling and graceful degradation when external APIs are unavailable
- **Performance Degradation**: Use AsyncOpenAI and optimize database queries to maintain response times
- **Data Consistency**: Ensure proper transaction handling for database operations
- **Dependency Conflicts**: Carefully manage package versions to avoid conflicts

## Success Criteria
- API response time under 5 seconds for 95% of requests
- All existing functionality continues to work without regression
- Proper error handling for external API failures
- Successful processing of 99% of valid requests
- Maintained backward compatibility with existing frontend

## Research Tasks
- Dependency management with uv: Research shows project should adopt uv for package management as specified in requirements
- OpenAI package version: Research indicates using openai>=1.0.0 for compatibility with OpenAI SDK format for Gemini API
- Google-generativeai package: Research shows this package is not currently used in existing codebase

## Open Questions
- Agentic reasoning patterns: Research indicates enhancing current RAG approach with better context management and session handling
- Performance requirements: Research confirms maintaining existing targets (sub-5 second responses for 95% of requests) is appropriate

## Technology Stack
- FastAPI
- OpenAI SDK (with Gemini)
- Neon Postgres
- Qdrant Vector Database
- Cohere for embeddings