# Data Model

## Entity Definitions

### Session
**Description**: Represents a user conversation session with context and metadata

**Fields**:
- `session_id`: VARCHAR(255) - Primary key, unique identifier for the session
- `user_id`: VARCHAR(255) - Optional identifier for the user
- `created_at`: TIMESTAMP - Time when the session was created
- `last_active`: TIMESTAMP - Time of the last activity in the session
- `context`: TEXT - JSON string containing session-specific context data

**Constraints**:
- `session_id` must be unique
- `created_at` defaults to current timestamp
- `last_active` defaults to current timestamp

**Relationships**:
- One-to-many with ChatHistory (one session can have many chat messages)

### ChatHistory
**Description**: Stores individual messages in a conversation

**Fields**:
- `id`: SERIAL - Primary key, auto-incrementing identifier
- `session_id`: VARCHAR(255) - Foreign key referencing Session.session_id
- `role`: VARCHAR(50) - Message role ('user' or 'assistant')
- `content`: TEXT - The actual message content
- `timestamp`: TIMESTAMP - Time when the message was created

**Constraints**:
- `role` must be either 'user' or 'assistant'
- `timestamp` defaults to current timestamp
- Foreign key constraint on `session_id` with cascade delete

**Relationships**:
- Many-to-one with Session (many chat messages belong to one session)

## Validation Rules

### Session Validation
- `session_id` must be a valid UUID format
- `user_id` if provided, should follow standard user identifier format
- `context` must be valid JSON if not null

### ChatHistory Validation
- `role` must be one of the allowed values ('user', 'assistant')
- `content` must not be empty
- `session_id` must reference an existing session

## State Transitions

### Session States
- New: Session is created when first message is sent without session_id
- Active: Session has recent activity (within last 24 hours)
- Inactive: Session has no activity for more than 24 hours

### ChatHistory States
- Pending: Message is being processed by the AI
- Completed: Message has been processed and response is available
- Error: Message processing failed

## Indexes

### Session Table
- Primary index on `session_id`
- Index on `last_active` for session cleanup operations

### ChatHistory Table
- Index on `session_id` for efficient session-based queries
- Index on `timestamp` for chronological ordering
- Composite index on (`session_id`, `timestamp`) for efficient retrieval of conversation history

## Data Flow

### Creation Flow
1. When a new message arrives without session_id → Create new Session with generated session_id
2. When a new message arrives with existing session_id → Validate session exists
3. Insert ChatHistory record with role='user' and the message content
4. Process the message through the RAG agent
5. Insert ChatHistory record with role='assistant' and the response content

### Retrieval Flow
1. Query ChatHistory table filtered by session_id
2. Order results by timestamp ascending to maintain conversation order
3. Combine messages to reconstruct conversation history

### Context Management
1. Session context is stored as JSON in the `context` field
2. Context includes selected/highlighted text from user interactions
3. Context is updated when user sends highlighted text via /api/chat/selection endpoint