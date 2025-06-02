#!/usr/bin/env python3
"""
Test script to verify the full MCP chat system is working.
This script:
1. Starts the FastAPI backend server (if not already running)
2. Tests the chat API with a simple request
3. Outputs the system status

Usage:
  python test_full_chat_system.py
"""

import asyncio
import aiohttp
import argparse
import sys
import os
import signal
import subprocess
import time
from urllib.parse import urljoin

# Configuration
API_BASE_URL = "http://localhost:8000"
API_CHAT_STATUS = "/api/chat/status"
API_CHAT_INITIALIZE = "/api/chat/initialize" 
API_CHAT = "/api/chat"

# Test messages to send
TEST_MESSAGES = [
    "List all documents",
    "What is 42 + 58?"
]

async def check_api_status(session):
    """Check if the API is reachable"""
    try:
        async with session.get(urljoin(API_BASE_URL, API_CHAT_STATUS)) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ API is reachable. Status: {data['status']}")
                return True, data
            else:
                print(f"✗ API returned status code {response.status}")
                return False, None
    except aiohttp.ClientError as e:
        print(f"✗ Could not connect to API: {e}")
        return False, None

async def initialize_chat_system(session):
    """Initialize the chat system if needed"""
    try:
        async with session.post(urljoin(API_BASE_URL, API_CHAT_INITIALIZE)) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ Chat system initialized. Status: {data['status']}")
                return True, data
            else:
                print(f"✗ Failed to initialize chat system: {response.status}")
                return False, None
    except aiohttp.ClientError as e:
        print(f"✗ Error initializing chat system: {e}")
        return False, None

async def send_test_message(session, message):
    """Send a test message to the chat API"""
    print(f"\n--- Testing message: '{message}' ---")
    try:
        payload = {"message": message}
        async with session.post(
            urljoin(API_BASE_URL, API_CHAT),
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ Message sent successfully")
                print(f"Response: {data['response']}")
                return True, data
            else:
                print(f"✗ Failed to send message: {response.status}")
                error_text = await response.text()
                print(f"Error: {error_text}")
                return False, None
    except aiohttp.ClientError as e:
        print(f"✗ Error sending message: {e}")
        return False, None

async def run_test():
    """Run the full test suite"""
    print("=== Testing Full MCP Chat System ===")
    
    async with aiohttp.ClientSession() as session:
        # Check API status
        api_available, status_data = await check_api_status(session)
        if not api_available:
            print("Cannot proceed with tests: API is not available")
            return False
            
        # Initialize chat system if needed
        if status_data and status_data.get("status") != "ready":
            print("Chat system needs initialization...")
            init_success, _ = await initialize_chat_system(session)
            if not init_success:
                print("Failed to initialize chat system, cannot proceed with tests")
                return False
        
        # Send test messages
        success = True
        for message in TEST_MESSAGES:
            msg_success, _ = await send_test_message(session, message)
            if not msg_success:
                success = False
                
        return success

def main():
    """Main entry point"""
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        success = asyncio.run(run_test())
        
        if success:
            print("\n✅ All tests completed successfully")
        else:
            print("\n⚠️ Some tests failed")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
