from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Mapping
from datetime import datetime, timedelta
import os
import motor.motor_asyncio
import logging
import json
import asyncio
import platform
import subprocess
import sys
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_service")

# Environment variables with defaults
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "iot_metrics")
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
USE_GPU = os.getenv("USE_GPU", "auto").lower()  # auto, true, false
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
N_CTX = int(os.getenv("N_CTX", "2048"))
N_THREADS = int(os.getenv("N_THREADS", str(os.cpu_count() or 4)))

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

def detect_gpu_capabilities():
    """Detect available GPU capabilities"""
    gpu_info = {
        "cuda": False,
        "opencl": False,
        "metal": False,
        "vulkan": False
    }
    
    # Check CUDA
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_info["cuda"] = True
            logger.info("CUDA GPU detected")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check Metal (macOS)
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                  capture_output=True, text=True, timeout=5)
            if "Metal" in result.stdout:
                gpu_info["metal"] = True
                logger.info("Metal GPU detected")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    # Check OpenCL
    try:
        import pyopencl
        platforms = pyopencl.get_platforms()
        if platforms:
            gpu_info["opencl"] = True
            logger.info("OpenCL GPU detected")
    except ImportError:
        pass
    except Exception:
        pass
    
    return gpu_info

def get_llama_cpp_config():
    """Get optimal llama-cpp-python configuration based on available hardware"""
    gpu_caps = detect_gpu_capabilities()
    
    config = {
        "model_path": MODEL_PATH,
        "temperature": 0.7,
        "max_tokens": 1024,
        "n_ctx": 2048,
        "top_p": 1,
        "verbose": True,
    }
    
    if USE_GPU == "false":
        # Force CPU-only mode
        config.update({
            "n_gpu_layers": 0,
            "n_threads": os.cpu_count() or 4,
            "n_batch": 128,
            "f16_kv": False,
        })
        logger.info("Using CPU-only mode (forced)")
        
    elif USE_GPU == "true" or (USE_GPU == "auto" and any(gpu_caps.values())):
        # Try GPU acceleration - TinyLlama has fewer layers than larger models
        if gpu_caps["cuda"]:
            config.update({
                "n_gpu_layers": 22,  # TinyLlama has 22 layers total
                "n_batch": 512,
                "f16_kv": True,
            })
            logger.info("Using CUDA GPU acceleration")
            
        elif gpu_caps["opencl"]:
            config.update({
                "n_gpu_layers": 22,  # TinyLlama has 22 layers total
                "n_batch": 512,
                "f16_kv": True,
            })
            logger.info("Using OpenCL GPU acceleration")
            
        elif gpu_caps["metal"]:
            config.update({
                "n_gpu_layers": 22,  # TinyLlama has 22 layers total
                "n_batch": 512,
                "f16_kv": True,
            })
            logger.info("Using Metal GPU acceleration")
            
        else:
            # Fallback to CPU
            config.update({
                "n_gpu_layers": 0,
                "n_threads": os.cpu_count() or 4,
                "n_batch": 128,
                "f16_kv": False,
            })
            logger.info("GPU requested but not available, falling back to CPU")
    else:
        # Default CPU mode
        config.update({
            "n_gpu_layers": 0,
            "n_threads": os.cpu_count() or 4,
            "n_batch": 128,
            "f16_kv": False,
        })
        logger.info("Using CPU-only mode (default)")
    
    return config

