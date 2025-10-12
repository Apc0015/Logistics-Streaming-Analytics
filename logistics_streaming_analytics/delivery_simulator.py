"""
Delivery Simulation Helper - Manually complete shipments for testing
"""
import random
from datetime import datetime, timedelta
from database_manager import DatabaseManager

def complete_random_shipments(count=5):
    """Manually complete some shipments to simulate deliveries"""
    db = DatabaseManager()
    
    try:
        # Get shipments that can be completed
        query = """
        SELECT shipment_id, departure_time, estimated_arrival 
        FROM shipments 
        WHERE status IN ('In Transit', 'Pending', 'Loading')
        ORDER BY departure_time ASC
        LIMIT %s
        """
        
        results = db.execute_query(query, params=(count * 2,), fetch=True)
        if not results:
            print("No active shipments found to complete")
            return 0
        
        completed = 0
        for row in results[:count]:
            shipment_id, departure_time, estimated_arrival = row
            
            # Generate realistic actual arrival time
            if estimated_arrival:
                # 80% on time, 20% delayed
                if random.random() < 0.8:
                    actual_arrival = estimated_arrival - timedelta(minutes=random.randint(-30, 30))
                else:
                    actual_arrival = estimated_arrival + timedelta(minutes=random.randint(30, 120))
            else:
                # Use departure time + random duration
                actual_arrival = departure_time + timedelta(hours=random.uniform(2, 48))
            
            # Update shipment to delivered
            update_query = """
            UPDATE shipments 
            SET status = 'Delivered', 
                actual_arrival = %s,
                updated_at = NOW()
            WHERE shipment_id = %s
            """
            
            success = db.execute_query(update_query, params=(actual_arrival, shipment_id))
            if success:
                completed += 1
                print(f"Completed shipment {shipment_id}")
                
                # Free up the vehicle
                vehicle_query = """
                UPDATE vehicles SET status = 'Available' 
                WHERE vehicle_id = (SELECT vehicle_id FROM shipments WHERE shipment_id = %s)
                """
                db.execute_query(vehicle_query, params=(shipment_id,))
        
        print(f"\nSuccessfully completed {completed} shipments!")
        return completed
        
    except Exception as e:
        print(f"Error completing shipments: {e}")
        return 0

if __name__ == "__main__":
    complete_random_shipments(10)