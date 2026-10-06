import socket

from tablero import (
    NAVES, crear_tablero, imprimir_tablero, imprimir_dos, validar_espacio,
    colocar_nave, nueva_nave, procesar_disparo, marcar_hundida,
    mensaje_resultado, parsear_resultado,
)

HOST = '127.0.0.1'
PUERTO = 65432
MAX_TIROS = 3


def enviar(sock, mensaje):
    sock.sendall(mensaje.encode("utf-8"))


def recibir(sock):
    datos = sock.recv(1024)
    if not datos:
        raise ConnectionError("El servidor cerró la conexión.")
    return datos.decode("utf-8").strip().split("|")


def pedir_entero(mensaje, minimo=0, maximo=9):
    while True:
        try:
            valor = int(input(mensaje))
            if minimo <= valor <= maximo:
                return valor
        except ValueError:
            pass
        print(f"[ERROR] Ingresa un número entre {minimo} y {maximo}.")


def colocar_naves_usuario(mi_tablero):
    flota = []
    print("\nDESPLIEGUE")
    for nombre_nave, longitud in NAVES:
        colocada = False
        while not colocada:
            print()
            imprimir_tablero(mi_tablero, "TU FLOTA")
            print(f"\nTurno de colocar: {nombre_nave} (Longitud: {longitud})")
            fila = pedir_entero("Fila inicial (0-9): ")
            col = pedir_entero("Columna inicial (0-9): ")
            orientacion = input("Orientación (H para horizontal, V para vertical): ").strip().upper()

            if validar_espacio(mi_tablero, fila, col, longitud, orientacion):
                celdas = colocar_nave(mi_tablero, fila, col, longitud, orientacion)
                flota.append(nueva_nave(nombre_nave, celdas))
                colocada = True
                print(f"{nombre_nave} colocado con éxito")
            else:
                print("\n[ERROR] Posición inválida. La nave se sale del tablero, "
                      "choca con otra o la orientación no es H/V. Intenta de nuevo.")
    print("\nToda tu flota está en posición")
    imprimir_tablero(mi_tablero, "TU FLOTA")
    return flota


def pedir_tiro(sock, mi_tablero, tablero_tiros, racha):
    if racha == 0:
        print("\n[TU TURNO]")
    imprimir_dos(mi_tablero, tablero_tiros, "TU FLOTA", "TUS TIROS")
    print(f"Tiro {racha + 1} de {MAX_TIROS}")
    while True:
        f = pedir_entero("Fila del tiro (0-9): ")
        c = pedir_entero("Columna del tiro (0-9): ")
        if tablero_tiros[f][c] != 0:
            print("[ERROR] Ya disparaste a esa casilla. Elige otra.")
            continue
        break
    enviar(sock, f"ATAQUE:{f},{c}")
    return (f, c)


def resultado_de_mi_tiro(segmento, tiro, tablero_tiros, racha):
    f, c = tiro
    tipo, nombre_nave, celdas = parsear_resultado(segmento)
    if tipo == "AGUA":
        tablero_tiros[f][c] = 'O'
        print("\n¡AGUA!")
    elif tipo == "IMPACTO":
        tablero_tiros[f][c] = 'X'
        print("\n¡IMPACTO!")
        racha += 1
    elif tipo == "HUNDIDO":
        marcar_hundida(tablero_tiros, celdas)
        print(f"\n¡IMPACTO! ¡Hundiste el {nombre_nave} enemigo!")
        racha += 1
    else:
        print("\n[ERROR] El servidor rechazó el tiro. Intenta de nuevo.")
    return racha


def recibir_ataque_pc(sock, segmento, mi_tablero, flota):
    f, c = map(int, segmento.split(":", 1)[1].split(","))
    print(f"\nLa PC disparó en: Fila {f}, Columna {c}")
    resultado, nave = procesar_disparo(mi_tablero, flota, f, c)
    if resultado in ("REPETIDO", "INVALIDO"):   # no debería ocurrir
        resultado, nave = "AGUA", None
    enviar(sock, mensaje_resultado(resultado, nave))

    if resultado == "AGUA":
        print("La PC disparó al agua.")
    elif resultado == "IMPACTO":
        print("La PC le dio a una de tus naves")
    else:
        print(f"¡La PC hundió tu {nave['nombre']}!")


def combate(sock, mi_tablero, tablero_tiros, flota, segmentos):
    racha = 0
    tiro = None
    while True:
        tirar_ahora = False
        for seg in segmentos:
            if seg.startswith("RESULTADO:"):
                racha = resultado_de_mi_tiro(seg, tiro, tablero_tiros, racha)
            elif seg == "TURNO:USUARIO":
                tirar_ahora = True
                if racha > 0:
                    print("¡Tienes otro tiro!")
            elif seg == "TURNO:PC":
                racha = 0
                print("\n[TURNO DE LA PC]")
            elif seg.startswith("ATAQUE_PC:"):
                recibir_ataque_pc(sock, seg, mi_tablero, flota)
            elif seg.startswith("FIN:"):
                return seg
        if tirar_ahora:
            tiro = pedir_tiro(sock, mi_tablero, tablero_tiros, racha)
        segmentos = recibir(sock)


def iniciar_cliente():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(f"Conectando al servidor {HOST}:{PUERTO}...")
        try:
            sock.connect((HOST, PUERTO))
        except OSError:
            print("[ERROR] No se pudo conectar. ¿Está corriendo servidor.py?")
            return None

        mi_tablero = crear_tablero()       # mis naves
        tablero_tiros = crear_tablero()    # mis tiros al rival

        nombre = ""
        while not nombre.strip():
            nombre = input("Ingresa tu nombre de jugador: ")

        try:
            enviar(sock, f"USUARIO:{nombre.strip()}")
            if recibir(sock)[0] != "COMANDOS:INICIO":
                print("[ERROR] El servidor no respondió con el inicio de juego.")
                return None

            flota = colocar_naves_usuario(mi_tablero)
            enviar(sock, "ESTADO:LISTO")

            segmentos = recibir(sock)
            if not segmentos[0].startswith("TURNO:"):
                print("[ERROR] Se esperaba el mensaje de turno.")
                return None
            print(f"\nEl servidor ha decidido que el primer turno es para: "
                  f"{segmentos[0].split(':', 1)[1]}")
            print("\nINICIA EL COMBATE")

            fin = combate(sock, mi_tablero, tablero_tiros, flota, segmentos)
        except ConnectionError:
            print("\n[ERROR] Se perdió la conexión con el servidor.")
            return None
        except ValueError as e:
            print(f"\n[ERROR] Mensaje inesperado del servidor: {e}")
            return None

        if fin == "FIN:VICTORIA":
            print("\nVICTORIA: Hundiste toda la flota de la PC")
        else:
            print("\nDERROTA: La PC hundió toda tu flota")
        return fin


if __name__ == "__main__":
    iniciar_cliente()
