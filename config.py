"""
Configuration Module
Contains API keys and environment variables
"""

import os
from dotenv import load_dotenv

# Load local environment variables (.env)
load_dotenv()

def get_secret(key: str) -> str:
    """
    Fetch secret from Streamlit (cloud) or .env (local)
    """
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return os.getenv(key, '')

# API Keys

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
