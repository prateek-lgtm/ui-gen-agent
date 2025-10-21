"""
FastAPI server for RAG Chatbot
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import chromadb
import openai
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(title="RAG Chatbot API", description="Natural language queries for your activity data")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    query: str

class RAGChatbotAPI:
    def __init__(self):
        """Initialize the RAG chatbot for API"""
        # Set up OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        api_key = api_key.strip().strip('"').strip("'")
        if not api_key.startswith('sk-'):
            raise ValueError("Invalid API key format")
        
        openai.api_key = api_key
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="./rag_chatbot_db")
        self.embedding_model = "text-embedding-3-large"
        
        # Get collection
        try:
            self.collection = self.client.get_collection("activity_data")
        except:
            raise ValueError("No data found. Please run rag_chatbot.py first to ingest data.")
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using OpenAI"""
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []
    
    def retrieve_context(self, query: str, n_results: int = 3) -> List[str]:
        """Retrieve relevant context from ChromaDB"""
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                return []
            
            # Search for similar documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def generate_response(self, query: str, context: List[str]) -> str:
        """Generate response using LLM"""
        try:
            context_text = "\n\n".join(context)
            
            system_prompt = """You are a helpful assistant that answers questions about user activity data, business plans, events, and usage patterns. 

You have access to the user's activity data including:
- Current business plans and pricing
- Upcoming events and entertainment
- Social media usage patterns
- User profile and account information

Use the provided context to answer questions accurately and helpfully. If the information isn't in the context, say so politely."""

            user_prompt = f"""Context:
{context_text}

User Question: {query}

Please provide a clear, helpful answer based on the context above."""

            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while generating a response."
    
    def chat(self, query: str) -> str:
        """Main chat function"""
        context = self.retrieve_context(query)
        
        if not context:
            return "I couldn't find relevant information to answer your question."
        
        return self.generate_response(query, context)

# Initialize chatbot
try:
    chatbot = RAGChatbotAPI()
except Exception as e:
    print(f"Failed to initialize chatbot: {e}")
    chatbot = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RAG Chatbot API", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    return {"status": "healthy", "model": "text-embedding-3-large"}

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    """Chat endpoint"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        response = chatbot.chat(request.query)
        return QueryResponse(response=response, query=request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/examples")
async def get_examples():
    """Get example queries"""
    return {
        "examples": [
            "What is my current plan?",
            "What are the upcoming events?",
            "How much data do I use on YouTube?",
            "When does my plan expire?",
            "What events are happening in Delhi?",
            "Based on my usage suggest a plan to buy"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)