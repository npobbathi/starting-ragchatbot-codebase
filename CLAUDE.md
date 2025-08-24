# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Retrieval-Augmented Generation (RAG) system for course materials built as a full-stack web application. It uses ChromaDB for vector storage, Anthropic's Claude for AI responses, and provides a web interface for querying course materials.

## Development Commands

### Running the Application
```bash
# Quick start (recommended)
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Package Management
```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name
```

### Environment Setup
Create a `.env` file in the root directory with:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Architecture Overview

### Core Components Structure
- **RAGSystem** (`backend/rag_system.py`): Main orchestrator that coordinates all components
- **VectorStore** (`backend/vector_store.py`): ChromaDB wrapper for semantic search and storage
- **AIGenerator** (`backend/ai_generator.py`): Anthropic Claude API integration with tool support
- **DocumentProcessor** (`backend/document_processor.py`): Processes course documents into searchable chunks
- **SessionManager** (`backend/session_manager.py`): Manages conversation history per session
- **ToolManager** (`backend/search_tools.py`): Implements search tools for Claude to use

### Request Flow
1. User submits query via frontend (`frontend/script.js`)
2. FastAPI app (`backend/app.py`) receives query at `/api/query`
3. RAGSystem orchestrates the response generation
4. AIGenerator uses Claude with search tools to generate contextual responses
5. Search tools query VectorStore for relevant course content
6. Response returned with sources to frontend

### Data Models
Core models in `backend/models.py`:
- **Course**: Represents a course with title, description, and lessons
- **Lesson**: Individual lesson within a course
- **CourseChunk**: Text chunks for vector storage with metadata

### Key Configuration
All settings are centralized in `backend/config.py`:
- Claude model: `claude-sonnet-4-20250514`
- Embedding model: `all-MiniLM-L6-v2` 
- Chunk size: 800 characters with 100 character overlap
- ChromaDB path: `./chroma_db`

## Development Patterns

### Adding New Course Documents
Documents are processed from the `docs/` folder on startup. Supported formats: PDF, DOCX, TXT.

### Tool-Based Architecture
The system uses Claude's tool calling capability where Claude can search the knowledge base using the CourseSearchTool when needed, rather than always retrieving context upfront.

### Session Management
Each conversation maintains session state for continuity. Sessions store up to 2 previous exchanges (configurable via `MAX_HISTORY`).

### Vector Storage Collections
ChromaDB maintains separate collections for:
- Course metadata (titles, descriptions)
- Course content chunks (searchable text segments)

## Important Implementation Details

### CORS and Proxy Support
The FastAPI app includes middleware for trusted hosts and CORS to support proxy deployments.

### Static File Serving
Frontend files are served with no-cache headers for development via custom `DevStaticFiles` class.

### Error Handling
All API endpoints include proper exception handling with HTTP status codes.

### Document Processing
Course documents are chunked with overlap to maintain context across chunk boundaries. Existing courses are detected to avoid duplicate processing.