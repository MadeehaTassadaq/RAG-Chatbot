#!/usr/bin/env python3
"""
Main FastAPI application for the RAG Agent Backend.
Implements API endpoints for chat interactions and selection handling.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import contextmanager
import json


# Database connection setup
DATABASE_URL = os.getenv("NEON_DATABASE_URL")

def get_db_connection():
    """Get a connection to the Neon Postgres database."""
    return psycopg2.connect(DATABASE_URL)

# Create tables if they don't exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            context TEXT
        )
    """)

    # Create chat_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) REFERENCES sessions(session_id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

# Initialize database
init_db()


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


import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
import google.generativeai as genai


class RAGAgent:
    """RAG Agent that handles retrieval, response generation, and citations using Gemini."""

    def __init__(self):
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = os.getenv("QDRANT_COLLECTION", "humanoid_robotics_docs")

        # Initialize Cohere client for embeddings
        self.cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))

        # Initialize Google Gemini client
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')  # Using Gemini Pro model

        # System prompt
        self.system_prompt = "You are the Physical AI and Humanoid Robotics Expert. Answer strictly using provided book context or highlighted text. Cite chapters."

    def retrieve_content(self, query: str, limit: int = 3) -> List[Dict]:
        """Retrieve relevant content from Qdrant based on the query."""
        try:
            # Generate embedding for the query using Cohere
            response = self.cohere_client.embed(
                texts=[query],
                model="embed-english-v3.0",
                input_type="search_query"
            )
            query_embedding = response.embeddings[0]

            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )

            # Extract content from search results
            retrieved_content = []
            for result in search_result:
                payload = result.payload
                retrieved_content.append({
                    'content': payload.get('content', ''),
                    'url': payload.get('url', ''),
                    'header': payload.get('header', ''),
                    'header_type': payload.get('header_type', ''),
                    'content_type': payload.get('content_type', ''),
                    'score': result.score
                })

            return retrieved_content
        except Exception as e:
            print(f"Error retrieving content: {e}")
            return []

    def generate_response(self, user_query: str, chat_history: List[Dict], additional_context: Dict = None) -> tuple[str, List[str]]:
        """
        Generate a response using Google Gemini with retrieved context.

        Returns:
            - Generated response text
            - List of citations (chapter references)
        """
        # Retrieve relevant content from Qdrant
        retrieved_content = self.retrieve_content(user_query)

        # Build context for the assistant
        context_parts = []

        # Add system prompt
        context_parts.append(self.system_prompt)

        # Add retrieved content from the book
        if retrieved_content:
            context_parts.append("Relevant book content:")
            for i, content in enumerate(retrieved_content):  # Include all retrieved results
                context_parts.append(f"Source: {content['url']}")
                context_parts.append(f"Section: {content['header']}")
                context_parts.append(f"Content: {content['content'][:500]}...")  # Limit content length

        # Add user-highlighted text if available
        if additional_context and 'selected_texts' in additional_context:
            context_parts.append("User-highlighted text (primary context):")
            for selection in additional_context['selected_texts'][-3:]:  # Last 3 selections
                context_parts.append(f"Highlighted: {selection['text']}")

        # Add chat history if available
        if chat_history:
            context_parts.append("Previous conversation:")
            for message in chat_history[-5:]:  # Last 5 messages
                role = message['role'].upper()
                content = message['content']
                context_parts.append(f"{role}: {content}")

        # Combine all context
        full_context = "\n\n".join(context_parts)

        # Create the prompt for Gemini
        prompt = f"{full_context}\n\nUser Query: {user_query}\n\nPlease provide a helpful response based on the provided context, citing relevant chapters when possible."

        try:
            # Generate response using Google Gemini
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000,
                }
            )

            # Extract the response text
            assistant_response = response.text if response.text else "I couldn't generate a proper response. Please try again."

            # Extract citations (try to identify chapter references)
            citations = self.extract_citations(assistant_response, retrieved_content)

            return assistant_response, citations
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I encountered an error while processing your request. Please try again.", []

    def extract_citations(self, response: str, retrieved_content: List[Dict]) -> List[str]:
        """
        Extract citations from the response based on the retrieved content.
        This is a simple implementation - in a real system, you'd want more sophisticated citation logic.
        """
        citations = set()

        # Look for URLs in the retrieved content that might be cited
        for content in retrieved_content:
            url = content.get('url', '')
            if url and url in response:
                citations.add(url)

            header = content.get('header', '')
            if header and header.lower() in response.lower():
                citations.add(f"Section: {header}")

        # Convert to list and limit to top 3 citations
        return list(citations)[:3]


