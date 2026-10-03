import socket

HOST = '127.0.0.1'
PUERTO = 65432

def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind((HOST, PUERTO))
        servidor.listen()
        print(f"Servidor a la escucha en {HOST}:{PUERTO}...")
        
        conexion, direccion = servidor.accept()
        
        with conexion:
            print(f"Cliente conectado desde {direccion}")            
            datos = conexion.recv(1024).decode('utf-8')
            if datos.startswith("USUARIO:"):
                nombre = datos.split(":")[1]
                print(f"Iniciando partida contra: {nombre}")               
                conexion.sendall("COMANDOS:INICIO".encode('utf-8'))

if __name__ == "__main__":
    iniciar_servidor()