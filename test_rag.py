#!/usr/bin/env python3
"""
Test script to verify RAG system functionality
Run this on your server to diagnose RAG issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_rag_system():
    """Test the RAG system components individually"""
    print("🔍 Testing RAG System Components\n")
    
    # Check environment variables
    print("1. Environment Variables:")
    openai_key = os.getenv('OPENAI_API_KEY')
    print(f"   OPENAI_API_KEY: {'✅ Present' if openai_key else '❌ Missing'}")
    if openai_key:
        print(f"   Key format: {'✅ Valid' if openai_key.startswith('sk-') else '❌ Invalid'}")
    print()
    
    # Check data files
    print("2. Data Files:")
    data_file = "data/user_activity/user_data_for_vectordb.txt"
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            content = f.read()
        print(f"   ✅ Data file exists: {len(content)} characters")
        print(f"   Preview: {content[:100]}...")
    else:
        print(f"   ❌ Data file missing: {data_file}")
    print()
    
    # Check ChromaDB directory
    print("3. ChromaDB Directory:")
    chroma_dir = "chroma_db"
    if os.path.exists(chroma_dir):
        files = os.listdir(chroma_dir)
        print(f"   ✅ ChromaDB directory exists with {len(files)} files: {files}")
    else:
        print(f"   ❌ ChromaDB directory missing: {chroma_dir}")
    print()
    
    # Test RAG Manager initialization
    print("4. RAG Manager Test:")
    if not openai_key:
        print("   ❌ Cannot test RAG Manager - OpenAI key missing")
        return
    
    try:
        sys.path.append('.')
        from src.rag import RAGManager
        
        print("   📝 Initializing RAG Manager...")
        rag_manager = RAGManager(api_key=openai_key)
        
        if os.path.exists(data_file):
            print("   📝 Initializing vector store...")
            rag_manager.initialize_vector_store(data_file)
            print("   ✅ Vector store initialized")
            
            # Test query
            print("   📝 Testing query...")
            results = rag_manager.query_user_data("what is my current plan", k=3)
            print(f"   ✅ Query successful: {len(results) if results else 0} results")
            
            if results:
                print("   📄 Sample result:")
                print(f"      {results[0][:200]}...")
            else:
                print("   ⚠️  No results found")
        else:
            print("   ❌ Cannot initialize vector store - data file missing")
            
    except Exception as e:
        print(f"   ❌ RAG Manager test failed: {e}")
    
    print("\n🏁 RAG System Test Complete")

if __name__ == "__main__":
    test_rag_system()