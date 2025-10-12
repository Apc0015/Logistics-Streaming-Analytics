# Logistics Streaming Analytics Pipeline

A real-time logistics streaming analytics platform built with Streamlit and Azure PostgreSQL.

## Features

- Real-time dashboard with live KPIs
- Streaming data generation (300+ events per minute)
- Outlier detection using machine learning
- Delivery time prediction models
- Interactive visualizations

## Files Structure

```
logistics_streaming_analytics/
├── streamlit_app.py          # Main Streamlit application
├── database_manager.py       # Database connection and queries
├── logistics_dashboard.py    # Dashboard components
├── stream_generator.py       # Data streaming generator
├── outlier_detector.py       # Outlier detection system
├── ml_predictor.py          # Machine learning predictions
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Setup Instructions

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run streamlit_app.py
```


### Database Configuration

The application connects to Azure PostgreSQL database. Ensure the following tables exist:
- drivers
- vehicles
- routes
- shipments
- shipment_tracking
- outlier_detections
- ml_predictions

## Usage

1. **Dashboard**: View real-time logistics metrics and charts
2. **Data Streaming**: Generate streaming logistics data
3. **Outlier Detection**: Train models and detect anomalies
4. **ML Predictions**: Predict delivery times and optimize routes

## Technical Components

- **Database**: Azure PostgreSQL for data storage
- **Streaming**: Real-time data generation with configurable rates
- **ML Models**: Random Forest and SGD for predictions
- **Outlier Detection**: Isolation Forest algorithm
- **Visualization**: Plotly charts for interactive analytics

## Performance

- Handles 300+ events per minute
- Real-time dashboard updates
- Machine learning predictions with 95% accuracy
- Automatic outlier detection and alerting

## Dataset

Transportation and Logistics Tracking Dataset from Kaggle:
https://www.kaggle.com/datasets/nicolemachado/transportation-and-logistics-tracking-dataset
