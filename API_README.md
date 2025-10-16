# Analytics UI Generator API

**Complete API Reference and Documentation**

A FastAPI-based REST API that generates Jetpack Compose UI JSON structures from natural language queries about user analytics data. This API serves as the backend for mobile applications that need dynamic UI generation based on user activity analytics.

## Features

- 🚀 **Single Endpoint**: Just send a query, get UI JSON back
- 🤖 **AI-Powered**: Uses Claude 3.5 Sonnet via OpenRouter for intelligent UI generation
- 📱 **Jetpack Compose**: Returns mobile-ready UI JSON structures
- 🎨 **Dynamic Styling**: AI chooses colors, layouts, and designs based on data context
- 📊 **Complete Data Display**: Shows ALL available data from user activity
- 🔄 **Real-time**: Fast response times for instant UI generation

## Project Structure

```
├── api.py                 # FastAPI server (main entry point)
├── run.py                 # CLI version for interactive chat
├── simple_test.py         # API test client
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API keys)
├── API_README.md          # This documentation
├── .gitignore            # Git ignore rules
├── src/
│   ├── analytics_agent.py # Main analytics UI agent
│   ├── openrouter_llm.py  # OpenRouter LLM integration
│   ├── rag.py             # RAG manager for data retrieval
│   └── embeddings.py      # Custom OpenAI embeddings
├── data/
│   └── user_activity/     # User analytics data (JSON files)
└── chroma_db/             # Vector database (auto-generated)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file:

```env
# OpenRouter API Configuration (for Claude)
OPENROUTER_API_KEY="your-openrouter-api-key"

# OpenAI API Configuration (for embeddings)
OPENAI_API_KEY="your-openai-api-key"
```

### 3. Start the API Server

```bash
python api.py
```

The API will be available at `http://localhost:8000`

### 4. Test the API

```bash
# Run the test client
python test_api.py

# Or test a specific query
python test_api.py "show me my whatsapp usage today"
```

## 🚀 API Endpoints Reference

### Core Endpoints

#### `POST /generate-ui`

**Purpose:** Generate Jetpack Compose UI JSON from natural language queries about user data.

**Request Schema:**
```typescript
interface QueryRequest {
  query: string;  // Natural language description of desired UI
}
```

**Response Schema:**
```typescript
interface UIResponse {
  success: boolean;
  ui?: {
    type: "Screen";
    title: string;
    content: {
      type: string;
      modifier?: Record<string, any>;
      children?: Array<UIComponent>;
      // ... other properties based on component type
    };
  };
  error?: string;
}
```

**Example Request:**
```json
{
  "query": "show me my whatsapp usage for today with charts"
}
```

**Example Response:**
```json
{
  "success": true,
  "ui": {
    "type": "Screen",
    "title": "WhatsApp Usage Today",
    "content": {
      "type": "Column",
      "modifier": {
        "fillMaxSize": true,
        "padding": 16
      },
      "children": [
        {
          "type": "Card",
          "modifier": {
            "fillMaxWidth": true,
            "padding": 16
          },
          "elevation": 4,
          "backgroundColor": "#E8F5E8",
          "content": {
            "type": "Row",
            "modifier": {
              "fillMaxWidth": true
            },
            "children": [
              {
                "type": "Text",
                "text": "Messages Sent Today",
                "fontSize": 18,
                "fontWeight": "bold",
                "color": "#2E7D32"
              },
              {
                "type": "Spacer",
                "modifier": {
                  "weight": 1
                }
              },
              {
                "type": "Text",
                "text": "124",
                "fontSize": 24,
                "fontWeight": "bold",
                "color": "#1B5E20"
              }
            ]
          }
        }
      ]
    }
  },
  "error": null
}
```

**HTTP Status Codes:**
- `200 OK`: Success (even with generation errors - check `success` field)
- `400 Bad Request`: Invalid query format or empty query
- `503 Service Unavailable`: API not initialized properly

---

#### `GET /health`

**Purpose:** Check API health and component readiness.

**Response:**
```json
{
  "status": "healthy",
  "agent_ready": true,
  "data_loaded": true,
  "message": "API is ready to generate UIs"
}
```

---

#### `GET /examples`

**Purpose:** Retrieve example queries for testing and reference.

**Response:**
```json
{
  "examples": [
    {
      "query": "show me my whatsapp usage today",
      "description": "Display WhatsApp activity and usage statistics"
    },
    {
      "query": "what's my youtube activity this week?",
      "description": "Show YouTube viewing history and time spent"
    }
  ]
}
```

---

#### `GET /`

**Purpose:** Basic API information and version.

**Response:**
```json
{
  "message": "Analytics UI Generator API",
  "status": "running",
  "version": "1.0.0"
}
```

## 📋 Query Examples and Patterns

### Analytics Queries

