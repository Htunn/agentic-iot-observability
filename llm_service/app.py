from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import motor.motor_asyncio
import logging
import json
import asyncio
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_service")

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "iot_metrics")
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/llama-2-7b-chat.Q4_K_M.gguf")

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

# Initialize LLM
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

try:
    # Check if model file exists and has valid size
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 10485760:  # >10MB
        # Initialize LLM inside a try block to handle cases where the model might not be available
        llm = LlamaCpp(
            model_path=MODEL_PATH,
            temperature=0.7,
            max_tokens=1024,
            n_ctx=2048,
            top_p=1,
            callback_manager=callback_manager,
            verbose=True,
        )
        logger.info(f"LLM initialized successfully with model: {MODEL_PATH}")
    else:
        # Model file doesn't exist or is too small (placeholder)
        raise FileNotFoundError(f"Model file at {MODEL_PATH} is missing or too small")
except Exception as e:
    logger.warning(f"Error initializing LLM: {e}")
    logger.info("Using mock LLM for development/testing")
    # Use a placeholder LLM that returns simulated responses for testing
    class MockLLM:
        def __call__(self, prompt):
            import re
            # Extract query from prompt
            query_match = re.search(r"USER QUERY:\s*(.+?)\s*ANSWER:", prompt, re.DOTALL)
            query = query_match.group(1) if query_match else "unknown query"
            
            # Simple response logic based on query content
            if "temperature" in query.lower():
                return "Based on the latest metrics, the temperature is around 22.5°C."
            elif "humidity" in query.lower():
                return "The current humidity level is approximately 55%."
            elif "living room" in query.lower():
                return "The Living Room Sensor reports a temperature of 23.1°C and humidity of 48%."
            elif "kitchen" in query.lower():
                return "The Kitchen Sensor reports a temperature of 24.3°C and humidity of 62%."
            else:
                return "This is a simulated response from the mock LLM. The actual model is not available. Please check that you have downloaded the Llama model and set the correct MODEL_PATH."
    llm = MockLLM()
    logger.info("Mock LLM initialized for development/testing")

# FastAPI app
app = FastAPI(title="IoT LLM Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's natural language query about IoT metrics")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context for the query")

class QueryResponse(BaseModel):
    answer: str
    metadata: Optional[Dict[str, Any]] = None

# Helper functions
async def get_latest_metrics():
    """Retrieve the latest metrics for each device from MongoDB"""
    try:
        # Get unique device IDs
        device_ids = await db.metrics.distinct("device_id")
        
        all_metrics = []
        for device_id in device_ids:
            # Get latest temperature for this device
            temp_cursor = db.metrics.find({"device_id": device_id, "type": "temperature"}).sort("timestamp", -1).limit(1)
            temp_metric = await temp_cursor.to_list(length=1)
            
            # Get latest humidity for this device
            humid_cursor = db.metrics.find({"device_id": device_id, "type": "humidity"}).sort("timestamp", -1).limit(1)
            humid_metric = await humid_cursor.to_list(length=1)
            
            if temp_metric and humid_metric:
                all_metrics.append({
                    "device_id": device_id,
                    "device_name": temp_metric[0]["device_name"],
                    "location": temp_metric[0]["location"],
                    "temperature": {
                        "value": temp_metric[0]["value"],
                        "unit": temp_metric[0]["unit"],
                        "timestamp": temp_metric[0]["timestamp"]
                    },
                    "humidity": {
                        "value": humid_metric[0]["value"],
                        "unit": humid_metric[0]["unit"],
                        "timestamp": humid_metric[0]["timestamp"]
                    }
                })
        
        return all_metrics
    except Exception as e:
        logger.error(f"Error getting latest metrics: {e}")
        return []

async def get_statistics():
    """Get statistical information about metrics"""
    try:
        # Get devices and locations
        devices = await db.metrics.distinct("device_id")
        locations = await db.metrics.distinct("location")
        
        # Get counts
        temp_count = await db.metrics.count_documents({"type": "temperature"})
        humid_count = await db.metrics.count_documents({"type": "humidity"})
        
        # Get time range
        first_doc = await db.metrics.find_one({}, sort=[("timestamp", 1)])
        last_doc = await db.metrics.find_one({}, sort=[("timestamp", -1)])
        
        start_time = first_doc["timestamp"] if first_doc else None
        end_time = last_doc["timestamp"] if last_doc else None
        
        return {
            "device_count": len(devices),
            "location_count": len(locations),
            "total_temperature_readings": temp_count,
            "total_humidity_readings": humid_count,
            "first_reading_time": start_time,
            "last_reading_time": end_time,
            "devices": devices,
            "locations": locations
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {}

async def process_query(query: str):
    """Process a natural language query about IoT metrics"""
    try:
        # Get latest metrics and statistics for context
        latest_metrics = await get_latest_metrics()
        stats = await get_statistics()
        
        # Create context for the LLM
        context = {
            "latest_metrics": latest_metrics,
            "statistics": stats,
            "current_time": datetime.utcnow().isoformat()
        }
        
        # Convert context to string
        context_str = json.dumps(context, indent=2)
        
        # Create prompt template
        template = """
        You are an IoT system assistant that provides information about temperature and humidity metrics from various devices.
        Use the following context to answer the user's question.
        
        CONTEXT:
        {context}
        
        USER QUERY:
        {query}
        
        Please provide a clear, concise answer based only on the data provided. If the information is not available in the context, explain what is missing.
        
        ANSWER:
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "query"]
        )
        
        # Create LLM chain
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Run the chain
        result = chain.run(context=context_str, query=query)
        
        return result.strip()
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return f"I apologize, but I encountered an error while processing your query: {str(e)}"

# API endpoints
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint - health check"""
    return {"status": "ok", "service": "IoT LLM Service"}

@app.get("/health")
async def health_check():
    """Health check endpoint required by Docker container healthcheck"""
    try:
        # Check MongoDB connection
        await db.command("ping")
        return {"status": "healthy", "message": "Service is running"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "message": str(e)}
        )

@app.post("/query", response_model=QueryResponse)
async def query_llm(request: QueryRequest):
    """Process a natural language query about IoT metrics"""
    try:
        answer = await process_query(request.query)
        
        # Get metadata for response
        stats = await get_statistics()
        
        return {
            "answer": answer,
            "metadata": {
                "processed_at": datetime.utcnow().isoformat(),
                "metrics_count": stats.get("total_temperature_readings", 0) + stats.get("total_humidity_readings", 0),
                "device_count": stats.get("device_count", 0),
                "query": request.query
            }
        }
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=Dict[str, Any])
async def get_llm_status():
    """Get status of the LLM service and available metrics"""
    try:
        stats = await get_statistics()
        return {
            "llm_status": "ready" if MODEL_PATH and os.path.exists(MODEL_PATH) else "model_not_found",
            "model_path": MODEL_PATH,
            "metrics_available": stats.get("total_temperature_readings", 0) > 0,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
