import paho.mqtt.client as mqtt
import json
from  InfluxDB_client import InfluxDBHandler

# MQTT Broker details
BROKER = "localhost"  # Replace with the broker's IP
MQTT_PORT = 1883
GPS_INFO_TOPIC = "gps_info"
USERNAME = "gortiz"
PASSWORD = "gorka"
MAX_PACKET_SIZE = 1400  # Safe UDP packet size limit

# InfluxDB details
DATABASE_NAME = "gps_info"
influx_handler = None

# Callback que se ejecuta al conectar con el broker
def on_connect(client, userdata, flags, rc):
    global influx_handler
    if rc == 0:
        print("Conectado exitosamente al broker")
        # Se suscribe al tópico 
        client.subscribe(GPS_INFO_TOPIC)

        # Inicializa la base de datos
        influx_handler = InfluxDBHandler(database=DATABASE_NAME)

    else:
        print("Error de conexión, código:", rc)

# Callback que se ejecuta al recibir un mensaje
def on_message(client, userdata, msg):
    try:
        global influx_handler

        # Se decodifica el payload
        payload = msg.payload.decode('utf-8')
        # Se convierte el mensaje JSON a un diccionario de Python
        data = json.loads(payload)
        
        # Se definen los nombres de los datos que se esperan
        claves_esperadas = ["latitud", "longitud", "altitud", "north_velocity", "east_velocity", "downward_velocity", "acceleration_forward", "acceleration_laterally", "acceleration_downward"]
        
        if all(clave in data for clave in claves_esperadas):
            print("Datos recibidos:")

            # Guardar información en la base de datos
            influx_handler.insert_gps_data(data['latitud'], data['longitud'], data['altitud'], data['north_velocity'], data['east_velocity'], data['downward_velocity'], data['acceleration_forward'], 
                                           data['acceleration_laterally'], data['acceleration_downward'])
        else:
            print("El mensaje no contiene todos los datos necesarios.")
    except json.JSONDecodeError:
        print("Error al decodificar el JSON del payload.")

def main():
    # Crea una instancia del cliente MQTT
    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
        
    client.on_connect = on_connect
    client.on_message = on_message

    # Conecta al broker
    client.connect(BROKER, MQTT_PORT, keepalive=60)

    # Mantiene el script en ejecución esperando mensajes
    client.loop_forever()

if __name__ == "__main__":
    main()