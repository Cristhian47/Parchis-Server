'''
SERVIDOR PARQUES PROYECTO FINAL SISTEMAS DISTRIBUIDOS

SOLICITUDES DE ENTRADA
{"tipo": "solicitud_color"}
{"tipo": "seleccion_color", "nombre": "Sarah", "color": "Red"}
{"tipo": "solicitud_iniciar_partida"}
{"tipo": "lanzar_dados", "dados": {"D1": 4, "D2": 1}}
{"tipo: "sacar_ficha", "ficha": "F1"}

RESPUESTAS DE SALIDA
{"tipo": "aprobado"}
{"tipo": "denegado", "razon": "mensaje"}
{"tipo": "iniciar_partida"}
{"tipo": "sacar_ficha"}

BROADCAST DE SALIDA
{"jugador": "Sarah", "color": "Red"}
{"turno_actual": "red", "ultimos_dados": {"D1" : 5, "D2" : 2}, ...}
'''

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

# Lista para el orden de los turnos en la partida
orden_turnos = []

# Variable que indica el estado actual del juego (lobby, lanzar_dados, sacar_ficha, mover_ficha) (juego, turnos)
estado_partida = "lobby"

# Diccionario para el valor de los dados de la ultima jugada (1-6,1-6)
ultimos_dados = {"D1" : None, "D2" : None}

# Lista para el registro de los dados de una ronda
registro_dados = {}

# Variable para contar los pares seguidos
pares_seguidos = 0

# Casillas especiales para los jugadores
casillas_seguras = [5,12,17,22,26,34,39,46,51,56,63,68]
casillas_giro = {"Yellow": 68, "Blue": 17, "Green": 34, "Red": 51}
casillas_salida = {"Yellow": 5, "Blue": 22, "Green": 39, "Red": 56}

