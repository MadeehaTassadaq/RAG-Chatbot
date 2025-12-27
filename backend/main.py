#!/usr/bin/env python3
"""
Main FastAPI application for the RAG Agent Backend.
Implements API endpoints for chat interactions and selection handling.
Uses AsyncOpenAI SDK for Gemini API integration with enhanced agentic reasoning.
"""

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Load environment variables from .env file
from dotenv import load_dotenv

# Get the directory where main.py is located
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path)

import asyncpg
import cohere
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http import models

app = FastAPI(title="RAG Agent Backend", version="1.1.0")

# Add CORS middleware to allow requests from Azure Static Web App
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agreeable-sand-0efbb301e.4.azurestaticapps.net",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection setup
DATABASE_URL = os.getenv("NEON_DATABASE_URL")


@asynccontextmanager
async def get_db_connection():
    """Get an async connection to the Neon Postgres database."""
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable not set")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()


async def init_db():
    """Initialize database tables asynchronously."""
    async with get_db_connection() as conn:
        # Create sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT
            )
        """)

        # Create chat_history table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) REFERENCES sessions(session_id) ON DELETE CASCADE,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_history_session_id
            ON chat_history(session_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp
            ON chat_history(timestamp)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_last_active
            ON sessions(last_active)
        """)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print(
            "Some features may not be available until database connection is established"
        )


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    citations: List[str]


class SelectionRequest(BaseModel):
    selected_text: str
    session_id: str


class SelectionResponse(BaseModel):
    status: str
    session_id: str


