# System Architecture Documentation

## Overview

The Huawei Analytics UI Generator is a sophisticated AI-powered system that transforms natural language queries into production-ready Jetpack Compose UI JSON structures. The architecture follows a modular, microservices-inspired design with clear separation of concerns and scalable components.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Client Applications                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Mobile Apps (Android) │  Web Interfaces │  CLI Tools │  Testing Clients   │
└─────────────────┬───────────────────┬─────────────┬─────────────────────────┘
                  │                   │             │
                  ▼                   ▼             ▼
         ┌────────────────────────────────────────────────────────┐
         │                FastAPI Server (api.py)                │
         │  ┌──────────────────────────────────────────────────┐  │
         │  │            HTTP Request Handling                │  │
         │  │  • CORS Configuration                           │  │
         │  │  • Request Validation                           │  │
         │  │  • Error Handling                               │  │
         │  │  • Response Formatting                          │  │
         │  └──────────────────────────────────────────────────┘  │
         └────────────────┬───────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────────────────────────┐
         │            Analytics UI Agent (analytics_agent.py)    │
         │  ┌──────────────────────────────────────────────────┐  │
         │  │               Intent Analysis                    │  │
         │  │  • Query Classification                          │  │
         │  │  • App Detection                                 │  │
         │  │  • Timeframe Extraction                          │  │
         │  │  • Metric Type Identification                    │  │
         │  └──────────────────────────────────────────────────┘  │
         │  ┌──────────────────────────────────────────────────┐  │
         │  │              UI Generation Engine                │  │
         │  │  • Component Selection                           │  │
         │  │  • Layout Optimization                           │  │
         │  │  • Color Theme Selection                         │  │
         │  │  • Typography Scaling                            │  │
         │  └──────────────────────────────────────────────────┘  │
         └────────────────┬───────────────┬───────────────────────┘
                          │               │
                    ┌─────▼─────┐    ┌────▼────────────────────────┐
                    │           │    │                             │
                    ▼           ▼    ▼                             ▼
    ┌─────────────────────┐   ┌──────────────────┐    ┌─────────────────────┐
    │   OpenRouter LLM    │   │   RAG Manager    │    │   User Activity     │
    │ (openrouter_llm.py) │   │    (rag.py)      │    │   Data Store        │
    │                     │   │                  │    │                     │
    │ ┌─────────────────┐ │   │ ┌──────────────┐ │    │ ┌─────────────────┐ │
    │ │  Claude 3.5     │ │   │ │  ChromaDB    │ │    │ │   JSON Files    │ │
    │ │  Sonnet API     │ │   │ │ Vector Store │ │    │ │                 │ │
    │ │  Integration    │ │   │ │              │ │    │ │ • WhatsApp Data │ │
    │ └─────────────────┘ │   │ └──────────────┘ │    │ │ • YouTube Data  │ │
    │                     │   │                  │    │ │ • Battery Data  │ │
    │ • Model Mapping     │   │ • Semantic Search│    │ │ • Usage Patterns│ │
    │ • Error Handling    │   │ • Document Chunks│    │ └─────────────────┘ │
    │ • Rate Limiting     │   │ • Embeddings     │    └─────────────────────┘
    └─────────────────────┘   └────────┬─────────┘                         
                                       │                                   
                                       ▼                                   
                          ┌─────────────────────────┐                     
                          │    OpenAI Embeddings   │                     
                          │   (embeddings.py)      │                     
                          │                        │                     
                          │ ┌────────────────────┐ │                     
                          │ │ text-embedding-    │ │                     
                          │ │ 3-small Model      │ │                     
                          │ │                    │ │                     
                          │ │ • 1536 Dimensions  │ │                     
                          │ │ • Semantic Search  │ │                     
                          │ │ • Query Matching   │ │                     
                          │ └────────────────────┘ │                     
                          └─────────────────────────┘                     
