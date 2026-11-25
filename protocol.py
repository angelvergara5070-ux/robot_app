"""
PROTOCOLO APP <-> ESP32-S3  (texto ASCII, un comando por línea, termina en \n)

APP -> ESP32  (característica RX, escritura sin respuesta)
  J,<x>,<y>,<DIR>   joystick. x e y de -100 a 100 (x: der+, y: adelante+)
                    DIR: ADE, ATR, IZQ, DER, ADE_IZQ, ADE_DER, ATR_IZQ, ATR_DER
  S                 detener robot
  H                 latido (sigue conectado, robot quieto)
  M,SUMO | M,FUT    cambio de modo
  R,UP | R,DOWN     (Sumo) subir / bajar rampa
  K                 (Futbolista) patear / empujar

Ejemplos reales:
  "J,-80,0,IZQ\n"      -> voy a la izquierda al 80 %
  "J,45,45,ADE_DER\n"  -> diagonal adelante-derecha
  "R,UP\n"             -> subir rampa
"""
import math

# UUID del servicio tipo "Nordic UART" (el ESP32 debe usar los mismos)
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # app -> ESP32 (write)
NOMBRE_ROBOT = "ROBOT"  # el ESP32 se anuncia como "ROBOT-S3"

ZONA_MUERTA = 0.08
_DIRS = ["DER", "ADE_DER", "ADE", "ADE_IZQ", "IZQ", "ATR_IZQ", "ATR", "ATR_DER"]


def direccion(x, y):
    """Convierte x,y (-100..100) en una etiqueta de dirección."""
    if math.hypot(x, y) < ZONA_MUERTA * 100:
        return "STOP"
    ang = math.degrees(math.atan2(y, x))
    return _DIRS[int(round(ang / 45.0)) % 8]


def joystick(x, y):
    return f"J,{x},{y},{direccion(x, y)}\n"


STOP = "S\n"
LATIDO = "H\n"
MODO_SUMO = "M,SUMO\n"
MODO_FUT = "M,FUT\n"
RAMPA_SUBIR = "R,UP\n"
RAMPA_BAJAR = "R,DOWN\n"
PATEAR = "K\n"
