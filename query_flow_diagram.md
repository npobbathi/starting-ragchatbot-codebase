# RAG System Query Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(script.js)
    participant API as FastAPI<br/>(app.py)
    participant RAG as RAG System<br/>(rag_system.py)
    participant SM as Session Manager
    participant AI as AI Generator<br/>(ai_generator.py)
    participant Claude as Claude Sonnet 4
    participant TM as Tool Manager
    participant VS as Vector Store<br/>(ChromaDB)

    User->>Frontend: Types query & hits Enter
    
    Frontend->>Frontend: Validate input & show loading
    Note over Frontend: script.js:46-59<br/>Disable input, create loading animation
    
    Frontend->>API: POST /api/query
    Note over Frontend,API: {"query": "user question", "session_id": "abc123"}
    
    API->>API: Validate QueryRequest model
    Note over API: app.py:56-63<br/>Create session if needed
    
    API->>RAG: rag_system.query(query, session_id)
    Note over API,RAG: app.py:66
    
    RAG->>SM: get_conversation_history(session_id)
    SM-->>RAG: Previous messages
    
    RAG->>AI: generate_response(query, history, tools, tool_manager)
    Note over RAG,AI: rag_system.py:122-127<br/>Includes tool definitions
    
    AI->>Claude: messages.create() with tools
    Note over AI,Claude: ai_generator.py:68-80<br/>System prompt + conversation context
    
    Claude-->>AI: Response with tool_use
    Note over Claude,AI: Wants to search course content
    
    AI->>TM: Execute tool calls
    Note over AI,TM: ai_generator.py:83-84
    
    TM->>VS: search_courses(query)
    Note over TM,VS: Semantic search with embeddings
    
    VS-->>TM: Relevant course chunks
    TM-->>AI: Tool execution results
    
    AI->>Claude: Continue conversation with tool results
    Claude-->>AI: Final answer with context
    
    AI-->>RAG: Generated response text
    RAG-->>API: (answer, sources) tuple
    
    API->>API: Wrap in QueryResponse model
    Note over API: app.py:68-72<br/>{"answer": "...", "sources": [...], "session_id": "..."}
    
    API-->>Frontend: JSON response
    
    Frontend->>Frontend: Process response
    Note over Frontend: script.js:76-85<br/>Update session ID, remove loading
    
    Frontend->>Frontend: Render message with markdown
    Note over Frontend: script.js:113-138<br/>Display answer + collapsible sources
    
    Frontend->>User: Show AI response in chat
    Note over Frontend,User: Re-enable input field
```

## Key Components Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Browser   │───▶│   FastAPI    │───▶│ RAG System  │───▶│ AI Generator │
│ (script.js) │    │   (app.py)   │    │(rag_system) │    │(ai_generator)│
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
       ▲                                        │                    │
       │                                        ▼                    ▼
       │                              ┌─────────────┐    ┌──────────────┐
       │                              │ Session Mgr │    │ Claude API   │
       │                              │   (history) │    │ (Sonnet 4)   │
       │                              └─────────────┘    └──────────────┘
       │                                                          │
       │            ┌─────────────────────────────────────────────┘
       │            │ Tool Use Request
       │            ▼
       │  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
       └──│Tool Manager │───▶│ Vector Store │───▶│  ChromaDB   │
          │ (CourseSearch) │    │ (semantic)   │    │ (embeddings)│
          └─────────────┘    └──────────────┘    └─────────────┘
```

## Data Flow Summary

1. **User Input** → `sendMessage()` in script.js:45
2. **HTTP Request** → POST `/api/query` with JSON payload
3. **API Handler** → `query_documents()` in app.py:56
4. **RAG Orchestration** → `rag_system.query()` in rag_system.py:102
5. **AI Generation** → Claude Sonnet 4 with tool access
6. **Tool Execution** → Vector search in ChromaDB when needed
7. **Response Assembly** → JSON with answer, sources, session_id
8. **Frontend Rendering** → Markdown parsing and UI update