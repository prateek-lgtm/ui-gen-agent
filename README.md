# Huawei Analytics UI Generator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **AI-powered mobile UI generation from natural language queries about user analytics data**

An intelligent system that transforms natural language queries about user activity data into beautiful, production-ready Jetpack Compose UI JSON structures. Perfect for dynamically generating analytics dashboards, data visualizations, and mobile interfaces.

## ✨ Key Features

- **🤖 AI-Powered UI Generation**: Uses Claude 3.5 Sonnet to understand queries and generate contextually appropriate UIs
- **📱 Jetpack Compose Ready**: Outputs complete JSON structures that map directly to Jetpack Compose components
- **📊 Smart Data Visualization**: Automatically analyzes user activity data and creates meaningful charts, cards, and layouts
- **🎨 Dynamic Styling**: AI chooses colors, typography, and layouts based on app context and data sentiment
- **🚀 FastAPI Backend**: High-performance REST API with automatic documentation
- **🔍 RAG-Enhanced**: Vector database integration for intelligent data retrieval and context understanding
- **💬 Interactive CLI**: Command-line interface for testing and development

## 🎯 Use Cases

- **Analytics Dashboards**: Generate mobile dashboards for WhatsApp, YouTube, and battery usage data
- **Dynamic UI Creation**: Create login pages, settings screens, and other standard mobile UIs on demand
- **Data Exploration**: Query complex user activity patterns and get instant visual representations
- **Rapid Prototyping**: Generate complete mobile screens from simple text descriptions

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastAPI Server │───▶│  Analytics Agent│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         │
                                ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ User Activity    │    │  OpenRouter LLM │
                       │ Data (JSON)      │    │ (Claude 3.5)    │
                       └──────────────────┘    └─────────────────┘
                                │                         │
                                ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ ChromaDB Vector  │    │   RAG Manager   │
                       │ Store            │    │                 │
                       └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- API keys for OpenRouter and OpenAI (see [Configuration](#configuration))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd huawei_agent_poc_openai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see Configuration section)
   ```

4. **Start the API server**
   ```bash
   python api.py
   ```

5. **Test the API**
   ```bash
   curl -X POST "http://localhost:8000/generate-ui" \
        -H "Content-Type: application/json" \
        -d '{"query": "show me my whatsapp usage today"}'
   ```

### Interactive CLI Mode

For development and testing:

```bash
python run.py
```

## 📋 Configuration

Create a `.env` file in the project root:

```env
# Required: OpenRouter API key for Claude 3.5 Sonnet
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Required: OpenAI API key for embeddings and vector search
OPENAI_API_KEY=your_openai_api_key_here
```

### Getting API Keys

- **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai) for access to Claude 3.5 Sonnet
- **OpenAI**: Get your API key from [platform.openai.com](https://platform.openai.com)

## 🔧 API Usage

### Generate UI Endpoint

**POST** `/generate-ui`

Generate a Jetpack Compose UI from a natural language query.

**Request Body:**
```json
{
  "query": "show me my whatsapp usage today"
}
```

**Response:**
```json
{
  "success": true,
  "ui": {
    "type": "Screen",
    "title": "WhatsApp Usage Today",
    "content": {
      "type": "Column",
      "modifier": {"fillMaxSize": true, "padding": 16},
      "children": [...]
    }
  },
  "error": null
}
```

### Example Queries

- `"show me my whatsapp usage today"` - WhatsApp activity dashboard
- `"display my youtube activity this week"` - YouTube analytics with charts
- `"show my battery performance"` - Battery usage visualization
- `"create a login page"` - Generate standard UI components
- `"what's my most active app?"` - Cross-app analysis

### API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger documentation when the server is running.

## 📁 Project Structure

```
├── api.py                     # FastAPI server (main entry point)
├── run.py                     # Interactive CLI interface
├── simple_test.py             # API testing client
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── API_README.md              # Detailed API documentation
├── CONTRIBUTING.md            # Development guidelines
├── LICENSE                    # MIT license
├── .env.example               # Environment variables template
├── .gitignore                # Git ignore patterns
├── src/                      # Core application modules
│   ├── analytics_agent.py    # Main AI agent for UI generation
│   ├── openrouter_llm.py     # OpenRouter API integration
│   ├── rag.py                # RAG system for data retrieval
│   ├── embeddings.py         # Custom OpenAI embeddings wrapper
│   └── __pycache__/          # Python bytecode cache
├── data/                     # User activity data
│   ├── README.md             # Data format documentation
│   ├── user_activity/        # JSON data files
│   │   ├── activity_data.json        # Structured user activity
│   │   └── user_data_for_vectordb.txt # Vector database content
│   └── ui_patterns/          # UI component templates
│       ├── analytics_patterns.txt   # Analytics UI patterns
│       └── common_patterns.txt      # Common UI patterns
├── chroma_db/                # Vector database (auto-generated)
│   ├── chroma.sqlite3        # SQLite database file
│   └── [uuid]/               # Vector embeddings storage
└── docs/                     # Additional documentation (optional)
    ├── architecture.md       # System architecture details
    ├── api-reference.md      # Complete API reference
    └── deployment.md         # Deployment instructions
```

## 🛠️ Development

### Local Development

1. **Install in development mode**
   ```bash
   pip install -e .
   ```

2. **Run with auto-reload**
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Run tests**
   ```bash
   python simple_test.py
   ```

### Code Style

This project follows Python best practices:
- Type hints for all function parameters and return values
- Comprehensive docstrings using Google/NumPy style
- PEP 8 compliance with 88-character line limit
- Clear variable and function naming

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style and formatting
- Testing requirements
- Pull request process
- Issue reporting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Common Issues

**API Key Errors:**
- Verify your `.env` file contains valid API keys
- Check API key permissions and billing status

**Vector Database Issues:**
- Delete `chroma_db/` folder and restart to rebuild
- Ensure sufficient disk space for embeddings

**UI Generation Failures:**
- Check that user activity data files are present in `data/user_activity/`
- Verify JSON data format matches expected schema

### Getting Help

1. Check the [API documentation](http://localhost:8000/docs) when server is running
2. Review logs for detailed error messages
3. Test with the provided example queries first
4. Ensure all dependencies are correctly installed

### Performance Tips

- The first request may be slower due to vector database initialization
- Subsequent requests leverage cached embeddings for faster responses
- Consider using the CLI mode for rapid development and testing

---

**Built with ❤️ for modern mobile development**