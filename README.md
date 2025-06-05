# Agentic IoT Observability Project

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

### Agentic LLM Workflow Sequence Diagram

```mermaid
sequenceDiagram
    participant User as User/API Client
    participant LLM as LLM Service
    participant Agent as LLM Agent
    participant DB as MongoDB
    participant Metrics as Metrics Service
    participant Analysis as Analysis Engine

    rect rgb(240, 240, 255)
        Note over User, Analysis: Agentic Query Processing
        User->>LLM: POST /query {"query": "Is there a temperature anomaly in the kitchen?"}
        
        LLM->>Agent: Parse query intent
        Agent->>Agent: Determine required metrics and analysis
        
        Agent->>DB: Query historical temperature data for kitchen
        DB-->>Agent: Return historical temperature data
        
        Agent->>Analysis: Perform anomaly detection
        Analysis->>Analysis: Apply statistical algorithms
        Analysis-->>Agent: Anomaly analysis results
        
        Agent->>Metrics: GET /metrics?location=kitchen&hours=24
        Metrics->>DB: Query recent kitchen metrics
        DB-->>Metrics: Return kitchen data
        Metrics-->>Agent: Latest kitchen metrics
        
        Agent->>Agent: Synthesize response with context
        Agent-->>LLM: Structured analysis with explanation
        
        LLM-->>User: "I've analyzed the kitchen temperature data. There appears to be an anomaly at 14:30 today, where the temperature spiked to 32°C, which is 8°C above the normal range for that time of day."
    end
    
    rect rgb(255, 240, 240)
        Note over User, Analysis: Autonomous Action Recommendation
        User->>LLM: POST /query {"query": "What should I do about high humidity in the basement?"}
        
        LLM->>Agent: Parse query intent
        Agent->>Agent: Identify action recommendation task
        
        Agent->>DB: Query humidity patterns in basement
        DB-->>Agent: Return humidity history
        
        Agent->>DB: Query related temperature data
        DB-->>Agent: Return temperature data
        
        Agent->>Analysis: Cross-analyze humidity and temperature
        Analysis-->>Agent: Correlation analysis
        
        Agent->>Agent: Generate recommended actions
        Agent-->>LLM: Structured recommendations
        
        LLM-->>User: "Based on the data, basement humidity has been above 75% for 3 days. I recommend: 1) Check for water leaks near the north wall where temperature readings are also abnormal, 2) Improve ventilation - current air exchange rate is low, 3) Consider a dehumidifier rated for your basement square footage. Would you like me to explain any of these recommendations in more detail?"
    end
```

### Component Diagram

```mermaid
graph TB
    subgraph "Data Generation Layer"
        IoT[IoT Simulator]
        RealIoT[Real IoT Devices]
    end
    
    subgraph "Data Collection Layer"
        MetricsAPI[Metrics Service API]
        MetricsAPI -->|Store| MongoDB[(MongoDB)]
    end
    
    subgraph "Analytics Layer"
        LLM[LLM Service]
        LLM -->|Query| MongoDB
        LLM -->|Embeddings| VectorDB[(Vector Store)]
    end
    
    subgraph "Visualization Layer"
        Grafana[Grafana Dashboards]
        Grafana -->|Query| MetricsAPI
    end
    
    subgraph "User Interaction Layer"
        CLI[Command Line Interface]
        WebUI[Web UI]
        API[REST API]
        
        CLI -->|Queries| LLM
        WebUI -->|Visualization| Grafana
        WebUI -->|Queries| LLM
        API -->|CRUD Operations| MetricsAPI
        API -->|Natural Language Queries| LLM
    end
    
    subgraph "Agent Components"
        QueryParser[Query Parser]
        ContextBuilder[Context Builder]
        ResponseGenerator[Response Generator]
        ActionRecommender[Action Recommender]
        AnomalyDetector[Anomaly Detector]
        
        LLM -->|Uses| QueryParser
        LLM -->|Uses| ContextBuilder
        LLM -->|Uses| ResponseGenerator
        LLM -->|Uses| ActionRecommender
        LLM -->|Uses| AnomalyDetector
    end
    
    IoT -->|Generate Data| MetricsAPI
    RealIoT -->|Send Data| MetricsAPI
    
    style IoT fill:#f9f9ff,stroke:#9370db,stroke-width:2px
    style LLM fill:#f9f9ff,stroke:#9370db,stroke-width:2px
    style Grafana fill:#f9f9ff,stroke:#9370db,stroke-width:2px
    style MongoDB fill:#f5f5f5,stroke:#666,stroke-width:2px
    style VectorDB fill:#f5f5f5,stroke:#666,stroke-width:2px
```

### Deployment Diagram

```mermaid
flowchart TB
    subgraph "Host Machine / Cloud Provider"
        subgraph "Docker Environment"
            subgraph "Data Processing"
                iot[IoT Simulator Container]
                metrics[Metrics Service Container]
                mongo[MongoDB Container]
                
                iot -->|port 8000| metrics
                metrics -->|port 27017| mongo
            end
            
            subgraph "Intelligence Layer"
                llm[LLM Service Container]
                llm -->|port 27017| mongo
            end
            
            subgraph "Visualization"
                grafana[Grafana Container]
                grafana -->|port 8000| metrics
            end
            
            subgraph "Persistence Volumes"
                mongodata[MongoDB Volume]
                modeldata[LLM Model Volume]
                grafanadata[Grafana Volume]
                
                mongo -.-> mongodata
                llm -.-> modeldata
                grafana -.-> grafanadata
            end
        end
        
        user[User / Client] -->|port 3000| grafana
        user -->|port 8000| metrics
        user -->|port 8080| llm
    end
    
    style iot fill:#e6f7ff,stroke:#1890ff
    style metrics fill:#e6f7ff,stroke:#1890ff
    style mongo fill:#f0f5ff,stroke:#597ef7
    style llm fill:#f6ffed,stroke:#52c41a
    style grafana fill:#fff7e6,stroke:#fa8c16
    style user fill:#fff0f6,stroke:#eb2f96
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

### Production Mode (Docker)

Send queries to the LLM service API endpoint:

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current temperature in the living room?"}'
```

### Development Mode (Local)

For local development with hot reload and GPU acceleration:

```bash
# Navigate to LLM service directory
cd llm_service

# Run the development server (requires TinyLlama model)
python3 run_dev.py
```

The development server will:
- Start on port 8082 (to avoid conflicts with containerized service)
- Enable hot reload for code changes
- Use local MongoDB connection (mongodb://localhost:27017/)
- Automatically detect and use Metal GPU acceleration (on macOS)
- Load the TinyLlama model from `llm_service/models/`

Access the development API at:
- API: http://localhost:8082
- Documentation: http://localhost:8082/docs
- Health check: http://localhost:8082/health

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
