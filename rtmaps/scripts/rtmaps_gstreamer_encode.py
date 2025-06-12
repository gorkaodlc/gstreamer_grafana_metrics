import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # base class
import numpy as np
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import time
import cv2
from PIL import Image
from PIL import ImageDraw
import os

# Inicializar GStreamer
Gst.init(None)

class rtmaps_python(BaseComponent):
    
    def __init__(self):
        BaseComponent.__init__(self) 
        self.streaming_started = False

    def Dynamic(self):
        self.add_output("imageOut", rtmaps.types.IPL_IMAGE)
        self.add_output("latencyOut", rtmaps.types.AUTO)
        self.add_output("jitterOut", rtmaps.types.AUTO)
        self.add_output("bitrateOut", rtmaps.types.AUTO)
        self.add_output("fpsOut", rtmaps.types.AUTO)
        
        self.add_property("port", "5000", subtype=rtmaps.types.AUTO)
        
# Birth() will be called once at diagram execution startup
    def Birth(self):
        # Cargar puerto
        self.port = self.get_property("ground_truth_trajectory")
        # Configuración del Pipeline de GStreamer
        self.pipeline_str = f"""
                udpsrc port={self.port} caps="application/x-rtp,encoding-name=H264,payload=96" !
                rtpjitterbuffer latency=100 !
                rtph264depay !
                h264parse !
                avdec_h264 !
                videoconvert !
                video/x-raw,format=BGR,width=1920,height=1536 !
                queue2 max-size-buffers=100 !
                identity name=identity_latency silent=false !
                appsink name=appsink sync=false max-buffers=1 drop=true
            """

        # Crear el pipeline
        self.pipeline = Gst.parse_launch(self.pipeline_str)

        # Variables globales para métricas
        self.previous_latency = None
        self.frame_count = 0
        self.start_time = time.time()
        self.total_bytes = 0
        self.previous_time = time.time()

        # Iniciar variable imagen        
        #first_img = Image.fromarray(cv2.colorChange(image, cv2.COLOR_BGR2RGB))
        self.image_out = rtmaps.types.Ioelt()
        self.image_out.data = rtmaps.types.IplImage()
        self.image_out.data.color_model = "COLR"  
        self.image_out.data.channel_seq = "RGB" 

        self.images_out = []
        self.latency_out = [0.0]
        self.jitter_out = [0.0]
        self.bitrate_out = [0.0]
        self.fps_out = [0.0]
        self.appsink = self.pipeline.get_by_name("appsink")

        # Para el procesamiento de un nuevo frame
        self.appsink = self.pipeline.get_by_name("appsink")
        self.appsink.set_property("emit-signals", True)
        self.appsink.connect("new-sample", self.on_new_sample)
        
        # Probes para métricas
        identity_latency = self.pipeline.get_by_name("identity_latency")
        if identity_latency:
            pad = identity_latency.get_static_pad("src")
            if pad:
                pad.add_probe(Gst.PadProbeType.BUFFER, self.latency_jitter_probe, None)
                pad.add_probe(Gst.PadProbeType.BUFFER, self.fps_probe, None)

        identity_bitrate = self.pipeline.get_by_name("identity_bitrate")
        if identity_bitrate:
            pad = identity_bitrate.get_static_pad("src")
            if pad:
                pad.add_probe(Gst.PadProbeType.BUFFER, self.bitrate_probe, None)

        # Iniciar el pipeline
        self.pipeline.set_state(Gst.State.PLAYING)

        # Ejecutar la medición de bitrate cada segundo
        GLib.timeout_add_seconds(1, self.calculate_bitrate)     

        # Publicar información cada 0.1 segundos
        #self.send_outputs(total=False)

    # Función para procesar un nuevo frame
    def on_new_sample(self, sink):
        if not self.streaming_started:
            print(' <---- /!\ STREAMING STARTED /!\ ')
            self.streaming_started = True
        
        sample = sink.emit("pull-sample")
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        width = caps.get_structure(0).get_value('width')
        height = caps.get_structure(0).get_value('height')
        #format = caps.get_structure(0).get_value('format')

        # Acceso directo a los datos del frame
        success, map_info = buffer.map(Gst.MapFlags.READ)
        if not success:
            return Gst.PadProbeReturn.OK

        # Convertir el buffer a un array de NumPy
        frame_data = np.frombuffer(map_info.data, dtype=np.uint8)

        frame_bgr = frame_data.reshape((height, width, 3))
        frame_rgb = cv2.colorChange(frame_bgr, cv2.COLOR_BGR2RGB)

        pil_image_rgb = Image.fromarray(frame_rgb)

        # Liberar el buffer
        buffer.unmap(map_info)

        # Guardar imagen para RTMaps
        print('Se va a crear la imagen')
        self.image_out = rtmaps.types.Ioelt()
        self.image_out.data = rtmaps.types.IplImage()
        self.image_out.data.color_model = "COLR"  
        self.image_out.data.channel_seq = "RGB" 
        print('Imagen creada')
        self.image_out.data.image_data = pil_image_rgb
        print('IPL asignado')
        self.write("imageOut", self.image_out)
        print('Imagen enviada')
        print('---------------')

        self.images_out.append(frame_bgr)

        return Gst.FlowReturn.OK

    def send_outputs(self):
        self.write("imageOut", self.images_out[-1])
        self.write("latencyOut", self.latency_out[-1])
        self.write("jitterOut", self.jitter_out[-1])
        self.write("bitrateOut", self.bitrate_out[-1])
        self.write("fpsOut", self.fps_out[-1])
            
