# cliente.py
import socket
from tablero import crear_tablero, imprimir_tablero, validar_espacio, colocar_nave

HOST = '127.0.0.1'
PUERTO = 65432

def iniciar_cliente():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
        print(f"Conectando al servidor {HOST}:{PUERTO}...")
        cliente.connect((HOST, PUERTO))
        
        mi_tablero = crear_tablero()
        tablero_tiros = crear_tablero()
        
        nombre = input("Ingresa tu nombre de jugador: ")
        mensaje = f"USUARIO:{nombre}"
        cliente.sendall(mensaje.encode('utf-8'))
        
        respuesta = cliente.recv(1024).decode('utf-8')
        if respuesta == "COMANDOS:INICIO":
            print("\nTu tablero de tiros:")
            imprimir_tablero(tablero_tiros)
            flota = {
                "Submarino": 5, "Acorazado": 4, "Crucero 1": 3,
                "Crucero 2": 3, "Destructor 1": 2, "Destructor 2": 2,
                "Destructor 3": 2
            }
            print("\nDESPLIEGUE")
            for nombre, longitud in flota.items():
                colocada = False
                while not colocada:
                    imprimir_tablero(mi_tablero)
                    print(f"\nTurno de colocar: {nombre} (Longitud: {longitud})")
                    
                    try:
                        fila = int(input("Ingresa la fila (0-9): "))
                        col = int(input("Ingresa la columna (0-9): "))
                        orientacion = input("Orientación (H para horizontal, V para vertical): ").upper()
                        
                        if validar_espacio(mi_tablero, fila, col, longitud, orientacion):
                            colocar_nave(mi_tablero, fila, col, longitud, orientacion)
                            colocada = True
                            print(f"{nombre} colocado con éxito")
                        else:
                            print("\n[ERROR] Posición inválida. La nave se sale del tablero o choca con otra. Intenta de nuevo.")
                    except ValueError:
                        print("\n[ERROR] Ingresa números válidos para fila y columna.")
            
            print("\nToda tu flota está en posición")
            imprimir_tablero(mi_tablero)
        
            cliente.sendall("ESTADO:LISTO".encode('utf-8'))

            respuesta_turno = cliente.recv(1024).decode('utf-8')
            if respuesta_turno.startswith("TURNO:"):
                quien_empieza = respuesta_turno.split(":")[1]
                print(f"\n El servidor ha decidido que el primer turno es para: {quien_empieza}")

                turno = quien_empieza
                vidas_usuario = 21
                vidas_pc = 21

                print("\n INICIA EL COMBATE")
                while vidas_usuario > 0 and vidas_pc > 0:
                    if turno == 'USUARIO':
                        print("\n[TU TURNO]")
                        tiros_seguidos = 0
                        while tiros_seguidos < 3 and vidas_pc > 0:
                            imprimir_tablero(tablero_tiros)
                            print(f"Tiro: {tiros_seguidos + 1} de 3")

                            f = int(input("Fila (0-9): "))
                            c = int(input("Columna (0-9): "))

                            cliente.sendall(f"ATAQUE:{f}, {c}".encode('utf-8'))

                            respuesta = cliente.recv(1024).decode('utf-8')
                            if respuesta == "RESULTADO:IMPACTO":
                                print("\n¡IMPACTO! Tienes otro tiro.")
                                tablero_tiros[f][c] = 'X'
                                vidas_pc -= 1
                                tiros_seguidos += 1
                            elif respuesta == "RESULTADO:AGUA":
                                print("\n¡AGUA! Fin de tu turno.")
                                tablero_tiros[f][c] = 'O'
                                break
                        turno = 'PC'
                        
                    else:
                        print("\n[TURNO DE LA PC]")
                        tiros_seguidos = 0
                        while tiros_seguidos < 3 and vidas_usuario > 0:
                            print("Esperando el tiro de la PC...")
                            msg = cliente.recv(1024).decode('utf-8')
                            
                            if msg.startswith("ATAQUE_PC:"):
                                f, c = map(int, msg.split(":")[1].split(","))
                                print(f"La PC disparó en: Fila {f}, Columna {c}")
                                
                                if mi_tablero[f][c] == 1:
                                    print("¡La PC le dio a una de tus naves!")
                                    mi_tablero[f][c] = 'X'
                                    vidas_usuario -= 1
                                    cliente.sendall("RESULTADO:IMPACTO".encode('utf-8'))
                                    tiros_seguidos += 1
                                else:
                                    print("La PC disparó al agua.")
                                    mi_tablero[f][c] = 'O'
                                    cliente.sendall("RESULTADO:AGUA".encode('utf-8'))
                                    break
                        turno = 'USUARIO'
                
                if vidas_usuario == 0:
                    print("\n DERROTA: La PC hundió toda tu flota")
                else:
                    print("\nVICTORIA: Hundiste toda la flota de la PC")

if __name__ == "__main__":
    iniciar_cliente()