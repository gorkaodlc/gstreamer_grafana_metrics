import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # base class
import paho.mqtt.client as mqtt
import socket
import time
import os
import json
import numpy as np

# MQTT Broker details
#MAX_PACKET_SIZE = 1400  # Safe UDP packet size limit

# Python class that will be called from RTMaps.
class rtmaps_python(BaseComponent):
    
    # Constructor has to call the BaseComponent parent class
    def __init__(self):
        BaseComponent.__init__(self)  # call base class constructor
        self.handshake_flag = False
        
    def Dynamic(self):
        # Add input
        self.add_input("TELEOP_IP", rtmaps.types.ANY)
        self.add_input("TELEOP_PORT", rtmaps.types.ANY)
        self.add_input("gps_pos_lla", rtmaps.types.ANY)
        self.add_input("north_velocity", rtmaps.types.ANY)
        self.add_input("east_velocity", rtmaps.types.ANY)
        self.add_input("downward_velocity", rtmaps.types.ANY)
        self.add_input("acceleration_forward", rtmaps.types.ANY)
        self.add_input("acceleration_laterally", rtmaps.types.ANY)
        self.add_input("acceleration_downward", rtmaps.types.ANY)        

        # Propiedades
        self.add_property("gps_info_topic", "gps_info")
        self.add_property("broker", "localhost")
        self.add_property("port", 1883)
        self.add_property("username", "gortiz")
        self.add_property("password", "gorka")       
# Birth() will be called once at diagram execution startup
    def Birth(self):
        self.gps_info_topic = self.get_property("gps_info_topic")
        self.broker = self.get_property("broker")
        self.port = self.get_property("port")
        self.username = self.get_property("username")
        self.password = self.get_property("password")
        
        # Initialize MQTT Client
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.broker, self.port)

        # Esperar 1 segundo a que se abra la conexión
        time.sleep(1)        
        print('Conexión abierta')

# Core() is called every time you have a new inputs available, depending on your chosen reading policy
    def Core(self):
        # Gestión de emepezar solo cuando se recive el handshake
        if not self.handshake_flag and self.inputs["TELEOP_IP"].ioelt is not None and self.inputs["TELEOP_PORT"].ioelt is not None: # Empezar el envio de métricas
            print(' -> HANDSHAKE RECEIVED !!')
            self.handshake_flag = True
            
        if self.handshake_flag:
            gps_pos_lla = self.inputs["gps_pos_lla"].ioelt
            latitud = np.float64(gps_pos_lla.data[0])
            longitud = np.float64(gps_pos_lla.data[1])
            altitud = np.float64(gps_pos_lla.data[2])        
            north_velocity = np.float64(self.inputs["north_velocity"].ioelt.data)
            east_velocity = np.float64(self.inputs["east_velocity"].ioelt.data)
            downward_velocity = np.float64(self.inputs["downward_velocity"].ioelt.data)
            acceleration_forward = np.float64(self.inputs["acceleration_forward"].ioelt.data)
            acceleration_laterally = np.float64(self.inputs["acceleration_laterally"].ioelt.data)
            acceleration_downward = np.float64(self.inputs["acceleration_downward"].ioelt.data)

            # Dump info a mensaje json
            gps_data_dict = {
                "id": 1111,
                "latitud": latitud,
                "longitud": longitud,
                "altitud": altitud,
                "north_velocity": north_velocity,
                "east_velocity": east_velocity,
                "downward_velocity": downward_velocity,
                "acceleration_forward": acceleration_forward,
                "acceleration_laterally": acceleration_laterally,
                "acceleration_downward": acceleration_downward,
            }
            
            gps_data_json = json.dumps(gps_data_dict)

            # Publicar info
            self.client.publish(self.gps_info_topic, gps_data_json)        
            #print('Datos enviados')

# Death() will be called once at diagram execution shutdown
    def Death(self):
        self.client.disconnect()
        print('Conexión cerrada')