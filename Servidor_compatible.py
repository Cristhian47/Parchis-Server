import socket
import threading
import json
import time

# Datos del servidor
HOST = 'localhost'  # El host del servidor
PORT = 8001        # El puerto del servidor

# Conectarse al servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORT))
servidor.listen(10)
print(f"Servidor esperando conexiones en {HOST}:{PORT}...")

# Lista de hilos para los clientes
hilos_clientes = []

# Diccionario para manejar los colores disponibles
colores_disponibles = {"Yellow": True , "Blue": True, "Green": True, "Red": True}

# Variable para el color del turno actual
turno_actual = None

# Lista para el orden de los colores de una ronda
orden_turnos = []

# Parametro de parada para el hilo de recibir clientes
iniciar_partida = False

# Diccionario para el valor de los dados de la ultima jugada (1-6,1-6)
ultimos_dados = {"D1" : None, "D2" : None}

# Lista para el registro de los dados de una ronda
registro_dados = {}

# Clase para manejar a los clientes
class Cliente(threading.Thread):
    def __init__(self, connection, address):
        super(Cliente, self).__init__()
        self.connection = connection
        self.ip, self.puerto = address
        self.nombre = None
        self.color = None
        self.aprobacion = False
        self.f1 = "Carcel"
        self.f2 = "Carcel"
        self.f3 = "Carcel"
        self.f4 = "Carcel"
        self.cont_f1 = 0
        self.cont_f2 = 0
        self.cont_f3 = 0
        self.cont_f4 = 0

    # Que es lo  que viene en el mensaje
    def procesar_informacion(self, msg):
        informacion = json.loads(msg)

        # El cliente solicita los colores disponibles
        if informacion["tipo"] == "solicitud_color":
            respuesta = colores_disponibles
            self.enviar_respuesta(respuesta)

        # El cliente se asigna un nombre y selecciona un color
        elif informacion["tipo"] == "seleccion_color":
            if colores_disponibles[informacion["color"]]:
                orden_turnos.append(informacion["color"])
                colores_disponibles[informacion["color"]] = False
                self.name = informacion["nombre"]
                self.color = informacion["color"]
                respuesta = {"color": informacion["color"], "disponible": True}
                self.enviar_respuesta(respuesta)
                broadcast({"jugador": self.name, "color": self.color})
            else:
                respuesta = {"color": informacion["color"], "disponible": False}
                self.enviar_respuesta(respuesta)

        # El cliente quiere iniciar la partida
        elif informacion["tipo"] == "solicitud_iniciar_partida":
            self.aprobacion = True
            respuesta = {"aprobacion": True}
            self.enviar_respuesta(respuesta)

        # El cliente lanza los dados
        elif informacion["tipo"] == "lanzar_dados":
            if self.color == turno_actual:
                ultimos_dados = informacion["dados"]
                registro_dados[self.color] = informacion["dados"]
                turno_actual = siguiente_turno(turno_actual)
                respuesta = {"aprobacion": True}
                self.enviar_respuesta(respuesta)
                broadcast(informacion_partida())
            else:
                respuesta = {"aprobacion": False}
                self.enviar_respuesta(respuesta)

    # Funcion para enviar la informacion actual del cliente
    def informacion(self):
        respuesta = {
            self.ip : {
                    "nombre": self.nombre,
                    "color": self.color,
                    "f1": self.f1,
                    "f2": self.f2,
                    "f3": self.f3,
                    "f4": self.f4,
                    "cont_f1": self.cont_f1,
                    "cont_f2": self.cont_f2,
                    "cont_f3": self.cont_f3,
                    "cont_f4": self.cont_f4
                }
            }
        return respuesta

    # Funcion para enviar una respuesta al cliente
    def enviar_respuesta(self, informacion):
        respuesta = json.dumps(informacion)
        self.connection.sendall(respuesta.encode('utf-8'))

    # Funcion que se ejecuta cuando se inicia el hilo
    def run(self):
        while True:
            # Recibe los datos del cliente
            mensaje = self.connection.recv(1024).decode('utf-8')
            if mensaje:
                self.procesar_informacion(mensaje)

# Funcion para enviar un mensaje a todos los clientes
def broadcast(mensaje):
        for client in hilos_clientes:
            client.enviar_respuesta(mensaje)

# Funcion que retorna la informacion de la partida
def informacion_partida():
    partida = {
        "turno_actual" : turno_actual,
        "ultimos_dados" : ultimos_dados,
    }
    for cliente in hilos_clientes:
        partida.update(cliente.informacion())
    return partida