```

## Component Architecture

### 1. API Layer (FastAPI Server)

**Purpose**: HTTP interface and request orchestration
**File**: `api.py`

**Responsibilities**:
- HTTP request/response handling
- CORS configuration for web clients
- Request validation and sanitization
- Error handling with consistent UI responses
- Service initialization and health monitoring

**Key Design Decisions**:
- Returns UI JSON even for errors (consistent client experience)
- Async initialization for non-blocking startup
- Global service instances for performance
- Comprehensive logging for monitoring

**Endpoints**:
```
POST /generate-ui    - Core UI generation endpoint
GET  /health        - Service health and readiness
GET  /examples      - Example queries for testing
GET  /             - Basic service information
```

### 2. AI Agent Layer (Analytics UI Agent)

**Purpose**: Intelligent query processing and UI generation
**File**: `src/analytics_agent.py`

**Core Capabilities**:
- **Intent Analysis**: Classifies queries into analytics vs. simple UI requests
- **App Detection**: Identifies target applications (WhatsApp, YouTube, Battery)
- **Timeframe Extraction**: Parses temporal references (today, week, month)
- **Dynamic Generation**: Creates contextually appropriate UI structures

**Agent Configuration**:
```python
Role: "Jetpack Compose UI Generator"
Goal: "Generate complete UI JSON structures based on user queries"
Tools: [QueryUIPatternsTool]  # RAG integration
LLM: OpenRouterLLM           # Claude 3.5 Sonnet
```

**UI Generation Pipeline**:
1. Query analysis and intent classification
2. Data retrieval through RAG tools
3. LLM prompt construction with full context
4. JSON generation and validation
5. Error handling with fallback UIs

### 3. Language Model Layer (OpenRouter Integration)

**Purpose**: LLM abstraction and external API management
**File**: `src/openrouter_llm.py`

**Key Features**:
- **Model Abstraction**: Custom LangChain LLM implementation
- **Provider Integration**: Seamless OpenRouter API communication
- **Conflict Resolution**: Bypasses CrewAI automatic model detection
- **Error Handling**: Comprehensive exception management

**Model Mapping Strategy**:
```python
Internal Name       →  OpenRouter Model
"claude-sonnet-4"   →  "anthropic/claude-3.5-sonnet"
```

**Benefits**:
- Avoids CrewAI framework conflicts
- Enables easy model switching
- Provides consistent interface
- Supports multiple providers

### 4. RAG System (Retrieval-Augmented Generation)

**Purpose**: Semantic data retrieval and context enhancement
**Files**: `src/rag.py`, `src/embeddings.py`

**Architecture**:
```
Query → Embedding → Vector Search → Relevant Chunks → Context
```

**Components**:
- **RAGManager**: Orchestrates retrieval operations
- **ChromaDB**: Persistent vector database
- **CustomOpenAIEmbeddings**: Text-to-vector conversion
- **Document Processing**: Chunking and preprocessing

**Performance Characteristics**:
- **Embedding Model**: text-embedding-3-small (1536 dimensions)
- **Chunk Size**: 500 characters with 100 character overlap
- **Query Time**: 100-500ms typical response
- **Storage**: Persistent across sessions

### 5. Data Layer (User Activity Storage)

**Purpose**: User analytics data management and access
**Location**: `data/user_activity/`

**Data Structure**:
```json
{
  "whatsapp": {
    "daily_usage": [
      {
        "date": "2025-10-14",
        "messages_sent": 124,
        "messages_received": 156,
        "active_time_minutes": 85,
        "peak_hours": ["12:00", "20:00"],
        "chat_categories": {...}
      }
    ],
    "weekly_summary": {...}
  },
  "youtube": {...},
  "battery": {...}
}
```

**Storage Formats**:
- **JSON Files**: Structured data for direct access
- **Text Files**: Formatted for vector database ingestion
- **Vector Database**: Embedded chunks for semantic search

## Data Flow Architecture

### 1. Request Processing Flow

```
Client Request → API Validation → Agent Initialization → Query Processing
                                                              ↓
