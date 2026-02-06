# Fortinet Content Brief Validator

A comprehensive validation tool for Fortinet brief documents that ensures compliance with AEM (Adobe Experience Manager) formatting standards. The tool supports both rule-based and AI-powered validation using OpenAI's GPT models.

## 🚀 Features

### Core Functionality
- **Document Format Support**: Validate DOCX files or live URLs from Fortinet's website
- **Comprehensive Validation**: Checks Meta Title, Meta Description, H1-H4 headers, FAQ sections, Product Navigation tabs, and CTA sections
- **Multiple Case Types**: Validates Capital Case, Title Case, and Sentence case formatting
- **Fortinet-Specific Rules**: Built-in dictionary of 80+ Fortinet products and cybersecurity terms

### AI-Powered Validation
- **Hybrid Validation**: Combines rule-based validation with OpenAI GPT-4 for enhanced accuracy
- **Smart Pattern Recognition**: Automatically preserves Fortinet product names (FortiCNAPP, FortiDevOps, etc.)
- **Acronym Handling**: Correctly handles technical acronyms (VPNs, APIs, SIEM, XDR, etc.)

### User Interface
- **Interactive Dashboard**: Clean Streamlit-based web interface
- **Detailed Reports**: View validation summary, failed items table, and passed items
- **Export Options**: Download validation reports as DOCX files


---

## 📋 Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [Project Structure](#project-structure)


---

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd FORTINET_VALIDATOR_APP
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI API Key (Optional - for AI-powered validation)
OPENAI_API_KEY=your_openai_api_key_here


```

### Configuration File

The `config.py` file automatically loads environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

```

**Note**: The tool works without API keys using rule-based validation only. AI features require a valid OpenAI API key.

---

## 🎯 Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Validation Workflow

#### Option 1: Upload DOCX File
1. Select "Upload DOCX File" option
2. Click "Browse files" and select your Fortinet brief document
3. Click "🔍 Run Validation"
4. Review validation results

#### Option 2: Enter Live URL
1. Select "Enter Live URL" option
2. Paste the Fortinet webpage URL (e.g., `https://www.fortinet.com/resources/cyberglossary/application-security`)
3. Click "Fetch & Extract"
4. Click "🔍 Run Validation"
5. Review validation results

## 📁 Project Structure

```
FORTINET_VALIDATOR/
├── app_validators/
│   ├── __init__.py
│   ├── docx_extractor.py      # Extracts content from DOCX files
│   ├── url_extractor.py       # Extracts content from live URLs
│   ├── validator.py           # Core validation logic (rule-based + AI)
│   └── openai_validator.py    # OpenAI API integration
├── utils/
│   └── __init__.py
├── .env                        # Environment variables (create this)
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Key Files Explained

**`app.py`**
- Main Streamlit application
- Handles UI, file uploads, and result display
- Generates DOCX reports

**`validator.py`**
- Core validation engine
- Implements validation rules for all case types
- Manages hybrid validation (rule-based + AI)
- Contains Fortinet terms dictionary

**`docx_extractor.py`**
- Extracts structured content from DOCX files
- Parses meta tags, headers, FAQs, product navigation
- Filters out internal linking sections

**`url_extractor.py`**
- Fetches and parses live Fortinet webpages
- Extracts same structured content as DOCX extractor
- Handles dynamic web content

**`openai_validator.py`**
- OpenAI API integration
- Implements hybrid validation logic
- Custom prompts for Title Case and Sentence case

---

