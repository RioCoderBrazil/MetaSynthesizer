"""
Test Anthropic API Key
"""

import os
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv('config/.env')

# Get API key
api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key: {api_key[:20]}...")

try:
    # Initialize client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Test with Claude 3.5 Sonnet v2 (newest model)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        temperature=0,
        messages=[{
            "role": "user", 
            "content": "Say 'API key is valid and Claude 3.5 Sonnet v2 is working!'"
        }]
    )
    
    print(f"✓ Success! Response: {response.content[0].text}")
    
except Exception as e:
    print(f"✗ Error: {e}")
