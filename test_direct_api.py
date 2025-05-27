"""
Direct test of Anthropic API
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# Load from root .env with absolute path
project_root = Path(__file__).parent
env_path = project_root / '.env'
print(f"Loading from: {env_path}")
load_dotenv(env_path, override=True)

api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"Using API Key: {api_key[:30]}..." if api_key else "NO API KEY FOUND")

try:
    client = anthropic.Anthropic(api_key=api_key)
    
    # Test mit Claude Sonnet 4
    print("Testing Claude Sonnet 4...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": "Say 'Hello, Claude Sonnet 4 is working!'"
        }]
    )
    print(f"✓ Success: {response.content[0].text}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    
    # Try Claude 3.5 Sonnet as fallback
    print("\nTrying Claude 3.5 Sonnet v2 as fallback...")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Say 'Hello, Claude 3.5 Sonnet is working!'"
            }]
        )
        print(f"✓ Success with Claude 3.5: {response.content[0].text}")
    except Exception as e2:
        print(f"✗ Error with Claude 3.5: {e2}")