UI JSON Response ← JSON Generation ← LLM Processing ← Data Retrieval
```

**Detailed Steps**:
1. **Request Reception**: FastAPI receives HTTP request
2. **Validation**: Pydantic models validate request structure
3. **Agent Invocation**: Analytics agent processes query
4. **Intent Analysis**: Query classification and parameter extraction
5. **Data Retrieval**: RAG system finds relevant user data
6. **LLM Generation**: Claude 3.5 Sonnet generates UI JSON
7. **Response Formatting**: Structured response with error handling

### 2. RAG Processing Flow

```
User Query → Text Embedding → Similarity Search → Document Ranking → Context Assembly
```

**Processing Pipeline**:
1. **Query Embedding**: Convert query to 1536-dimensional vector
2. **Vector Search**: Cosine similarity against stored documents
3. **Ranking**: Order results by relevance score
4. **Context Assembly**: Combine top-k results for LLM context
5. **Cache Management**: Optimize repeated queries

### 3. UI Generation Flow

```
Intent + Data → Prompt Construction → LLM Processing → JSON Parsing → Validation
```

**Generation Process**:
1. **Context Building**: Combine user intent with retrieved data
2. **Prompt Engineering**: Structured prompt with examples and constraints
3. **LLM Invocation**: Claude 3.5 Sonnet processes request
4. **JSON Extraction**: Parse and validate generated UI structure
5. **Error Handling**: Fallback UIs for generation failures

## Design Decisions and Rationale

### 1. CrewAI Framework Choice

**Decision**: Use CrewAI for agent orchestration
**Rationale**:
- Structured approach to AI agent development
- Built-in tool integration capabilities
- Task and goal-oriented design
- Extensive LLM compatibility

**Trade-offs**:
- ✅ Rapid development and structured patterns
- ✅ Built-in error handling and retry logic
- ❌ Framework overhead and dependencies
- ❌ LLM detection conflicts (solved with custom wrapper)

### 2. OpenRouter vs. Direct LLM Integration

**Decision**: Use OpenRouter as LLM proxy
**Rationale**:
- Access to multiple models through single API
- No need for multiple provider integrations
- Cost optimization through model comparison
- Simplified billing and usage tracking

**Benefits**:
- Model flexibility and easy switching
- Reduced integration complexity
- Better cost management
- Future-proof architecture

### 3. Vector Database Choice (ChromaDB)

**Decision**: ChromaDB for vector storage
**Rationale**:
- Lightweight and embeddable
- Excellent LangChain integration
- Persistent storage capabilities
- Open-source with active development

**Alternatives Considered**:
- **Pinecone**: Cloud-based, but added complexity and cost
- **Weaviate**: More features, but over-engineered for use case
- **FAISS**: Fast but lacks persistence and metadata

### 4. Embedding Model Selection

**Decision**: OpenAI text-embedding-3-small
**Rationale**:
- Excellent quality-to-cost ratio
- Optimized for retrieval tasks
- 1536 dimensions for good semantic representation
- Proven performance in production systems

**Performance Comparison**:
```
Model                    Dimensions  Quality  Cost   Speed
text-embedding-3-small   1536       High     Low    Fast
text-embedding-3-large   3072       Higher   High   Medium
text-embedding-ada-002   1536       Good     Low    Fast
```

### 5. API Design Philosophy

**Decision**: UI-first error handling
**Rationale**:
- Mobile clients need consistent UI structures
- Error states should be visually represented
- Simplifies client-side error handling
- Better user experience in production

**Implementation**:
```python
# Always return UI JSON, even for errors
return UIResponse(
    success=False,
    ui=error_ui_structure,
    error=error_message
)
```

## Scalability and Performance

### 1. Current Performance Characteristics

**Latency**:
- Cold start: 3-5 seconds (initialization)
- Warm requests: 1-2 seconds (generation)
- Vector search: 100-500ms
- LLM generation: 800-1500ms

**Throughput**:
- Concurrent requests: Limited by LLM API rate limits
- Vector database: Handles 100+ QPS
- Memory usage: ~200MB base + vector storage

### 2. Optimization Strategies

**Implemented**:
- Persistent vector storage (avoids re-embedding)
- Global service instances (reduces initialization)
- Efficient chunking strategy (optimal retrieval)
- Custom LLM wrapper (bypasses framework overhead)

**Future Optimizations**:
- Response caching for common queries
- Async LLM calls for better concurrency
- Model quantization for faster inference
- CDN deployment for global availability

### 3. Scaling Patterns

**Horizontal Scaling**:
```
Load Balancer → Multiple API Instances → Shared Vector Database
```

**Vertical Scaling**:
- Increase memory for larger vector databases
- More CPU cores for concurrent request handling
- SSD storage for faster vector operations

**Microservices Decomposition**:
```
API Gateway → UI Generation Service → RAG Service → Data Service
                                        ↓              ↓
                                  Vector Database  User Data Store
