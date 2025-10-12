import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error
import streamlit as st
import logging
import pickle
from datetime import datetime
from decimal import Decimal

class LogisticsMLPredictor:
    """Machine learning system for delivery time prediction and route optimization"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.delivery_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.delay_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.online_model = SGDRegressor(random_state=42)
        
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.is_trained = False
        
        self.feature_columns = [
            'distance_km', 'cargo_weight', 'vehicle_type_encoded', 'route_difficulty_encoded',
            'hour_of_day', 'day_of_week', 'weather_factor', 'driver_experience',
            'vehicle_age', 'fuel_efficiency', 'priority_encoded'
        ]
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _convert_decimal_columns(self, df):
        """Convert PostgreSQL Decimal types to float to prevent math operation errors"""
        try:
            # List of columns that commonly come as Decimal from PostgreSQL
            potential_decimal_columns = [
                'cargo_weight', 'distance_km', 'fuel_efficiency', 
                'actual_duration_hours', 'delay_minutes', 'year', 
                'experience_years', 'cost', 'rating', 'capacity_kg',
                'estimated_duration_hours', 'toll_cost'
            ]
            
            for col in potential_decimal_columns:
                if col in df.columns:
                    # Check if column contains Decimal types
                    if df[col].dtype == 'object' or any(isinstance(x, Decimal) for x in df[col].iloc[:5] if x is not None):
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
                        self.logger.debug(f"Converted {col} from Decimal to float")
            
            return df
            
        except Exception as e:
            self.logger.warning(f"Error in decimal conversion: {e}")
            return df
    
    def prepare_training_data(self):
        """Prepare comprehensive training dataset"""
        self.logger.info("Starting training data preparation")

        # First check if we have basic data
        data_check = self._check_data_availability()
        if not data_check['has_sufficient_data']:
            self.logger.warning(f"Insufficient data: {data_check['message']}")
            return pd.DataFrame(), data_check['message']

        # Use LEFT JOINs and handle missing data gracefully
        query = """
        SELECT
            s.shipment_id,
            s.departure_time,
            s.estimated_arrival,
            s.actual_arrival,
            s.cargo_weight,
            COALESCE(s.priority, 'Medium') as priority,
            COALESCE(r.distance_km, 100) as distance_km,
            COALESCE(r.difficulty_level, 'Medium') as difficulty_level,
            COALESCE(v.vehicle_type, 'Truck') as vehicle_type,
            COALESCE(v.year, 2020) as year,
            COALESCE(v.fuel_efficiency, 10.0) as fuel_efficiency,
            COALESCE(d.experience_years, 5) as experience_years,
            EXTRACT(EPOCH FROM (s.actual_arrival - s.departure_time))/3600 as actual_duration_hours,
            EXTRACT(EPOCH FROM (s.actual_arrival - s.estimated_arrival))/60 as delay_minutes
        FROM shipments s
        LEFT JOIN routes r ON s.route_id = r.route_id
        LEFT JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        LEFT JOIN drivers d ON s.driver_id = d.driver_id
        WHERE s.actual_arrival IS NOT NULL
        AND s.departure_time >= CURRENT_DATE - INTERVAL '60 days'
        AND s.status = 'Delivered'
        ORDER BY s.departure_time DESC
        """

        try:
            self.logger.info("Executing training data query")
            results = self.db_manager.execute_query(query, fetch=True)

            if not results:
                self.logger.warning("No completed shipments found in the last 60 days")
                return pd.DataFrame(), "No completed shipments found in the last 60 days"

            df = pd.DataFrame(results, columns=[
                'shipment_id', 'departure_time', 'estimated_arrival', 'actual_arrival',
                'cargo_weight', 'priority', 'distance_km', 'difficulty_level',
                'vehicle_type', 'year', 'fuel_efficiency', 'experience_years',
                'actual_duration_hours', 'delay_minutes'
            ])

            self.logger.info(f"Retrieved {len(df)} completed shipments for training")

            # Convert PostgreSQL Decimal types to float FIRST
            df = self._convert_decimal_columns(df)

            # Feature engineering
            df['departure_time'] = pd.to_datetime(df['departure_time'])
            df['hour_of_day'] = df['departure_time'].dt.hour
            df['day_of_week'] = df['departure_time'].dt.dayofweek

            # Now safe to perform mathematical operations
            df['vehicle_age'] = 2025 - df['year']  # Now safe subtraction
            df['driver_experience'] = df['experience_years']  # Map experience_years to driver_experience
            df['weather_factor'] = np.random.uniform(0.8, 1.2, len(df))  # Mock weather data

            # Validate data quality
            if len(df) < 10:
                self.logger.warning(f"Only {len(df)} training samples available. Need at least 10 for reliable training.")
                return df, f"Only {len(df)} training samples available. Need at least 10 for reliable training."

            self.logger.info(f"Successfully prepared training data with {len(df)} samples")
            return df, "Data prepared successfully"

        except Exception as e:
            self.logger.error(f"Error preparing training data: {e}")
            return pd.DataFrame(), f"Database error: {str(e)}"
    
    def _check_data_availability(self):
        """Check if sufficient data exists for training"""
        try:
            # Check completed shipments
            completed_query = "SELECT COUNT(*) FROM shipments WHERE status = 'Delivered' AND actual_arrival IS NOT NULL"
            completed_result = self.db_manager.execute_query(completed_query, fetch=True)
            completed_count = completed_result[0][0] if completed_result else 0
            
            # Check total shipments
            total_query = "SELECT COUNT(*) FROM shipments"
            total_result = self.db_manager.execute_query(total_query, fetch=True)
            total_count = total_result[0][0] if total_result else 0
            
            # Check required tables
            tables_exist = all([
                self.db_manager.get_table_exists(table) 
                for table in ['shipments', 'routes', 'vehicles', 'drivers']
            ])
            
            if not tables_exist:
                return {
                    'has_sufficient_data': False,
                    'message': 'Required database tables are missing. Please run data streaming first.'
                }
            
            if total_count == 0:
                return {
                    'has_sufficient_data': False,
                    'message': 'No shipments found in database. Please run data streaming to generate sample data.'
                }
            
            if completed_count < 5:
                return {
                    'has_sufficient_data': False,
                    'message': f'Only {completed_count} completed shipments found. Need at least 5 for training. Please run data streaming and wait for shipments to complete.'
                }
            
            return {
                'has_sufficient_data': True,
                'message': f'Found {completed_count} completed shipments out of {total_count} total shipments.'
            }
            
        except Exception as e:
            return {
                'has_sufficient_data': False,
                'message': f'Error checking data availability: {str(e)}'
            }
    
    def generate_sample_completed_shipments(self, count=20):
        """Generate sample completed shipments for training when no data exists"""
        try:
            st.info(f"Generating {count} sample completed shipments for training...")
            
            from datetime import datetime, timedelta
            import random
            from faker import Faker
            fake = Faker()
            
            # Generate sample data
            sample_shipments = []
            for i in range(count):
                departure_time = datetime.now() - timedelta(days=random.randint(1, 30), 
                                                          hours=random.randint(0, 23))
                duration_hours = random.uniform(2, 48)
                estimated_arrival = departure_time + timedelta(hours=duration_hours + random.uniform(-2, 4))
                actual_arrival = departure_time + timedelta(hours=duration_hours + random.uniform(-1, 6))
                
                shipment = {
                    'shipment_id': f'SAMPLE_{i+1:03d}',
                    'vehicle_id': f'VEH_{random.randint(1, 10):03d}',
                    'driver_id': f'DRV_{random.randint(1, 20):03d}',
                    'route_id': f'RT_{random.randint(1, 15):03d}',
                    'departure_time': departure_time,
                    'estimated_arrival': estimated_arrival,
                    'actual_arrival': actual_arrival,
                    'cargo_weight': random.uniform(500, 5000),
                    'cargo_type': random.choice(['Electronics', 'Food', 'Furniture', 'Machinery', 'Textiles']),
                    'priority': random.choice(['Low', 'Medium', 'High']),
                    'status': 'Delivered',
                    'cost': random.uniform(100, 2000)
                }
                sample_shipments.append(shipment)
            
            # Insert into database
            for shipment in sample_shipments:
                insert_query = """
                INSERT INTO shipments (shipment_id, vehicle_id, driver_id, route_id, departure_time, 
                                     estimated_arrival, actual_arrival, cargo_weight, cargo_type, 
                                     priority, status, cost, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (shipment_id) DO NOTHING
                """
                
                self.db_manager.execute_query(insert_query, params=(
                    shipment['shipment_id'], shipment['vehicle_id'], shipment['driver_id'],
                    shipment['route_id'], shipment['departure_time'], shipment['estimated_arrival'],
                    shipment['actual_arrival'], shipment['cargo_weight'], shipment['cargo_type'],
                    shipment['priority'], shipment['status'], shipment['cost'], datetime.now()
                ))
            
            st.success(f"Generated {count} sample completed shipments")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating sample data: {e}")
            st.error(f"Failed to generate sample data: {str(e)}")
            return False
    
    def encode_categorical_features(self, df, fit=True):
        """Encode categorical features"""
        categorical_columns = ['vehicle_type', 'difficulty_level', 'priority']
        
        for col in categorical_columns:
            if col in df.columns:
                encoded_col = f"{col.replace('_level', '')}_encoded"
                
                if fit:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    df[encoded_col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    if col in self.label_encoders:
                        # Handle unseen categories
                        unique_vals = df[col].astype(str).unique()
                        known_vals = self.label_encoders[col].classes_
                        for val in unique_vals:
                            if val not in known_vals:
                                # Add new category to encoder
                                self.label_encoders[col].classes_ = np.append(known_vals, val)
                        
                        df[encoded_col] = self.label_encoders[col].transform(df[col].astype(str))
                    else:
                        df[encoded_col] = 0  # Default encoding
        
        return df
    
    def train_models(self):
        """Train delivery time and delay prediction models"""
        try:
            self.logger.info("Starting model training process")

            # Get training data with detailed error messages
            df, message = self.prepare_training_data()

            if df.empty:
                st.error(f"Training failed: {message}")
                st.info("**How to fix this:**")
                st.info("1. Go to the 'Data Streaming' tab")
                st.info("2. Start data streaming for at least 5-10 minutes")
                st.info("3. Wait for some shipments to be marked as 'Delivered'")
                st.info("4. Return here and try training again")
                self.logger.error(f"Training failed: {message}")
                return False

            st.info(f"Status: {message}")
            st.info(f"Training with {len(df)} samples...")
            self.logger.info(f"Training with {len(df)} samples")

            # Encode categorical features
            df = self.encode_categorical_features(df, fit=True)

            # Prepare features - use only available columns
            available_features = []
            for col in self.feature_columns:
                if col in df.columns:
                    available_features.append(col)
                else:
                    # Create missing features with defaults
                    if col == 'weather_factor':
                        df[col] = np.random.uniform(0.8, 1.2, len(df))
                        available_features.append(col)
                    elif col.endswith('_encoded'):
                        # Already handled in encoding
                        continue
                    else:
                        st.warning(f"Missing feature: {col}, using default values")
                        df[col] = 0
                        available_features.append(col)

            if len(available_features) < 3:
                st.error("Insufficient features available for training")
                self.logger.error("Insufficient features available for training")
                return False

            X = df[available_features]
            y_duration = df['actual_duration_hours']
            y_delay = df['delay_minutes']

            # Convert any remaining Decimal types to float to prevent math operation errors
            X = X.apply(pd.to_numeric, errors='coerce').astype(float)
            y_duration = pd.to_numeric(y_duration, errors='coerce').astype(float)
            y_delay = pd.to_numeric(y_delay, errors='coerce').astype(float)
            
            self.logger.info("Converted all feature and target data to float type")

            # Handle missing values
            X = X.fillna(X.mean() if len(X) > 0 else 0)
            y_duration = y_duration.fillna(y_duration.mean() if len(y_duration) > 0 else 24)
            y_delay = y_delay.fillna(0)

            # Validate target variables
            if y_duration.std() == 0:
                st.warning("All delivery times are identical. Adding small variations for training.")
                y_duration = y_duration + np.random.normal(0, 0.1, len(y_duration))

            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            self.logger.info(f"Feature scaling completed. Shape: {X_scaled.shape}")

            # Train delivery time model
            st.info("Training delivery time prediction model...")
            self.logger.info("Training delivery time prediction model")
            self.delivery_model.fit(X_scaled, y_duration)

            # Train delay prediction model
            st.info("Training delay prediction model...")
            self.logger.info("Training delay prediction model")
            self.delay_model.fit(X_scaled, y_delay)

            # Train online learning model
            st.info("Training online learning model...")
            self.logger.info("Training online learning model")
            self.online_model.fit(X_scaled, y_duration)

            self.is_trained = True
            self.feature_columns = available_features  # Update to actual available features

            # Calculate training performance
            duration_pred = self.delivery_model.predict(X_scaled)
            delay_pred = self.delay_model.predict(X_scaled)

            duration_mae = mean_absolute_error(y_duration, duration_pred)
            delay_mae = mean_absolute_error(y_delay, delay_pred)

            # Calculate R² score for additional metrics
            from sklearn.metrics import r2_score
            duration_r2 = r2_score(y_duration, duration_pred)
            delay_r2 = r2_score(y_delay, delay_pred)

            st.success("Models trained successfully!")
            self.logger.info("Models trained successfully")

            # Display performance metrics in columns
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Duration Prediction MAE", f"{duration_mae:.2f} hours")
                st.metric("Duration R² Score", f"{duration_r2:.3f}")
            with col2:
                st.metric("Delay Prediction MAE", f"{delay_mae:.2f} minutes")
                st.metric("Delay R² Score", f"{delay_r2:.3f}")

            st.info(f"Training completed with {len(available_features)} features on {len(df)} samples")
            self.logger.info(f"Training completed with {len(available_features)} features on {len(df)} samples")

            return True

        except Exception as e:
            self.logger.error(f"Error training models: {e}")
            st.error(f"Model training failed: {str(e)}")
            st.info("**Troubleshooting:**")
            st.info("- Check database connection")
            st.info("- Ensure data streaming has been run")
            st.info("- Verify database schema is complete")
            return False
    
    def predict_delivery_time(self, shipment_data):
        """Predict delivery time for a shipment"""
        if not self.is_trained:
            st.warning("Models not trained. Please train models first.")
            return None
        
        try:
            # Convert input to DataFrame
            input_df = pd.DataFrame([shipment_data])
            
            # Add missing features with defaults
            feature_defaults = {
                'hour_of_day': datetime.now().hour,
                'day_of_week': datetime.now().weekday(),
                'vehicle_age': 5,
                'driver_experience': 5,
                'fuel_efficiency': 10.0,
                'weather_factor': 1.0
            }
            
            for feature, default_value in feature_defaults.items():
                if feature not in input_df.columns:
                    input_df[feature] = default_value
            
            # Encode categorical features
            input_df = self.encode_categorical_features(input_df, fit=False)
            
            # Convert any Decimal types to float
            input_df = self._convert_decimal_columns(input_df)
            
            # Prepare features - only use features that were used in training
            available_features = [col for col in self.feature_columns if col in input_df.columns]
            
            if not available_features:
                st.error("No valid features found for prediction")
                return None
            
            X = input_df[available_features]
            
            # Convert any Decimal types to float to prevent math operation errors
            X = X.apply(pd.to_numeric, errors='coerce').astype(float)
            
            # Handle missing values
            X = X.fillna(0)
            
            # Scale features
            try:
                X_scaled = self.scaler.transform(X)
            except Exception as e:
                st.error(f"Error scaling features: {e}")
                return None
            
            # Make predictions
            predicted_duration = self.delivery_model.predict(X_scaled)[0]
            
            # Store prediction in database (optional, may fail if shipment_id doesn't exist)
            try:
                self._store_prediction({
                    'shipment_id': shipment_data.get('shipment_id', 'PRED_' + str(int(datetime.now().timestamp()))),
                    'predicted_duration': predicted_duration,
                    'predicted_delay': 0,  # Not calculating delay for new predictions
                    'model_name': 'RandomForest',
                    'prediction_type': 'delivery_time'
                })
            except:
                # Ignore database storage errors for predictions
                pass
            
            return max(predicted_duration, 0.1)  # Ensure positive prediction
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            st.error(f"Prediction failed: {str(e)}")
            return None
    
    def predict_optimal_route(self, route_data):
        """Predict optimal route score"""
        try:
            # Simple route optimization score based on distance and urgency
            base_score = 100
            
            distance_penalty = route_data.get('distance_km', 500) * 0.01
            urgency_bonus = {'high': 10, 'medium': 5, 'low': 0}.get(
                route_data.get('urgency', 'medium').lower(), 0
            )
            
            optimization_score = base_score - distance_penalty + urgency_bonus
            return max(optimization_score, 0)
            
        except Exception as e:
            self.logger.error(f"Error in route optimization: {e}")
            return 0
    
    def _store_prediction(self, prediction_data):
        """Store prediction result in database"""
        try:
            query = """
            INSERT INTO ml_predictions 
            (shipment_id, model_name, prediction_type, predicted_value, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            self.db_manager.execute_query(query, params=(
                prediction_data['shipment_id'],
                prediction_data['model_name'],
                prediction_data['prediction_type'],
                prediction_data['predicted_duration'],
                datetime.now()
            ))
            
        except Exception as e:
            self.logger.error(f"Error storing prediction: {e}")
    
    def get_model_performance(self, days=7):
        """Get model performance metrics"""
        try:
            query = """
            SELECT
                model_name,
                prediction_type,
                COUNT(*) as prediction_count,
                AVG(ABS(CAST(predicted_value AS NUMERIC) - CAST(actual_value AS NUMERIC))) as mae,
                AVG(accuracy_score) as avg_accuracy
            FROM ml_predictions
            WHERE created_at >= NOW() - INTERVAL '%s days'
            AND actual_value IS NOT NULL
            GROUP BY model_name, prediction_type
            """
            
            results = self.db_manager.execute_query(
                query % days, 
                fetch=True
            )
            
            if results:
                return pd.DataFrame(results, columns=[
                    'Model', 'Type', 'Predictions', 'MAE', 'Accuracy'
                ])
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error getting model performance: {e}")
            return pd.DataFrame()
    
    def update_model_online(self, new_data):
        """Update model with new data (online learning)"""
        if not self.is_trained:
            return False
        
        try:
            # Prepare new data
            input_df = pd.DataFrame([new_data])
            input_df = self.encode_categorical_features(input_df, fit=False)
            
            available_features = [col for col in self.feature_columns if col in input_df.columns]
            X = input_df[available_features].fillna(0)
            X_scaled = self.scaler.transform(X)
            
            # Update online model
            y = [new_data.get('actual_duration_hours', 0)]
            self.online_model.partial_fit(X_scaled, y)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating model online: {e}")
            return False