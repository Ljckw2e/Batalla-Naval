def crear_tablero():
    return [[0 for _ in range(10)] for _ in range(10)]

def imprimir_tablero(tablero):
    print("  0 1 2 3 4 5 6 7 8 9")
    for i, fila in enumerate(tablero):
        print(f"{i} {' '.join(str(casilla) for casilla in fila)}")

def validar_espacio(tablero, fila, col, longitud, orientacion):
    "Verifica si la nave cabe en el tablero sin chocar ni salirse."
    if orientacion == 'H':
        if col + longitud > 10: 
            return False
        for c in range(col, col + longitud):
            if tablero[fila][c] != 0: 
                return False
                
    elif orientacion == 'V':
        if fila + longitud > 10: 
            return False
        for f in range(fila, fila + longitud):
            if tablero[f][col] != 0: 
                return False
    else:
        return False
        
    return True

def colocar_nave(tablero, fila, col, longitud, orientacion):
    "Escribe los '1's en la matriz una vez que el espacio es válido."
    if orientacion == 'H':
        for c in range(col, col + longitud):
            tablero[fila][c] = 1
    elif orientacion == 'V':
        for f in range(fila, fila + longitud):
            tablero[f][col] = 1