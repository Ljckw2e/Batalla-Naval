import random
import socket

from tablero import (
    NAVES, crear_tablero, colocar_flota_aleatoria, procesar_disparo,
    flota_hundida, marcar_hundida, elegir_tiro_pc, imprimir_dos,
    mensaje_resultado, parsear_resultado, parsear_ataque,
)

HOST = '127.0.0.1'
PUERTO = 65432

MAX_TIROS = 3             # tiros consecutivos permitidos por turno
TOTAL_NAVES = len(NAVES)  # 7 naves = 21 casillas


class ErrorProtocolo(Exception):
    pass


class Partida:
    """Estado de una partida. procesar() recibe el mensaje del cliente y
    devuelve (respuesta_unica_para_el_cliente, partida_terminada)."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.tablero_pc = crear_tablero()          # naves de la PC
        self.tablero_tiros_pc = crear_tablero()    # tiros de la PC al usuario
        self.flota_pc = colocar_flota_aleatoria(self.tablero_pc)
        self.hundidas_usuario = 0
        self.turno = random.choice(['USUARIO', 'PC'])
        self.tiros = 0                 # aciertos seguidos en el turno actual
        self.ultimo_tiro_pc = None
        self._mostrar_tableros()

    def _mostrar_tableros(self):
        print()
        imprimir_dos(self.tablero_pc, self.tablero_tiros_pc,
                     "TABLERO DE LA PC", "TIROS DE LA PC")

    def _nuevo_tiro_pc(self):
        f, c = elegir_tiro_pc(self.tablero_tiros_pc)
        self.ultimo_tiro_pc = (f, c)
        return f"ATAQUE_PC:{f},{c}"

    def mensaje_inicial(self):
        print(f"El primer turno es para: {self.turno}")
        if self.turno == 'USUARIO':
            return "TURNO:USUARIO"
        return f"TURNO:PC|{self._nuevo_tiro_pc()}"

    def procesar(self, mensaje):
        if self.turno == 'USUARIO':
            return self._ataque_del_usuario(mensaje)
        return self._resultado_del_tiro_pc(mensaje)

    def _ataque_del_usuario(self, mensaje):
        ataque = parsear_ataque(mensaje)
        if ataque is None:
            return "RESULTADO:INVALIDO|TURNO:USUARIO", False

        f, c = ataque
        resultado, nave = procesar_disparo(self.tablero_pc, self.flota_pc, f, c)
        texto = mensaje_resultado(resultado, nave)

        if resultado in ("INVALIDO", "REPETIDO"):
            return f"{texto}|TURNO:USUARIO", False     # no cuenta como tiro

        detalle = f"hundió el {nave['nombre']}" if nave else resultado.lower()
        print(f"El usuario disparó a ({f},{c}): {detalle}")
        self._mostrar_tableros()

        if flota_hundida(self.flota_pc):
            print(f"\n{self.nombre} hundió toda la flota de la PC. Gana {self.nombre}.")
            return f"{texto}|FIN:VICTORIA", True

        if resultado != "AGUA":
            self.tiros += 1
        if resultado == "AGUA" or self.tiros >= MAX_TIROS:
            self.turno, self.tiros = 'PC', 0
            return f"{texto}|TURNO:PC|{self._nuevo_tiro_pc()}", False
        return f"{texto}|TURNO:USUARIO", False         # sigue tirando

    # turno de la PC 
    def _resultado_del_tiro_pc(self, mensaje):
        try:
            tipo, nombre_nave, celdas = parsear_resultado(mensaje)
        except ValueError as e:
            raise ErrorProtocolo(str(e))
        f, c = self.ultimo_tiro_pc

        if tipo == "AGUA":
            self.tablero_tiros_pc[f][c] = 'O'
        elif tipo == "IMPACTO":
            self.tablero_tiros_pc[f][c] = 'X'
            self.tiros += 1
        elif tipo == "HUNDIDO":
            marcar_hundida(self.tablero_tiros_pc, celdas)
            self.hundidas_usuario += 1
            self.tiros += 1
        else:
            raise ErrorProtocolo(f"resultado no esperado del cliente: {tipo}")

        detalle = f"hundió el {nombre_nave}" if tipo == "HUNDIDO" else tipo.lower()
        print(f"La PC disparó a ({f},{c}): {detalle}")
        self._mostrar_tableros()

        if self.hundidas_usuario >= TOTAL_NAVES:
            print("\nLa PC hundió toda la flota del usuario. Gana la PC.")
            return "FIN:DERROTA", True

        if tipo == "AGUA" or self.tiros >= MAX_TIROS:
            self.turno, self.tiros = 'USUARIO', 0
            return "TURNO:USUARIO", False
        return self._nuevo_tiro_pc(), False            # la PC sigue tirando


def recibir(conexion):
    datos = conexion.recv(1024)
    if not datos:
        raise ConnectionError("El cliente cerró la conexión.")
    return datos.decode("utf-8").strip()


def enviar(conexion, mensaje):
    conexion.sendall(mensaje.encode("utf-8"))


def jugar(conexion):
    mensaje = recibir(conexion)
    if not mensaje.startswith("USUARIO:"):
        raise ErrorProtocolo("Se esperaba USUARIO:<nombre>")
    nombre = mensaje.split(":", 1)[1].strip() or "Jugador"
    print(f"Iniciando partida contra: {nombre}")
    enviar(conexion, "COMANDOS:INICIO")

    if recibir(conexion) != "ESTADO:LISTO":
        raise ErrorProtocolo("Se esperaba ESTADO:LISTO")
    print(f"{nombre} está listo. Acomodando flota de la PC...")

    partida = Partida(nombre)
    enviar(conexion, partida.mensaje_inicial())

    terminada = False
    while not terminada:
        respuesta, terminada = partida.procesar(recibir(conexion))
        enviar(conexion, respuesta)


def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PUERTO))
        servidor.listen(1)
        print(f"Servidor a la escucha en {HOST}:{PUERTO}...")

        conexion, direccion = servidor.accept()
        # Solo se atiende a un cliente: se deja de escuchar, así cualquier
        # otro intento de conexión es rechazado.
        servidor.close()

        with conexion:
            print(f"Cliente conectado desde {direccion}")
            try:
                jugar(conexion)
            except ErrorProtocolo as e:
                print(f"[ERROR DE PROTOCOLO] {e}")
            except (ConnectionError, OSError):
                print("Se perdió la conexión con el cliente.")


if __name__ == "__main__":
    iniciar_servidor()
