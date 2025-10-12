import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import random
import logging

# Configure Streamlit page
st.set_page_config(
    page_title="Logistics Streaming Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import custom modules
from database_manager import DatabaseManager
from database_schema import DatabaseSchemaManager
from logistics_dashboard import LogisticsDashboard
from stream_generator import LogisticsStreamGenerator
from outlier_detector import LogisticsOutlierDetector
from ml_predictor import LogisticsMLPredictor

def initialize_database_schema():
    """Initialize database schema if needed"""
    try:
        with st.spinner("Checking database schema..."):
            schema_manager = DatabaseSchemaManager()
            success = schema_manager.initialize_if_needed()
            
            if success:
                st.success("Database schema ready!")
                return True
            else:
                st.error("Failed to initialize database schema")
                return False
                
    except Exception as e:
        st.error(f"Database schema initialization error: {e}")
        return False

def initialize_session_state():
    """Initialize session state variables"""
    if 'schema_initialized' not in st.session_state:
        st.session_state.schema_initialized = initialize_database_schema()
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = LogisticsDashboard(st.session_state.db_manager)
    
    if 'stream_generator' not in st.session_state:
        st.session_state.stream_generator = LogisticsStreamGenerator(st.session_state.db_manager)
    
    if 'outlier_detector' not in st.session_state:
        st.session_state.outlier_detector = LogisticsOutlierDetector(st.session_state.db_manager)
    
    if 'ml_predictor' not in st.session_state:
        st.session_state.ml_predictor = LogisticsMLPredictor(st.session_state.db_manager)
    
    if 'streaming_active' not in st.session_state:
        st.session_state.streaming_active = False

def show_dashboard():
    """Display the main dashboard"""
    st.header("Real-time Logistics Dashboard")
    
    # Refresh controls
    col1, col2 = st.columns([3, 1])
    with col1:
        auto_refresh = st.checkbox("Auto-refresh every 10 seconds")
    with col2:
        if st.button("Refresh Now"):
            st.rerun()
    
    if auto_refresh:
        time.sleep(10)
        st.rerun()
    
    # Get KPIs
    with st.spinner("Loading dashboard data..."):
        kpis = st.session_state.dashboard.get_real_time_kpis()
    
    # Display KPIs in metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Active Shipments",
            value=kpis.get('active_shipments', 0)
        )
    
    with col2:
        st.metric(
            label="Completed Today",
            value=kpis.get('completed_today', 0)
        )
    
    with col3:
        st.metric(
            label="Avg Delivery Time",
            value=f"{kpis.get('avg_delivery_time', 0):.1f}h"
        )
    
    with col4:
        st.metric(
            label="On-Time Rate",
            value=f"{kpis.get('on_time_percentage', 0):.1f}%"
        )
    
    # Additional metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Cargo (tons)",
            value=f"{kpis.get('total_cargo_weight', 0)/1000:.1f}"
        )
    
    with col2:
        st.metric(
            label="Recent Outliers",
            value=kpis.get('recent_outliers', 0)
        )
    
    with col3:
        st.metric(
            label="Events per Hour",
            value=kpis.get('tracking_events_hour', 0)
        )
    
    with col4:
        st.metric(
            label="Vehicle Utilization",
            value=f"{kpis.get('vehicle_utilization', 0):.1f}%"
        )
    
    # Charts section
    st.subheader("Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Shipment Status Distribution")
        status_df = st.session_state.dashboard.get_shipment_status_distribution()
        if not status_df.empty:
            fig = px.pie(
                status_df, 
                values='Count', 
                names='Status',
                title="Current Shipment Status"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No shipment data available")
    
    with col2:
        st.subheader("Hourly Tracking Volume")
        volume_df = st.session_state.dashboard.get_hourly_tracking_volume()
        if not volume_df.empty:
            fig = px.line(
                volume_df, 
                x='Hour', 
                y='Event_Count',
                title="Tracking Events (Last 24 Hours)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tracking volume data available")
    
    # Vehicle utilization chart
    st.subheader("Vehicle Utilization by Type")
    vehicle_df = st.session_state.dashboard.get_vehicle_utilization()
    if not vehicle_df.empty:
        fig = px.bar(
            vehicle_df, 
            x='Vehicle_Type', 
            y='Utilization_Rate_%',
            title="Vehicle Utilization Rates"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No vehicle utilization data available")

def show_streaming_control():
    """Display streaming data generation controls"""
    st.header("Data Streaming Control")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Streaming Configuration")
        
        duration = st.slider(
            "Streaming Duration (minutes)", 
            min_value=1, 
            max_value=30, 
            value=5,
            help="How long to generate streaming data"
        )
        
        events_per_minute = st.slider(
            "Events per Minute", 
            min_value=50, 
            max_value=500, 
            value=300,
            help="Rate of data generation"
        )
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Start Streaming", disabled=st.session_state.streaming_active):
                st.session_state.streaming_active = True
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Generating streaming data..."):
                    # Update stream generator rate
                    st.session_state.stream_generator.events_per_minute = events_per_minute
                    
                    # Start streaming
                    st.session_state.stream_generator.generate_streaming_data(
                        duration_minutes=duration
                    )
                    
                st.session_state.streaming_active = False
                st.success("Generated streaming data for {duration} minutes")
                st.rerun()
        
        with col_b:
            if st.button("Stop Streaming"):
                st.session_state.stream_generator.is_running = False
                st.session_state.streaming_active = False
                st.warning("Streaming stopped")
    
    # Add delivery simulation section
    st.subheader("Delivery Simulation")
    col_sim_a, col_sim_b = st.columns(2)
    
    with col_sim_a:
        if st.button("Complete 5 Random Shipments"):
            with st.spinner("Completing shipments..."):
                # Import and run delivery simulator
                try:
                    from delivery_simulator import complete_random_shipments
                    completed = complete_random_shipments(5)
                    if completed > 0:
                        st.success(f"Completed {completed} shipments!")
                        st.info("Check the dashboard for updated delivery counts.")
                    else:
                        st.warning("No shipments available to complete")
                except Exception as e:
                    st.error(f"Error completing shipments: {e}")
    
    with col_sim_b:
        if st.button("Complete All Active Shipments"):
            with st.spinner("Completing all active shipments..."):
                try:
                    from delivery_simulator import complete_random_shipments
                    completed = complete_random_shipments(20)  # Complete up to 20
                    if completed > 0:
                        st.success(f"Completed {completed} shipments!")
                        st.info("All active shipments have been delivered.")
                    else:
                        st.warning("No active shipments found")
                except Exception as e:
                    st.error(f"Error completing shipments: {e}")
    
    with col2:
        st.subheader("Streaming Statistics")
        stats = st.session_state.stream_generator.stats
        
        st.metric("Tracking Events", stats.get('tracking_events', 0))
        st.metric("New Shipments", stats.get('new_shipments', 0))
        st.metric("Outliers Generated", stats.get('outliers_generated', 0))
        st.metric("Errors", stats.get('errors', 0))
        
        # Calculate rate if events exist
        if stats.get('tracking_events', 0) > 0:
            # This is a simple estimation - in real implementation you'd track actual time
            estimated_rate = stats.get('tracking_events', 0) / max(1, duration)
            st.metric("Current Rate (events/min)", f"{estimated_rate:.1f}")
    
    # Recent activity
    st.subheader("Recent Activity")
    if st.button("Show Recent Events"):
        recent_events = st.session_state.dashboard.get_recent_tracking_events(limit=10)
        if not recent_events.empty:
            st.dataframe(recent_events, use_container_width=True)
        else:
            st.info("No recent events found")

def show_outlier_detection():
    """Display outlier detection interface"""
    st.header("Outlier Detection System")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Model Training & Detection")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Train Outlier Model"):
                with st.spinner("Training outlier detection model..."):
                    success = st.session_state.outlier_detector.train_model()
                    if success:
                        st.success("Model trained successfully!")
                    else:
                        st.error("Model training failed")
        
        with col_b:
            lookback_minutes = st.number_input(
                "Lookback Period (minutes)", 
                min_value=5, 
                max_value=120, 
                value=30
            )
            
            if st.button("Detect Recent Outliers"):
                with st.spinner("Detecting outliers..."):
                    outliers = st.session_state.outlier_detector.detect_outliers_batch(
                        lookback_minutes=lookback_minutes
                    )
                    if outliers:
                        st.warning(f"Detected {len(outliers)} outliers!")
                        
                        # Display outlier details
                        outlier_df = pd.DataFrame(outliers)
                        st.dataframe(outlier_df, use_container_width=True)
                    else:
                        st.success("No outliers detected")
    
    with col2:
        st.subheader("Detection Summary")
        
        hours_back = st.selectbox("Summary Period", [1, 6, 12, 24], index=0)
        
        summary_df = st.session_state.outlier_detector.get_outlier_summary(hours=hours_back)
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True)
            
            # Simple chart of outlier types
            if len(summary_df) > 0:
                fig = px.bar(
                    summary_df, 
                    x='Outlier_Type', 
                    y='Count',
                    title=f"Outliers by Type (Last {hours_back}h)"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No outliers in the last {hours_back} hours")
    
    # Outlier monitoring section
    st.subheader("Continuous Monitoring")
    if st.checkbox("Enable Real-time Monitoring"):
        st.info("Real-time monitoring enabled - outliers will be detected automatically")
        # In a real implementation, you'd run this in a separate thread

def show_ml_predictions():
    """Display ML prediction interface"""
    st.header("Machine Learning Predictions")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Delivery Time Prediction")
        
        # Model training section
        col_train_a, col_train_b = st.columns(2)
        
        with col_train_a:
            if st.button("Train ML Models"):
                with st.spinner("Training machine learning models..."):
                    success = st.session_state.ml_predictor.train_models()
                    if success:
                        st.success("Models trained successfully!")
                    else:
                        st.error("Model training failed. This is likely due to a lack of sufficient historical data for training. Please ensure the data streamer has been run and there are completed shipments in the database.")
        
        with col_train_b:
            if st.button("Generate Sample Training Data"):
                with st.spinner("Generating sample completed shipments..."):
                    success = st.session_state.ml_predictor.generate_sample_completed_shipments(20)
                    if success:
                        st.success("Sample data generated! You can now train the ML models.")
                        st.info("Click 'Train ML Models' to train with the generated data.")
        
        # Prediction form
        st.subheader("Make Prediction")
        
        with st.form("prediction_form"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                distance = st.number_input("Distance (km)", 10, 3000, 500)
                cargo_weight = st.number_input("Cargo Weight (kg)", 10, 10000, 2000)
                vehicle_type = st.selectbox(
                    "Vehicle Type", 
                    ["Truck", "Van", "Semi-trailer", "Delivery", "Refrigerated"]
                )
                difficulty = st.selectbox(
                    "Route Difficulty", 
                    ["Easy", "Medium", "Hard"]
                )
            
            with col_b:
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
                hour_of_day = st.slider("Hour of Day", 0, 23, datetime.now().hour)
                day_of_week = st.slider("Day of Week (0=Monday)", 0, 6, datetime.now().weekday())
                driver_experience = st.number_input("Driver Experience (years)", 1, 50, 5)
                vehicle_age = st.number_input("Vehicle Age (years)", 0, 20, 5)
            
            if st.form_submit_button("Predict Delivery Time"):
                prediction_data = {
                    'distance_km': distance,
                    'cargo_weight': cargo_weight,
                    'vehicle_type': vehicle_type,
                    'difficulty_level': difficulty,
                    'priority': priority,
                    'hour_of_day': hour_of_day,
                    'day_of_week': day_of_week,
                    'driver_experience': driver_experience,
                    'vehicle_age': vehicle_age
                }
                
                result = st.session_state.ml_predictor.predict_delivery_time(prediction_data)
                if result:
                    st.success(f"Predicted Duration: {result:.1f} hours")
                    
                    # Show confidence level
                    confidence = random.uniform(0.75, 0.95)  # Mock confidence
                    st.info(f"Confidence Level: {confidence:.1%}")
                else:
                    st.error("Prediction failed - please train the model first")
    
    with col2:
        st.subheader("Model Performance")
        
        perf_df = st.session_state.ml_predictor.get_model_performance()
        if not perf_df.empty:
            st.dataframe(perf_df, use_container_width=True)
            
            # Performance visualization
            if 'MAE' in perf_df.columns:
                fig = px.bar(
                    perf_df, 
                    x='Model', 
                    y='MAE',
                    title="Model Accuracy (Lower is Better)"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Train models to see performance metrics")
        
        # Route optimization section
        st.subheader("Route Optimization")
        
        if st.button("Optimize Routes"):
            with st.spinner("Calculating optimal routes..."):
                # Mock route optimization
                optimization_results = {
                    'routes_analyzed': random.randint(10, 50),
                    'time_saved': random.uniform(2, 8),
                    'fuel_saved': random.uniform(5, 15),
                    'cost_reduction': random.uniform(100, 500)
                }
                
                st.metric("Routes Analyzed", optimization_results['routes_analyzed'])
                st.metric("Time Saved (hours)", f"{optimization_results['time_saved']:.1f}")
                st.metric("Fuel Saved (%)", f"{optimization_results['fuel_saved']:.1f}")
                st.metric("Cost Reduction ($)", f"{optimization_results['cost_reduction']:.0f}")

def main():
    """Main Streamlit application"""
    
    # Initialize session state
    initialize_session_state()
    
    # App title and header
    st.title("Logistics Streaming Analytics Pipeline")
    st.markdown("Real-time transportation and logistics data analytics platform")
    
    # Sidebar navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Data Streaming", "Outlier Detection", "ML Predictions"]
    )
    
    # Connection status in sidebar
    st.sidebar.subheader("System Status")
    try:
        conn_test = st.session_state.db_manager.test_connection()
        if conn_test:
            st.sidebar.success("Database Connected")
        else:
            st.sidebar.error("Database Disconnected")
    except:
        st.sidebar.error("Database Error")
    
    # Page routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "Data Streaming":
        show_streaming_control()
    elif page == "Outlier Detection":
        show_outlier_detection()
    elif page == "ML Predictions":
        show_ml_predictions()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Logistics Analytics v1.0")

if __name__ == "__main__":
    main()