# Core() is called every time you have a new inputs available, depending on your chosen reading policy
    def Core(self):
        if self.streaming_started:
            self.send_outputs()   
        else:
            print(' --> /!\ STREAMING NOT STARTED')     

# Death() will be called once at diagram execution shutdown
    def Death(self):
        pass

    # Función para medir latencia y jitter
    def latency_jitter_probe(self, pad, info, user_data):
        buffer = info.get_buffer()
        if buffer is None:
            return Gst.PadProbeReturn.OK

        timestamp_ns = buffer.pts
        if timestamp_ns == Gst.CLOCK_TIME_NONE:
            return Gst.PadProbeReturn.OK

        base_time_ns = self.pipeline.get_base_time()
        clock = self.pipeline.get_clock()
        if clock:
            now_ns = clock.get_time() - base_time_ns
        else:
            return Gst.PadProbeReturn.OK

        latency_ms = (now_ns - timestamp_ns) / 1_000_000
        jitter = abs(latency_ms - self.previous_latency) if self.previous_latency is not None else 0
        self.previous_latency = latency_ms

        # Guardar latencia y jitter a los outputs de RTMaps
        self.latency_out.append(latency_ms)
        self.jitter_out.append(jitter)

        return Gst.PadProbeReturn.OK

    # Función para medir el bitrate
    def bitrate_probe(self, pad, info, user_data):
        buffer = info.get_buffer()
        if buffer:
            self.total_bytes += buffer.get_size()
        return Gst.PadProbeReturn.OK    
    def calculate_bitrate(self):
        current_time = time.time()
        elapsed_time = current_time - self.previous_time
        print('Elapsded time', elapsed_time)
        if elapsed_time > 0:
            bitrate = (self.total_bytes * 8) / elapsed_time
            self.total_bytes = 0
            self.previous_time = current_time
            # Guardar bitrate para RTMaps
            self.bitrate_out.append(bitrate)
        return True

    # Función para calcular FPS
    def fps_probe(self, pad, info, user_data):
        buffer = info.get_buffer()
        if buffer is None:
            return Gst.PadProbeReturn.OK

        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1:
            fps = self.frame_count / elapsed_time
            self.frame_count = 0
            self.start_time = time.time()
            # Guardar FPS para RTMaps
            self.fps_out.append(fps)
        return Gst.PadProbeReturn.OK