app = FastAPI(title="RAG Agent Backend", version="1.0.0")

# Add CORS middleware to allow requests from Azure Static Web App
app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://agreeable-sand-0efbb301e.4.azurestaticapps.net'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def get_session_context(session_id: str) -> Dict:
    """Retrieve session context from database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT context FROM sessions WHERE session_id = %s",
            (session_id,)
        )
        result = cursor.fetchone()
        if result:
            context_json = result[0]
            if context_json:
                return json.loads(context_json)
            else:
                return {}
        else:
            return {}
    except json.JSONDecodeError:
        return {}
    finally:
        cursor.close()
        conn.close()


def update_session_context(session_id: str, context: Dict):
    """Update session context in database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        context_json = json.dumps(context)
        cursor.execute(
            "INSERT INTO sessions (session_id, context, last_active) VALUES (%s, %s, CURRENT_TIMESTAMP) "
            "ON CONFLICT (session_id) DO UPDATE SET context = %s, last_active = CURRENT_TIMESTAMP",
            (session_id, context_json, context_json)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def save_chat_message(session_id: str, role: str, content: str):
    """Save a chat message to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Ensure the session exists before inserting chat history
        # This creates the session if it doesn't exist
        cursor.execute(
            "INSERT INTO sessions (session_id, created_at, last_active) VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) "
            "ON CONFLICT (session_id) DO NOTHING",
            (session_id,)
        )

        # Now insert the chat message
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, content) VALUES (%s, %s, %s)",
            (session_id, role, content)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_chat_history(session_id: str) -> List[Dict]:
    """Retrieve chat history for a session."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT role, content, timestamp FROM chat_history WHERE session_id = %s ORDER BY timestamp ASC",
            (session_id,)
        )
        rows = cursor.fetchall()
        return [{"role": row[0], "content": row[1], "timestamp": row[2]} for row in rows]
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """Main chat endpoint that handles user queries and returns assistant responses."""
    # Create or validate session ID
    session_id = chat_request.session_id or str(uuid.uuid4())

    # Initialize the agent
    agent = RAGAgent()

    # Get session context
    context = get_session_context(session_id)

    # Get chat history for context
    history = get_chat_history(session_id)

    # Generate response using the agent
    try:
        response, citations = agent.generate_response(
            user_query=chat_request.message,
            chat_history=history,
            additional_context=context
        )

        # Save user message and assistant response to history
        save_chat_message(session_id, "user", chat_request.message)
        save_chat_message(session_id, "assistant", response)

        return ChatResponse(
            response=response,
            session_id=session_id,
            citations=citations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@app.post("/chat/selection", response_model=SelectionResponse)
async def handle_selection(selection_request: SelectionRequest):
    """Endpoint to handle user-highlighted text as primary context."""
    session_id = selection_request.session_id

    # Get current context
    context = get_session_context(session_id)

    # Update context with the selected text
    if 'selected_texts' not in context:
        context['selected_texts'] = []

    # Add the new selection
    context['selected_texts'].append({
        "text": selection_request.selected_text,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Update the session context
    update_session_context(session_id, context)

    return SelectionResponse(status="Selection saved successfully", session_id=session_id)


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