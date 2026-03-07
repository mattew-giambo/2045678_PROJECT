import stomp
import time
import json
import os

# Usiamo 'activemq' come default al posto di localhost, fondamentale su Docker!
ACTIVEMQ_HOST = os.getenv("BROKER_HOST", "activemq")
ACTIVEMQ_PORT = int(os.getenv("BROKER_PORT", "61613"))

# 1. L'ASCOLTATORE (IL CAMPANELLO)
class MarsAutomationListener(stomp.ConnectionListener):
    def on_error(self, frame):
        print(f"❌ Errore dal broker: {frame.body}")

    def on_message(self, frame):
        topic_di_provenienza = frame.headers['destination']
        dati_ricevuti = json.loads(frame.body)
        
        print(f"\n🔔 [NUOVO EVENTO] Ricevuto da {topic_di_provenienza}")
        print(f"🌡️ Sensore: {dati_ricevuti['device_id']}")
        print(f"📊 Valori: {dati_ricevuti['metrics']}")

# 2. IL RETRY LOOP (Quello che mancava!)
def connect_to_activemq():
    print("⏳ Connessione ad ActiveMQ in corso...")
    
    while True:
        try:
            # Spostiamo l'inizializzazione della connessione DENTRO il ciclo
            conn = stomp.Connection([(ACTIVEMQ_HOST, ACTIVEMQ_PORT)])
            conn.set_listener('', MarsAutomationListener())
            conn.connect('admin', 'admin', wait=True)
            print("✅ Connesso con successo ad ActiveMQ!")
            return conn
        except Exception as e:
            print(f"ActiveMQ non è ancora pronto. Riprovo tra 3 secondi... (Errore: {e})")
            time.sleep(3)

# 3. AVVIO DEL MOTORE
def start_automation_engine():
    print("🤖 Motore di Automazione in avvio...")
    
    # Ora usa la funzione sicura con il loop
    conn = connect_to_activemq()
    
    conn.subscribe(destination='/topic/sensor.rest.*', id=1, ack='auto')
    print("🎧 In ascolto passivo sui sensori REST...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Spegnimento...")
        conn.disconnect()

if __name__ == "__main__":
    start_automation_engine()