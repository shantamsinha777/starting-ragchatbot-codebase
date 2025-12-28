# OpenRouter Migration Summary

## Overview
Successfully migrated the RAG system from **Anthropic Claude** to **OpenRouter** with MiMo V2 Flash model.

## Files Changed

### 1. Configuration (`backend/config.py`)
```diff
# OLD
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

# NEW
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "xiaomi/mimo-v2-flash")
```

### 2. AI Generator (`backend/ai_generator.py`)
**Complete rewrite** - changed from Anthropic SDK to OpenAI-compatible format:

**Key Changes:**
- **Client**: `anthropic.Anthropic()` → `openai.OpenAI(base_url="https://openrouter.ai/api/v1")`
- **API Calls**: `client.messages.create()` → `client.chat.completions.create()`
- **Response Format**: `response.content[0].text` → `response.choices[0].message.content`
- **Tool Format**: Automatic conversion from Anthropic's `input_schema` to OpenAI's `function.parameters`
- **Tool Execution**: Handles OpenAI's `tool_calls` format vs Anthropic's `tool_use`

**New Capabilities:**
- Parses conversation history (User/Assistant format) into message array
- Converts tool definitions dynamically
- Handles tool results in OpenAI format

### 3. RAG System (`backend/rag_system.py`)
```diff
# Line 19 - Updated constructor
self.ai_generator = AIGenerator(config.OPENROUTER_API_KEY, config.OPENROUTER_MODEL)
```

### 4. Search Tools (`backend/search_tools.py`)
- **Updated comment**: Clarifies tool definition format is provider-agnostic
- **Functionality**: Unchanged (still returns `input_schema` format)

### 5. Dependencies (`pyproject.toml`)
```diff
# OLD
"anthropic==0.58.2",

# NEW
"openai==1.58.0",
```

### 6. Environment & Documentation
- `.env.example`: Updated for OpenRouter keys
- `README.md`: Updated for MiMo V2 Flash
- `run.sh`: Updated environment variable message

## New .env Structure

```bash
# Required
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL=xiaomi/mimo-v2-flash

# Optional - swap models without code changes:
# OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
# OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct
```

## Installation & Running

```bash
# 1. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# 2. Install dependencies
uv sync

# 3. Create .env with your API key
echo "OPENROUTER_API_KEY=your_key_here" > .env
echo "OPENROUTER_MODEL=xiaomi/mimo-v2-flash" >> .env

# 4. Run the system
./run.sh
# OR manually:
cd backend && uv run uvicorn app:app --reload --port 8000

# 5. Access at http://localhost:8000
```

## Testing

A test script was created: `test_migration.py`

```bash
source .venv/bin/activate
python test_migration.py
```

All tests should pass before running the full application.

## Benefits of This Migration

1. **Model Flexibility**: Can swap between models via environment variable
2. **Cost Management**: OpenRouter routing can be cheaper
3. **No Vendor Lock-in**: Easier to migrate away from any single provider
4. **Xiaomi MiMo**: Uses your desired V2 Flash model
5. **Future Proof**: Easy to add more providers

## Flow Comparison

### Original (Anthropic)
```
User → Frontend → RAG System → Anthropic API (tool call) → Vector Search → Anthropic API (synthesis) → Response
```

### New (OpenRouter)
```
User → Frontend → RAG System → OpenRouter API (tool call) → Vector Search → OpenRouter API (synthesis) → Response
```

**Same architecture, different API format!**

## Critical Implementation Details

### Tool Call Conversion
```python
# Anthropic format from tool definition
{
    "name": "search_course_content",
    "description": "...",
    "input_schema": {"type": "object", ...}  # ← Our format
}

# Converted to OpenAI format for API
{
    "type": "function",
    "function": {
        "name": "search_course_content",
        "description": "...",
        "parameters": {"type": "object", ...}  # ← Changed to 'parameters'
    }
}
```

### Message Format
OpenRouter uses standard OpenAI message format:
```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "What is RAG?"},
    {"role": "assistant", "content": None, "tool_calls": [...]}
]
```

### Tool Results
Tool results returned as user message:
```python
{
    "role": "user",
    "content": [
        {
            "tool_call_id": "...",
            "role": "tool",
            "name": "search_course_content",
            "content": "Search results..."
        }
    ]
}
```

## Troubleshooting

### Issue: "No module named 'openai'"
**Solution**: Run `uv sync` to install openai package

### Issue: "Invalid API key"
**Solution**: Verify `.env` file exists with correct key format

### Issue: "Model not found"
**Solution**: Check `OPENROUTER_MODEL` value matches an available OpenRouter model

### Issue: "Tool execution failed"
**Solution**: Check that tool names match between definition and execution

## Next Steps

1. ✅ **Completed**: Code migration complete
2. ✅ **Completed**: Dependencies installed
3. ⏳ **Pending**: Set up `.env` with your OpenRouter key
4. ⏳ **Pending**: Run `./run.sh` and test
5. ⏳ **Optional**: Try different models by changing `OPENROUTER_MODEL`

The migration is complete! Just add your API key and run.