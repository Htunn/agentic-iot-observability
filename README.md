# IoT Observability Project

This project implements a complete observability solution for IoT devices, collecting temperature and humidity metrics, storing them in MongoDB, visualizing them in Grafana, and enabling natural language queries through an LLM (Llama) service.

## System Architecture

The system consists of the following components:

- **IoT Simulator**: Generates simulated temperature and humidity metrics from virtual IoT devices
- **Metrics Service**: REST API service that collects and stores metrics in MongoDB
- **MongoDB**: Database for storing time-series metrics data
- **LLM Service**: API service that uses Llama model to answer natural language queries about the IoT metrics
- **Grafana**: Visualization dashboard for metrics monitoring

All components are containerized and orchestrated using Docker Compose.

### Data Flow Sequence Diagram

```mermaid
sequenceDiagram
    participant IoT as IoT Simulator
    participant Metrics as Metrics Service
    participant DB as MongoDB
    participant Grafana as Grafana Dashboard
    participant LLM as LLM Service
    participant User as User/API Client

    Note over IoT, User: System Startup & Data Collection Flow
    
    rect rgb(240, 248, 255)
        Note over IoT, DB: Continuous Data Generation (Every 5 seconds)
        IoT->>IoT: Generate temperature & humidity for 5 devices
        IoT->>Metrics: POST /metrics (device data)
        Metrics->>DB: Store metric in iot_metrics collection
        Metrics-->>IoT: 200 OK
    end

    rect rgb(248, 255, 240)
        Note over Grafana, DB: Real-time Visualization
        Grafana->>Metrics: GET /metrics?metric_type=temperature&limit=100
        Metrics->>DB: Query temperature metrics
        DB-->>Metrics: Return temperature data
        Metrics-->>Grafana: JSON response with metrics
        
        Grafana->>Metrics: GET /metrics?metric_type=humidity&limit=100
        Metrics->>DB: Query humidity metrics
        DB-->>Metrics: Return humidity data
        Metrics-->>Grafana: JSON response with metrics
        
        Note over Grafana: Update charts and visualizations
    end

    rect rgb(255, 248, 240)
        Note over User, DB: Natural Language Queries
        User->>LLM: POST /query {"query": "What's the temperature in living room?"}
        LLM->>DB: Query latest metrics for context
        DB-->>LLM: Return recent IoT data
        LLM->>LLM: Process with Llama model
        LLM-->>User: Natural language response
    end

    rect rgb(248, 240, 255)
        Note over User, Metrics: Direct API Access
        User->>Metrics: GET /metrics?device_id=device_001
        Metrics->>DB: Query device-specific metrics
        DB-->>Metrics: Return device metrics
        Metrics-->>User: JSON response
        
        User->>LLM: GET /status
        LLM->>DB: Get metrics statistics
        DB-->>LLM: Return stats
        LLM-->>User: Service status & metrics summary
    end

    Note over IoT, User: Health Monitoring
    IoT->>Metrics: Health check (every 30s)
    Grafana->>Grafana: Health check (every 30s)
    LLM->>LLM: Health check (every 30s)
```

### Component Interactions

1. **Data Generation**: IoT Simulator continuously generates temperature and humidity metrics for 5 virtual devices
2. **Data Storage**: Metrics Service receives and stores data in MongoDB with proper indexing
3. **Visualization**: Grafana queries the Metrics Service API to display real-time charts and dashboards
4. **AI Queries**: LLM Service processes natural language queries by retrieving context from MongoDB and using the Llama model
5. **Health Monitoring**: All services include health checks for reliability and monitoring

## Prerequisites

- Docker and Docker Compose
- At least 8GB of RAM (for running the Llama model)
- Internet connection (for downloading Docker images and the Llama model)

## Getting Started

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd iot-observability-aiops
   ```

2. Start the system:
   ```bash
   docker compose up -d
   ```

3. Access the services:
   - Grafana: http://localhost:3000 (username: admin, password: admin)
   - Metrics Service API: http://localhost:8000
   - LLM Service API: http://localhost:8080

## Using the LLM Service

The LLM service allows you to query IoT metrics using natural language. Example queries:

- What's the current temperature in the living room?
- Show me the humidity trends in the kitchen for the last hour
- Which room is the hottest right now?
- What's the average temperature across all sensors?

Send queries to the LLM service API endpoint:

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current temperature in the living room?"}'
```

## Project Structure

```
.
├── docker-compose.yml       # Docker Compose configuration
├── iot_simulator/           # IoT device simulator
│   ├── Dockerfile           # Docker configuration for simulator
│   ├── requirements.txt     # Python dependencies
│   └── simulator.py         # Simulator implementation
├── metrics_service/         # Metrics collection service
│   ├── Dockerfile           # Docker configuration for metrics service
│   ├── app.py               # FastAPI implementation
│   └── requirements.txt     # Python dependencies
├── llm_service/             # LLM service for natural language queries
│   ├── Dockerfile           # Docker configuration for LLM service
│   ├── app.py               # FastAPI implementation
│   ├── entrypoint.sh        # Script to download the Llama model
│   └── requirements.txt     # Python dependencies
└── grafana/                 # Grafana configuration
    ├── dashboards/          # Pre-built dashboards
    └── provisioning/        # Provisioning configuration
        ├── dashboards/      # Dashboard provisioning
        └── datasources/     # Data source provisioning
```

## Customization

### Modifying Simulation Parameters

Edit environment variables in `docker-compose.yml` to change:
- `SIMULATION_INTERVAL`: Time between data points (seconds)
- Add more virtual devices by editing `simulator.py`

### Adding New Metrics

1. Update `simulator.py` to generate new metric types
2. Modify `metrics_service/app.py` to handle the new metric types
3. Update Grafana dashboards to visualize the new metrics

### Changing LLM Model

1. Update `MODEL_PATH` environment variable in `docker-compose.yml`
2. Modify `llm_service/entrypoint.sh` to download the desired model

## License

MIT
