import time
import stomp

from confing import ACTIVEMQ_HOST, ACTIVEMQ_PORT

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
