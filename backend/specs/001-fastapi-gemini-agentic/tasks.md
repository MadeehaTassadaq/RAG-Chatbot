# Implementation Tasks

## Feature: FastAPI Backend Refactor with OpenAI Agent SDK for Gemini API Integration

### Phase 1: Setup
**Goal**: Initialize project structure and configure dependencies per implementation plan

- [x] T001 Set up project directory structure following implementation plan
- [x] T002 [P] Install uv package manager as specified in requirements
- [x] T003 [P] Update requirements.txt with openai>=1.0.0 and other dependencies
- [x] T004 [P] Create .env file template with required environment variables
- [x] T005 Verify current main.py structure and identify refactoring points

### Phase 2: Foundational
**Goal**: Implement blocking prerequisites for all user stories

- [x] T006 Create AsyncRAGAgent class with enhanced agentic reasoning patterns
- [x] T007 [P] Implement async database connection functions for Neon Postgres
- [x] T008 [P] Create async session management functions (get_session_context, update_session_context)
- [x] T009 [P] Create async chat history functions (save_chat_message, get_chat_history)
- [x] T010 [P] Set up async Qdrant client for document retrieval
- [x] T011 [P] Set up async Cohere client for embeddings
- [x] T012 [P] Configure AsyncOpenAI client with Gemini base URL: https://generativelanguage.googleapis.com/v1beta/openai/

### Phase 3: [US1] AI Interaction with Contextual Reasoning
**Goal**: Enable users to interact with an AI assistant that can reason about complex queries using contextual information from documents

**Independent Test Criteria**: Users can send messages to /api/chat and receive contextual responses based on stored documents

- [x] T013 [P] [US1] Create async chat endpoint POST /api/chat in main.py
- [x] T014 [P] [US1] Enhance AsyncRAGAgent.retrieve_content method with async operations
- [x] T015 [US1] Enhance AsyncRAGAgent.generate_response method with async operations and better context handling
- [x] T016 [US1] Implement async extract_citations method in AsyncRAGAgent
- [x] T017 [US1] Test basic chat functionality with mocked Qdrant and Gemini responses

### Phase 4: [US2] Text Highlighting Context
**Goal**: Enable users to highlight text in documents and have the AI use it as primary context for questions

**Independent Test Criteria**: Users can send highlighted text to /api/chat/selection and see it used as primary context in subsequent queries

- [x] T018 [P] [US2] Create async selection endpoint POST /api/chat/selection in main.py
- [x] T019 [US2] Enhance session context management to store selected text with timestamps
- [x] T020 [US2] Update AsyncRAGAgent to prioritize selected text context in response generation
- [x] T021 [US2] Test selection functionality and context integration with chat

### Phase 5: [US3] Conversation History Preservation
**Goal**: Preserve conversation history between sessions so users can continue discussions

**Independent Test Criteria**: Conversation history persists across multiple requests within the same session

- [x] T022 [P] [US3] Enhance database schema initialization with proper indexes
- [x] T023 [US3] Implement efficient async chat history retrieval with proper ordering
- [x] T024 [US3] Ensure session creation and management works correctly with UUID-based identifiers
- [x] T025 [US3] Test conversation history persistence across multiple requests

### Phase 6: [US4] Citation Provision
**Goal**: Provide citations for information so users can verify sources

**Independent Test Criteria**: API responses include relevant citations when referencing source material

- [x] T026 [P] [US4] Enhance citation extraction logic in AsyncRAGAgent
- [x] T027 [US4] Improve citation matching between retrieved content and AI responses
- [x] T028 [US4] Ensure citations are properly formatted and returned in API responses
- [x] T029 [US4] Test citation accuracy with various document types and content

### Phase 7: Testing & Validation
**Goal**: Validate all functionality meets requirements

- [x] T030 [P] Create unit tests for AsyncRAGAgent functionality
- [x] T031 [P] Create integration tests for API endpoints
- [x] T032 [P] Create performance tests to validate response times
- [x] T033 [P] Create error condition tests for API failures
- [x] T034 Run complete test suite and validate all tests pass

### Phase 8: Polish & Cross-Cutting Concerns
**Goal**: Finalize implementation with error handling, security, and deployment readiness

- [x] T035 [P] Implement comprehensive error handling for external API failures
- [x] T036 [P] Add proper logging throughout the application
- [x] T037 [P] Ensure proper validation of all user inputs
- [x] T038 [P] Optimize database queries with appropriate indexes
- [x] T039 [P] Update health check endpoint to verify all services
- [x] T040 [P] Update render.yaml for deployment with uv package manager
- [x] T041 [P] Create/update documentation for new async implementation
- [x] T042 Final integration testing and performance validation

## Dependencies

- User Story 2 (Text Highlighting) depends on foundational Session entity functionality
- User Story 1 (AI Interaction) is independent but enhanced by User Story 2 context
- User Story 3 (Conversation History) depends on foundational ChatHistory entity functionality
- User Story 4 (Citations) depends on User Story 1 AI interaction functionality

## Parallel Execution Examples

**For US1 (AI Interaction)**:
- T013, T014 can run in parallel (endpoint and retrieval method)
- T015, T016 can run in parallel (response generation and citation extraction)

**For US2 (Text Highlighting)**:
- T018, T019 can run in parallel (endpoint and context management)

**For US3 (Conversation History)**:
- T023, T024 can run in parallel (history retrieval and session management)

## Implementation Strategy

1. **MVP Scope**: Complete Phase 1-3 (Setup, Foundational, US1) to have basic chat functionality with async OpenAI integration
2. **Incremental Delivery**: Add each user story as a complete, testable increment
3. **Async-First**: Prioritize async implementation throughout to improve performance
4. **Backward Compatibility**: Maintain existing API contracts while enhancing functionality