# Clase para manejar a los clientes
class Cliente(threading.Thread):
    def __init__(self, connection, address):
        super(Cliente, self).__init__()
        self.connection = connection
        self.ip, self.puerto = address
        self.iniciar_partida = False
        self.turnos = 3
        self.nombre = None
        self.color = None
        self.F1 = "Carcel"
        self.F2 = "Carcel"
        self.F3 = "Carcel"
        self.F4 = "Carcel"
        self.cont_F1 = 0
        self.cont_F2 = 0
        self.cont_F3 = 0
        self.cont_F4 = 0

    # Que es lo  que viene en el mensaje
    def procesar_informacion(self, msg):   
        informacion = json.loads(msg)

        # Se importan las variables globales
        global ultimos_dados  
        global registro_dados
        global pares_seguidos

        # Se valida que la partida este en estado de lobby
        if estado_partida == "lobby":

            # El cliente solicita los colores disponibles {"tipo": "solicitud_color"}
            if informacion["tipo"] == "solicitud_color":
                # Se envia la respuesta al cliente
                respuesta = colores_disponibles
                self.enviar_respuesta(respuesta)

            # El cliente se asigna un nombre y selecciona un color {"tipo": "seleccion_color", "nombre": "Johan", "color": "Blue"}
            elif informacion["tipo"] == "seleccion_color":
                if colores_disponibles[informacion["color"]]:
                    colores_disponibles[informacion["color"]] = False
                    self.name = informacion["nombre"]
                    self.color = informacion["color"]
                    # Se envia la respuesta al cliente
                    respuesta = {"tipo": "aprobado"}
                    self.enviar_respuesta(respuesta)
                    # Se envia el mensaje de seleccion de color a todos los clientes
                    mensaje = {"jugador": self.name, "color": self.color}
                    broadcast(mensaje)
                else:
                    # Se envia la respuesta al cliente
                    respuesta = {"tipo": "denegado", "razon": "color no disponible"}
                    self.enviar_respuesta(respuesta)

            # El cliente quiere iniciar la partida {"tipo": "solicitud_iniciar_partida"}
            elif informacion["tipo"] == "solicitud_iniciar_partida":
                self.iniciar_partida = True
                # Se envia la respuesta al cliente
                respuesta = {"tipo": "aprobado"}
                self.enviar_respuesta(respuesta)
                # Se valida si todos los clientes quieren iniciar la partida
                if aprobacion_partida() == True:
                    # Se ordenan los turnos segun el orden de los colores
                    ordenar_turnos(hilos_clientes[0].color)
                    # Se envia el mensaje de partida iniciada a todos los clientes
                    mensaje = {"tipo": "iniciar_partida"}
                    broadcast(mensaje)

        # Se valida que la partida este en estado de lanzar dados en la fase de definir turnos
        elif estado_partida == "lanzar_dados_turnos":
            # Se valida que sea el turno del cliente
            if self.color == turno_actual:

                # El cliente lanza los dados {"tipo": "lanzar_dados", "dados": {"D1": 4, "D2": 1}}
                if informacion["tipo"] == "lanzar_dados":
                    # Se actualiza el registro de los ultimos dados
                    ultimos_dados = informacion["dados"]
                    # Se actualiza el registro de los dados de la ronda
                    registro_dados[self.color] = informacion["dados"]
                    # Se valida que todos los jugadores hayan lanzado los dados
                    if len(registro_dados) == len(orden_turnos):
                        # Se definen los turnos segun quien saco el mayor valor
                        definir_turnos()

            else:
                respuesta = {"tipo": "denegado", "razon": "no es su turno"}
                self.enviar_respuesta(respuesta)


        # Se valida que la partida este en estado de lanzar dados en la fase de juego
        elif estado_partida == "lanzar_dados_juego":
            # Se valida que sea el turno del cliente
            if self.color == turno_actual:

                # El cliente lanza los dados {"tipo": "lanzar_dados", "dados": {"D1": 4, "D2": 1}}
                if informacion["tipo"] == "lanzar_dados":
                    # Se actualiza el registro de los ultimos dados
                    ultimos_dados = informacion["dados"]
                    # Se comprueba si saco pares
                    if ultimos_dados["D1"] == ultimos_dados["D2"]:
                        #Si saca par, tiene derecho a otro turno
                        self.turnos == 1
                        # Si saca 3 pares seguidos saca ficha
                        pares_seguidos += 1
                        if pares_seguidos == 3:
                            # Se envia la respuesta al cliente
                            respuesta = {"tipo": "sacar_ficha"}
                            self.enviar_respuesta(respuesta)
                    else:
                        # Si no saca par, se reinicia el contador de pares seguidos
                        pares_seguidos = 0
                        # Se comprueba si aun tiene turnos
                        if self.turnos == 0:
                            # Se actualiza el turno actual
                            siguiente_turno()
                        else:
                            self.turnos -= 1
                        # Se envia la respuesta al cliente
                        respuesta = {"tipo": "aprobado"}
                        self.enviar_respuesta(respuesta)

            else:
                respuesta = {"tipo": "denegado", "razon": "no es su turno"}
                self.enviar_respuesta(respuesta) 


        # Se valida que la partida este en estado de sacar ficha
        elif estado_partida == "sacar_ficha":
            # Se valida que sea el turno del cliente
            if self.color == turno_actual:
                
                # El cliente saca una ficha {"tipo": "sacar_ficha", "ficha": "F1"}
                if informacion["tipo"] == "sacar_ficha":
                    # Se valida que haya sacado 3 pares seguidos
                    if pares_seguidos == 3:
                        # Se valida que la ficha sea valida
                        if informacion["ficha"] in ["F1", "F2", "F3", "F4"]:
                            # Se actualiza la posicion de la ficha
                            self.informacion["ficha"] = "Meta"
                            # Se reinicia el contador de pares seguidos
                            pares_seguidos = 0
                            # Se envia la respuesta al cliente
                            respuesta = {"tipo": "aprobado"}
                            self.enviar_respuesta(respuesta)
                            # Se envia la informacion de la partida actualizada a todos los clientes
                            mensaje = informacion_partida()
                            broadcast(mensaje)
                        else:
                            # Se envia la respuesta al cliente
                            respuesta = {"tipo": "denegado", "razon": "ficha no valida"}
                            self.enviar_respuesta(respuesta)
                    else: 
                        # Se envia la respuesta al cliente
                        respuesta = {"tipo": "denegado", "razon": "no ha sacado 3 pares seguidos"}
                        self.enviar_respuesta(respuesta)

            else:
                respuesta = {"tipo": "denegado", "razon": "no es su turno"}
                self.enviar_respuesta(respuesta) 


        # Se valida que la partida este en estado de mover ficha
        elif estado_partida == "mover_ficha":
            # Se valida que sea el turno del cliente
            if self.color == turno_actual:

                # El cliente mueve una ficha {"tipo": "mover_ficha", "D1":"F2", "D2":"F4}
                if informacion["tipo"] == "mover_ficha":
                    # Se actualiza la posicion de la ficha
                    match informacion["D1"]:
                        case "F1":
                            self.F1 += ultimos_dados["D1"]
                            self.cont_F1 += ultimos_dados["D1"]
                        case "F2":
                            self.F2 += ultimos_dados["D1"]
                            self.cont_F2 += ultimos_dados["D1"]
                        case "F3":
                            self.F3 += ultimos_dados["D1"]
                            self.cont_F3 += ultimos_dados["D1"]
                        case "F4":
                            self.F4 += ultimos_dados["D1"]
                            self.cont_F4 += ultimos_dados["D1"]
                    match informacion["D2"]:
                        case "F1":
                            self.F1 += ultimos_dados["D2"]
                            self.cont_F1 += ultimos_dados["D2"]
                        case "F2":
                            self.F2 += ultimos_dados["D2"]
                            self.cont_F2 += ultimos_dados["D2"]
                        case "F3":
                            self.F3 += ultimos_dados["D2"]
                            self.cont_F3 += ultimos_dados["D2"]
                        case "F4":
                            self.F4 += ultimos_dados["D2"]
                            self.cont_F4 += ultimos_dados["D2"]

                    # Se envia la respuesta al cliente
                    respuesta = {"tipo": "aprobado"}
                    self.enviar_respuesta(respuesta)
                    # Se envia la informacion de la partida actualizada a todos los clientes
                    mensaje = informacion_partida()
                    broadcast(mensaje)
                    
            else:
                respuesta = {"tipo": "denegado", "razon": "no es su turno"}
                self.enviar_respuesta(respuesta)  


        else:
            respuesta = {"tipo": "denegado", "razon": "no es la solicitud esperada"}
            self.enviar_respuesta(respuesta)

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
    # Se crea el diccionario con la informacion de la partida
    partida = {
        "turno_actual" : turno_actual,
        "ultimos_dados" : ultimos_dados,
    }
    # Se agrega la informacion de cada cliente
    for cliente in hilos_clientes:
        informacion_cliente = {
            cliente.ip : {
                    "nombre": cliente.nombre,
                    "color": cliente.color,
                    "F1": cliente.F1,
                    "F2": cliente.F2,
                    "F3": cliente.F3,
                    "F4": cliente.F4,
                    "cont_F1": cliente.cont_F1,
                    "cont_F2": cliente.cont_F2,
                    "cont_F3": cliente.cont_F3,
                    "cont_F4": cliente.cont_F4
                }
            }
        partida.update(informacion_cliente)
    return partida

