import requests
import time
import json
import stomp
import sys
import os

# CONFIGURATION & ENVIRONMENT VARIABLES 
# Fetching environment variables with fallback default values.
SIMULATOR_BASE_URL = os.getenv("SIMULATOR_URL", "http://simulator:8080")
ACTIVEMQ_HOST = os.getenv("BROKER_HOST", "activemq")
ACTIVEMQ_PORT = int(os.getenv("BROKER_PORT", "61613")) # STOMP protocol port

# List of REST endpoints (sensors) to poll based on the project contracts
SENSORS_TO_POLL = [
    "greenhouse_temperature", 
    "entrance_humidity", 
    "co2_hall", 
    "corridor_pressure",
    "hydroponic_ph",
    "air_quality_voc"
]

def normalize_rest_data(raw_data):
    """
    Transforms the raw JSON payload from the simulator into our Standard Event format.
    Handles both 'rest.scalar.v1' (single value) and 'rest.chemistry.v1' (array of measurements).
    """
    # Base structure for our Standard Event
    normalized_event = {
        "device_id": raw_data.get("sensor_id", "unknown_device"),
        "timestamp": raw_data.get("captured_at", ""),
        "status": raw_data.get("status", "ok"), # Default to 'ok' if missing
        "metrics": {},
        "metadata": {}
    }

    # Handle 'rest.scalar.v1' schema (e.g., temperature, humidity)
    if "metric" in raw_data and "value" in raw_data:
        normalized_event["metrics"][raw_data["metric"]] = raw_data["value"]
        if "unit" in raw_data:
            normalized_event["metadata"]["unit"] = raw_data["unit"]

    # Handle 'rest.chemistry.v1' schema (e.g., air quality with multiple measurements)
    elif "measurements" in raw_data:
        for item in raw_data["measurements"]:
            metric_name = item.get("metric")
            if metric_name and "value" in item:
                normalized_event["metrics"][metric_name] = item["value"]
                if "unit" in item:
                    # Prefixing the unit with the metric name to avoid overwriting
                    normalized_event["metadata"][f"{metric_name}_unit"] = item["unit"]

    return normalized_event

def connect_to_activemq():
    """
    Establishes a connection to ActiveMQ using the STOMP protocol.
    Implements a retry loop to wait for the broker to fully start up.
    """
    print("Connecting to ActiveMQ...")
    
    # Configure the connection to the broker container
    conn = stomp.Connection([(ACTIVEMQ_HOST, ACTIVEMQ_PORT)])
    
    while True:
        try:
            # Default ActiveMQ credentials (admin/admin)
            conn.connect('admin', 'admin', wait=True)
            print("Successfully connected to ActiveMQ!")
            return conn
        except Exception as e:
            print(f"ActiveMQ is not ready yet. Retrying in 3 seconds... (Error: {e})")
            time.sleep(3)

def poll_sensors():
    """
    Main execution loop.
    Periodically fetches data from the REST API, normalizes it, and publishes it to the broker.
    """
    conn = connect_to_activemq()
    print("Starting REST Polling service on ActiveMQ...")
    
    while True:
        for sensor_id in SENSORS_TO_POLL:
            url = f"{SIMULATOR_BASE_URL}/api/sensors/{sensor_id}"
            
            try:
                # 1. Fetch data from the simulator
                response = requests.get(url)
                
                if response.status_code == 200:
                    raw_data = response.json()
                    
                    # 2. Normalize the raw data
                    standard_event = normalize_rest_data(raw_data)
                    
                    # 3. Define the destination Topic (STOMP topics start with /topic/)
                    destination = f"/topic/sensor.rest.{sensor_id}"
                    
                    # 4. Publish the normalized event to the broker
                    conn.send(
                        body=json.dumps(standard_event), 
                        destination=destination
                    )
                    
                    print(f"📡 [Published] {destination}")
                    
            except Exception as e:
                print(f"Error polling {sensor_id}: {e}")
                
        # Wait 5 seconds before the next polling cycle
        time.sleep(5)

if __name__ == "__main__":
    poll_sensors()