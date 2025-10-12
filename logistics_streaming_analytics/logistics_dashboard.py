import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

class LogisticsDashboard:
    """Real-time logistics dashboard with live KPIs and visualizations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.last_update = None
    
    def get_real_time_kpis(self):
        """Get current KPIs and metrics"""
        queries = {
            'active_shipments': """
                SELECT COUNT(*) 
                FROM shipments 
                WHERE status IN ('In Transit', 'Loading', 'Delayed')
            """,
            'completed_today': """
                SELECT COUNT(*) 
                FROM shipments 
                WHERE status = 'Delivered' 
                AND DATE(actual_arrival) = CURRENT_DATE
            """,
            'avg_delivery_time': """
                SELECT AVG(EXTRACT(EPOCH FROM (actual_arrival - departure_time))/3600) 
                FROM shipments 
                WHERE actual_arrival IS NOT NULL 
                AND departure_time >= CURRENT_DATE - INTERVAL '7 days'
            """,
            'on_time_percentage': """
                SELECT 
                    ROUND(100.0 * COUNT(CASE WHEN actual_arrival <= estimated_arrival THEN 1 END) 
                    / NULLIF(COUNT(*), 0), 2) 
                FROM shipments 
                WHERE actual_arrival IS NOT NULL 
                AND departure_time >= CURRENT_DATE - INTERVAL '7 days'
            """,
            'total_cargo_weight': """
                SELECT COALESCE(SUM(cargo_weight), 0) 
                FROM shipments 
                WHERE status IN ('In Transit', 'Loading')
            """,
            'recent_outliers': """
                SELECT COUNT(*) 
                FROM shipment_tracking 
                WHERE is_outlier = true 
                AND timestamp >= NOW() - INTERVAL '1 hour'
            """,
            'tracking_events_hour': """
                SELECT COUNT(*) 
                FROM shipment_tracking 
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
            """,
            'vehicle_utilization': """
                SELECT 
                    ROUND(100.0 * COUNT(CASE WHEN status = 'In Transit' THEN 1 END) 
                    / NULLIF(COUNT(*), 0), 2) 
                FROM vehicles
            """
        }
        
        kpis = {}
        for kpi_name, query in queries.items():
            try:
                result = self.db_manager.execute_query(query, fetch=True)
                value = result[0][0] if result and result[0] and result[0][0] is not None else 0
                kpis[kpi_name] = value
            except Exception as e:
                st.warning(f"Error getting {kpi_name}: {e}")
                kpis[kpi_name] = 0
        
        self.last_update = datetime.now()
        return kpis
    
    def get_shipment_status_distribution(self):
        """Get distribution of shipment statuses"""
        query = """
        SELECT status, COUNT(*) as count
        FROM shipments
        GROUP BY status
        ORDER BY count DESC
        """
        try:
            results = self.db_manager.execute_query(query, fetch=True)
            if results:
                return pd.DataFrame(results, columns=['Status', 'Count'])
            return pd.DataFrame()
        except Exception as e:
            st.warning(f"Error getting status distribution: {e}")
            return pd.DataFrame()
    
    def get_hourly_tracking_volume(self):
        """Get tracking events volume by hour"""
        query = """
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour,
            COUNT(*) as event_count
        FROM shipment_tracking
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY DATE_TRUNC('hour', timestamp)
        ORDER BY hour
        """
        try:
            results = self.db_manager.execute_query(query, fetch=True)
            if results:
                df = pd.DataFrame(results, columns=['Hour', 'Event_Count'])
                df['Hour'] = pd.to_datetime(df['Hour'])
                return df
            return pd.DataFrame()
        except Exception as e:
            st.warning(f"Error getting tracking volume: {e}")
            return pd.DataFrame()
    
    def get_vehicle_utilization(self):
        """Get vehicle utilization metrics"""
        query = """
        SELECT 
            v.vehicle_type,
            COUNT(DISTINCT v.vehicle_id) as total_vehicles,
            COUNT(DISTINCT CASE WHEN v.status = 'In Transit' THEN v.vehicle_id END) as active_vehicles,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN v.status = 'In Transit' THEN v.vehicle_id END) 
                  / NULLIF(COUNT(DISTINCT v.vehicle_id), 0), 2) as utilization_rate
        FROM vehicles v
        GROUP BY v.vehicle_type
        ORDER BY utilization_rate DESC
        """
        try:
            results = self.db_manager.execute_query(query, fetch=True)
            if results:
                return pd.DataFrame(results, columns=[
                    'Vehicle_Type', 'Total_Vehicles', 'Active_Vehicles', 'Utilization_Rate_%'
                ])
            return pd.DataFrame()
        except Exception as e:
            st.warning(f"Error getting vehicle utilization: {e}")
            return pd.DataFrame()
    
    def get_recent_tracking_events(self, limit=10):
        """Get recent tracking events"""
        query = """
        SELECT 
            st.shipment_id,
            st.current_location,
            st.speed_kmh,
            st.fuel_level,
            st.status_update,
            st.is_outlier,
            st.timestamp
        FROM shipment_tracking st
        ORDER BY st.timestamp DESC
        LIMIT %s
        """
        try:
            results = self.db_manager.execute_query(query, params=(limit,), fetch=True)
            if results:
                df = pd.DataFrame(results, columns=[
                    'Shipment_ID', 'Location', 'Speed_KMH', 'Fuel_%', 
                    'Status', 'Is_Outlier', 'Timestamp'
                ])
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                return df
            return pd.DataFrame()
        except Exception as e:
            st.warning(f"Error getting recent events: {e}")
            return pd.DataFrame()
    
    def get_route_performance(self):
        """Get route performance metrics"""
        query = """
        SELECT 
            r.route_name,
            r.distance_km,
            COUNT(s.shipment_id) as total_shipments,
            AVG(EXTRACT(EPOCH FROM (s.actual_arrival - s.departure_time))/3600) as avg_duration,
            COUNT(CASE WHEN s.actual_arrival <= s.estimated_arrival THEN 1 END) as on_time_count
        FROM routes r
        LEFT JOIN shipments s ON r.route_id = s.route_id
        WHERE s.actual_arrival IS NOT NULL
        GROUP BY r.route_id, r.route_name, r.distance_km
        HAVING COUNT(s.shipment_id) > 0
        ORDER BY on_time_count DESC
        LIMIT 10
        """
        try:
            results = self.db_manager.execute_query(query, fetch=True)
            if results:
                return pd.DataFrame(results, columns=[
                    'Route_Name', 'Distance_KM', 'Total_Shipments', 
                    'Avg_Duration_Hours', 'On_Time_Count'
                ])
            return pd.DataFrame()
        except Exception as e:
            st.warning(f"Error getting route performance: {e}")
            return pd.DataFrame()