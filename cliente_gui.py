import socket
import threading
import time
import customtkinter as ctk

from tablero import (
    NAVES, TAM, crear_tablero, validar_espacio, colocar_nave, nueva_nave,
    procesar_disparo, marcar_hundida, mensaje_resultado, parsear_resultado,
)

HOST = '127.0.0.1'
PUERTO = 65432
MAX_TIROS = 3
PAUSA_PC = 0.8     # pausa visual antes de mostrar el tiro de la PC

# Colores
C_CASILLA = "#3b4252"
C_NAVE = "#a3be8c"
C_RADAR = "#5e81ac"
C_IMPACTO = "#bf616a"
C_AGUA_RADAR = "#4c566a"
C_AGUA_PROPIA = "#81a1c1"
C_HUNDIDA = "#b48ead"

# Tema visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ClienteBatallaNaval:
    def __init__(self, ventana):
        self.mi_tablero = crear_tablero()        # mis naves
        self.tablero_tiros = crear_tablero()     # mis tiros al rival (radar)
        self.flota = []
        self.inventario = list(NAVES)
        self.nave_actual = 0
        self.orientacion_var = ctk.StringVar(value="H")

        self.mi_turno = False
        self.racha_tiros = 0
        self.ultimo_ataque = None
        self.texto_resultado = ""
        self.juego_terminado = False
        self.socket_cliente = None

        self.ventana = ventana
        self.ventana.title("Batalla Naval - Interfaz Gráfica")
        self.ventana.geometry("900x600")

        self.lbl_estado = ctk.CTkLabel(ventana, text="Esperando conexión...", font=("Roboto", 16, "bold"))
        self.lbl_estado.pack(pady=10)

        self.frame_conexion = ctk.CTkFrame(ventana)
        self.frame_conexion.pack(pady=10)

        self.entry_nombre = ctk.CTkEntry(self.frame_conexion, placeholder_text="Tu nombre", width=200)
        self.entry_nombre.pack(side="left", padx=10, pady=10)

        self.btn_conectar = ctk.CTkButton(self.frame_conexion, text="Conectar al Servidor", command=self.iniciar_conexion)
        self.btn_conectar.pack(side="left", padx=10, pady=10)

        self.frame_tableros = ctk.CTkFrame(ventana, fg_color="transparent")

        self.frame_mi_flota = ctk.CTkFrame(self.frame_tableros)
        self.frame_mi_flota.pack(side="left", padx=20)
        ctk.CTkLabel(self.frame_mi_flota, text="Mi Flota", font=("Roboto", 14)).pack()
        self.botones_flota = [[None] * TAM for _ in range(TAM)]

        self.frame_radar = ctk.CTkFrame(self.frame_tableros)
        self.frame_radar.pack(side="right", padx=20)
        ctk.CTkLabel(self.frame_radar, text="Radar de Ataque", font=("Roboto", 14)).pack()
        self.botones_radar = [[None] * TAM for _ in range(TAM)]

    def ui(self, funcion):
        self.ventana.after(0, funcion)

    def decir(self, texto):
        """Muestra un texto de estado y lo guarda para completarlo con el turno."""
        self.texto_resultado = texto
        self.ui(lambda: self.lbl_estado.configure(text=texto))

    def pintar_radar(self, f, c, simbolo):
        estilos = {'X': (C_IMPACTO, "X"), 'O': (C_AGUA_RADAR, "O"), '#': (C_HUNDIDA, "■")}
        color, texto = estilos[simbolo]
        self.ui(lambda: self.botones_radar[f][c].configure(fg_color=color, text=texto, state="disabled"))

    def pintar_flota(self, f, c, simbolo):
        estilos = {'X': (C_IMPACTO, "X"), 'O': (C_AGUA_PROPIA, "O"), '#': (C_HUNDIDA, "■")}
        color, texto = estilos[simbolo]
        self.ui(lambda: self.botones_flota[f][c].configure(fg_color=color, text=texto))

    def habilitar_radar(self):
        if self.juego_terminado or not self.mi_turno:
            return
        for f in range(TAM):
            for c in range(TAM):
                if self.tablero_tiros[f][c] == 0:
                    self.botones_radar[f][c].configure(state="normal")

    def deshabilitar_radar(self):
        for fila in self.botones_radar:
            for btn in fila:
                btn.configure(state="disabled")

    # ------------------------------------------------------------------
    # Conexión y despliegue
    # ------------------------------------------------------------------
    def iniciar_conexion(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            return

        self.btn_conectar.configure(state="disabled")
        self.lbl_estado.configure(text="Conectando...")

        hilo_red = threading.Thread(target=self.proceso_red, args=(nombre,))
        hilo_red.daemon = True
        hilo_red.start()

    def proceso_red(self, nombre):
        try:
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((HOST, PUERTO))

            self.socket_cliente.sendall(f"USUARIO:{nombre}".encode("utf-8"))
            respuesta = self.socket_cliente.recv(1024).decode("utf-8").strip()
            if respuesta == "COMANDOS:INICIO":
                self.ui(lambda: self.lbl_estado.configure(text="¡Conectado! Fase de despliegue."))
                self.ui(self.dibujar_tableros)
        except Exception:
            self.ui(lambda: self.lbl_estado.configure(text="Error de conexión."))
            self.ui(lambda: self.btn_conectar.configure(state="normal"))

    def dibujar_tableros(self):
        self.frame_conexion.pack_forget()
        self.frame_tableros.pack(pady=10, fill="both", expand=True)

        self.frame_controles = ctk.CTkFrame(self.frame_mi_flota, fg_color="transparent")
        self.frame_controles.pack(pady=(0, 10))

        nombre, long = self.inventario[self.nave_actual]
        self.lbl_instruccion = ctk.CTkLabel(self.frame_controles, text=f"Coloca: {nombre} ({long} casillas)", font=("Roboto", 14, "bold"))
        self.lbl_instruccion.pack(side="left", padx=10)

        self.switch_orientacion = ctk.CTkSegmentedButton(self.frame_controles, values=["H", "V"], variable=self.orientacion_var)
        self.switch_orientacion.pack(side="left")

        frame_grid_flota = ctk.CTkFrame(self.frame_mi_flota)
        frame_grid_flota.pack()
        frame_grid_radar = ctk.CTkFrame(self.frame_radar)
        frame_grid_radar.pack()

        for f in range(TAM):
            for c in range(TAM):
                btn_flota = ctk.CTkButton(frame_grid_flota, text="", width=35, height=35, corner_radius=2,
                                          fg_color=C_CASILLA,
                                          command=lambda fila=f, col=c: self.intentar_colocar(fila, col))
                btn_flota.grid(row=f, column=c, padx=1, pady=1)
                self.botones_flota[f][c] = btn_flota

                btn_radar = ctk.CTkButton(frame_grid_radar, text="", width=35, height=35, corner_radius=2,
                                          fg_color=C_RADAR, state="disabled",
                                          command=lambda fila=f, col=c: self.enviar_ataque(fila, col))
                btn_radar.grid(row=f, column=c, padx=1, pady=1)
                self.botones_radar[f][c] = btn_radar

    def intentar_colocar(self, f, c):
        if self.nave_actual >= len(self.inventario):
            return

        nombre, longitud = self.inventario[self.nave_actual]
        orientacion = self.orientacion_var.get()

        if not validar_espacio(self.mi_tablero, f, c, longitud, orientacion):
            self.lbl_estado.configure(text="Posición inválida: se sale del tablero o choca con otra nave.")
            return

        celdas = colocar_nave(self.mi_tablero, f, c, longitud, orientacion)
        self.flota.append(nueva_nave(nombre, celdas))
        for fi, co in celdas:
            self.botones_flota[fi][co].configure(fg_color=C_NAVE, state="disabled")

        self.nave_actual += 1
        self.lbl_estado.configure(text="¡Conectado! Fase de despliegue.")

        if self.nave_actual < len(self.inventario):
            sig_nombre, sig_long = self.inventario[self.nave_actual]
            self.lbl_instruccion.configure(text=f"Coloca: {sig_nombre} ({sig_long} casillas)")
        else:
            self.lbl_instruccion.configure(text="¡Flota lista! Esperando al servidor...")
            self.switch_orientacion.configure(state="disabled")
            threading.Thread(target=self.proceso_partida, daemon=True).start()

    # Partida: un solo hilo escucha al servidor y reacciona a cada mensaje
    def proceso_partida(self):
        try:
            self.socket_cliente.sendall(b"ESTADO:LISTO")
            self.escuchar_servidor()
        except OSError:
            self.conexion_perdida()

    def escuchar_servidor(self):
        while True:
            try:
                datos = self.socket_cliente.recv(1024)
            except OSError:
                datos = b""
            if not datos:
                self.conexion_perdida()
                return

            # Un solo recv() = una respuesta del servidor, con 1 o más
            # segmentos separados por '|'
            for segmento in datos.decode("utf-8").strip().split("|"):
                if segmento.startswith("ATAQUE_PC:"):
                    time.sleep(PAUSA_PC)     # pausa visual antes del tiro de la PC
                if self.manejar_mensaje(segmento):
                    return

    def conexion_perdida(self):
        if not self.juego_terminado:
            self.ui(self.deshabilitar_radar)
            self.ui(lambda: self.lbl_estado.configure(text="Se perdió la conexión con el servidor."))

    def manejar_mensaje(self, msg):
        """Procesa un segmento del servidor. Devuelve True si terminó el juego."""
        if msg.startswith("RESULTADO:"):
            self.resultado_de_mi_ataque(msg)
        elif msg.startswith("ATAQUE_PC:"):
            self.recibir_ataque_pc(msg)
        elif msg == "TURNO:USUARIO":
            base, self.texto_resultado = self.texto_resultado, ""
            self.mi_turno = True
            if self.racha_tiros > 0:
                texto = f"{base} Tienes otro tiro ({self.racha_tiros}/{MAX_TIROS})."
            else:
                texto = f"{base} ¡Es tu turno! Ataca en el radar."
            self.ui(lambda: self.lbl_estado.configure(text=texto.strip()))
            self.ui(self.habilitar_radar)
        elif msg == "TURNO:PC":
            base, self.texto_resultado = self.texto_resultado, ""
            self.mi_turno = False
            self.racha_tiros = 0
            texto = f"{base} Turno de la PC. Esperando ataque..."
            self.ui(lambda: self.lbl_estado.configure(text=texto.strip()))
        elif msg.startswith("FIN:"):
            self.terminar(msg == "FIN:VICTORIA")
            return True
        return False

    def enviar_ataque(self, f, c):
        if not self.mi_turno or self.juego_terminado:
            return
        self.deshabilitar_radar()
        self.ultimo_ataque = (f, c)
        try:
            self.socket_cliente.sendall(f"ATAQUE:{f},{c}".encode("utf-8"))
        except OSError:
            self.conexion_perdida()

    def resultado_de_mi_ataque(self, msg):
        """Respuesta del servidor a un tiro mío: se refleja en el radar."""
        if self.ultimo_ataque is None:
            return
        f, c = self.ultimo_ataque
        try:
            tipo, nombre, celdas = parsear_resultado(msg)
        except ValueError:
            return

        if tipo == "AGUA":
            self.tablero_tiros[f][c] = 'O'
            self.pintar_radar(f, c, 'O')
            self.racha_tiros = 0
            self.decir("Agua.")
        elif tipo == "IMPACTO":
            self.tablero_tiros[f][c] = 'X'
            self.pintar_radar(f, c, 'X')
            self.racha_tiros += 1
            self.decir("¡IMPACTO!")
        elif tipo == "HUNDIDO":
            marcar_hundida(self.tablero_tiros, celdas)
            for fi, co in celdas:
                self.pintar_radar(fi, co, '#')
            self.racha_tiros += 1
            self.decir(f"¡Hundiste el {nombre} enemigo!")
        else:
            self.decir("Tiro no válido, elige otra casilla.")

    def recibir_ataque_pc(self, msg):
        """Tiro de la PC: lo valido contra mi tablero y respondo."""
        try:
            f, c = map(int, msg.split(":", 1)[1].split(","))
        except ValueError:
            return
        resultado, nave = procesar_disparo(self.mi_tablero, self.flota, f, c)
        if resultado in ("REPETIDO", "INVALIDO"):   # no debería ocurrir
            resultado, nave = "AGUA", None
        self.socket_cliente.sendall(mensaje_resultado(resultado, nave).encode("utf-8"))

        if resultado == "AGUA":
            self.pintar_flota(f, c, 'O')
            self.decir(f"La PC disparó a ({f},{c}): agua.")
        elif resultado == "IMPACTO":
            self.pintar_flota(f, c, 'X')
            self.decir(f"¡La PC acertó en ({f},{c})!")
        else:
            for fi, co in nave["celdas"]:
                self.pintar_flota(fi, co, '#')
            self.decir(f"¡La PC hundió tu {nave['nombre']}!")

    def terminar(self, victoria):
        self.juego_terminado = True
        self.mi_turno = False
        if victoria:
            texto, color = "¡GANASTE! Hundiste toda la flota de la PC.", "#a3be8c"
        else:
            texto, color = "DERROTA. La PC hundió toda tu flota.", "#bf616a"
        self.ui(self.deshabilitar_radar)
        self.ui(lambda: self.lbl_estado.configure(text=texto, text_color=color, font=("Roboto", 18, "bold")))
        try:
            self.socket_cliente.close()
        except OSError:
            pass


if __name__ == "__main__":
    ventana_principal = ctk.CTk()
    app = ClienteBatallaNaval(ventana_principal)
    ventana_principal.mainloop()
