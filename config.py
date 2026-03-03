"""
Configuration Module
Handles environment variables for both local and Streamlit Cloud
"""

import os
from dotenv import load_dotenv

# Load local .env file (does nothing in Streamlit Cloud)
load_dotenv()


def get_secret(key: str) -> str:
    """
    Fetch secret from:
    1️⃣ Streamlit Cloud secrets
    2️⃣ Local .env file
    """

    # Try Streamlit secrets (Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    # Fallback to local .env
    return os.getenv(key)


# === API Keys ===
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")