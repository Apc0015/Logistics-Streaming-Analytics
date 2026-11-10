import sys
from pathlib import Path
from decimal import Decimal
import numpy as np
import pandas as pd
import pytest

# Add package to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "logistics_streaming_analytics"))
sys.path.insert(0, str(project_root))

from logistics_streaming_analytics.stream_generator import LogisticsStreamGenerator
from logistics_streaming_analytics.ml_predictor import LogisticsMLPredictor
from logistics_streaming_analytics.outlier_detector import LogisticsOutlierDetector


def test_stream_generator_tracking_event():
    """Verify stream generator creates structured tracking events with required fields"""
    generator = LogisticsStreamGenerator(db_manager=None, events_per_minute=100)
    event = generator.generate_tracking_event("SH99999")
    
    assert event is not None
    assert event["shipment_id"] == "SH99999"
    assert "current_location" in event
    assert "latitude" in event
    assert "longitude" in event
    assert "speed_kmh" in event
    assert "fuel_level" in event
    assert "temperature" in event
    assert "humidity" in event
    assert "status_update" in event
    assert "is_outlier" in event
    assert isinstance(event["is_outlier"], bool)
    assert -90 <= event["latitude"] <= 90
    assert -180 <= event["longitude"] <= 180


def test_stream_generator_new_shipment():
    """Verify new shipment generation produces consistent schemas and resource assignments"""
    generator = LogisticsStreamGenerator(db_manager=None)
    drivers = ["D001", "D002"]
    vehicles = ["V001", "V002"]
    routes = ["R001", "R002"]
    
    shipment = generator.generate_new_shipment(drivers, vehicles, routes)
    assert shipment is not None
    assert shipment["shipment_id"].startswith("SH")
    assert shipment["driver_id"] in drivers
    assert shipment["vehicle_id"] in vehicles
    assert shipment["route_id"] in routes
    assert shipment["cargo_weight"] >= 100
    assert shipment["cost"] > 0
    assert shipment["status"] in ["Pending", "Loading", "In Transit"]


def test_decimal_column_conversion():
    """Verify decimal types returned by PostgreSQL are cleanly converted to float to prevent type errors"""
    predictor = LogisticsMLPredictor(db_manager=None)
    
    sample_df = pd.DataFrame({
        "cargo_weight": [Decimal("1250.50"), Decimal("800.25"), Decimal("3100.00")],
        "distance_km": [Decimal("450.75"), Decimal("120.00"), Decimal("950.50")],
        "cost": [Decimal("1500.00"), Decimal("650.00"), Decimal("3200.00")],
        "status": ["In Transit", "Delivered", "In Transit"]
    })
    
    converted_df = predictor._convert_decimal_columns(sample_df)
    
    assert converted_df["cargo_weight"].dtype == float or np.issubdtype(converted_df["cargo_weight"].dtype, np.floating)
    assert converted_df["distance_km"].dtype == float or np.issubdtype(converted_df["distance_km"].dtype, np.floating)
    assert converted_df["cost"].dtype == float or np.issubdtype(converted_df["cost"].dtype, np.floating)
    
    # Ensure math operations succeed without Decimal TypeError
    assert (converted_df["cost"] / converted_df["distance_km"]).iloc[0] > 0


def test_outlier_detection_isolation_forest():
    """Verify IsolationForest correctly isolates extreme outliers from normal logistics telemetry"""
    detector = LogisticsOutlierDetector(db_manager=None)
    
    # Train detector on realistic normal data
    np.random.seed(42)
    normal_data = pd.DataFrame({
        "speed_kmh": np.random.uniform(50, 90, 200),
        "fuel_level": np.random.uniform(40, 95, 200),
        "temperature": np.random.uniform(10, 25, 200),
        "humidity": np.random.uniform(40, 70, 200),
        "hour_of_day": np.random.randint(0, 24, 200),
        "day_of_week": np.random.randint(0, 7, 200),
        "shipment_duration_hours": np.random.uniform(1, 10, 200)
    })
    
    scaled_train = detector.scaler.fit_transform(normal_data[detector.feature_columns])
    detector.isolation_forest.fit(scaled_train)
    detector.is_trained = True
    
    # Test extreme anomaly (speed 195 km/h, fuel 1%, temp 75°C)
    anomaly_point = pd.DataFrame([{
        "speed_kmh": 195.0,
        "fuel_level": 1.0,
        "temperature": 75.0,
        "humidity": 10.0,
        "hour_of_day": 3,
        "day_of_week": 2,
        "shipment_duration_hours": 15.0
    }])
    
    scaled_anomaly = detector.scaler.transform(anomaly_point[detector.feature_columns])
    pred = detector.isolation_forest.predict(scaled_anomaly)
    # IsolationForest outputs -1 for anomalies
    assert pred[0] == -1
