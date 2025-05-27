"""
Test environment variable loading
"""

import os
from dotenv import load_dotenv

# Test 1: Load from root .env
print("=== Testing root .env ===")
load_dotenv('.env', override=True)
api_key_root = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key from root .env: {api_key_root[:20] if api_key_root else 'NOT FOUND'}...")

# Test 2: Load from config/.env
print("\n=== Testing config/.env ===")
load_dotenv('config/.env', override=True)
api_key_config = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key from config/.env: {api_key_config[:20] if api_key_config else 'NOT FOUND'}...")

# Test 3: Current environment
print("\n=== Current environment ===")
print(f"Current ANTHROPIC_API_KEY: {os.getenv('ANTHROPIC_API_KEY', 'NOT SET')[:20]}...")
