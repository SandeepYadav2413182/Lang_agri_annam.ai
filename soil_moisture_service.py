import datetime
import random
import math
import time
import threading
from queue import Queue
import database as db

class SoilMoistureService:
    """
    Service for managing soil moisture sensor data and simulating IoT devices
    in the absence of actual hardware sensors.
    """
    
    def __init__(self):
        """Initialize the soil moisture service"""
        self.simulation_running = False
        self.simulation_thread = None
        self.data_queue = Queue()
        self.registered_callbacks = []
    
    def register_callback(self, callback):
        """Register a callback function to receive real-time data"""
        if callback not in self.registered_callbacks:
            self.registered_callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """Unregister a callback function"""
        if callback in self.registered_callbacks:
            self.registered_callbacks.remove(callback)
    
    def _notify_callbacks(self, data):
        """Notify all registered callbacks with new data"""
        for callback in self.registered_callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in callback: {str(e)}")
    
    def start_simulation(self, user_id):
        """
        Start a background thread that simulates IoT soil moisture sensor data
        
        Args:
            user_id (int): The user ID to generate data for
        """
        if self.simulation_running:
            return False
        
        self.simulation_running = True
        self.simulation_thread = threading.Thread(
            target=self._simulation_worker,
            args=(user_id,),
            daemon=True
        )
        self.simulation_thread.start()
        return True
    
    def stop_simulation(self):
        """Stop the simulation thread"""
        self.simulation_running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=1.0)
            self.simulation_thread = None
    
    def _simulation_worker(self, user_id):
        """
        Background worker that simulates IoT sensor data
        
        Args:
            user_id (int): The user ID to generate data for
        """
        # Get the user's sensors
        sensors = db.get_soil_moisture_sensors(user_id)
        
        # If no sensors exist, create some sample ones
        if not sensors:
            # Get user's locations
            locations = db.get_saved_locations(user_id)
            if locations:
                for i, loc in enumerate(locations[:3]):  # Use up to 3 saved locations
                    sensor_id = f"SENSOR_{i+1}_{int(time.time())}"
                    depth = random.choice([5, 10, 20, 30])
                    sensor_type = random.choice(["Capacitive", "Resistive", "TDR"])
                    
                    # Register a new sensor
                    db.register_soil_moisture_sensor(
                        user_id=user_id,
                        name=f"Soil Sensor {i+1} - {loc['name']}",
                        sensor_id=sensor_id,
                        location_name=loc['name'],
                        latitude=loc['latitude'],
                        longitude=loc['longitude'],
                        field_area=f"Field {i+1}",
                        depth=depth,
                        sensor_type=sensor_type
                    )
            
            # Reload sensors
            sensors = db.get_soil_moisture_sensors(user_id)
        
        # If we still have no sensors, we can't simulate
        if not sensors:
            print("No sensors available for simulation")
            self.simulation_running = False
            return
        
        # Create initial sensor states for simulation
        sensor_states = {}
        for sensor in sensors:
            # Start with a random moisture level between 25% and 80%
            sensor_states[sensor['id']] = {
                'moisture': random.uniform(25, 80),
                'moisture_trend': random.choice([-0.1, 0, 0.1]),  # Declining, stable, or rising
                'temperature': random.uniform(18, 25),
                'ec': random.uniform(500, 1500),  # Electrical conductivity in µS/cm
                'battery': random.uniform(70, 100),
                'signal': random.randint(-90, -50),  # Signal strength in dBm
                'last_reading': datetime.datetime.now() - datetime.timedelta(
                    minutes=random.randint(5, 60)
                )
            }
        
        # Simulation loop
        while self.simulation_running:
            # Determine which sensor to update (random selection)
            sensor = random.choice(sensors)
            sensor_id = sensor['id']
            state = sensor_states[sensor_id]
            
            # Calculate time since last reading
            now = datetime.datetime.now()
            time_diff = (now - state['last_reading']).total_seconds() / 60  # minutes
            
            # Update the sensor state with realistic changes
            
            # 1. Moisture level - changes slowly based on trend
            moisture_change = state['moisture_trend'] * time_diff * random.uniform(0.01, 0.05)
            # Add some randomness to simulate noise
            moisture_change += random.uniform(-0.2, 0.2)
            state['moisture'] += moisture_change
            
            # Make sure moisture stays in a realistic range (0-100%)
            state['moisture'] = max(0, min(100, state['moisture']))
            
            # Occasionally change the trend
            if random.random() < 0.1:  # 10% chance to change trend
                state['moisture_trend'] = random.choice([-0.1, 0, 0.1])
            
            # 2. Temperature - changes slowly with small fluctuations
            temp_change = random.uniform(-0.1, 0.1) * time_diff
            state['temperature'] += temp_change
            # Keep temperature in realistic range
            state['temperature'] = max(10, min(35, state['temperature']))
            
            # 3. Electrical conductivity - relatively stable
            ec_change = random.uniform(-5, 5) * time_diff
            state['ec'] += ec_change
            # Keep EC in realistic range
            state['ec'] = max(100, min(3000, state['ec']))
            
            # 4. Battery - slowly decreases
            battery_change = -0.01 * time_diff  # Decrease about 1% per 100 minutes
            state['battery'] += battery_change
            
            # 5. Signal strength - fluctuates a bit
            signal_change = random.randint(-2, 2)
            state['signal'] += signal_change
            # Keep signal in realistic range
            state['signal'] = max(-100, min(-40, state['signal']))
            
            # Update last reading time
            state['last_reading'] = now
            
            # Record the reading in the database
            reading = db.record_soil_moisture_reading(
                sensor_id=sensor_id,
                moisture_percentage=state['moisture'],
                temperature=state['temperature'],
                electrical_conductivity=state['ec'],
                battery_level=state['battery'],
                signal_strength=state['signal']
            )
            
            # Add sensor context to the reading
            if reading:
                reading['sensor_name'] = sensor['name']
                reading['location_name'] = sensor['location_name']
                reading['depth'] = sensor['depth']
                reading['sensor_type'] = sensor['sensor_type']
                reading['field_area'] = sensor['field_area']
                
                # Push to queue for real-time updates
                self.data_queue.put(reading)
                
                # Notify callbacks
                self._notify_callbacks(reading)
            
            # Sleep for a random interval (1-5 seconds for simulation)
            # In a real app with real sensors, this would be driven by actual sensor data
            time.sleep(random.uniform(1, 5))
    
    def get_latest_readings(self, max_items=10):
        """
        Get the latest readings from the queue without waiting
        
        Args:
            max_items (int): Maximum number of readings to retrieve
            
        Returns:
            list: List of the latest sensor readings
        """
        readings = []
        for _ in range(min(max_items, self.data_queue.qsize())):
            if not self.data_queue.empty():
                readings.append(self.data_queue.get())
            else:
                break
        return readings
    
    def get_moisture_status(self, moisture_level):
        """
        Get the status and recommendations based on moisture level
        
        Args:
            moisture_level (float): Soil moisture percentage (0-100)
            
        Returns:
            dict: Status and recommendations
        """
        if moisture_level < 20:
            return {
                "status": "Critically Dry",
                "condition": "danger",
                "recommendation": "Immediate irrigation needed. Plants may be experiencing severe water stress."
            }
        elif moisture_level < 35:
            return {
                "status": "Dry",
                "condition": "warning",
                "recommendation": "Schedule irrigation soon. Soil moisture approaching critical levels."
            }
        elif moisture_level < 65:
            return {
                "status": "Optimal",
                "condition": "good",
                "recommendation": "Moisture levels ideal. Maintain current irrigation schedule."
            }
        elif moisture_level < 80:
            return {
                "status": "Moist",
                "condition": "moderate",
                "recommendation": "Moisture adequate. Consider reducing irrigation frequency."
            }
        else:
            return {
                "status": "Saturated",
                "condition": "danger",
                "recommendation": "Soil over-saturated. Pause irrigation to prevent root rot and nutrient leaching."
            }

# Create a singleton instance
soil_moisture_service = SoilMoistureService()