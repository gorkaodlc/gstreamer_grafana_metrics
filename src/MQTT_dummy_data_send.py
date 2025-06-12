import paho.mqtt.client as mqtt
import socket
import time
import os
import json
import numpy as np

# MQTT Broker details
BROKER = "localhost"  # Replace with the broker's IP
MQTT_PORT = 1883
GPS_INFO_TOPIC = "gps_info"
USERNAME = "gortiz"
PASSWORD = "12345678"
MAX_PACKET_SIZE = 1400  # Safe UDP packet size limit

class MQTT_Broker:
    def __init__(self, username = USERNAME, password = PASSWORD, 
                 broker_ip = BROKER, broker_port = MQTT_PORT, init_broker = True):
        
        self.username = username
        self.password = password
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        if init_broker:
            self.init_broker()

    def init_broker(self):
        # Iniciar MQTT Client
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.broker_ip, self.broker_port)

        # Esperar 1 segundo a que se abra la conexión
        time.sleep(1)        
        print('Conexión abierta')

    def send_data(self, gps_info_topic, video_metrics_topic):
        id = 1111

        # Dump gps data in a json msg
        gps_data_dict = {
            "id": id,
            "send_ts": np.random.random(),
            "latitud": np.random.random(),
            "longitud": np.random.random(),
            "altitud": np.random.random(),
            "north_velocity": np.random.random(),
            "east_velocity": np.random.random(),
            "downward_velocity": np.random.random(),
            "acceleration_forward": np.random.random(),
            "acceleration_laterally": np.random.random(),
            "acceleration_downward": np.random.random(),
        }
        
        gps_data_json = json.dumps(gps_data_dict)

        # Dump metrics data in a json msg
        video_metrics_data_dict = {
            "id": id,
            "send_ts": np.random.random(),
            "latency": np.random.random(),
            "jitter": np.random.random(),
            "bitrate": np.random.random(),
            "fps": np.random.random(),
        }
        
        video_metrics_data_json = json.dumps(video_metrics_data_dict)

        # Publish info
        self.client.publish(gps_info_topic, gps_data_json)        
        self.client.publish(video_metrics_topic, video_metrics_data_json)
        
        print('Datos enviados', gps_data_json)

def main():
    gps_info_topic = 'gps_info'
    video_metrics_topic = 'video_metrics'
    mqtt_broker = MQTT_Broker()
    try:
        while True:
            mqtt_broker.send_data(gps_info_topic, video_metrics_topic)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\n Se ha presionado CTRL+C, parando')

if __name__ == "__main__":
    print('SENDING DATA')
    main()