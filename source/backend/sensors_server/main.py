import requests
import time
import json
import stomp
import sys
import os

SIMULATOR_BASE_URL = os.getenv("SIMULATOR_URL", "http://simulator:8080")
# ActiveMQ espone la porta 61613 per il protocollo STOMP
ACTIVEMQ_HOST = os.getenv("BROKER_HOST", "activemq")
ACTIVEMQ_PORT = int(os.getenv("BROKER_PORT", "61613"))

SENSORS_TO_POLL = [
    "greenhouse_temperature", 
    "entrance_humidity", 
    "co2_hall", 
    "corridor_pressure",
    "hydroponic_ph",
    "air_quality_voc"
]

def normalize_rest_data(raw_data):
    """Traduciamo il JSON del simulatore nel nostro Evento Standard"""
    normalized_event = {
        "device_id": raw_data.get("sensor_id", "unknown_device"),
        "timestamp": raw_data.get("captured_at", ""),
        "status": raw_data.get("status", "ok"),
        "metrics": {},
        "metadata": {}
    }

    if "metric" in raw_data and "value" in raw_data:
        normalized_event["metrics"][raw_data["metric"]] = raw_data["value"]
        if "unit" in raw_data:
            normalized_event["metadata"]["unit"] = raw_data["unit"]

    elif "measurements" in raw_data:
        for item in raw_data["measurements"]:
            metric_name = item.get("metric")
            if metric_name and "value" in item:
                normalized_event["metrics"][metric_name] = item["value"]
                if "unit" in item:
                    normalized_event["metadata"][f"{metric_name}_unit"] = item["unit"]

    return normalized_event

def connect_to_activemq():
    """Tenta di connettersi ad ActiveMQ usando il protocollo STOMP"""
    print("⏳ Connessione ad ActiveMQ in corso...")
    
    # Configuriamo la connessione verso il container 'activemq' sulla porta 61613
    conn = stomp.Connection([(ACTIVEMQ_HOST, ACTIVEMQ_PORT)])
    
    while True:
        try:
            # Le credenziali di default di ActiveMQ sono admin/admin
            conn.connect('admin', 'admin', wait=True)
            print("✅ Connesso con successo ad ActiveMQ!")
            return conn
        except Exception as e:
            print(f"ActiveMQ non è ancora pronto. Riprovo tra 3 secondi... (Errore: {e})")
            time.sleep(3)

def poll_sensors():
    conn = connect_to_activemq()
    print("🚀 Avvio del ciclo di REST Polling su ActiveMQ...")
    
    while True:
        for sensor_id in SENSORS_TO_POLL:
            url = f"{SIMULATOR_BASE_URL}/api/sensors/{sensor_id}"
            
            try:
                response = requests.get(url)
                
                if response.status_code == 200:
                    raw_data = response.json()
                    standard_event = normalize_rest_data(raw_data)
                    
                    # Definiamo il Topic. In STOMP i topic iniziano per /topic/
                    destination = f"/topic/sensor.rest.{sensor_id}"
                    
                    # SPEDIAMO IL MESSAGGIO AL TOPIC
                    conn.send(
                        body=json.dumps(standard_event), 
                        destination=destination
                    )
                    
                    print(f"📡 [Inviato] {destination}")
                    
            except Exception as e:
                print(f"❌ Errore durante il polling di {sensor_id}: {e}")
                
        time.sleep(5)

if __name__ == "__main__":
    poll_sensors()