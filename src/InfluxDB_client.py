from influxdb import InfluxDBClient
import numpy as np

class InfluxDBHandler:
    def __init__(self, host='localhost', port=8086, database='gps_info'):
        # Conectar al servidor InfluxDB
        self.client = InfluxDBClient(host=host, port=port)
        self.database = database
        self._init_db()

    def _init_db(self):
        # Verifica si la base de datos existe; si no, la crea
        databases = self.client.get_list_database()
        if not any(db['name'] == self.database for db in databases):
            self.client.create_database(self.database)
            print('No existe la base de datos {0}, se ha creado'.format(self.database))
        self.client.switch_database(self.database)
        print('La base de datos {0} se ha cargado correctamente'.format(self.database))

    def insert_stream_metrics_data(self, id, latency, jitter, bitrate, fps):
        json_body = [
            {
                "measurement": self.database,
                "tags": {}, 
                "fields": {
                    "id": np.float64(id),
                    "latency": np.float64(latency),
                    "jitter": np.float64(jitter),
                    "bitrate": np.float64(bitrate),
                    "fps": np.float64(fps)
                }
            }
        ]
        print(json_body)
        # Inserta el punto de datos en la base de datos
        self.client.write_points(json_body)
        print("Datos insertados correctamente.")
        
    def insert_gps_data(self, id, latitud, longitud, altitud, north_velocity, east_velocity, downward_velocity,
                    acceleration_forward, acceleration_laterally, acceleration_downward):
        # Prepara el punto de datos a insertar; en este ejemplo, usamos el nombre de la base de datos
        # como el "measurement". Puedes cambiarlo si lo prefieres.
        velocidad_resultante = np.sqrt(north_velocity**2 + east_velocity**2 + downward_velocity**2)
        aceleracion_resultante = np.sqrt(acceleration_forward**2 + acceleration_laterally**2 + acceleration_downward**2)

        json_body = [
            {
                "measurement": self.database,
                "tags": {}, 
                "fields": {
                    "id": np.float64(id),
                    "latitud": np.float64(latitud),
                    "longitud": np.float64(longitud),
                    "altitud": np.float64(altitud),
                    "north_velocity": np.float64(north_velocity),
                    "east_velocity": np.float64(east_velocity),
                    "downward_velocity": np.float64(downward_velocity),
                    "velocidad_resultante": np.float64(velocidad_resultante),
                    "acceleration_forward": np.float64(acceleration_forward),
                    "acceleration_laterally": np.float64(acceleration_laterally),
                    "acceleration_downward": np.float64(acceleration_downward),
                    "aceleracion_resultante": np.float64(aceleracion_resultante)
                }
            }
        ]
        print(json_body)
        # Inserta el punto de datos en la base de datos
        self.client.write_points(json_body)
        print("Datos insertados correctamente.")

# Ejemplo de uso:
if __name__ == "__main__":
    # Instancia el handler para la base de datos 'gps_info'
    influx_handler = InfluxDBHandler(database='gps_info')
    
    # Inserta un conjunto de datos de ejemplo
    influx_handler.insert_gps_data(
        latitud=40.4168,
        longitud=-3.7038,
        altitud=667,
        north_velocity=5.0,
        east_velocity=5.0,
        downward_velocity=0.0,
        acceleration_forward=0.1,
        acceleration_laterally=0.0,
        acceleration_downward=0.05
    )