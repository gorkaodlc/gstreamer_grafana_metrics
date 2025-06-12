import paho.mqtt.client as mqtt
import time
import argparse

class MQTTHandshake:
    def __init__(self, broker="localhost", port=1883, username="gortiz", password="gorka", 
                 handshake_topic="handshake", response_topic="handshake/response", timeout_duration=100):
        """
        Initialize the MQTT handshake handler.
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.handshake_topic = handshake_topic
        self.response_topic = response_topic
        self.timeout_duration = timeout_duration
        self.server_address = None
        self.handshake_received = False
        
        self.client = mqtt.Client(userdata=self)
        self.client.username_pw_set(self.username, self.password)
        self.client.on_message = self.on_message

    def on_message(self, client, userdata, message):
        """Callback function to handle received messages."""
        print(f" DEBUG: Received message on topic {message.topic}: {message.payload.decode()}")
        self.server_address = message.payload.decode()
        self.handshake_received = True

    def perform_handshake(self):
        """
        Perform MQTT handshake and return the server address.
        """
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        
        print(f" DEBUG: Subscribing to {self.response_topic}...")
        self.client.subscribe(self.response_topic)
        
        time.sleep(1)  # Ensure subscription is active before publishing
        
        print(f" Client sending handshake request to {self.handshake_topic}...")
        self.client.publish(self.handshake_topic, "Request: Connect")
        
        timeout = time.time() + self.timeout_duration
        while self.server_address is None:
            if time.time() > timeout:
                print(" ERROR: No response from server!")
                self.client.loop_stop()
                self.client.disconnect()
                return None
            time.sleep(0.1)
        
        self.client.loop_stop()
        self.client.disconnect()
        
        server_ip, server_port = self.server_address.split(":")
        return server_ip, int(server_port)

    def start_handshake_server(self, server_ip="127.0.0.1", server_port=5005):
        """
        Start an MQTT server that listens for handshake requests and responds with the server's IP and port.
        """
        def on_message(client, userdata, message):
            print(f" Received handshake request: {message.payload.decode()}")
            response = f"{server_ip}:{server_port}"
            print(f" Sending server address: {response}")
            client.publish(self.response_topic, response)
            self.handshake_received = True
        
        self.client.on_message = on_message
        self.client.connect(self.broker, self.port)
        self.client.subscribe(self.handshake_topic)
        self.client.loop_start()
        
        print(" Server is waiting for handshake requests...")
        
        start_time = time.time()
        while not self.handshake_received and (time.time() - start_time < self.timeout_duration):
            time.sleep(1)
        
        if self.handshake_received:
            print(" Handshake received, proceeding...")
            return True
        else:
            print(" Handshake wait time exceeded 10 seconds.")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT Handshake Script")
    parser.add_argument("mode", choices=["send", "receive"], help="Mode: send (client) or receive (server)")
    args = parser.parse_args()
    
    mqtt_handshake = MQTTHandshake()
    
    if args.mode == "send":
        server_info = mqtt_handshake.perform_handshake()
        if server_info:
            print(f" Server IP: {server_info[0]}, Port: {server_info[1]}")
        else:
            print("⚠️ Handshake failed. Exiting.")
    elif args.mode == "receive":
        mqtt_handshake.start_handshake_server()