import asyncio
from collections import deque

from bleak import BleakClient, BleakScanner

import protocol as P


class RobotBLE:
    """Una sola conexión BLE que se mantiene viva al cambiar de modo."""

    def __init__(self, on_state=None):
        self.client = None
        self.on_state = on_state or (lambda s: None)
        self.cmds = deque()       # comandos puntuales (rampa, patear, stop...)
        self.joy = (0, 0)         # último valor del joystick
        self._task = None

    @property
    def connected(self):
        return self.client is not None and self.client.is_connected

    async def scan(self, timeout=5.0):
        self.on_state("buscando")
        devs = await BleakScanner.discover(timeout=timeout)
        self.on_state("conectado" if self.connected else "desconectado")
        # solo dispositivos con nombre; los del robot primero
        devs = [d for d in devs if d.name]
        devs.sort(key=lambda d: not d.name.upper().startswith(P.NOMBRE_ROBOT))
        return [(d.name, d.address) for d in devs]

    async def connect(self, address):
        await self.disconnect()
        self.on_state("conectando")
        self.client = BleakClient(address, disconnected_callback=self._perdida)
        try:
            await self.client.connect()
        except Exception:
            self.client = None
            self.on_state("error")
            return False
        self.on_state("conectado")
        self._task = asyncio.ensure_future(self._tx_loop())
        return True

    async def disconnect(self):
        if self._task:
            self._task.cancel()
            self._task = None
        if self.client:
            try:
                await self.client.write_gatt_char(P.RX_UUID, P.STOP.encode(), response=False)
                await self.client.disconnect()
            except Exception:
                pass
        self.client = None
        self.on_state("desconectado")

    def _perdida(self, _client):
        self.on_state("desconectado")  # el ESP32 frena solo por su watchdog

    # ---- API para la interfaz ----
    def set_joystick(self, x, y):
        if (x, y) == (0, 0) and self.joy != (0, 0):
            self.cmds.append(P.STOP)   # al soltar: stop inmediato
        self.joy = (x, y)

    def send(self, cmd):
        if self.connected:
            self.cmds.append(cmd)

    # ---- bucle de envío (20 veces por segundo) ----
    async def _write(self, texto):
        await self.client.write_gatt_char(P.RX_UUID, texto.encode(), response=False)

    async def _tx_loop(self):
        try:
            while self.connected:
                while self.cmds:
                    await self._write(self.cmds.popleft())
                x, y = self.joy
                await self._write(P.joystick(x, y) if (x or y) else P.LATIDO)
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        self.on_state("desconectado")
