"""
Database schema setup and initialization for Logistics Streaming Analytics
"""

import psycopg2
import logging
from database_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSchemaManager:
    """Manages database schema creation and initialization"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        
        # Database Schema SQL Definitions
        self.schema_sql = """
        -- Drivers table stores driver information and status
        CREATE TABLE IF NOT EXISTS drivers (
            driver_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,  -- Changed from driver_name to name
            license_number VARCHAR(50) UNIQUE NOT NULL,
            experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
            phone VARCHAR(20),
            rating DECIMAL(3,2) CHECK (rating >= 0 AND rating <= 5),
            status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'On Leave', 'Training', 'Inactive')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Vehicles table stores vehicle information and specifications
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id VARCHAR(20) PRIMARY KEY,
            vehicle_type VARCHAR(50) NOT NULL,
            make VARCHAR(50) NOT NULL,
            model VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL CHECK (year >= 1990 AND year <= 2030),
            capacity_kg DECIMAL(10,2) NOT NULL CHECK (capacity_kg > 0),
            fuel_efficiency DECIMAL(5,2) CHECK (fuel_efficiency > 0),
            status VARCHAR(20) DEFAULT 'Available' CHECK (status IN ('Available', 'In Use', 'Maintenance', 'Out of Service')),
            last_maintenance DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Routes table stores predefined shipping routes
        CREATE TABLE IF NOT EXISTS routes (
            route_id VARCHAR(20) PRIMARY KEY,
            route_name VARCHAR(100) NOT NULL,
            origin_city VARCHAR(100) NOT NULL,
            destination_city VARCHAR(100) NOT NULL,
            distance_km DECIMAL(8,2) NOT NULL CHECK (distance_km > 0),
            estimated_duration_hours DECIMAL(5,2) NOT NULL CHECK (estimated_duration_hours > 0),
            route_type VARCHAR(30) DEFAULT 'Standard' CHECK (route_type IN ('Express', 'Standard', 'Economy')),
            toll_cost DECIMAL(8,2) DEFAULT 0 CHECK (toll_cost >= 0),
            difficulty_level VARCHAR(20) DEFAULT 'Medium' CHECK (difficulty_level IN ('Easy', 'Medium', 'Hard', 'Extreme')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Shipments table stores individual shipment records
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id VARCHAR(20) PRIMARY KEY,
            vehicle_id VARCHAR(20) REFERENCES vehicles(vehicle_id),
            driver_id VARCHAR(20) REFERENCES drivers(driver_id),
            route_id VARCHAR(20) REFERENCES routes(route_id),
            departure_time TIMESTAMP NOT NULL,
            estimated_arrival TIMESTAMP NOT NULL,
            actual_arrival TIMESTAMP,
            cargo_weight DECIMAL(10,2) NOT NULL CHECK (cargo_weight > 0),
            cargo_type VARCHAR(50) NOT NULL,
            priority VARCHAR(20) DEFAULT 'Medium' CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
            status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Loading', 'In Transit', 'Delivered', 'Delayed', 'Cancelled')),
            customer_id VARCHAR(20),
            cost DECIMAL(12,2) CHECK (cost >= 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_arrival_after_departure CHECK (estimated_arrival > departure_time)
        );

        -- Shipment tracking table stores real-time tracking events
        CREATE TABLE IF NOT EXISTS shipment_tracking (
            tracking_id SERIAL PRIMARY KEY,
            shipment_id VARCHAR(20) REFERENCES shipments(shipment_id) ON DELETE CASCADE,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            current_location VARCHAR(200),
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            speed_kmh DECIMAL(5,2) CHECK (speed_kmh >= 0),
            fuel_level DECIMAL(5,2) CHECK (fuel_level >= 0 AND fuel_level <= 100),
            temperature DECIMAL(5,2),
            humidity DECIMAL(5,2) CHECK (humidity >= 0 AND humidity <= 100),
            status_update VARCHAR(100),
            is_outlier BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Outlier detections table stores anomaly detection results
        CREATE TABLE IF NOT EXISTS outlier_detections (
            outlier_id SERIAL PRIMARY KEY,
            shipment_id VARCHAR(20) REFERENCES shipments(shipment_id) ON DELETE CASCADE,
            tracking_id INTEGER REFERENCES shipment_tracking(tracking_id) ON DELETE CASCADE,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            outlier_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) DEFAULT 'Medium' CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
            confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
            description TEXT,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ML predictions table stores machine learning prediction results
        CREATE TABLE IF NOT EXISTS ml_predictions (
            prediction_id SERIAL PRIMARY KEY,
            shipment_id VARCHAR(20) REFERENCES shipments(shipment_id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_name VARCHAR(50) NOT NULL,
            prediction_type VARCHAR(50) NOT NULL,
            predicted_value TEXT NOT NULL,
            actual_value TEXT,
            accuracy_score DECIMAL(5,4) CHECK (accuracy_score >= 0 AND accuracy_score <= 1),
            confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
            features_used TEXT,
            model_version VARCHAR(20) DEFAULT '1.0'
        );
        """

        self.indexes_sql = """
        -- Performance indexes for efficient querying

        -- Shipments table indexes
        CREATE INDEX IF NOT EXISTS idx_shipments_departure ON shipments(departure_time);
        CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);
        CREATE INDEX IF NOT EXISTS idx_shipments_vehicle ON shipments(vehicle_id);
        CREATE INDEX IF NOT EXISTS idx_shipments_route ON shipments(route_id);
        CREATE INDEX IF NOT EXISTS idx_shipments_priority ON shipments(priority);
        CREATE INDEX IF NOT EXISTS idx_shipments_estimated_arrival ON shipments(estimated_arrival);

        -- Tracking table indexes for real-time queries
        CREATE INDEX IF NOT EXISTS idx_tracking_timestamp ON shipment_tracking(timestamp);
        CREATE INDEX IF NOT EXISTS idx_tracking_shipment ON shipment_tracking(shipment_id);
        CREATE INDEX IF NOT EXISTS idx_tracking_location ON shipment_tracking(latitude, longitude);
        CREATE INDEX IF NOT EXISTS idx_tracking_outlier ON shipment_tracking(is_outlier);

        -- Outlier detections indexes
        CREATE INDEX IF NOT EXISTS idx_outliers_detected_at ON outlier_detections(detected_at);
        CREATE INDEX IF NOT EXISTS idx_outliers_severity ON outlier_detections(severity);
        CREATE INDEX IF NOT EXISTS idx_outliers_resolved ON outlier_detections(resolved);
        CREATE INDEX IF NOT EXISTS idx_outliers_shipment ON outlier_detections(shipment_id);

        -- ML predictions indexes
        CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON ml_predictions(created_at);
        CREATE INDEX IF NOT EXISTS idx_predictions_shipment ON ml_predictions(shipment_id);
        CREATE INDEX IF NOT EXISTS idx_predictions_model ON ml_predictions(model_name);
        CREATE INDEX IF NOT EXISTS idx_predictions_type ON ml_predictions(prediction_type);

        -- Driver and vehicle performance indexes
        CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(status);
        CREATE INDEX IF NOT EXISTS idx_drivers_rating ON drivers(rating);
        CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);
        CREATE INDEX IF NOT EXISTS idx_vehicles_type ON vehicles(vehicle_type);

        -- Route optimization indexes
        CREATE INDEX IF NOT EXISTS idx_routes_distance ON routes(distance_km);
        CREATE INDEX IF NOT EXISTS idx_routes_duration ON routes(estimated_duration_hours);
        CREATE INDEX IF NOT EXISTS idx_routes_origin ON routes(origin_city);
        CREATE INDEX IF NOT EXISTS idx_routes_destination ON routes(destination_city);
        """

        self.views_sql = """
        -- Analytical views for dashboard and reporting

        -- Active shipments view - shows all shipments currently in progress
        CREATE OR REPLACE VIEW active_shipments AS
        SELECT 
            s.shipment_id,
            s.status,
            s.departure_time,
            s.estimated_arrival,
            s.priority,
            s.cargo_weight,
            s.cargo_type,
            d.name as driver_name,
            d.phone as driver_phone,
            d.rating as driver_rating,
            v.vehicle_type,
            v.make as vehicle_make,
            v.model as vehicle_model,
            CONCAT(r.origin_city, ' to ', r.destination_city) as route_name,
            r.origin_city,
            r.destination_city,
            r.distance_km,
            r.estimated_duration_hours,
            CASE 
                WHEN s.estimated_arrival < CURRENT_TIMESTAMP AND s.status IN ('In Transit', 'Loading')
                THEN 'Delayed'
                ELSE 'On Time'
            END as delivery_status,
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - s.departure_time))/3600 as hours_in_transit
        FROM shipments s
        JOIN drivers d ON s.driver_id = d.driver_id
        JOIN vehicles v ON s.vehicle_id = v.vehicle_id
        JOIN routes r ON s.route_id = r.route_id
        WHERE s.status IN ('Loading', 'In Transit', 'Pending');

        -- Shipment summary view - daily aggregated statistics
        CREATE OR REPLACE VIEW shipment_summary AS
        SELECT 
            DATE(s.departure_time) as date,
            COUNT(*) as total_shipments,
            COUNT(CASE WHEN s.status = 'Delivered' THEN 1 END) as delivered_shipments,
            COUNT(CASE WHEN s.status = 'In Transit' THEN 1 END) as in_transit_shipments,
            COUNT(CASE WHEN s.status = 'Delayed' THEN 1 END) as delayed_shipments,
            ROUND(AVG(s.cargo_weight), 2) as avg_cargo_weight,
            ROUND(SUM(s.cargo_weight), 2) as total_cargo_weight,
            ROUND(AVG(r.distance_km), 2) as avg_distance_km,
            ROUND(SUM(r.distance_km), 2) as total_distance_km,
            COUNT(DISTINCT s.driver_id) as unique_drivers,
            COUNT(DISTINCT s.vehicle_id) as unique_vehicles,
            ROUND(AVG(CASE 
                WHEN s.actual_arrival IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (s.actual_arrival - s.departure_time))/3600 
                ELSE NULL 
            END), 2) as avg_actual_duration_hours,
            COUNT(CASE 
                WHEN s.actual_arrival IS NOT NULL AND s.actual_arrival <= s.estimated_arrival 
                THEN 1 
            END) as on_time_deliveries,
            ROUND(
                COUNT(CASE 
                    WHEN s.actual_arrival IS NOT NULL AND s.actual_arrival <= s.estimated_arrival 
                    THEN 1 
                END) * 100.0 / NULLIF(COUNT(CASE WHEN s.status = 'Delivered' THEN 1 END), 0), 
                2
            ) as on_time_percentage
        FROM shipments s
        JOIN routes r ON s.route_id = r.route_id
        GROUP BY DATE(s.departure_time)
        ORDER BY date DESC;

        -- Real-time dashboard view
        CREATE OR REPLACE VIEW real_time_dashboard AS
        SELECT 
            (SELECT COUNT(*) FROM shipments WHERE status = 'In Transit') as active_shipments,
            (SELECT COUNT(*) FROM shipments WHERE status = 'Delivered' AND DATE(actual_arrival) = CURRENT_DATE) as today_deliveries,
            (SELECT COUNT(*) FROM drivers WHERE status = 'Active') as active_drivers,
            (SELECT COUNT(*) FROM vehicles WHERE status = 'In Use') as vehicles_in_use,
            (SELECT COUNT(*) FROM outlier_detections WHERE DATE(detected_at) = CURRENT_DATE AND resolved = FALSE) as unresolved_outliers,
            (SELECT ROUND(AVG(cargo_weight), 2) FROM shipments WHERE status = 'In Transit') as avg_cargo_in_transit,
            (SELECT COUNT(*) FROM shipments WHERE estimated_arrival < CURRENT_TIMESTAMP AND status IN ('In Transit', 'Loading')) as delayed_shipments;
        """
    
    def create_schema(self):
        """Create the complete database schema"""
        try:
            logger.info("Creating database schema...")
            
            # Skip table creation if all tables already exist
            if self.verify_schema():
                logger.info("All tables already exist, skipping table creation...")
            else:
                # Create tables
                logger.info("Creating tables...")
                if not self.db_manager.execute_query(self.schema_sql):
                    raise Exception("Failed to create tables")
            
            # Create indexes (safe to run multiple times)
            logger.info("Creating indexes...")
            if not self.db_manager.execute_query(self.indexes_sql):
                raise Exception("Failed to create indexes")
            
            # Create views (safe to run multiple times)
            logger.info("Creating views...")
            if not self.db_manager.execute_query(self.views_sql):
                raise Exception("Failed to create views")
            
            logger.info("Database schema created successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            return False
    
    def verify_schema(self):
        """Verify that all required tables exist"""
        required_tables = [
            'drivers', 'vehicles', 'routes', 'shipments', 
            'shipment_tracking', 'outlier_detections', 'ml_predictions'
        ]
        
        for table in required_tables:
            if not self.db_manager.get_table_exists(table):
                logger.warning(f"Table {table} does not exist")
                return False
        
        logger.info("All required tables exist")
        return True
    
    def initialize_if_needed(self):
        """Initialize schema if tables don't exist"""
        if not self.verify_schema():
            logger.info("Schema verification failed, creating schema...")
            return self.create_schema()
        
        logger.info("Schema already exists and is valid")
        return True

if __name__ == "__main__":
    # Test schema creation
    schema_manager = DatabaseSchemaManager()
    success = schema_manager.initialize_if_needed()
    
    if success:
        print("Database schema is ready!")
    else:
        print("Failed to initialize database schema!")