# Mock LLM class for fallback
class MockLLM:
    def __init__(self):
        self.model_path = "mock_model"
        
    def __call__(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        # Extract context and query from prompt
        context_match = re.search(r"CONTEXT:\s*(.+?)\s*USER QUERY:", prompt, re.DOTALL)
        query_match = re.search(r"USER QUERY:\s*(.+?)\s*(?:Please provide|ANSWER:)", prompt, re.DOTALL)
        
        context_str = context_match.group(1) if context_match else ""
        query = query_match.group(1).strip() if query_match else "unknown query"
        
        try:
            # Parse context to get actual data
            if "latest_metrics" in context_str:
                # Extract metrics from context
                context_data = json.loads(context_str)
                latest_metrics = context_data.get("latest_metrics", [])
                stats = context_data.get("statistics", {})
                
                # Analyze query and provide relevant response
                query_lower = query.lower()
                
                if "living room" in query_lower:
                    living_room_metrics = [m for m in latest_metrics if m.get("location", "").lower() == "living room"]
                    if living_room_metrics:
                        temp_metric = next((m for m in living_room_metrics if m.get("type") == "temperature"), None)
                        humid_metric = next((m for m in living_room_metrics if m.get("type") == "humidity"), None)
                        
                        response_parts = []
                        if temp_metric:
                            response_parts.append(f"temperature is {temp_metric['value']}°{temp_metric['unit']}")
                        if humid_metric:
                            response_parts.append(f"humidity is {humid_metric['value']}{humid_metric['unit']}")
                        
                        if response_parts:
                            return f"Based on the latest readings from the Living Room Sensor, the {' and '.join(response_parts)}."
                
                elif "temperature" in query_lower:
                    temp_metrics = [m for m in latest_metrics if m.get("type") == "temperature"]
                    if temp_metrics:
                        temps = [f"{m['location']}: {m['value']}°{m['unit']}" for m in temp_metrics]
                        return f"Current temperature readings: {', '.join(temps)}."
                
                elif "humidity" in query_lower:
                    humid_metrics = [m for m in latest_metrics if m.get("type") == "humidity"]
                    if humid_metrics:
                        humids = [f"{m['location']}: {m['value']}{m['unit']}" for m in humid_metrics]
                        return f"Current humidity readings: {', '.join(humids)}."
                
                elif any(loc in query_lower for loc in ["kitchen", "bedroom", "bathroom", "garden"]):
                    location_name = None
                    for loc in ["kitchen", "bedroom", "bathroom", "garden"]:
                        if loc in query_lower:
                            location_name = loc.title()
                            break
                    
                    if location_name:
                        location_metrics = [m for m in latest_metrics if m.get("location", "").lower() == location_name.lower()]
                        if location_metrics:
                            readings = []
                            for metric in location_metrics:
                                if metric.get("type") == "temperature":
                                    readings.append(f"temperature: {metric['value']}°{metric['unit']}")
                                elif metric.get("type") == "humidity":
                                    readings.append(f"humidity: {metric['value']}{metric['unit']}")
                            
                            if readings:
                                return f"Latest readings from the {location_name} Sensor: {', '.join(readings)}."
                
                # Default response with stats
                device_count = stats.get("device_count", 0)
                total_readings = stats.get("total_temperature_readings", 0) + stats.get("total_humidity_readings", 0)
                return f"Based on {total_readings} readings from {device_count} IoT devices, I can provide information about temperature and humidity across different locations. Please specify which device or location you're interested in."
                
        except Exception as e:
            logger.error(f"Error in MockLLM processing: {e}")
        
        # Fallback simple responses
        if "temperature" in query.lower():
            return "Based on the latest metrics, the temperature readings are available for all monitored locations."
        elif "humidity" in query.lower():
            return "Current humidity readings are available for all monitored devices."
        else:
            return "This is a simulated response from the mock LLM. The actual Llama model is not available. Please check that you have downloaded the correct model file."

# Initialize LLM
llm = None

try:
    # Import langchain components with fallback
    try:
        from langchain_community.llms import LlamaCpp
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        langchain_available = True
    except ImportError:
        logger.warning("LangChain not available, using basic implementation")
        langchain_available = False
    
    # Check if model file exists and has valid size
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 10485760:  # >10MB
        if langchain_available:
            # Get optimal configuration
            config = get_llama_cpp_config()
            
            # Initialize LLM with detected configuration
            llm = LlamaCpp(**config)
            logger.info(f"LLM initialized successfully using model: {MODEL_PATH}")
            logger.info(f"Configuration: {config}")
        else:
            logger.warning("LangChain not available, using mock LLM")
            llm = MockLLM()
    else:
        # Model file doesn't exist or is too small (placeholder)
        logger.warning(f"Model file at {MODEL_PATH} is missing or too small, using mock LLM")
        llm = MockLLM()
        
except Exception as e:
    logger.warning(f"Error initializing LLM: {e}")
    logger.info("Using mock LLM for development/testing")
    llm = MockLLM()

# FastAPI app
app = FastAPI(title="IoT LLM Service", version="1.0.0")

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
        
        # Create prompt
        template = """You are an IoT system assistant that provides information about temperature and humidity metrics from various devices.
Use the following context to answer the user's question.

CONTEXT:
{context}

USER QUERY:
{query}

Please provide a clear, concise answer based only on the data provided. If the information is not available in the context, explain what is missing.

ANSWER:"""
        
        prompt_text = template.format(context=context_str, query=query)
        
        # Handle different LLM types
        if isinstance(llm, MockLLM):
            # Use MockLLM directly
            result = llm(prompt_text)
        else:
            # Use modern LangChain LCEL pattern
            from langchain_core.prompts import PromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            # Create prompt template
            prompt = PromptTemplate(
                template=template,
                input_variables=["context", "query"]
            )
            
            # Create chain using LCEL (LangChain Expression Language)
            chain = prompt | llm | StrOutputParser()
            
            # Run the chain
            result = chain.invoke({"context": context_str, "query": query})
        
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
