import asyncio
import math

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hx, platform

import protocol as P

if platform != "android":
    Window.size = (900, 420)  # simula pantalla horizontal en el PC

ROJO, VERDE, FONDO = "#ff4d6d", "#22d3a0", "#0b1020"
COLORES_ESTADO = {"conectado": VERDE, "conectando": "#ffd166", "buscando": "#ffd166",
                  "desconectado": "#8a93b8", "error": ROJO}


# ------------------------------------------------------------------ widgets
class Joystick(Widget):
    """Joystick táctil. Entrega x,y de -100 a 100 (velocidad = distancia)."""

    def __init__(self, color, on_change, **kw):
        super().__init__(**kw)
        self.color = hx(color)
        self.on_change = on_change
        self._touch = None
        self.kx = self.ky = 0.0
        self.bind(pos=self._draw, size=self._draw)

    @property
    def radio(self):
        return min(self.width, self.height) / 2

    def _draw(self, *_):
        self.canvas.clear()
        cx, cy = self.center
        r = self.radio
        travel = r * 0.62
        with self.canvas:
            Color(*self.color[:3], 0.12)
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            Color(*self.color[:3], 0.8)
            Line(circle=(cx, cy, r), width=dp(2))
            Color(*self.color[:3], 0.35)
            Line(circle=(cx, cy, travel), width=dp(1))
            Color(*self.color[:3], 1)
            kr = r * 0.38
            Ellipse(pos=(cx + self.kx * travel - kr, cy + self.ky * travel - kr),
                    size=(2 * kr, 2 * kr))

    def _mover(self, touch):
        cx, cy = self.center
        travel = self.radio * 0.62
        dx, dy = (touch.x - cx) / travel, (touch.y - cy) / travel
        m = math.hypot(dx, dy)
        if m > 1:
            dx, dy, m = dx / m, dy / m, 1
        if m < P.ZONA_MUERTA:
            dx = dy = 0.0
        self.kx, self.ky = dx, dy
        self._draw()
        self.on_change(int(round(dx * 100)), int(round(dy * 100)))

    def on_touch_down(self, touch):
        if self._touch is None and math.hypot(touch.x - self.center_x,
                                              touch.y - self.center_y) <= self.radio * 1.25:
            self._touch = touch
            self._mover(touch)
            return True
        return False

    def on_touch_move(self, touch):
        if touch is self._touch:
            self._mover(touch)
            return True
        return False

    def on_touch_up(self, touch):
        if touch is self._touch:
            self._touch = None
            self.kx = self.ky = 0.0   # vuelve al centro
            self._draw()
            self.on_change(0, 0)      # y el robot se detiene
            return True
        return False


class BotonAccion(Widget):
    """Botón circular con multitáctil propio (funciona a la vez que el joystick)."""

    def __init__(self, texto, color, on_down, **kw):
        super().__init__(**kw)
        self.color = hx(color)
        self.on_down = on_down
        self._touch = None
        self.activo = False
        self.lbl = Label(text=texto, bold=True, font_size=sp(16), halign="center",
                         color=self.color)
        self.add_widget(self.lbl)
        self.bind(pos=self._draw, size=self._draw)

    def set_text(self, t):
        self.lbl.text = t

    def _draw(self, *_):
        self.canvas.before.clear()
        cx, cy = self.center
        r = min(self.size) / 2
        with self.canvas.before:
            Color(*self.color[:3], 0.9 if self._touch or self.activo else 0.12)
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            Color(*self.color[:3], 1)
            Line(circle=(cx, cy, r), width=dp(3))
        self.lbl.center = self.center
        self.lbl.size = self.size
        self.lbl.text_size = self.size
        self.lbl.color = (0.05, 0.06, 0.1, 1) if (self._touch or self.activo) else self.color

    def on_touch_down(self, touch):
        r = min(self.size) / 2
        if self._touch is None and math.hypot(touch.x - self.center_x,
                                              touch.y - self.center_y) <= r:
            self._touch = touch
            self._draw()
            self.on_down()
            return True
        return False

    def on_touch_up(self, touch):
        if touch is self._touch:
            self._touch = None
            self._draw()
            return True
        return False


def fondo(widget, color):
    with widget.canvas.before:
        Color(*hx(color))
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda w, v: setattr(rect, "pos", v),
                size=lambda w, v: setattr(rect, "size", v))


