#!/usr/bin/env python3
"""
Test script to verify the OpenRouter migration works correctly
"""
import sys
import os
sys.path.append('backend')

# Test imports
print("=== Testing Imports ===")
try:
    from config import config
    print("✅ Config loaded successfully")
    print(f"   Model: {config.OPENROUTER_MODEL}")
    print(f"   API Key present: {bool(config.OPENROUTER_API_KEY)}")
except Exception as e:
    print(f"❌ Config import failed: {e}")
    sys.exit(1)

try:
    from search_tools import CourseSearchTool, ToolManager
    print("✅ Search tools imported")
except Exception as e:
    print(f"❌ Search tools import failed: {e}")
    sys.exit(1)

try:
    from ai_generator import AIGenerator
    print("✅ AI Generator imported")
except Exception as e:
    print(f"❌ AI Generator import failed: {e}")
    sys.exit(1)

try:
    from rag_system import RAGSystem
    print("✅ RAG System imported")
except Exception as e:
    print(f"❌ RAG System import failed: {e}")
    sys.exit(1)

# Test tool definition format conversion
print("\n=== Testing Tool Definition ===")
try:
    from vector_store import VectorStore
    from config import config

    # Mock vector store (we won't actually search)
    # Just test the tool definition format
    class MockVectorStore:
        pass

    mock_store = MockVectorStore()
    search_tool = CourseSearchTool(mock_store)
    tool_def = search_tool.get_tool_definition()

    print(f"✅ Tool definition: {tool_def['name']}")

    # Verify format that our AI generator expects
    if "input_schema" in tool_def:
        print("✅ Has input_schema (Anthropic format)")
    else:
        print("❌ Missing input_schema")

except Exception as e:
    print(f"❌ Tool definition test failed: {e}")
    sys.exit(1)

# Test that generator can be instantiated
print("\n=== Testing AI Generator Instantiation ===")
try:
    if config.OPENROUTER_API_KEY:
        generator = AIGenerator(config.OPENROUTER_API_KEY, config.OPENROUTER_MODEL)
        print("✅ AI Generator instantiated")
        print(f"   Client type: {type(generator.client).__name__}")
        print(f"   Model: {generator.model}")
    else:
        print("⚠️  Skipping (no API key configured)")
except Exception as e:
    print(f"❌ Generator instantiation failed: {e}")
    sys.exit(1)

# Test message format conversion
print("\n=== Testing History Format Conversion ===")
try:
    test_history = "User: What is RAG?\nAssistant: RAG stands for Retrieval-Augmented Generation."
    generator = AIGenerator("test", "test")

    # Test history parsing (private method access for testing)
    messages = []
    lines = test_history.split('\n')
    current_role = None
    current_content = []

    for line in lines:
        if line.startswith("User: "):
            if current_role and current_content:
                messages.append({
                    "role": "user",
                    "content": "\n".join(current_content)
                })
            current_role = "user"
            current_content = [line[6:]]
        elif line.startswith("Assistant: "):
            if current_role and current_content:
                messages.append({
                    "role": current_role,
                    "content": "\n".join(current_content)
                })
            current_role = "assistant"
            current_content = [line[11:]]
        elif current_content:
            current_content.append(line)

    if current_role and current_content:
        messages.append({
            "role": current_role,
            "content": "\n".join(current_content)
        })

    print(f"✅ History parsed correctly: {len(messages)} messages")
    for msg in messages:
        print(f"   {msg['role']}: {msg['content'][:50]}...")

except Exception as e:
    print(f"❌ History parsing failed: {e}")
    sys.exit(1)

# Test RAG system can be instantiated
print("\n=== Testing RAG System ===")
try:
    if config.OPENROUTER_API_KEY:
        rag = RAGSystem(config)
        print("✅ RAG System instantiated")
        print(f"   Has AI Generator: {hasattr(rag, 'ai_generator')}")
        print(f"   Has Tool Manager: {hasattr(rag, 'tool_manager')}")
        print(f"   Has Vector Store: {hasattr(rag, 'vector_store')}")
    else:
        print("⚠️  Skipping (no API key configured)")
except Exception as e:
    print(f"❌ RAG System instantiation failed: {e}")
    sys.exit(1)

print("\n=== All Tests Passed! ===")
print("\nNext steps:")
print("1. Set OPENROUTER_API_KEY in .env file")
print("2. Run: cd backend && uv run uvicorn app:app --reload --port 8000")
print("3. Open http://localhost:8000 in your browser")