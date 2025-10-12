# Big Data Projects Collection

This repository contains multiple big data analytics projects developed for academic and demonstration purposes.

## Projects

### 1. Logistics Streaming Analytics Pipeline

A real-time logistics streaming analytics platform built with Streamlit and Azure PostgreSQL.

**Location**: `logistics_streaming_analytics/`

**Features**:
- Real-time dashboard with live KPIs
- Streaming data generation (300+ events per minute)
- Outlier detection using machine learning
- Delivery time prediction models
- Interactive visualizations

**Tech Stack**:
- Backend: Python, PostgreSQL (Azure)
- Frontend: Streamlit
- ML: scikit-learn (Random Forest, SGD)
- Data Processing: pandas, numpy
- Visualization: Plotly

**Quick Start**:
```bash
cd logistics_streaming_analytics
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### 2. LLM Benchmarking Platform

Performance benchmarking and analytics platform for Large Language Models.

**Location**: `llm-benchmark-dashboard/`

**Features**:
- Model performance comparison
- Live benchmarking
- User authentication
- Analytics dashboard

**Tech Stack**:
- Backend: Python
- Frontend: Streamlit
- Database: PostgreSQL

### 3. LLM Performance Analysis

Jupyter notebook-based analysis of LLM performance metrics.

**Location**: `LLM_Performance_Benchmark.ipynb`

## Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Big_Data_Project
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Navigate to specific project and install dependencies:
```bash
cd logistics_streaming_analytics
pip install -r requirements.txt
```

### Database Configuration

For projects requiring PostgreSQL:

1. Update database configuration in `database_manager.py`
2. Ensure PostgreSQL server is running
3. Create required database and tables (handled automatically by schema manager)

## Project Structure

```
Big_Data_Project/
├── logistics_streaming_analytics/      # Main logistics analytics project
│   ├── streamlit_app.py               # Main Streamlit application
│   ├── database_manager.py            # Database connection management
│   ├── database_schema.py             # Database schema definitions
│   ├── logistics_dashboard.py         # Dashboard components
│   ├── stream_generator.py            # Real-time data generation
│   ├── outlier_detector.py           # Anomaly detection system
│   ├── ml_predictor.py               # Machine learning models
│   ├── delivery_simulator.py         # Delivery completion simulator
│   └── requirements.txt              # Python dependencies
├── llm-benchmark-dashboard/           # LLM benchmarking platform
├── notebooks/                        # Jupyter notebooks
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

## Usage

### Logistics Streaming Analytics

1. **Start the application**:
```bash
cd logistics_streaming_analytics
streamlit run streamlit_app.py
```

2. **Generate sample data**:
   - Go to "Data Streaming" tab
   - Click "Start Streaming" to generate logistics data
   - Use "Complete Random Shipments" for immediate testing

3. **Train ML models**:
   - Go to "ML Predictions" tab
   - Click "Generate Sample Training Data" (if needed)
   - Click "Train ML Models"

4. **View analytics**:
   - Dashboard tab shows real-time KPIs
   - Outlier Detection tab for anomaly analysis

## Features

### Real-time Dashboard
- Active shipments tracking
- Delivery performance metrics
- Vehicle utilization statistics
- Interactive charts and visualizations

### Machine Learning
- Delivery time prediction using Random Forest
- Online learning with SGD
- Outlier detection with Isolation Forest
- Model performance tracking

### Data Streaming
- Configurable event generation rates
- Realistic logistics event simulation
- Automatic shipment lifecycle progression
- Database constraint compliance

### Outlier Detection
- Real-time anomaly detection
- Configurable detection parameters
- Outlier type classification
- Historical outlier analysis

## Technical Details

### Database Schema
- **Drivers**: Driver information and status
- **Vehicles**: Vehicle specifications and availability
- **Routes**: Shipping route definitions
- **Shipments**: Individual shipment records
- **Shipment Tracking**: Real-time tracking events
- **Outlier Detections**: Anomaly detection results
- **ML Predictions**: Model prediction storage

### Performance
- Handles 300+ events per minute
- Real-time dashboard updates
- Automatic data type conversion (Decimal to float)
- Efficient database queries with proper indexing

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify PostgreSQL is running
   - Check database credentials in `database_manager.py`
   - Ensure network connectivity to Azure PostgreSQL

2. **Decimal Type Errors**:
   - Fixed with automatic type conversion
   - PostgreSQL Decimal types converted to float

3. **No Training Data**:
   - Run data streaming first
   - Use "Generate Sample Training Data" button
   - Ensure shipments are completed (status = 'Delivered')

4. **Import Errors**:
   - Verify all dependencies are installed
   - Check Python virtual environment is activated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is developed for educational purposes. Please refer to your institution's guidelines for usage and distribution.

## Contact

For questions or issues, please create an issue in the repository or contact the project maintainer.