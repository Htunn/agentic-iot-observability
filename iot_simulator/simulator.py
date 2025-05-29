import os
import time
import random
import json
import requests
import logging
import sys
from datetime import datetime
import uuid
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('iot_simulator')

# Configure requests with retry strategy
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http_session = requests.Session()
http_session.mount("http://", adapter)
http_session.mount("https://", adapter)

# Environment variables
SIMULATION_INTERVAL = int(os.getenv('SIMULATION_INTERVAL', '5'))
METRICS_SERVICE_URL = os.getenv('METRICS_SERVICE_URL', 'http://localhost:8000/metrics')

# Define device IDs and their locations
DEVICES = [
    {"id": "device_001", "name": "Living Room Sensor", "location": "Living Room"},
    {"id": "device_002", "name": "Bedroom Sensor", "location": "Bedroom"},
    {"id": "device_003", "name": "Kitchen Sensor", "location": "Kitchen"},
    {"id": "device_004", "name": "Bathroom Sensor", "location": "Bathroom"},
    {"id": "device_005", "name": "Outdoor Sensor", "location": "Garden"}
]

def generate_temperature(location):
    """Generate realistic temperature values based on location"""
    base_temp = 22.0  # baseline room temperature in Celsius
    
    if location == "Living Room":
        return round(base_temp + random.uniform(-2, 3), 1)
    elif location == "Bedroom":
        return round(base_temp + random.uniform(-3, 1), 1)
    elif location == "Kitchen":
        return round(base_temp + random.uniform(0, 5), 1)
    elif location == "Bathroom":
        return round(base_temp + random.uniform(-1, 4), 1)
    elif location == "Garden":
        return round(base_temp + random.uniform(-10, 15), 1)
    
    return round(base_temp + random.uniform(-5, 5), 1)

def generate_humidity(location):
    """Generate realistic humidity values based on location"""
    base_humidity = 50.0  # baseline humidity percentage
    
    if location == "Living Room":
        return round(base_humidity + random.uniform(-10, 10), 1)
    elif location == "Bedroom":
        return round(base_humidity + random.uniform(-15, 5), 1)
    elif location == "Kitchen":
        return round(base_humidity + random.uniform(0, 20), 1)
    elif location == "Bathroom":
        return round(base_humidity + random.uniform(10, 30), 1)
    elif location == "Garden":
        return round(base_humidity + random.uniform(-20, 40), 1)
    
    return round(base_humidity + random.uniform(-20, 20), 1)

def send_metric(device, metric_type, value):
    """Send metric to metrics service"""
    timestamp = datetime.utcnow().isoformat()
    metric_id = str(uuid.uuid4())
    
    payload = {
        "id": metric_id,
        "device_id": device["id"],
        "device_name": device["name"],
        "location": device["location"],
        "type": metric_type,
        "value": value,
        "unit": "C" if metric_type == "temperature" else "%",
        "timestamp": timestamp
    }
    
    try:
        # Use session with retry strategy
        response = http_session.post(
            METRICS_SERVICE_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10  # Add a timeout
        )
        
        if response.status_code == 200:
            logger.info(f"Sent {metric_type} metric for {device['name']}: {value}")
        else:
            logger.error(f"Failed to send metric: {response.status_code} - {response.text}")
    
    except Exception as e:
        logger.error(f"Error sending metric: {e}")

def simulate_metrics():
    """Main simulation loop"""
    logger.info(f"Starting IoT metrics simulation. Sending data every {SIMULATION_INTERVAL} seconds")
    
    while True:
        for device in DEVICES:
            # Generate temperature
            temp = generate_temperature(device["location"])
            send_metric(device, "temperature", temp)
            
            # Generate humidity
            humidity = generate_humidity(device["location"])
            send_metric(device, "humidity", humidity)
        
        # Wait for next interval
        time.sleep(SIMULATION_INTERVAL)

if __name__ == "__main__":
    # Wait a bit to ensure metrics service is up
    logger.info("Waiting for metrics service to be available...")
    time.sleep(5)
    
    simulate_metrics()
