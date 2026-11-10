# Logistics Streaming Analytics Pipeline

[![CI](https://github.com/Apc0015/Logistics-Streaming-Analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/Apc0015/Logistics-Streaming-Analytics/actions/workflows/ci.yml)

I built this real-time logistics analytics platform to simulate, stream, and monitor high-frequency fleet telemetry. It combines a streaming event generator (300+ events/min), an Azure PostgreSQL relational backbone, an Isolation Forest anomaly detector, and delivery-duration prediction models served through an interactive Streamlit dashboard.

---

## What I Built

Logistics tracking often suffers from disconnected telemetry, late anomaly alerts (such as fuel theft or engine overheating), and static ETA estimations. I designed this project to handle end-to-end event generation, storage, real-time ML inference, and dashboard monitoring:

1. **Streaming Telemetry Generator**: Generates 300+ simulated tracking events per minute for active shipments, modeling realistic speed, fuel levels, temperature readings, and geographic coordinates across US routes.
2. **Relational Data Layer**: Integrated with Azure Database for PostgreSQL across 7 relational tables tracking drivers, vehicles, routes, active shipments, and model inferences.
3. **Real-Time Anomaly Detection**: Built an `IsolationForest` detector trained on speed, fuel, temperature, humidity, and route duration to flag transit outliers (e.g., severe speed spikes or sudden fuel depletion).
4. **Predictive Delivery Modeling**: Implemented batch forecasting with `RandomForestRegressor` for ETA and delay minutes, coupled with `SGDRegressor` for incremental online weight updates as new shipment events arrive.
5. **Interactive Operations Dashboard**: Built in Streamlit with Plotly visualizations to monitor active fleet health, track route anomalies on live maps, and run manual ML prediction scenarios.

---

## System Architecture

```
[ Synthetic Fleet Generator ]
            │  (300+ events/min: speed, fuel, temp, lat/lon)
            ▼
[ Azure PostgreSQL Database ]
    ├── drivers / vehicles / routes
    ├── shipments & shipment_tracking
    └── outlier_detections & ml_predictions
            │
            ├──► [ Isolation Forest ] ──► Flags anomalies (fuel drops, speed anomalies)
            │
            ├──► [ Random Forest & SGD ] ──► Predicts delivery duration & delays
            │
            ▼
[ Streamlit Real-Time Dashboard ]
    ├── Live Fleet Status & Metric Cards
    ├── Anomaly Heatmaps & Alerts
    └── Interactive Delivery Time Estimator
```

---

## Machine Learning & Anomaly Detection

### 1. Anomaly Detection (`outlier_detector.py`)
- **Algorithm**: `IsolationForest` (`n_estimators=100`, `contamination=0.10`).
- **Feature Set**: `speed_kmh`, `fuel_level`, `temperature`, `humidity`, `hour_of_day`, `day_of_week`, and `shipment_duration_hours`.
- **Purpose**: Flags telemetry that diverges from normal transit behavior (e.g., cargo temperature spikes in refrigerated units or anomalous route delays).

### 2. Delivery Time & Delay Prediction (`ml_predictor.py`)
- **Batch Models**: `RandomForestRegressor` for estimated transit duration (hours) and expected delay (minutes).
- **Online Learning**: `SGDRegressor` with standard scaling to iteratively update weights on newly delivered shipments without full retraining.
- **Engineered Features**: Route distance, cargo weight, vehicle type encoding, route difficulty, departure hour, driver experience, vehicle age, and weather factor.
- **Type Safety**: Built explicit decimal-to-float conversions for PostgreSQL `NUMERIC` types to avoid runtime precision errors in scikit-learn.

---

## Database Schema (Azure PostgreSQL)

The platform manages 7 relational tables:
- `drivers`: Driver ID, name, license status, experience years, rating.
- `vehicles`: Vehicle ID, model, year, capacity (kg), fuel efficiency, maintenance status.
- `routes`: Route ID, origin, destination, distance (km), average time, difficulty.
- `shipments`: Shipment ID, foreign keys to vehicle/driver/route, cargo weight, departure/arrival timestamps, priority, cost.
- `shipment_tracking`: Real-time telemetry log (latitude, longitude, speed, fuel, temp, status).
- `outlier_detections`: Records flagged by the Isolation Forest with confidence scores and alert reasons.
- `ml_predictions`: Historic predictions vs. actual delivery durations for model performance tracking.

---

## Repository Structure

```
Logistics-Streaming-Analytics/
├── logistics_streaming_analytics/
│   ├── streamlit_app.py          # Main application entry point & navigation
│   ├── database_manager.py       # Azure PostgreSQL connection pool & queries
│   ├── database_schema.py        # Table initialization and seed scripts
│   ├── stream_generator.py       # High-throughput synthetic telemetry generator
│   ├── outlier_detector.py       # Isolation Forest implementation
│   ├── ml_predictor.py           # Random Forest & SGD delivery predictors
│   ├── logistics_dashboard.py    # Visual components and KPI metrics
│   ├── delivery_simulator.py     # Batch simulation engine
│   └── styles.css                # Custom UI styling
├── tests/
│   └── test_pipeline.py          # Unit tests for generators, conversion, and models
├── .env.example                  # Template for database credentials
├── requirements.txt              # Core project dependencies
└── pytest.ini                    # Test runner configuration
```

---

## How to Run It Locally

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/Apc0015/Logistics-Streaming-Analytics.git
cd Logistics-Streaming-Analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` and populate your PostgreSQL credentials:
```bash
cp .env.example .env
```
```env
AZURE_POSTGRES_HOST=your-azure-postgres-server.postgres.database.azure.com
AZURE_POSTGRES_DB=postgres
AZURE_POSTGRES_USER=your_user
AZURE_POSTGRES_PASSWORD=your_password
AZURE_POSTGRES_PORT=5432
AZURE_POSTGRES_SSLMODE=require
```

### 3. Run the Unit Tests
```bash
pytest
```

### 4. Launch the Streamlit App
```bash
cd logistics_streaming_analytics
streamlit run streamlit_app.py
```
Open `http://localhost:8501` to view the live dashboard, trigger telemetry streaming, or run predictions.
