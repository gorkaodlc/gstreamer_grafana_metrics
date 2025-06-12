#!/bin/bash

# Ejecutar script de Python en segundo plano
/home/VICOMTECH/gortiz/anaconda3/envs/rtmaps/bin/python3 ~/Proyectos/BasqueCCAM_Video_Streaming/2_Codigo/scripts/GPS_info_receive_MQTT.py &

# Ejecutar RTMaps en segundo plano
sudo rtmaps_runtime --run ~/Proyectos/BasqueCCAM_Video_Streaming/4_Modelos/diagramas_rtmaps/GPS_info.rtd > /dev/null 2>&1 &

# Esperar hasta que RTMaps esté en ejecución
echo "Esperando a que RTMaps se inicie..."
while ! pgrep -f "rtmaps_runtime" > /dev/null; do
    sleep 1
done
echo "RTMaps iniciado."

# Abrir Google Chrome con la URL
google-chrome "http://127.0.0.1:3000/d/eediu43z3mnlsa/gps-info?orgId=1&from=now-5m&to=now&timezone=browser&refresh=auto"
