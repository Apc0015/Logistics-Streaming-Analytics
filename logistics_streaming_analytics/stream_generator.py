import random
import time
from datetime import datetime, timedelta
from faker import Faker
import streamlit as st
import logging

class LogisticsStreamGenerator:
    """Real-time logistics data generator simulating 300+ events per minute"""
    
    def __init__(self, db_manager, events_per_minute=300):
        self.db_manager = db_manager
        self.events_per_minute = events_per_minute
        self.fake = Faker()
        self.is_running = False
        self.stats = {
            'tracking_events': 0,
            'new_shipments': 0,
            'outliers_generated': 0,
            'errors': 0
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_active_shipments(self):
        """Get list of active shipments for tracking updates"""
        try:
            query = "SELECT shipment_id FROM shipments WHERE status IN ('In Transit', 'Loading') LIMIT 100"
            results = self.db_manager.execute_query(query, fetch=True)
            return [row[0] for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Error getting active shipments: {e}")
            return []
    
    def get_available_resources(self):
        """Get available drivers, vehicles, and routes for new shipments"""
        try:
            # Get drivers
            driver_query = "SELECT driver_id FROM drivers WHERE status = 'Active' LIMIT 50"
            driver_results = self.db_manager.execute_query(driver_query, fetch=True)
            drivers = [row[0] for row in driver_results] if driver_results else []
            
            # Get vehicles
            vehicle_query = "SELECT vehicle_id FROM vehicles WHERE status = 'Available' LIMIT 50"
            vehicle_results = self.db_manager.execute_query(vehicle_query, fetch=True)
            vehicles = [row[0] for row in vehicle_results] if vehicle_results else []
            
            # Get routes
            route_query = "SELECT route_id FROM routes LIMIT 50"
            route_results = self.db_manager.execute_query(route_query, fetch=True)
            routes = [row[0] for row in route_results] if route_results else []
            
            return drivers, vehicles, routes
            
        except Exception as e:
            self.logger.error(f"Error getting available resources: {e}")
            return [], [], []
    
    def generate_tracking_event(self, shipment_id):
        """Generate a realistic tracking event for a shipment"""
        try:
            # Get current location from a realistic distribution
            base_lat = 39.8283 + random.uniform(-10, 10)  # US center
            base_lon = -98.5795 + random.uniform(-20, 20)
            
            # Introduce outliers occasionally
            is_outlier = random.random() < 0.05  # 5% outlier rate
            
            event_data = {
                'shipment_id': shipment_id,
                'current_location': f"{self.fake.city()}, {self.fake.state_abbr()}",
                'latitude': round(base_lat, 6),
                'longitude': round(base_lon, 6),
                'speed_kmh': random.uniform(40, 120) if not is_outlier else random.uniform(150, 200),
                'fuel_level': random.uniform(10, 100) if not is_outlier else random.uniform(0, 5),
                'temperature': random.uniform(-5, 35) if not is_outlier else random.uniform(60, 80),
                'humidity': random.uniform(30, 80),
                'status_update': random.choice([
                    'On Route', 'Stopped', 'Loading', 'Unloading', 
                    'Refueling', 'Rest Break', 'Traffic Delay'
                ]),
                'is_outlier': is_outlier
            }
            
            if is_outlier:
                self.stats['outliers_generated'] += 1
                
            return event_data
            
        except Exception as e:
            self.logger.error(f"Error generating tracking event: {e}")
            self.stats['errors'] += 1
            return None
    
    def generate_new_shipment(self, drivers, vehicles, routes):
        """Generate a new shipment"""
        try:
            if not drivers or not vehicles or not routes:
                return None
                
            shipment_id = f"SH{random.randint(10000, 99999)}"
            
            shipment_data = {
                'shipment_id': shipment_id,
                'vehicle_id': random.choice(vehicles),
                'driver_id': random.choice(drivers),
                'route_id': random.choice(routes),
                'departure_time': datetime.now(),
                'estimated_arrival': datetime.now() + timedelta(hours=random.uniform(2, 48)),
                'cargo_weight': random.uniform(100, 5000),
                'cargo_type': random.choice(['Electronics', 'Food', 'Clothing', 'Machinery', 'Medical']),
                'priority': random.choice(['High', 'Medium', 'Low']),
                'status': random.choice(['Pending', 'Loading', 'In Transit']),  # Fixed: Use valid statuses
                'customer_id': f"CUST{random.randint(1000, 9999)}",
                'cost': random.uniform(800, 4000)
            }
            
            self.stats['new_shipments'] += 1
            return shipment_data
            
        except Exception as e:
            self.logger.error(f"Error generating new shipment: {e}")
            self.stats['errors'] += 1
            return None
    
    def insert_tracking_event(self, event_data):
        """Insert tracking event into database"""
        try:
            query = """
            INSERT INTO shipment_tracking
            (shipment_id, current_location, latitude, longitude, speed_kmh,
             fuel_level, temperature, humidity, status_update, is_outlier)
            VALUES (%(shipment_id)s, %(current_location)s, %(latitude)s, %(longitude)s,
                    %(speed_kmh)s, %(fuel_level)s, %(temperature)s, %(humidity)s,
                    %(status_update)s, %(is_outlier)s)
            """
            result = self.db_manager.execute_query(query, params=event_data)
            if result is None:
                self.logger.error(f"Failed to insert tracking event for shipment {event_data.get('shipment_id')}")
                self.stats['errors'] += 1
            else:
                self.stats['tracking_events'] += 1
                self.logger.debug(f"Inserted tracking event for shipment {event_data.get('shipment_id')}")

        except Exception as e:
            self.logger.error(f"Error inserting tracking event: {e}")
            self.stats['errors'] += 1
    
    def update_shipment_status(self):
        """Update shipment statuses to simulate delivery progress"""
        try:
            # Get shipments that should be delivered (past estimated arrival)
            query = """
            SELECT shipment_id, status, estimated_arrival, departure_time 
            FROM shipments 
            WHERE status IN ('In Transit', 'Loading', 'Pending')
            AND estimated_arrival < NOW()
            ORDER BY estimated_arrival DESC
            LIMIT 10
            """
            
            results = self.db_manager.execute_query(query, fetch=True)
            if not results:
                return
            
            for row in results:
                shipment_id, current_status, estimated_arrival, departure_time = row
                
                # 80% chance of successful delivery, 20% chance of delay
                if random.random() < 0.8:
                    # Mark as delivered
                    actual_arrival = datetime.now()
                    update_query = """
                    UPDATE shipments 
                    SET status = 'Delivered', actual_arrival = %s, updated_at = NOW()
                    WHERE shipment_id = %s
                    """
                    self.db_manager.execute_query(update_query, params=(actual_arrival, shipment_id))
                    
                    # Free up the vehicle
                    vehicle_query = """
                    UPDATE vehicles SET status = 'Available' 
                    WHERE vehicle_id = (SELECT vehicle_id FROM shipments WHERE shipment_id = %s)
                    """
                    self.db_manager.execute_query(vehicle_query, params=(shipment_id,))
                    
                else:
                    # Mark as delayed
                    update_query = """
                    UPDATE shipments 
                    SET status = 'Delayed', updated_at = NOW()
                    WHERE shipment_id = %s
                    """
                    self.db_manager.execute_query(update_query, params=(shipment_id,))
                    
        except Exception as e:
            self.logger.error(f"Error updating shipment statuses: {e}")
    
    def progress_active_shipments(self):
        """Progress shipments through their lifecycle"""
        try:
            # Update pending shipments to loading
            pending_query = """
            UPDATE shipments 
            SET status = 'Loading', updated_at = NOW()
            WHERE status = 'Pending' 
            AND departure_time <= NOW() + INTERVAL '30 minutes'
            AND random() < 0.3
            """
            self.db_manager.execute_query(pending_query)
            
            # Update loading shipments to in transit
            loading_query = """
            UPDATE shipments 
            SET status = 'In Transit', updated_at = NOW()
            WHERE status = 'Loading' 
            AND departure_time <= NOW()
            AND random() < 0.5
            """
            self.db_manager.execute_query(loading_query)
            
        except Exception as e:
            self.logger.error(f"Error progressing shipments: {e}")
    
    def insert_new_shipment(self, shipment_data):
        """Insert new shipment into database"""
        try:
            query = """
            INSERT INTO shipments
            (shipment_id, vehicle_id, driver_id, route_id, departure_time,
             estimated_arrival, cargo_weight, cargo_type, priority, status,
             customer_id, cost)
            VALUES (%(shipment_id)s, %(vehicle_id)s, %(driver_id)s, %(route_id)s,
                    %(departure_time)s, %(estimated_arrival)s, %(cargo_weight)s,
                    %(cargo_type)s, %(priority)s, %(status)s, %(customer_id)s, %(cost)s)
            """
            result = self.db_manager.execute_query(query, params=shipment_data)
            if result is None:
                self.logger.error(f"Failed to insert new shipment {shipment_data.get('shipment_id')}")
                self.stats['errors'] += 1
                return

            # Update vehicle status
            # Update vehicle status to "In Use" (valid status)
            update_query = "UPDATE vehicles SET status = 'In Use' WHERE vehicle_id = %(vehicle_id)s"
            update_result = self.db_manager.execute_query(update_query, params={'vehicle_id': shipment_data['vehicle_id']})
            if update_result is None:
                self.logger.warning(f"Failed to update vehicle status for {shipment_data['vehicle_id']}")

            self.stats['new_shipments'] += 1
            self.logger.info(f"Successfully inserted new shipment {shipment_data.get('shipment_id')}")

        except Exception as e:
            self.logger.error(f"Error inserting new shipment: {e}")
            self.stats['errors'] += 1
    
    def generate_streaming_data(self, duration_minutes=5):
        """Generate streaming logistics data for specified duration"""
        st.info(f"Starting data generation for {duration_minutes} minutes...")
        st.info(f"Target rate: {self.events_per_minute} events per minute")

        self.logger.info(f"Starting data generation for {duration_minutes} minutes at {self.events_per_minute} events/min")

        self.is_running = True
        start_time = time.time()

        # Get available resources
        drivers, vehicles, routes = self.get_available_resources()
        st.info(f"Available resources: {len(drivers)} drivers, {len(vehicles)} vehicles, {len(routes)} routes")
        self.logger.info(f"Available resources - Drivers: {len(drivers)}, Vehicles: {len(vehicles)}, Routes: {len(routes)}")

        if not drivers or not vehicles or not routes:
            st.error("No available resources found. Please populate the database first.")
            self.logger.error("No available resources found for data generation")
            return

        event_interval = 60.0 / self.events_per_minute  # seconds between events
        self.logger.info(f"Event interval: {event_interval:.2f} seconds")

        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        events_generated = 0
        total_events_target = int(duration_minutes * self.events_per_minute)

        try:
            while self.is_running and (time.time() - start_time) < (duration_minutes * 60):
                # Get active shipments for tracking updates
                active_shipments = self.get_active_shipments()
                self.logger.debug(f"Active shipments count: {len(active_shipments)}")

                # Generate tracking events (80% of events)
                if active_shipments and random.random() < 0.8:
                    shipment_id = random.choice(active_shipments)
                    event_data = self.generate_tracking_event(shipment_id)
                    if event_data:
                        self.insert_tracking_event(event_data)
                        events_generated += 1
                        self.logger.debug(f"Generated tracking event for shipment {shipment_id}")

                # Generate new shipments occasionally (20% of events)
                elif random.random() < 0.2:
                    shipment_data = self.generate_new_shipment(drivers, vehicles, routes)
                    if shipment_data:
                        self.insert_new_shipment(shipment_data)
                        events_generated += 1
                        self.logger.info(f"Generated new shipment: {shipment_data['shipment_id']}")

                # Update shipment statuses every 10 events
                if events_generated % 10 == 0:
                    self.progress_active_shipments()
                    self.update_shipment_status()
                    self.logger.debug("Updated shipment statuses")

                # Update progress
                elapsed = time.time() - start_time
                progress = min(elapsed / (duration_minutes * 60), 1.0)
                progress_bar.progress(progress)

                current_rate = events_generated / max(elapsed / 60, 0.1)
                status_text.text(f"Generated {events_generated} events | Rate: {current_rate:.1f}/min | Outliers: {self.stats['outliers_generated']}")

                # Sleep until next event
                time.sleep(event_interval)

        except Exception as e:
            st.error(f"Error during streaming: {e}")
            self.logger.error(f"Error during streaming: {e}")
            self.is_running = False

        # Final statistics
        elapsed_time = time.time() - start_time
        progress_bar.progress(1.0)

        st.success("Streaming session completed!")
        st.info(f"Duration: {elapsed_time/60:.2f} minutes")
        st.info(f"Tracking events: {self.stats['tracking_events']}")
        st.info(f"New shipments: {self.stats['new_shipments']}")
        st.info(f"Outliers generated: {self.stats['outliers_generated']}")
        st.info(f"Average rate: {self.stats['tracking_events']/(elapsed_time/60):.2f} events/minute")

        self.logger.info(f"Streaming session completed - Duration: {elapsed_time/60:.2f} min, Events: {self.stats['tracking_events']}, Shipments: {self.stats['new_shipments']}, Outliers: {self.stats['outliers_generated']}")

        self.is_running = False
    
    def generate_sample_data(self, n_records=100):
        """Generate sample data for testing"""
        sample_data = []
        for i in range(n_records):
            event_data = self.generate_tracking_event(f"SH{10000 + i}")
            if event_data:
                sample_data.append(event_data)
        return sample_data