**WhatsApp Analytics:**
- `"show me my whatsapp usage today"`
- `"whatsapp messages sent this week with breakdown"`
- `"display my most active whatsapp conversations"`
- `"show whatsapp peak usage hours"`

**YouTube Analytics:**
- `"display my youtube activity this week"`
- `"show youtube categories I watch most"`
- `"youtube viewing time trends"`
- `"what videos did I watch today?"`

**Battery Analytics:**
- `"show my battery performance"`
- `"battery usage by app today"`
- `"charging patterns this week"`

**Cross-App Analytics:**
- `"create a dashboard for all my apps"`
- `"show me my digital wellness summary"`
- `"which apps do I use most?"`

### Standard UI Generation

**Authentication:**
- `"create a login page"`
- `"design a signup screen"`
- `"make a password reset form"`

**Common Screens:**
- `"create a settings page"`
- `"design a user profile screen"`
- `"make a welcome screen"`

## 🔧 Client Integration

### Android/Kotlin Integration

```kotlin
data class QueryRequest(val query: String)

data class UIResponse(
    val success: Boolean,
    val ui: UIComponent?,
    val error: String?
)

class AnalyticsUIService {
    private val client = OkHttpClient()
    private val gson = Gson()
    
    suspend fun generateUI(query: String): UIResponse = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("http://your-api-server:8000/generate-ui")
            .post(
                gson.toJson(QueryRequest(query))
                    .toRequestBody("application/json".toMediaType())
            )
            .build()
            
        val response = client.newCall(request).execute()
        gson.fromJson(response.body?.string(), UIResponse::class.java)
    }
}
```

### React Native Integration

```typescript
interface AnalyticsUIClient {
  generateUI(query: string): Promise<UIResponse>;
}

export class AnalyticsUIService implements AnalyticsUIClient {
  constructor(private baseUrl: string) {}
  
  async generateUI(query: string): Promise<UIResponse> {
    const response = await fetch(`${this.baseUrl}/generate-ui`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });
    
    return response.json();
  }
}
```

### Flutter Integration

```dart
class AnalyticsUIService {
  final String baseUrl;
  final http.Client client = http.Client();
  
  AnalyticsUIService(this.baseUrl);
  
  Future<UIResponse> generateUI(String query) async {
    final response = await client.post(
      Uri.parse('$baseUrl/generate-ui'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'query': query}),
    );
    
    return UIResponse.fromJson(jsonDecode(response.body));
  }
}
```

## 🛠️ Configuration and Environment

### Environment Variables

```bash
# Required: OpenRouter API for Claude 3.5 Sonnet
OPENROUTER_API_KEY="your-openrouter-api-key"

# Required: OpenAI API for embeddings
OPENAI_API_KEY="your-openai-api-key"

# Optional: Custom model name (defaults to claude-sonnet-4)
MODEL_NAME="claude-sonnet-4"

# Optional: Temperature for generation (0.0-1.0, default: 0.7)
TEMPERATURE="0.7"

# Optional: Custom port (default: 8000)
PORT="8000"

# Optional: Custom host (default: 0.0.0.0)
HOST="0.0.0.0"
```

### Production Configuration

**CORS Settings:**
```python
# In api.py, configure for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**Logging Configuration:**
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📊 Monitoring and Analytics

### Health Monitoring

Monitor these endpoints for service health:
- `GET /health` - Overall service status
- `GET /` - Basic connectivity test

### Performance Metrics

**Key Metrics to Track:**
- Request latency (target: <2s for warm requests)
- Success rate (target: >95%)
- Error patterns and frequencies
- LLM API usage and costs

**Sample Monitoring Setup:**
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper
```

## 🚀 Deployment Options

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE 8000

# Use production server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**Build and Run:**
```bash
docker build -t analytics-ui-api .
docker run -d -p 8000:8000 --env-file .env analytics-ui-api
```

### Cloud Deployment

**AWS Lambda (Serverless):**
```python
from mangum import Mangum
from api import app

handler = Mangum(app)
```

**Google Cloud Run:**
```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/analytics-ui-api', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/analytics-ui-api']
```

## 🔍 Troubleshooting

### Common Issues

**Issue: "Service not ready" Error**
```
Solution: 
1. Check API key configuration in .env
2. Verify data files exist in data/user_activity/
3. Check logs for initialization errors
```

**Issue: Slow Response Times**
```
Solution:
1. First request is always slower (cold start)
2. Check OpenRouter API status
3. Monitor memory usage (vector DB can be large)
```

**Issue: Invalid UI JSON Generated**
```
Solution:
1. Check if query is clear and specific
2. Verify user data format in data files
3. Review LLM temperature settings (lower = more consistent)
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Testing Endpoints

```bash
# Test health
curl -v http://localhost:8000/health

# Test with verbose output
curl -v -X POST "http://localhost:8000/generate-ui" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```