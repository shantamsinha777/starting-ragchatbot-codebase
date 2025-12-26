# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
# Development
source .venv/bin/activate
cd backend
uvicorn app:app --reload --port 8000

# Access
# Web UI: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Architecture Overview

This is a **full-stack Retrieval-Augmented Generation (RAG) system** for querying course materials. The system follows a tool-based architecture where the AI can call a search function to retrieve relevant course content.

### Core Flow
```
User Query → RAGSystem.query() → AI Generator (OpenRouter) → Tool Decision → Vector Search → Final Answer
```

### Key Components

**`backend/ai_generator.py`** - AI Integration Layer
- Uses OpenRouter API with OpenAI-compatible format
- Handles tool call conversion: Anthropic format → OpenAI format
- Manages two-step API calls: (1) decide to search, (2) synthesize answer
- Converts conversation history strings to message arrays

**`backend/rag_system.py`** - Orchestrator
- Coordinates all subsystems
- `query()`: Main entry point, handles session management and sources tracking
- `add_course_folder()`: Batch processes documents on startup

**`backend/vector_store.py`** - ChromaDB Storage
- **Dual collections strategy**:
  - `course_catalog`: Single entries per course (title, instructor, metadata)
  - `course_content`: Chunks of actual course material for semantic search
- Smart course name resolution via vector similarity

**`backend/document_processor.py`** - Text Processing
- Sentence-based chunking with configurable overlap (800 chars, 100 overlap)
- Regex handles abbreviations (e.g., "Dr.", "e.g.") to avoid breaking sentences
- First chunk of each lesson gets prefixed context: "Lesson X content: ..."

**`backend/search_tools.py`** - Tool Interface
- `CourseSearchTool`: Wraps vector store for AI tool consumption
- `ToolManager`: Registers and executes tools
- Returns formatted results with source tracking

**`frontend/`** - Static Web Interface
- Vanilla JS with `marked.js` for markdown rendering
- Two-column layout: sidebar (course stats + suggestions) + chat area
- Maintains session ID for conversation history

## Configuration

### Environment Variables (`.env`)
```bash
OPENROUTER_API_KEY=sk-or-v1-...      # Required - OpenRouter API key
OPENROUTER_MODEL=xiaomi/mimo-v2-flash:free  # Default, can swap to any OpenRouter model
```

### Backend Configuration (`backend/config.py`)
```python
CHUNK_SIZE = 800        # Characters per chunk
CHUNK_OVERLAP = 100     # Overlap between chunks
MAX_RESULTS = 5         # Results per search
MAX_HISTORY = 2         # Conversation pairs to remember
```

## Tool-Based Search Architecture

The system uses **function calling** rather than direct RAG:

1. **AI decides** if a search is needed based on query
2. **Tool executes** `search_course_content(query, course_name?, lesson_number?)`
3. **Vector search** returns top-k most relevant chunks
4. **AI synthesizes** results into final answer

**Tool Definition Format:**
- Stored internally as Anthropic-compatible (`input_schema`)
- Converted to OpenAI format at API call time (`function.parameters`)
- Supports filtering by course name (fuzzy match) and lesson number

## Document Format

Course documents in `/docs/*.txt` must follow this structure:
```text
Course Title: Course Name Here
Course Link: https://optional-link.com
Course Instructor: Instructor Name

Lesson 0: Introduction
Lesson Link: https://optional-lesson-link.com
[Content starts here... multi-line]

Lesson 1: Overview
[Content...]
```

## Common Development Tasks

**Adding a new document:**
```bash
# Documents auto-load on startup from /docs/
# Or programmatically:
cd backend && python -c "
from config import config
from rag_system import RAGSystem
rag = RAGSystem(config)
rag.add_course_folder('../docs')
"
```

**Testing tool calling:**
```bash
python test_migration.py  # Validates configuration, tools, API connectivity
```

**Viewing ChromaDB data:**
```python
# Inspect stored data
vector_store = VectorStore('./chroma_db', 'all-MiniLM-L6-v2')
print(vector_store.course_catalog.get())  # Course metadata
print(vector_store.course_content.get())  # Content chunks
```

## Model Switching

To change AI models without code changes:
```bash
# In .env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
# OR
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct
```

All models that support OpenAI-compatible function calling will work.

## Debug Flags

The `ai_generator.py` contains debug prints showing:
- Message structure being sent to API
- Tool call detection and execution
- Error responses from OpenRouter

Look for `[AI_DEBUG]` and `[AI_ERROR]` in server logs.

## Critical OpenRouter-Specific Details

- Uses `https://openrouter.ai/api/v1` as base URL
- **System prompt** must be in `messages` array as `{"role": "system", "content": "..."}`
- **Tool results** are individual messages with `{"role": "tool", ...}`
- **Model names** may need suffixes: `xiaomi/mimo-v2-flash:free`
- Xiaomi models require `content` to be non-empty in all user messages

## Security Notes

- `.env` file is gitignored - never commit API keys
- CORS allows all origins (appropriate for local dev)
- Session management is in-memory (resets on server restart)