"""
Configuration Module
Contains API keys and environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Anthropic API Key (for future content validation if needed)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# Gemini API Key (if you were using it before)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# OpenAI API Key (for hybrid validation)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')