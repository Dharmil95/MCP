#!/usr/bin/env python3
"""Test the chat API integration with the supervisor."""

import asyncio
import sys
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the API base URL - adjust this if your server runs on a different port
API_BASE_URL = "http://localhost:8000"

async def test_chat_api():
    """Test the chat API endpoints."""
    print("Testing Chat API Integration...")
    
    # Test initialization endpoint
    try:
        print("\n--- Testing chat initialization ---")
        response = requests.post(f"{API_BASE_URL}/api/chat/initialize")
        response.raise_for_status()  # Raise exception for HTTP errors
        print(f"Initialization response: {response.json()}")
    except Exception as e:
        print(f"Initialization error: {e}")
        return
    
    # Test document listing
    try:
        print("\n--- Testing document listing via API ---")
        chat_response = requests.post(
            f"{API_BASE_URL}/api/chat/",
            json={"message": "List all documents"}
        )
        chat_response.raise_for_status()
        result = chat_response.json()
        print(f"Document response: {result}")
        
        # Store thread ID if provided
        thread_id = result.get("thread_id")
        print(f"Thread ID: {thread_id}")
        
        # Test math calculation with the same thread if available
        print("\n--- Testing math calculation via API ---")
        math_request = {"message": "15 + 23"}
        if thread_id:
            math_request["thread_id"] = thread_id
        
        math_response = requests.post(
            f"{API_BASE_URL}/api/chat/",
            json=math_request
        )
        math_response.raise_for_status()
        math_result = math_response.json()
        print(f"Math response: {math_result}")
        
    except Exception as e:
        print(f"Chat API error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # We're using requests which is synchronous, so no need for asyncio.run()
    test_chat_api()
