import socket
import threading
import customtkinter as ctk

from tablero import crear_tablero, validar_espacio, colocar_nave

HOST = '127.0.0.1'
PUERTO = 65432

# Tema visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ClienteBatallaNaval:
    def __init__(self, ventana):
        self.mi_tablero = crear_tablero()
                        
        self.inventario = [
                ("Submarino", 5), ("Acorazado", 4), ("Crucero 1", 3),
                ("Crucero 2", 3), ("Destructor 1", 2), ("Destructor 2", 2),
                ("Destructor 3", 2)
        ]
        self.nave_actual = 0
        self.orientacion_var = ctk.StringVar(value="H")
        
        self.mi_turno = False
         
        self.ventana = ventana
        self.ventana.title("Batalla Naval - Interfaz Gráfica")
        self.ventana.geometry("900x600")
        
        self.socket_cliente = None
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
        self.botones_flota = [[None]*10 for _ in range(10)]
        
        self.frame_radar = ctk.CTkFrame(self.frame_tableros)
        self.frame_radar.pack(side="right", padx=20)
        ctk.CTkLabel(self.frame_radar, text="Radar de Ataque", font=("Roboto", 14)).pack()
        self.botones_radar = [[None]*10 for _ in range(10)]

    def iniciar_conexion(self):
        nombre = self.entry_nombre.get()
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
            
            self.socket_cliente.sendall(f"USUARIO:{nombre}".encode('utf-8'))
            respuesta = self.socket_cliente.recv(1024).decode('utf-8')
            if respuesta == "COMANDOS:INICIO":
                self.ventana.after(0, lambda: self.lbl_estado.configure(text="¡Conectado! Fase de despliegue."))
                self.ventana.after(0, self.dibujar_tableros)
                
        except Exception as e:
            self.ventana.after(0, lambda: self.lbl_estado.configure(text="Error de conexión."))
            self.ventana.after(0, lambda: self.btn_conectar.configure(state="normal"))

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
        
        for f in range(10):
            for c in range(10):
                btn_flota = ctk.CTkButton(frame_grid_flota, text="", width=35, height=35, corner_radius=2, 
                                          fg_color="#3b4252",
                                          command=lambda fila=f, col=c: self.intentar_colocar(fila, col))
                btn_flota.grid(row=f, column=c, padx=1, pady=1)
                self.botones_flota[f][c] = btn_flota
                
                btn_radar = ctk.CTkButton(frame_grid_radar, text="", width=35, height=35, corner_radius=2, 
                                          fg_color="#5e81ac", state="disabled", command = lambda fila = f, col = c: self.enviar_ataque(fila,col))
                btn_radar.grid(row=f, column=c, padx=1, pady=1)
                self.botones_radar[f][c] = btn_radar

    def intentar_colocar(self, f, c):
            if self.nave_actual >= len(self.inventario):
                return
            
            nombre, longitud = self.inventario[self.nave_actual]
            orientacion = self.orientacion_var.get()
        
            if validar_espacio(self.mi_tablero, f, c, longitud, orientacion):
                colocar_nave(self.mi_tablero, f, c, longitud, orientacion)
                
                if orientacion == 'H':
                    for col in range(c, c + longitud):
                        self.botones_flota[f][col].configure(fg_color="#a3be8c", state="disabled")
                else:
                    for fila in range(f, f + longitud):
                        self.botones_flota[fila][c].configure(fg_color="#a3be8c", state="disabled")
                
                self.nave_actual += 1
                
                if self.nave_actual < len(self.inventario):
                    sig_nombre, sig_long = self.inventario[self.nave_actual]
                    self.lbl_instruccion.configure(text=f"Coloca: {sig_nombre} ({sig_long} casillas)")
                else:
                    self.lbl_instruccion.configure(text="¡Flota lista! Esperando al servidor...")
                    self.switch_orientacion.configure(state="disabled")
                    threading.Thread(target=self.enviar_listo, daemon=True).start()

    def enviar_listo(self):
        self.socket_cliente.sendall("ESTADO:LISTO".encode('utf-8'))
        respuesta = self.socket_cliente.recv(1024).decode('utf-8')
        if respuesta.startswith("TURNO:"):
            quien = respuesta.split(":")[1]
            self.mi_turno = (quien == "USUARIO")

            texto = "Tu turno, ataca en el radar." if self.mi_turno else "Turno de la PC. Esperando ataque..."
            self.ventana.after(0, lambda: self.lbl_estado.configure(text=texto))
            if self.mi_turno:
                self.ventana.after(0, self.habilitar_radar)

            threading.Thread(target=self.escuchar_servidor, daemon=True).start()
            
    def habilitar_radar(self):
        for f in range(10):
            for c in range(10):
                if self.botones_radar[f][c].cget("text") == "":
                    self.botones_radar[f][c].configure(state="normal")                 

    def enviar_ataque(self, f, c):
        if not self.mi_turno: return
        for fila in self.botones_radar:
            for btn in fila:
                btn.configure(state="disabled")

        self.ultimo_ataque = (f, c)
        self.socket_cliente.sendall(f"ATAQUE:{f}{c}".encode('utf-8'))

    def escuchar_servidor(self):
        while True:
            try:
                mensaje = self.socket_cliente.recv(1024).decode('utf-8')
                if not mensaje:
                    break
                if mensaje == "RESULTADO:IMPACTO":
                    f, c = self.ultimo_ataque
                    self.ventana.after(0, lambda: self.botones_radar[f][c].configure(fg_color="#bf616a", text="X"))
                    self.ventana.after(0, self.habilitar_radar)
                elif mensaje == "RESULTADO:AGUA":
                    f, c = self.ultimo_ataque
                    self.ventana.after(0, lambda: self.botones_radar[f][c].configure(fg_color="#4c566a", texto="0"))
                    self.mi_turno = False
                    self.ventana.after(0, lambda: self.lbl_estado.configure(text="Fallaste. Turno de la PC..."))
                elif mensaje.startswith("ATAQUE_PC:"):
                    f, c = map(int, mensaje.split(":")[1].split(","))
                
                    if self.mi_tablero[f][c] == 1:
                        self.mi_tablero[f][c] = 'X'
                        self.socket_cliente.sendall("RESULTADO:IMPACTO".encode('utf-8'))
                        self.ventana.after(0, lambda: self.botones_flota[f][c].configure(fg_color="#bf616a", text="X"))
                        self.ventana.after(0, lambda:self.lbl_estado.configure(text="La PC acertó, sigue tirando..."))
                    else:
                        self.mi_tablero[f][c] = 'O'
                        self.socket_cliente.sendall("RESULTADO:AGUA".encode('utf-8'))
                        self.ventana.after(0, lambda: self.botones_flota[f][c].configure(fg_color="#81a1c1", text="O"))
                        self.mi_turno = True
                        self.ventana.after(0, lambda: self.lbl_estado.configure(text="La PC falló. ¡ES TU TURNO!"))
                        self.ventana.after(0, self.habilitar_radar)
            except Exception as e:
                print ("Conexión perdida:", e)
                break

if __name__ == "__main__":
    ventana_principal = ctk.CTk()
    app = ClienteBatallaNaval(ventana_principal)
    ventana_principal.mainloop()