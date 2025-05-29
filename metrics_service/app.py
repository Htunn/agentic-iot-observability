from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import motor.motor_asyncio
import logging
from bson import ObjectId

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("metrics_service")

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "iot_metrics")

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

# FastAPI app
app = FastAPI(title="IoT Metrics Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Metric(BaseModel):
    id: str
    device_id: str
    device_name: str
    location: str
    type: str
    value: float
    unit: str
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "device_id": "device_001",
                "device_name": "Living Room Sensor",
                "location": "Living Room",
                "type": "temperature",
                "value": 22.5,
                "unit": "C",
                "timestamp": "2023-09-05T14:48:00.000Z"
            }
        }

class MetricResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None

# API endpoints
@app.get("/", response_model=MetricResponse)
async def root():
    """Root endpoint - health check"""
    return {"success": True, "message": "IoT Metrics Service is running"}

@app.post("/metrics", response_model=MetricResponse)
async def create_metric(metric: Metric):
    """Save a new metric to the database"""
    try:
        metric_dict = metric.dict()
        result = await db.metrics.insert_one(metric_dict)
        logger.info(f"Inserted metric with ID: {result.inserted_id}")
        return {"success": True, "message": "Metric saved successfully"}
    except Exception as e:
        logger.error(f"Error saving metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics", response_model=MetricResponse)
async def get_metrics(
    device_id: Optional[str] = None,
    location: Optional[str] = None,
    metric_type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    skip: int = 0
):
    """Get metrics with optional filtering"""
    try:
        # Build filter
        query = {}
        if device_id:
            query["device_id"] = device_id
        if location:
            query["location"] = location
        if metric_type:
            query["type"] = metric_type
        
        # Time range filter
        if start_time or end_time:
            query["timestamp"] = {}
            if start_time:
                query["timestamp"]["$gte"] = start_time
            if end_time:
                query["timestamp"]["$lte"] = end_time
        
        # Execute query
        cursor = db.metrics.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        metrics = await cursor.to_list(length=limit)
        
        # Convert ObjectId to str for JSON serialization
        for metric in metrics:
            if '_id' in metric:
                metric['_id'] = str(metric['_id'])
        
        return {
            "success": True, 
            "data": metrics,
            "message": f"Retrieved {len(metrics)} metrics"
        }
    
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/latest", response_model=MetricResponse)
async def get_latest_metrics(metric_type: Optional[str] = None):
    """Get latest metric for each device"""
    try:
        # Get unique device IDs
        device_ids = await db.metrics.distinct("device_id")
        
        latest_metrics = []
        for device_id in device_ids:
            # Filter by metric_type if provided
            query = {"device_id": device_id}
            if metric_type:
                query["type"] = metric_type
            
            # Get latest metric for this device
            cursor = db.metrics.find(query).sort("timestamp", -1).limit(1)
            metric = await cursor.to_list(length=1)
            if metric:
                metric[0]['_id'] = str(metric[0]['_id'])
                latest_metrics.append(metric[0])
        
        return {
            "success": True,
            "data": latest_metrics,
            "message": f"Retrieved latest metrics for {len(latest_metrics)} devices"
        }
    
    except Exception as e:
        logger.error(f"Error retrieving latest metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/stats", response_model=MetricResponse)
async def get_metric_stats(
    device_id: Optional[str] = None,
    location: Optional[str] = None, 
    metric_type: str = "temperature",
    hours: int = 24
):
    """Get statistical data for metrics"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Build filter
        query = {"type": metric_type}
        if device_id:
            query["device_id"] = device_id
        if location:
            query["location"] = location
        query["timestamp"] = {"$gte": start_time.isoformat(), "$lte": end_time.isoformat()}
        
        # Get data for statistics
        cursor = db.metrics.find(query)
        metrics = await cursor.to_list(length=1000)  # Adjust limit as needed
        
        if not metrics:
            return {
                "success": True,
                "data": {"count": 0},
                "message": "No metrics found for the specified criteria"
            }
        
        # Calculate statistics
        values = [m["value"] for m in metrics]
        stats = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[0] if values else None
        }
        
        return {
            "success": True,
            "data": stats,
            "message": f"Calculated statistics for {len(values)} {metric_type} metrics"
        }
    
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