# Funcion que valida si todos los usuarios (minimo 2) quieren iniciar la partida
def aprobacion_partida():
    if len(hilos_clientes) >= 2:
        aprobaciones = 0
        # Se valida si todos los clientes quieren iniciar la partida
        for cliente in hilos_clientes:
            if cliente.aprobacion == True:
                aprobaciones += 1
        if aprobaciones == len(hilos_clientes):
            return True
    return False

# Funcion que retorna el o los colores con el valor maximo de la suma de los dados
def mayor_valor(diccionario):
    # Se obtiene el valor maximo de la suma de los dados
    mayor_suma = max(diccionario.values(), key=lambda x: x['D1'] + x['D2'])['D1'] + max(diccionario.values(), key=lambda x: x['D1'] + x['D2'])['D2']
    # Se obtiene el o los colores con el valor maximo de la suma de los dados
    mayor_valor = [k for k, v in diccionario.items() if v['D1'] + v['D2'] == mayor_suma]
    return mayor_valor

# Funcion que retorna el color del siguiente turno
def siguiente_turno(turno_actual):
    if turno_actual in orden_turnos:
        # Se obtiene el índice del color actual
        indice_siguiente = (orden_turnos.index(turno_actual) + 1) % len(orden_turnos)
        return orden_turnos[indice_siguiente]

# Funcion que asigna los turnos para pasar a la derecha (Green->Red->Yellow->Blue->Green...)
def ordenar_turnos(primer_lugar, orden_turnos):
    orden_colores = ["Green", "Red", "Yellow", "Blue"]
    # Se obtiene la posición del color en la lista del orden
    inicio = orden_colores.index(primer_lugar)
    # Se crea una nueva lista con los colores en el orden correcto
    nuevo_orden = orden_colores[inicio:] + orden_colores[:inicio]
    # Se crea una nueva lista ordenada de acuerdo al nuevo orden
    nuevo_orden_turnos = [c for c in nuevo_orden if c in orden_turnos]
    return nuevo_orden_turnos

# Funcion que actua como receptor de clientes (se ejecuta en un hilo)
def recibir_clientes():
    while True:
        # Espera a que un cliente se conecte
        connection, address = servidor.accept()
        if len(hilos_clientes) < 4 and iniciar_partida == False:
                # Si hay menos de 4 clientes y no ha iniciado la partida, se acepta la conexion
                print('Conexión establecida por', address)
                # Crea un hilo para manejar al cliente
                thread = Cliente(connection, address)
                hilos_clientes.append(thread)
                thread.start()
        else:
            # Si hay 4 clientes o ya inicio la partida, se rechaza la conexion
            mensaje = "No se pueden aceptar más clientes"
            connection.sendall(mensaje.encode('utf-8'))
            connection.close()

# Hilo que actua como receptor de clientes
thread = threading.Thread(target=recibir_clientes)
thread.start()

# Ciclo principal de juego  
while True:
    # Se espera a que todos los jugadores quieran iniciar la partida
    while True: 
        iniciar_partida = aprobacion_partida()
        if iniciar_partida == True:
            broadcast({"iniciar_partida": True})
            break
            
    # Se definen los turnos segun quien saca el mayor valor en los dados (se inicia con el primero en entrar)
    orden_turnos = ordenar_turnos(orden_turnos[0], orden_turnos)

    # Se espera a que todos los jugadores lancen los dados para definir el orden de los turnos
    while True:
        print(orden_turnos)
        # Una vez que todos los jugadores hayan lanzado los dados, se busca quien saco el mayor valor
        if len(registro_dados) == len(orden_turnos):
            primer_lugar = mayor_valor(registro_dados)
            # Si hay un jugador con el valor maximo, se asignan los turnos a su derecha
            if len(primer_lugar) == 1:
                for cliente in hilos_clientes:
                    if cliente.color not in orden_turnos:
                        orden_turnos.append(cliente.color)
                orden_turnos = ordenar_turnos(primer_lugar, orden_turnos)
                break
            # Si hay un empate con el valor maximo, se debe hacer un desempate
            else:
                # Se reasignan los turnos para que solo lancen los jugadores del empate
                orden_turnos = [color for color in orden_turnos if color in primer_lugar]
                # Se limpia el registro de lanzamientos
                registro_dados.clear()

    # Una vez definidos los turnos, se inicia el juego
    while True:
        break