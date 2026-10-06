import random

TAM = 10

NAVES = [
    ("Submarino", 5), ("Acorazado", 4), ("Crucero 1", 3),
    ("Crucero 2", 3), ("Destructor 1", 2), ("Destructor 2", 2),
    ("Destructor 3", 2),
]

SIMBOLOS = {0: '~', 1: 'N', 'X': 'X', 'O': 'O', '#': '#'}
# Creación e impresión
def crear_tablero():
    return [[0 for _ in range(TAM)] for _ in range(TAM)]


def _fila_texto(tablero, i):
    return f"{i} " + " ".join(SIMBOLOS[x] for x in tablero[i])


def imprimir_tablero(tablero, titulo=None):
    if titulo:
        print(titulo)
    print("  0 1 2 3 4 5 6 7 8 9")
    for i in range(TAM):
        print(_fila_texto(tablero, i))


def imprimir_dos(izq, der, titulo_izq, titulo_der): #dos tableros
    ancho = 24
    print(titulo_izq.ljust(ancho) + titulo_der)
    cab = "  0 1 2 3 4 5 6 7 8 9"
    print(cab.ljust(ancho) + cab)
    for i in range(TAM):
        print(_fila_texto(izq, i).ljust(ancho) + _fila_texto(der, i))
    print("(~ agua, N nave, X impacto, O fallo, # hundida)")
# Colocación de naves
def validar_espacio(tablero, fila, col, longitud, orientacion):
    if not (0 <= fila < TAM and 0 <= col < TAM):
        return False
    if orientacion == 'H':
        if col + longitud > TAM:
            return False
        return all(tablero[fila][c] == 0 for c in range(col, col + longitud))
    if orientacion == 'V':
        if fila + longitud > TAM:
            return False
        return all(tablero[f][col] == 0 for f in range(fila, fila + longitud))
    return False


def colocar_nave(tablero, fila, col, longitud, orientacion):
    if orientacion == 'H':
        celdas = [(fila, c) for c in range(col, col + longitud)]
    else:
        celdas = [(f, col) for f in range(fila, fila + longitud)]
    for f, c in celdas:
        tablero[f][c] = 1
    return celdas


def nueva_nave(nombre, celdas):
    return {"nombre": nombre, "celdas": celdas, "hundida": False}


def colocar_flota_aleatoria(tablero):
    flota = []
    for nombre, longitud in NAVES:
        while True:
            fila = random.randint(0, TAM - 1)
            col = random.randint(0, TAM - 1)
            orientacion = random.choice(['H', 'V'])
            if validar_espacio(tablero, fila, col, longitud, orientacion):
                celdas = colocar_nave(tablero, fila, col, longitud, orientacion)
                flota.append(nueva_nave(nombre, celdas))
                break
    return flota
# Disparos
def marcar_hundida(tablero, celdas):
    for f, c in celdas:
        tablero[f][c] = '#'


def procesar_disparo(tablero, flota, f, c):
    if not (0 <= f < TAM and 0 <= c < TAM):
        return "INVALIDO", None
    if tablero[f][c] in ('X', 'O', '#'):
        return "REPETIDO", None
    if tablero[f][c] == 0:
        tablero[f][c] = 'O'
        return "AGUA", None

    tablero[f][c] = 'X'
    for nave in flota:
        if (f, c) in nave["celdas"]:
            if all(tablero[a][b] == 'X' for a, b in nave["celdas"]):
                nave["hundida"] = True
                marcar_hundida(tablero, nave["celdas"])
                return "HUNDIDO", nave
            break
    return "IMPACTO", None


def flota_hundida(flota):
    return all(nave["hundida"] for nave in flota)


def elegir_tiro_pc(tablero_tiros):
    libres = [(f, c) for f in range(TAM) for c in range(TAM)
              if tablero_tiros[f][c] == 0]
    return random.choice(libres)

def celdas_a_texto(celdas):
    return ";".join(f"{f},{c}" for f, c in celdas)


def texto_a_celdas(texto):
    celdas = []
    for par in texto.split(";"):
        f, c = (int(x) for x in par.split(","))
        if not (0 <= f < TAM and 0 <= c < TAM):
            raise ValueError("casilla fuera del tablero")
        celdas.append((f, c))
    return celdas


def mensaje_resultado(resultado, nave=None):
    if resultado == "HUNDIDO":
        return f"RESULTADO:HUNDIDO:{nave['nombre']}:{celdas_a_texto(nave['celdas'])}"
    return f"RESULTADO:{resultado}"


def parsear_resultado(linea):
    partes = linea.split(":", 3)
    if len(partes) < 2 or partes[0] != "RESULTADO":
        raise ValueError(f"mensaje inesperado: {linea!r}")
    tipo = partes[1]
    if tipo == "HUNDIDO":
        if len(partes) < 4:
            raise ValueError("RESULTADO:HUNDIDO incompleto")
        return tipo, partes[2], texto_a_celdas(partes[3])
    if tipo not in ("AGUA", "IMPACTO", "REPETIDO", "INVALIDO"):
        raise ValueError(f"resultado desconocido: {tipo!r}")
    return tipo, None, []


def parsear_ataque(linea):
    try:
        prefijo, coords = linea.split(":", 1)
        if prefijo != "ATAQUE":
            return None
        f, c = (int(x) for x in coords.split(","))
        return f, c
    except ValueError:
        return None