def etiqueta_estado(app):
    lbl = Label(font_size=sp(12), size_hint=(None, None), size=(dp(220), dp(24)),
                halign="left")

    def act(*_):
        lbl.text = f"BLE: {app.estado}"
        lbl.color = hx(COLORES_ESTADO.get(app.estado, "#ffffff"))
        lbl.text_size = lbl.size

    app.bind(estado=act)
    act()
    return lbl


# ------------------------------------------------------------------ pantallas
class Inicio(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        app = App.get_running_app()
        raiz = FloatLayout()
        fondo(raiz, FONDO)
        self.titulo = Label(text="ROBOT ARENA", font_size=sp(44), bold=True,
                            pos_hint={"center_x": .5, "center_y": .72}, color=hx("#e8ecff"))
        sub = Label(text="elige tu modo de combate", font_size=sp(14), color=hx("#6b7aa8"),
                    pos_hint={"center_x": .5, "center_y": .6})
        sumo = Button(text="SUMO", font_size=sp(24), bold=True, background_normal="",
                      background_color=hx(ROJO), color=hx("#150a12"),
                      size_hint=(.3, .26), pos_hint={"center_x": .3, "center_y": .32})
        fut = Button(text="FUTBOLISTA", font_size=sp(24), bold=True, background_normal="",
                     background_color=hx(VERDE), color=hx("#08150f"),
                     size_hint=(.3, .26), pos_hint={"center_x": .7, "center_y": .32})
        sumo.bind(on_release=lambda *_: self.ir("sumo"))
        fut.bind(on_release=lambda *_: self.ir("futbol"))
        con = Button(text="Conectar robot", font_size=sp(13), background_normal="",
                     background_color=hx("#1c2440"), size_hint=(None, None),
                     size=(dp(150), dp(34)), pos_hint={"right": .98, "top": .98})
        con.bind(on_release=lambda *_: setattr(self.manager, "current", "escaneo"))
        st = etiqueta_estado(app)
        st.pos_hint = {"x": .02, "top": .98}
        for w in (self.titulo, sub, sumo, fut, con, st):
            raiz.add_widget(w)
        self.add_widget(raiz)
        self._pulso(sumo), self._pulso(fut, 0.4)

    def _pulso(self, w, retraso=0.0):
        a = Animation(opacity=0.65, duration=0.9) + Animation(opacity=1, duration=0.9)
        a.repeat = True
        Clock.schedule_once(lambda dt: a.start(w), retraso)

    def on_enter(self, *_):
        a = Animation(font_size=sp(48), duration=1.2) + Animation(font_size=sp(44), duration=1.2)
        a.repeat = True
        a.start(self.titulo)

    def on_leave(self, *_):
        Animation.cancel_all(self.titulo)

    def ir(self, modo):
        app = App.get_running_app()
        if not app.ble.connected:
            self.manager.current = "escaneo"  # primero hay que conectar
        else:
            self.manager.current = modo


class Escaneo(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = App.get_running_app()
        raiz = FloatLayout()
        fondo(raiz, FONDO)
        raiz.add_widget(Label(text="DISPOSITIVOS BLE", font_size=sp(20), bold=True,
                              pos_hint={"center_x": .5, "top": 1}, size_hint=(1, .15)))
        self.lista = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        sv = ScrollView(size_hint=(.7, .6), pos_hint={"center_x": .5, "center_y": .52})
        sv.add_widget(self.lista)
        buscar = Button(text="Buscar", background_normal="", background_color=hx(VERDE),
                        color=hx("#08150f"), size_hint=(.25, .13), pos_hint={"x": .05, "y": .04})
        volver = Button(text="Volver", background_normal="", background_color=hx("#1c2440"),
                        size_hint=(.25, .13), pos_hint={"right": .95, "y": .04})
        buscar.bind(on_release=lambda *_: asyncio.ensure_future(self.buscar()))
        volver.bind(on_release=lambda *_: setattr(self.manager, "current", "inicio"))
        st = etiqueta_estado(self.app)
        st.pos_hint = {"center_x": .5, "y": .06}
        for w in (sv, buscar, volver, st):
            raiz.add_widget(w)
        self.add_widget(raiz)

    def on_enter(self, *_):
        asyncio.ensure_future(self.buscar())

    async def buscar(self):
        self.lista.clear_widgets()
        try:
            devs = await self.app.ble.scan()
        except Exception as e:
            self.lista.add_widget(Label(text=f"Error: {e}", size_hint_y=None, height=dp(40)))
            return
        for nombre, addr in devs:
            b = Button(text=f"{nombre}   [{addr}]", size_hint_y=None, height=dp(44),
                       background_normal="", background_color=hx("#1c2440"))
            b.bind(on_release=lambda _b, a=addr: asyncio.ensure_future(self.conectar(a)))
            self.lista.add_widget(b)

    async def conectar(self, addr):
        if await self.app.ble.connect(addr):
            self.manager.current = "inicio"


class Juego(Screen):
    """Pantalla de juego base: joystick izquierda, botón de acción derecha."""
    MODO = ""
    COLOR = VERDE
    FONDO = FONDO
    TXT_ACCION = ""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = App.get_running_app()
        raiz = FloatLayout()
        fondo(raiz, self.FONDO)
        self.joy = Joystick(self.COLOR, self.al_mover, size_hint=(None, None),
                            size=(dp(190), dp(190)), pos_hint={"x": .06, "y": .1})
        self.accion = BotonAccion(self.TXT_ACCION, self.COLOR, self.al_accion,
                                   size_hint=(None, None), size=(dp(150), dp(150)),
                                   pos_hint={"right": .92, "y": .14})
        self.info = Label(text="X 0 · Y 0 · STOP", font_size=sp(13), color=hx(self.COLOR),
                          size_hint=(None, None), size=(dp(220), dp(24)),
                          pos_hint={"right": .98, "top": .98})
        volver = Button(text="< Menu", size_hint=(None, None), size=(dp(80), dp(34)),
                        background_normal="", background_color=hx("#1c2440"),
                        pos_hint={"x": .02, "top": .98})
        volver.bind(on_release=lambda *_: setattr(self.manager, "current", "inicio"))
        stop = Button(text="STOP", bold=True, size_hint=(None, None), size=(dp(80), dp(34)),
                      background_normal="", background_color=hx(ROJO),
                      pos_hint={"center_x": .5, "top": .98})
        stop.bind(on_release=lambda *_: self.parar())
        st = etiqueta_estado(self.app)
        st.pos_hint = {"x": .13, "top": .98}
        for w in (self.joy, self.accion, self.info, volver, stop, st):
            raiz.add_widget(w)
        self.add_widget(raiz)

    def al_mover(self, x, y):
        self.app.ble.set_joystick(x, y)
        self.info.text = f"X {x} · Y {y} · {P.direccion(x, y)}"

    def parar(self):
        self.joy.kx = self.joy.ky = 0
        self.joy._draw()
        self.al_mover(0, 0)
        self.app.ble.send(P.STOP)

    def al_accion(self):
        pass

    def on_enter(self, *_):
        self.app.ble.send(P.MODO_SUMO if self.MODO == "SUMO" else P.MODO_FUT)

    def on_leave(self, *_):
        self.parar()


class Sumo(Juego):
    MODO, COLOR, FONDO, TXT_ACCION = "SUMO", ROJO, "#150a12", "RAMPA\nSUBIR"
    rampa_arriba = False

    def al_accion(self):
        self.rampa_arriba = not self.rampa_arriba
        self.accion.activo = self.rampa_arriba
        self.accion.set_text("RAMPA\nBAJAR" if self.rampa_arriba else "RAMPA\nSUBIR")
        self.app.ble.send(P.RAMPA_SUBIR if self.rampa_arriba else P.RAMPA_BAJAR)


class Futbol(Juego):
    MODO, COLOR, FONDO, TXT_ACCION = "FUT", VERDE, "#08150f", "PATEAR"

    def al_accion(self):
        self.app.ble.send(P.PATEAR)


# ------------------------------------------------------------------ app
class RobotApp(App):
    estado = StringProperty("desconectado")

    def build(self):
        try:
            return self._construir()
        except Exception:
            import traceback
            return Label(text=traceback.format_exc(), font_size=sp(11),
                         halign="left", valign="top")

    def _construir(self):
        if platform == "android":
            from android.permissions import request_permissions
            request_permissions([
                "android.permission.BLUETOOTH_SCAN",
                "android.permission.BLUETOOTH_CONNECT",
                "android.permission.ACCESS_FINE_LOCATION",
            ])
        from ble_client import RobotBLE
        self.ble = RobotBLE(on_state=lambda s: setattr(self, "estado", s))
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(Inicio(name="inicio"))
        sm.add_widget(Escaneo(name="escaneo"))
        sm.add_widget(Sumo(name="sumo"))
        sm.add_widget(Futbol(name="futbol"))
        return sm


if __name__ == "__main__":
    asyncio.run(RobotApp().async_run(async_lib="asyncio"))
