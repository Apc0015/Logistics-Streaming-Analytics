import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import streamlit as st
import logging

class LogisticsOutlierDetector:
    """Outlier detection system for logistics data"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'speed_kmh', 'fuel_level', 'temperature', 'humidity',
            'hour_of_day', 'day_of_week', 'shipment_duration_hours'
        ]
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def extract_features_for_detection(self, df):
        """Extract features for outlier detection"""
        if df.empty:
            return pd.DataFrame()
            
        features_df = df.copy()
        
        # Time-based features
        features_df['timestamp'] = pd.to_datetime(features_df['timestamp'])
        features_df['hour_of_day'] = features_df['timestamp'].dt.hour
        features_df['day_of_week'] = features_df['timestamp'].dt.dayofweek
        
        # Get shipment information for context
        shipment_info_query = """
        SELECT s.shipment_id, 
               EXTRACT(EPOCH FROM (NOW() - s.departure_time))/3600 as duration_hours,
               r.distance_km,
               s.cargo_weight
        FROM shipments s
        JOIN routes r ON s.route_id = r.route_id
        WHERE s.shipment_id = ANY(%s)
        """
        
        try:
            shipment_ids = list(features_df['shipment_id'].unique())
            results = self.db_manager.execute_query(
                shipment_info_query, 
                params=(shipment_ids,), 
                fetch=True
            )
            
            if results:
                shipment_df = pd.DataFrame(results, columns=[
                    'shipment_id', 'shipment_duration_hours', 'distance_km', 'cargo_weight'
                ])
                features_df = features_df.merge(shipment_df, on='shipment_id', how='left')
                features_df['shipment_duration_hours'] = features_df['shipment_duration_hours'].fillna(0)
            else:
                features_df['shipment_duration_hours'] = 0
                
        except Exception as e:
            self.logger.error(f"Error getting shipment info: {e}")
            features_df['shipment_duration_hours'] = 0
        
        # Select only the required features
        available_features = [col for col in self.feature_columns if col in features_df.columns]
        return features_df[available_features]
    
    def train_model(self):
        """Train the outlier detection model"""
        try:
            # Get training data
            query = """
            SELECT shipment_id, speed_kmh, fuel_level, temperature, humidity, timestamp
            FROM shipment_tracking
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            ORDER BY timestamp DESC
            LIMIT 10000
            """
            
            results = self.db_manager.execute_query(query, fetch=True)
            if not results:
                st.warning("No training data available")
                return False
            
            df = pd.DataFrame(results, columns=[
                'shipment_id', 'speed_kmh', 'fuel_level', 'temperature', 'humidity', 'timestamp'
            ])
            
            # Extract features
            features_df = self.extract_features_for_detection(df)
            
            if features_df.empty:
                st.warning("No features extracted for training")
                return False
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features_df)
            
            # Train model
            self.isolation_forest.fit(features_scaled)
            self.is_trained = True
            
            st.success("Outlier detection model trained successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error training outlier model: {e}")
            st.error(f"Model training failed: {e}")
            return False
    
    def detect_outliers_batch(self, lookback_minutes=30):
        """Detect outliers in recent data"""
        if not self.is_trained:
            st.warning("Model not trained. Please train the model first.")
            return []
        
        try:
            query = """
            SELECT shipment_id, speed_kmh, fuel_level, temperature, humidity, 
                   timestamp, current_location, status_update
            FROM shipment_tracking
            WHERE timestamp >= NOW() - INTERVAL '%s minutes'
            ORDER BY timestamp DESC
            """
            
            results = self.db_manager.execute_query(
                query % lookback_minutes, 
                fetch=True
            )
            
            if not results:
                return []
            
            df = pd.DataFrame(results, columns=[
                'shipment_id', 'speed_kmh', 'fuel_level', 'temperature', 'humidity',
                'timestamp', 'current_location', 'status_update'
            ])
            
            # Extract features
            features_df = self.extract_features_for_detection(df)
            
            if features_df.empty:
                return []
            
            # Scale features
            features_scaled = self.scaler.transform(features_df)
            
            # Predict outliers
            outlier_predictions = self.isolation_forest.predict(features_scaled)
            outlier_scores = self.isolation_forest.score_samples(features_scaled)
            
            # Mark outliers and store results
            outliers = []
            for i, (prediction, score) in enumerate(zip(outlier_predictions, outlier_scores)):
                if prediction == -1:  # Outlier
                    outlier_data = {
                        'shipment_id': df.iloc[i]['shipment_id'],
                        'outlier_type': self._classify_outlier_type(df.iloc[i]),
                        'confidence_score': abs(score),
                        'description': self._generate_outlier_description(df.iloc[i]),
                        'timestamp': df.iloc[i]['timestamp'],
                        'location': df.iloc[i]['current_location']
                    }
                    outliers.append(outlier_data)
                    
                    # Store in database
                    self._store_outlier_detection(outlier_data)
            
            return outliers
            
        except Exception as e:
            self.logger.error(f"Error detecting outliers: {e}")
            return []
    
    def _classify_outlier_type(self, row):
        """Classify the type of outlier based on values"""
        if row['speed_kmh'] > 150:
            return 'Speed Anomaly'
        elif row['fuel_level'] < 5:
            return 'Low Fuel'
        elif row['temperature'] > 50 or row['temperature'] < -10:
            return 'Temperature Anomaly'
        else:
            return 'General Anomaly'
    
    def _generate_outlier_description(self, row):
        """Generate human-readable description of the outlier"""
        descriptions = []
        
        if row['speed_kmh'] > 150:
            descriptions.append(f"Excessive speed: {row['speed_kmh']:.1f} km/h")
        
        if row['fuel_level'] < 5:
            descriptions.append(f"Critical fuel level: {row['fuel_level']:.1f}%")
        
        if row['temperature'] > 50:
            descriptions.append(f"High temperature: {row['temperature']:.1f}°C")
        elif row['temperature'] < -10:
            descriptions.append(f"Low temperature: {row['temperature']:.1f}°C")
        
        return "; ".join(descriptions) if descriptions else "Anomalous pattern detected"
    
    def _store_outlier_detection(self, outlier_data):
        """Store outlier detection result in database"""
        try:
            query = """
            INSERT INTO outlier_detections 
            (shipment_id, outlier_type, confidence_score, description, detected_at)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            self.db_manager.execute_query(query, params=(
                outlier_data['shipment_id'],
                outlier_data['outlier_type'],
                outlier_data['confidence_score'],
                outlier_data['description'],
                outlier_data['timestamp']
            ))
            
        except Exception as e:
            self.logger.error(f"Error storing outlier detection: {e}")
    
    def get_outlier_summary(self, hours=24):
        """Get summary of outliers detected in the specified time period"""
        try:
            query = """
            SELECT outlier_type, 
                   COUNT(*) as count,
                   AVG(confidence_score) as avg_confidence
            FROM outlier_detections
            WHERE detected_at >= NOW() - INTERVAL '%s hours'
            GROUP BY outlier_type
            ORDER BY count DESC
            """
            
            results = self.db_manager.execute_query(
                query % hours, 
                fetch=True
            )
            
            if results:
                return pd.DataFrame(results, columns=['Outlier_Type', 'Count', 'Avg_Confidence'])
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error getting outlier summary: {e}")
            return pd.DataFrame()