```

## Security Considerations

### 1. API Security

**Current Measures**:
- Environment variable for API keys
- CORS configuration for web clients
- Input validation through Pydantic models
- Error message sanitization

**Production Enhancements**:
- API key authentication
- Rate limiting per client
- Request size limitations
- HTTPS enforcement

### 2. Data Privacy

**User Data**:
- Local storage (no external data sharing)
- Structured format (predictable processing)
- No personally identifiable information in examples

**LLM Interactions**:
- Queries processed through secure APIs
- No persistent storage of user queries
- API keys managed through environment variables

### 3. Dependency Security

**Regular Updates**:
- Monitor security advisories for dependencies
- Automated dependency scanning
- Minimal dependency surface area
- Trusted package sources only

## Monitoring and Observability

### 1. Logging Strategy

**Structured Logging**:
```python
import logging
logger = logging.getLogger(__name__)

# Component-specific loggers
api_logger = logging.getLogger("api")
agent_logger = logging.getLogger("agent")
rag_logger = logging.getLogger("rag")
```

**Log Levels**:
- **DEBUG**: Detailed execution flow
- **INFO**: Request processing and status
- **WARNING**: Recoverable errors and performance issues
- **ERROR**: Failed requests and system errors

### 2. Metrics Collection

**Key Metrics**:
- Request latency (p50, p95, p99)
- Success/error rates
- LLM API usage and costs
- Vector database performance
- Memory and CPU utilization

**Monitoring Stack** (Production):
```
Application Metrics → Prometheus → Grafana Dashboard
                         ↓
                    AlertManager → Notification System
```

### 3. Health Checks

**Implemented Endpoints**:
- `/health`: Component readiness status
- `/`: Basic connectivity test

**Health Check Components**:
- Agent initialization status
- Vector database connectivity
- User data availability
- LLM API accessibility

## Future Architecture Evolution

### 1. Microservices Migration

**Phase 1**: Service Decomposition
```
Monolithic API → UI Generation Service + RAG Service + Data Service
```

**Phase 2**: Event-Driven Architecture
```
API Gateway → Event Bus → Microservices → Response Aggregation
```

### 2. Multi-Model Support

**Architecture Enhancement**:
```
Model Router → [Claude 3.5 Sonnet | GPT-4 | Local Models] → Response Merger
```

**Benefits**:
- Model comparison and A/B testing
- Cost optimization through model selection
- Reduced dependency on single provider
- Quality improvements through ensemble methods

### 3. Real-Time Features

**Streaming Responses**:
```
Client ←→ WebSocket ←→ Streaming LLM API
```

**Progressive UI Generation**:
- Stream UI components as they're generated
- Real-time user feedback integration
- Incremental UI updates and refinements

### 4. Edge Deployment

**Architecture Pattern**:
```
CDN Edge Locations → Cached Responses + Local Models → Origin Services
```

**Components**:
- Edge-cached common UI patterns
- Lightweight models for simple queries
- Origin fallback for complex generation
- Regional data compliance

This architecture documentation provides a comprehensive understanding of the system design, implementation decisions, and future evolution paths for the Huawei Analytics UI Generator.