class RAGAgent:
    """RAG Agent that handles retrieval, response generation, and citations using OpenAI SDK for Gemini."""

    def __init__(self):
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = os.getenv("QDRANT_COLLECTION", "humanoid_robotics_docs")

        # Initialize Cohere client for embeddings
        self.cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))

        # Initialize OpenAI client for Gemini via OpenRouter
        self.client = OpenAI(
            api_key=os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("GEMINI_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

        # System prompt with enhanced agentic reasoning
        self.system_prompt = """You are the Physical AI and Humanoid Robotics Expert.
Your goal is to provide accurate, helpful responses based on the provided context.
Follow these reasoning patterns:

1. Analyze the user's question to understand what specific information they're seeking
2. Retrieve and review relevant document passages to find the best answer
3. If highlighted text is available, prioritize it as primary context
4. Synthesize information from multiple sources when possible
5. Provide clear, well-reasoned answers with proper citations

Always cite the sources (chapters/sections) you used to form your answer.
If you're unsure about something, acknowledge that uncertainty rather than guessing."""

    def retrieve_content(self, query: str, limit: int = 3) -> List[Dict]:
        """Retrieve relevant content from Qdrant based on the query."""
        try:
            # Generate embedding for the query using Cohere
            response = self.cohere_client.embed(
                texts=[query], model="embed-english-v3.0", input_type="search_query"
            )
            query_embedding = response.embeddings[0]

            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
            )

            # Extract content from search results
            retrieved_content = []
            for result in search_result:
                payload = result.payload
                retrieved_content.append(
                    {
                        "content": payload.get("content", ""),
                        "url": payload.get("url", ""),
                        "header": payload.get("header", ""),
                        "header_type": payload.get("header_type", ""),
                        "content_type": payload.get("content_type", ""),
                        "score": result.score,
                    }
                )

            return retrieved_content
        except Exception as e:
            print(f"Error retrieving content: {e}")
            return []

    def generate_response(
        self, user_query: str, chat_history: List[Dict], additional_context: Dict = None
    ) -> tuple[str, List[str]]:
        """
        Generate a response using OpenAI SDK with Gemini with retrieved context.

        Returns:
            - Generated response text
            - List of citations (chapter references)
        """
        # Retrieve relevant content from Qdrant
        retrieved_content = self.retrieve_content(user_query)

        # Build context for the assistant with enhanced reasoning
        context_parts = []

        # Add system prompt
        context_parts.append(self.system_prompt)

        # Add user-highlighted text if available (prioritized as primary context)
        if additional_context and "selected_texts" in additional_context:
            context_parts.append("USER HIGHLIGHTED TEXT (PRIMARY CONTEXT):")
            for selection in additional_context["selected_texts"][-5:]:
                context_parts.append(
                    f"[Highlighted at {selection.get('timestamp', 'unknown')}]"
                )
                context_parts.append(f"Text: {selection['text']}")

        # Add retrieved content from the document collection
        if retrieved_content:
            context_parts.append("RELEVANT DOCUMENT SECTIONS:")
            for i, content in enumerate(retrieved_content):
                context_parts.append(f"--- Source {i + 1} ---")
                context_parts.append(f"URL: {content['url']}")
                context_parts.append(f"Section: {content['header']}")
                context_parts.append(
                    f"Content: {content['content'][:800]}..."
                )

        # Add chat history if available
        if chat_history:
            context_parts.append("CONVERSATION HISTORY:")
            for message in chat_history[-8:]:
                role = message["role"].upper()
                content = message["content"]
                context_parts.append(f"{role}: {content}")

        # Combine all context
        full_context = "\n\n".join(context_parts)

        # Create the messages for OpenAI SDK
        messages = [
            {"role": "system", "content": full_context},
            {
                "role": "user",
                "content": f"User Query: {user_query}\n\nPlease provide a helpful, well-reasoned response based on the provided context. Cite relevant sources.",
            },
        ]

        try:
            # Generate response using OpenAI SDK with OpenRouter
            response = self.client.chat.completions.create(
                model=os.getenv("MODEL", "mistralai/devstral-2512:free"),
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
            )

            # Extract the response text
            assistant_response = (
                response.choices[0].message.content
                if response.choices[0].message.content
                else "I couldn't generate a proper response. Please try again."
            )

            # Extract citations
            citations = self.extract_citations(assistant_response, retrieved_content)

            return assistant_response, citations
        except Exception as e:
            print(f"Error generating response: {e}")
            return (
                "I encountered an error while processing your request. Please try again.",
                [],
            )

    def extract_citations(
        self, response: str, retrieved_content: List[Dict]
    ) -> List[str]:
        """
        Extract citations from the response based on the retrieved content.
        Enhanced citation extraction with better matching logic.
        """
        citations = set()

        # Look for URLs in the retrieved content that might be cited
        for content in retrieved_content:
            url = content.get("url", "")
            if url and url in response:
                citations.add(url)

            header = content.get("header", "")
            if header and header.lower() in response.lower():
                citations.add(f"Section: {header}")

        # Convert to list and limit to top 5 citations
        return list(citations)[:5]


async def get_session_context(session_id: str) -> Dict:
    """Retrieve session context from database asynchronously."""
    async with get_db_connection() as conn:
        try:
            result = await conn.fetchval(
                "SELECT context FROM sessions WHERE session_id = $1", session_id
            )
            if result:
                return json.loads(result)
            else:
                return {}
        except json.JSONDecodeError:
            return {}


async def update_session_context(session_id: str, context: Dict):
    """Update session context in database asynchronously."""
    async with get_db_connection() as conn:
        context_json = json.dumps(context)
        await conn.execute(
            "INSERT INTO sessions (session_id, context, last_active) VALUES ($1, $2, CURRENT_TIMESTAMP) "
            "ON CONFLICT (session_id) DO UPDATE SET context = $2, last_active = CURRENT_TIMESTAMP",
            session_id,
            context_json,
        )


async def save_chat_message(session_id: str, role: str, content: str):
    """Save a chat message to the database asynchronously."""
    async with get_db_connection() as conn:
        # Ensure the session exists before inserting chat history
        await conn.execute(
            "INSERT INTO sessions (session_id, created_at, last_active) VALUES ($1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) "
            "ON CONFLICT (session_id) DO NOTHING",
            session_id,
        )

        # Now insert the chat message
        await conn.execute(
            "INSERT INTO chat_history (session_id, role, content) VALUES ($1, $2, $3)",
            session_id,
            role,
            content,
        )


async def get_chat_history(session_id: str) -> List[Dict]:
    """Retrieve chat history for a session asynchronously."""
    async with get_db_connection() as conn:
        try:
            rows = await conn.fetch(
                "SELECT role, content, timestamp FROM chat_history WHERE session_id = $1 ORDER BY timestamp ASC",
                session_id,
            )
            return [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []


@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """Main chat endpoint that handles user queries and returns assistant responses."""
    # Create or validate session ID
    session_id = chat_request.session_id or str(uuid.uuid4())

    # Initialize the agent
    agent = RAGAgent()

    # Get session context
    context = await get_session_context(session_id)

    # Get chat history for context
    history = await get_chat_history(session_id)

    # Generate response using the agent
    try:
        response, citations = agent.generate_response(
            user_query=chat_request.message,
            chat_history=history,
            additional_context=context,
        )

        # Save user message and assistant response to history
        await save_chat_message(session_id, "user", chat_request.message)
        await save_chat_message(session_id, "assistant", response)

        return ChatResponse(
            response=response, session_id=session_id, citations=citations
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@app.post("/api/chat/selection", response_model=SelectionResponse)
async def handle_selection(selection_request: SelectionRequest):
    """Endpoint to handle user-highlighted text as primary context."""
    session_id = selection_request.session_id

    # Get current context
    context = await get_session_context(session_id)

    # Update context with the selected text
    if "selected_texts" not in context:
        context["selected_texts"] = []

    # Add the new selection with enhanced metadata
    context["selected_texts"].append(
        {
            "text": selection_request.selected_text,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
        }
    )

    # Update the session context
    await update_session_context(session_id, context)

    return SelectionResponse(
        status="Selection saved successfully", session_id=session_id
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint for Render health check."""
    return {"status": "Chatbot API is live"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