# Funcion que valida si todos los usuarios (minimo 2) quieren iniciar la partida
def aprobacion_partida():
    # Se importan las variables globales
    global estado_partida
    # Se valida si hay minimo 2 clientes conectados
    if len(hilos_clientes) >= 2:
        aprobaciones = 0
        # Se valida si todos los clientes quieren iniciar la partida
        for cliente in hilos_clientes:
            if cliente.iniciar_partida == True:
                aprobaciones += 1
        if aprobaciones == len(hilos_clientes):
            estado_partida = "Turnos"
            return True
    return False

# Funcion que retorna el o los colores con el valor maximo de la suma de los dados
def mayor_valor(dados):
    # Se obtiene el valor maximo de la suma de los dados
    mayor_suma = max(dados.values(), key=lambda x: x['D1'] + x['D2'])['D1'] + max(dados.values(), key=lambda x: x['D1'] + x['D2'])['D2']
    # Se obtiene el o los colores con el valor maximo de la suma de los dados
    mayor_valor = [k for k, v in dados.items() if v['D1'] + v['D2'] == mayor_suma]
    return mayor_valor

# Funcion que actualiza el turno
def siguiente_turno():
    # Se importan las variables globales
    global turno_actual
    # Se obtiene el índice del siguiente color
    indice_siguiente = (orden_turnos.index(turno_actual) + 1) % len(orden_turnos)
    # Se actualiza el turno actual
    turno_actual = orden_turnos[indice_siguiente]

# Funcion que asigna los turnos para pasar a la derecha (Green->Red->Yellow->Blue->Green...)
def ordenar_turnos(inicio):
    # Se importan las variables globales
    global orden_turnos
    global turno_actual
    # Se define el orden de los colores
    orden_colores = ["Green", "Red", "Yellow", "Blue"]
    # Se obtiene la posición del color en la lista del orden
    posicion = orden_colores.index(inicio)
    # Se crea una nueva lista con los colores en el orden correcto
    nuevo_orden = orden_colores[posicion:] + orden_colores[:posicion]
    # Se agregan los colores de los jugadores a la lista de turnos
    for cliente in hilos_clientes:
        if cliente.color not in orden_turnos:
            orden_turnos.append(cliente.color)
    # Se crea una nueva lista ordenada de acuerdo al nuevo orden
    orden_turnos = [color for color in nuevo_orden if color in orden_turnos]
    # Se define el turno actual
    turno_actual = orden_turnos[0]

# Funcion que define el orden de los turnos 
def definir_turnos():
    # Se importan las variables globales
    global orden_turnos
    global registro_dados
    global estado_partida
    # Se busca el jugador con el valor maximo
    primer_lugar = mayor_valor(registro_dados)
    # Si hay un jugador con el valor maximo, se asignan los turnos a su derecha
    if len(primer_lugar) == 1:
        ordenar_turnos(primer_lugar[0])
        estado_partida = "Juego"
    # Si hay un empate con el valor maximo, se debe hacer un desempate
    else:
        # Se reasignan los turnos para que solo lancen los jugadores del empate
        orden_turnos = [color for color in orden_turnos if color in primer_lugar]
        # Se limpia el registro de lanzamientos
        registro_dados.clear()

# Funcion para conectarse al BotAI
def conexion_bot():
    # Se crea el socket para conectarse al BotAI
    servidor_bot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_bot.connect(("10.253.61.122", 8002))
    # Se envia el mensaje al BotAI
    mensaje = {"tipo": "Activar_bot"}
    servidor_bot.sendall(json.dumps(mensaje).encode('utf-8'))

conexion_bot()

# Funcion que actua como receptor de clientes (se ejecuta en un hilo)
def recibir_clientes():
    while True:
        # Espera a que un cliente se conecte
        connection, address = servidor.accept()
        print(len(hilos_clientes), estado_partida)
        if len(hilos_clientes) < 4 and estado_partida == "lobby":
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