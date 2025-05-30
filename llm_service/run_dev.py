#!/usr/bin/env python3
"""
Development runner for LLM service.
This script runs the LLM service in development mode using the virtual environment.
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for development
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB"] = "iot_metrics"
os.environ["MODEL_PATH"] = str(Path(__file__).parent / "models" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
os.environ["USE_MOCK_LLM"] = "false"
os.environ["USE_GPU"] = "auto"

def main():
    """Run the development server"""
    # Override environment variables for local development after any .env loading
    local_model_path = str(Path(__file__).parent / "models" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    
    # Force local development settings
    os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
    os.environ["MONGODB_DB"] = "iot_metrics"
    os.environ["MODEL_PATH"] = local_model_path
    os.environ["USE_MOCK_LLM"] = "false"
    os.environ["USE_GPU"] = "auto"
    
    print("🚀 Starting LLM Service in Development Mode")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🤖 Model Path: {os.environ.get('MODEL_PATH')}")
    print(f"🔗 MongoDB URI: {os.environ.get('MONGODB_URI')}")
    print(f"💾 Database: {os.environ.get('MONGODB_DB')}")
    print("-" * 50)
    
    # Check if model file exists
    model_path = os.environ.get('MODEL_PATH')
    if not os.path.exists(model_path):
        print(f"❌ Model file not found at: {model_path}")
        print("Please ensure the TinyLlama model is downloaded.")
        sys.exit(1)
    
    # Check model file size
    model_size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"✓ Model file found: {model_size_mb:.1f} MB")
    
    try:
        # Import and run the FastAPI app
        import uvicorn
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8081,  # Use different port to avoid conflicts
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
