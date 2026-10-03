import socket
import random
from tablero import crear_tablero, validar_espacio, colocar_nave, imprimir_tablero

HOST = '127.0.0.1'
PUERTO = 65432

def colocar_naves_pc(tablero):
    "Acomoda las 7 naves de la PC de forma aleatoria."
    flota = {
        "Submarino": 5, "Acorazado": 4, "Cruecero 1": 3,
        "Crucero 2": 3, "Destructor 1": 2, "Destructor 2": 2,
        "Destructor 3": 2 
    }

    for nombre, longitud in flota.items():
        colocada = False
        while not colocada:
            fila = random.randint(0,9)
            col = random.randint(0,9)
            orientacion = random.choice(['H', 'V'])

            if validar_espacio(tablero, fila, col, longitud, orientacion):
                colocar_nave(tablero, fila, col, longitud, orientacion)
                colocada = True

def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind((HOST, PUERTO))
        servidor.listen()
        print(f"Servidor a la escucha en {HOST}:{PUERTO}...")
        
        conexion, direccion = servidor.accept()
        
        with conexion:
            print(f"Cliente conectado desde {direccion}")      
            tablero_pc = crear_tablero()

            datos = conexion.recv(1024).decode('utf-8')
            if datos.startswith("USUARIO:"):
                nombre = datos.split(":")[1]
                print(f"Iniciando partida contra: {nombre}")
                conexion.sendall("COMANDOS:INICIO".encode('utf-8'))

                datos = conexion.recv(1024).decode('utf-8')
                if datos == "ESTADO:LISTO":
                    print(f"{nombre} está listo. Acomodando flota de la PC...")
                    colocar_naves_pc(tablero_pc)
                    print("Tablero oculto de la PC")
                    imprimir_tablero(tablero_pc)
                    turno = random.choice(['USUARIO', 'PC'])
                    print(f"El primer turno es para: {turno}")
                    conexion.sendall(f"TURNO:{turno}".encode('utf-8'))
                    vidas_usuario = 21
                    vidas_pc = 21

                    while vidas_usuario > 0 and vidas_pc > 0:
                        if turno == 'USUARIO':
                            tiro_seguidos = 0
                            while tiro_seguidos < 3 and vidas_pc > 0:
                                msg = conexion.recv(1024).decode('utf-8')
                                if msg.startswith("ATAQUE:"):
                                    f, c= map(int, msg.split(":")[1].split(","))

                                if tablero_pc[f][c] == 1:
                                    tablero_pc[f][c] = 'X'
                                    vidas_pc -= 1
                                    conexion.sendall("RESULTADO:IMPACTO".encode('utf-8'))
                                    tiro_seguidos += 1
                                else:
                                    tablero_pc[f][c] = '0'
                                    conexion.sendall("RESULTADO:AGUA".encode('utf-8'))
                                    break
                            turno = 'PC'
                        else:
                            tiro_seguidos = 0
                            while tiro_seguidos < 3 and vidas_usuario > 0:
                                f, c= random.randint(0,9), random.randint(0,9)
                                conexion.sendall(f"ATAQUE_PC:{f}{c}".encode('utf-8'))

                                respuesta = conexion.recv(1024).decode('utf-8')
                                if respuesta == "RESULTADO:IMPACTO":
                                    vidas_usuario -= 1
                                    tiro_seguidos += 1
                                elif respuesta == "RESULTADO:AGUA":
                                    break
                            turno = 'USUARIO'

if __name__ == "__main__":
    iniciar_servidor()