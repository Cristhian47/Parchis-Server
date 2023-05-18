'''
SERVIDOR PARQUES PROYECTO FINAL SISTEMAS DISTRIBUIDOS

SOLICITUDES DE ENTRADA
{"tipo": "solicitud_color"}
{"tipo": "seleccion_color", "nombre": "Sarah", "color": "Red"}
{"tipo": "solicitud_iniciar_partida"}
{"tipo": "lanzar_dados", "dados": {"D1": 4, "D2": 1}}
{"tipo: "sacar_ficha", "ficha": "F1"}
{"tipo: "mover_ficha", ...}

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

# Variable que indica el estado actual del juego (lobby, turnos, juego, finalizada)
estado_partida = "lobby"

# Variable que indica la solicitud esperada de la ronda (lanzar_dados, sacar_ficha, mover_ficha)
solicitud_esperada = None

# Diccionario para el valor de los dados de la ultima jugada (1-6,1-6)
ultimos_dados = {"D1" : None, "D2" : None}

# Lista para el registro de los dados de una ronda
registro_dados = {}

# Variable para contar los pares seguidos
pares_seguidos = 0

# Clase para manejar a los clientes
class Cliente(threading.Thread):
    def __init__(self, connection, address):
        super(Cliente, self).__init__()
        # Atributos de la conexion
        self.connection = connection
        self.ip, self.puerto = address
        # Atributos para la partida
        self.iniciar_partida = False
        self.turnos = 2
        # Atributos del jugador
        self.nombre = None
        self.color = None
        self.fichas = {
            "F1": "Carcel",
            "F2": "Carcel",
            "F3": "Carcel",
            "F4": "Carcel"
            }
        self.contadores_fichas = {
            "F1": 0,
            "F2": 0,
            "F3": 0,
            "F4": 0
            }

    # Que es lo  que viene en el mensaje
    def procesar_informacion(self, mensaje):  
        # Se traduce el archivo json 
        informacion = json.loads(mensaje)

        # Diccionario para manejar las solicitudes esperadas en lobby
        solicitudes_lobby = {
            "solicitud_color": self.procesar_solicitud_color,
            "seleccion_color": self.procesar_seleccion_color,
            "solicitud_iniciar_partida": self.procesar_solicitud_iniciar_partida,
        }

        # Diccionario para manejar las solicitudes esperadas en juego
        solicitudes_juego = {
            "lanzar_dados": self.procesar_lanzar_dados,
            "sacar_ficha": self.procesar_sacar_ficha,
            "sacar_carcel": self.procesar_sacar_carcel,
            "mover_ficha": self.procesar_mover_ficha,
        }

        # Se obtiene el tipo de solicitud
        solicitud = informacion["tipo"]
        # Si el estado de la partida es lobby se ejecuta una accion
        if solicitud in solicitudes_lobby and estado_partida == "lobby":
            solicitudes_lobby[solicitud](informacion)
        # Si el estado de la partida es juego o turnos se ejecuta una accion
        elif solicitud in solicitudes_juego and (estado_partida == "juego" or estado_partida == "turnos"):
            # Se verifica que sea el turno del jugador
            if self.color == turno_actual:
                # Se verifica que la solicitud sea la esperada
                if solicitud == solicitud_esperada:
                    # Se ejecuta la accion correspondiente
                    solicitudes_juego[solicitud](informacion)
                else: 
                    respuesta = {"tipo": "denegado", "razon": "no es la solicitud esperada"}
                    self.enviar_respuesta(respuesta) 
            else:
                respuesta = {"tipo": "denegado", "razon": "no es tu turno"}
                self.enviar_respuesta(respuesta)
        else:
            respuesta = {"tipo": "denegado", "razon": "solicitud no valida"}
            self.enviar_respuesta(respuesta)

    # El cliente solicita los colores disponibles {"tipo": "solicitud_color"}
    def procesar_solicitud_color(self, informacion):
        # Se envia la respuesta al cliente
        respuesta = colores_disponibles
        self.enviar_respuesta(respuesta)

    # El cliente se asigna un nombre y selecciona un color {"tipo": "seleccion_color", "nombre": "Johan", "color": "Blue"}
    def procesar_seleccion_color(self, informacion):
        color = informacion["color"]
        if color in ["Yellow", "Blue", "Green", "Red"]:
            if colores_disponibles[color]:
                colores_disponibles[color] = False
                self.nombre = informacion["nombre"]
                self.color = color
                # Se envia la respuesta al cliente
                respuesta = {"tipo": "aprobado"}
                self.enviar_respuesta(respuesta)
                # Se envia el mensaje de seleccion de color a todos los clientes
                mensaje = {"jugador": self.nombre, "color": self.color}
                broadcast(mensaje)
            else:
                # Se envia la respuesta al cliente
                respuesta = {"tipo": "denegado", "razon": "color no disponible"}
                self.enviar_respuesta(respuesta)
        else:
            # Se envia la respuesta al cliente
            respuesta = {"tipo": "denegado", "razon": "color no valido"}
            self.enviar_respuesta(respuesta)

    # El cliente quiere iniciar la partida {"tipo": "solicitud_iniciar_partida"}
    def procesar_solicitud_iniciar_partida(self, informacion):
        if self.nombre != None and self.color != None:
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
        else:
            # Se envia la respuesta al cliente
            respuesta = {"tipo": "denegado", "razon": "no ha seleccionado un color"}
            self.enviar_respuesta(respuesta)

    # El cliente lanza los dados {"tipo": "lanzar_dados", "dados": {"D1": 4, "D2": 1}}
    def procesar_lanzar_dados(self, informacion):
        D1 = informacion["dados"]["D1"]
        D2 = informacion["dados"]["D2"]
        if isinstance(D1, int) and isinstance(D2, int) and 1 <= D1 <= 6 and 1 <= D2 <= 6:
            # Se importan las variables globales
            global ultimos_dados  
            global registro_dados
            global pares_seguidos
            global solicitud_esperada
            # El estado de la partida es definir turnos
            if estado_partida == "turnos":
                # Se actualiza el registro de los ultimos dados
                ultimos_dados = informacion["dados"]
                # Se actualiza el registro de los dados de la ronda
                registro_dados[self.color] = informacion["dados"]
                # Se valida que todos los jugadores hayan lanzado los dados
                if len(registro_dados) == len(orden_turnos):
                    # Se definen los turnos segun quien saco el mayor valor
                    definir_turnos()
                else:
                    # # Se actualiza el turno
                    siguiente_turno()
                # Se envia la respuesta al cliente
                respuesta = {"tipo": "aprobado"}
                self.enviar_respuesta(respuesta)
            # El estado de la partida es en juego
            elif estado_partida == "juego":
                # Se actualiza el registro de los ultimos dados
                ultimos_dados = informacion["dados"]
                # Se comprueba si saco pares
                if ultimos_dados["D1"] == ultimos_dados["D2"]:
                    # Si saca par tiene derecho a otro turno
                    self.turnos == 1
                    # Se incrementa el contador de pares seguidos
                    pares_seguidos += 1
                    # Si saca 3 pares seguidos saca ficha
                    if pares_seguidos == 3:
                        # Se reinicia el contador de pares seguidos
                        pares_seguidos = 0
                        # Se actualiza la solicitud esperada
                        solicitud_esperada = "sacar_ficha"
                        # Se envia la respuesta al cliente
                        respuesta = {"tipo": "sacar_ficha"}
                        self.enviar_respuesta(respuesta)
                    elif self.fichas_carcel():
                        # Se actualiza la solicitud esperada
                        solicitud_esperada = "sacar_carcel"
                        # Se envia la respuesta al cliente
                        respuesta = {"tipo": "sacar_carcel"}
                        self.enviar_respuesta(respuesta)
                    else:
                        # Se actualiza la solicitud esperada
                        solicitud_esperada = "mover_ficha"
                        # Se envia la respuesta al cliente
                        respuesta = {"tipo": "aprobado"}
                        self.enviar_respuesta(respuesta)
                # No saca par
                else:
                    # Se reinicia el contador de pares seguidos
                    pares_seguidos = 0
                    if self.comprobar_carcel():
                        # Se actualiza los turnos
                        if self.turnos == 0:
                            siguiente_turno()
                        else:
                            self.turnos -= 1
                        # Se envia la respuesta al cliente
                        respuesta = {"tipo": "aprobado"}
                        self.enviar_respuesta(respuesta)
                    else:
                        # Se actualiza la solicitud esperada
                        solicitud_esperada = "mover_ficha"
                        # Se envia la respuesta al cliente
                        respuesta = {"tipo": "aprobado"}
                        self.enviar_respuesta(respuesta)
        else:
            # Se envia la respuesta al cliente
            respuesta = {"tipo": "denegado", "razon": "dados no validos"}
            self.enviar_respuesta(respuesta)

    # El cliente saca una ficha del tablero {"tipo": "sacar_ficha", "ficha": "F1"}
    def procesar_sacar_ficha(self, informacion):
        # Se importan las variables globales
        global solicitud_esperada
        # Se extrae la informacion de la ficha
        ficha = informacion["ficha"]
        # Se valida que la ficha sea valida
        if ficha in self.fichas:
            # Se actualiza la posicion de la ficha
            self.fichas[ficha] = "Meta"
            # Se actualiza los turnos
            self.turnos = 0
            # Se actualiza el turno
            siguiente_turno()
            # Se actualiza la solicitud esperada
            solicitud_esperada = "lanzar_dados"
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

    # El cliente saca una ficha de la carcel {"tipo": "sacar_carcel", "ficha": "F1"}
    def procesar_sacar_carcel(self, informacion):
        # Se importan las variables globales
        global solicitud_esperada
        # Casillas de salida segun el color del jugador
        casillas_salida = {"Yellow": 5, "Blue": 22, "Green": 39, "Red": 56}
        # Se extrae la informacion de la ficha
        ficha = informacion["ficha"]
        # Se valida que la ficha sea valida
        if ficha in self.fichas:
            # Se comprueba si la ficha esta en la carcel
            if self.fichas[ficha] == "Carcel":
                # Se actualiza la posicion de la ficha
                self.fichas[ficha] = casillas_salida[self.color]
                # Se actualiza los turnos
                if self.turnos == 0:
                    siguiente_turno()
                else:
                    self.turnos -= 1
                # Se actualiza la solicitud esperada
                solicitud_esperada = "lanzar_dados"
                # Se envia la respuesta al cliente
                respuesta = {"tipo": "aprobado"}
                self.enviar_respuesta(respuesta)
                # Se envia la informacion de la partida actualizada a todos los clientes
                mensaje = informacion_partida()
                broadcast(mensaje)
            else:
                # Se envia la respuesta al cliente
                respuesta = {"tipo": "denegado", "razon": "ficha no esta en la carcel"}
                self.enviar_respuesta(respuesta)
        else:
            # Se envia la respuesta al cliente
            respuesta = {"tipo": "denegado", "razon": "ficha no valida"}
            self.enviar_respuesta(respuesta)

    # El cliente mueve una ficha {"tipo": "mover_ficha", "ficha": "F1"}
    def procesar_mover_ficha(self, informacion):
        # Se importan las variables globales
        global estado_partida
        global hilos_clientes
        global solicitud_esperada

        # Se extrae la informacion de la ficha
        ficha = informacion["ficha"]
        nueva_posicion = self.fichas[ficha] + ultimos_dados["D1"] + ultimos_dados["D2"]

        # Se comprueba si la ficha esta en la escalera
        if self.comprobar_giro(ficha):
            # Se calcula la nueva posicion
            pass
        # Se comprueba si la ficha excede el limite del mapa
        elif nueva_posicion > 68:
            # Se calcula la nueva posicion
            nueva_posicion = nueva_posicion - 68

        # Se comprueba si la ficha puede comer a otras
        if not self.comprobar_seguro(ficha):
            for cliente in hilos_clientes:
                if cliente.color != self.color:
                    for ficha, posicion in cliente.fichas.items():
                        if posicion == nueva_posicion:
                            cliente.fichas[ficha] = "Carcel"
                            cliente.contadores_fichas[ficha] = 0

        # Se actualiza la posicion de la ficha
        self.fichas[ficha] = nueva_posicion
        self.contadores_fichas[ficha] += ultimos_dados["D1"] + ultimos_dados["D2"]

        # Se comprueba si todas las fichas estan en la meta
        if self.comprobar_meta():
            # Se actualiza el estado de la partida
            estado_partida = "finalizada"
            # Se envia el mensaje a todos los clientes
            mensaje = ({"tipo": "finalizar", "ganador": self.color})
            broadcast(mensaje)
        else:
            # Se actualiza los turnos
            if self.turnos == 0:
                siguiente_turno()
            else:
                self.turnos -= 1
            # Se actualiza la solicitud esperada
            solicitud_esperada = "lanzar_dados"
            # Se envia la respuesta al cliente
            respuesta = {"tipo": "aprobado"}
            self.enviar_respuesta(respuesta)
            # Se envia la informacion de la partida actualizada a todos los clientes
            mensaje = informacion_partida()
            broadcast(mensaje)

    # Funcion que comprueba si todas las fichas estan en la meta
    def comprobar_meta(self):
        for ficha, posicion in self.fichas.items():
            if posicion != "Meta":
                return False
        return True

    # Funcion que comprueba si todas la fichas estan en la carcel
    def comprobar_carcel(self):
        for ficha, posicion in self.fichas.items():
            if posicion != "Carcel":
                return False
        return True

    # Funcion que comprueba si tiene alguna ficha en la carcel
    def fichas_carcel(self):
        for ficha in self.fichas:
            if self.fichas[ficha] == "Carcel":
                return True
        return False

    # Funcion que comprueba si la ficha esta en casilla de seguro
    def comprobar_seguro(self, ficha):
        if self.fichas[ficha] in [5,12,17,22,26,34,39,46,51,56,63,68]:
            return True
        return False
    
    # Funcion que comprueba si la ficha esta en casilla de giro
    def comprobar_giro(self, ficha):
        casillas_giro = {"Yellow": 68, "Blue": 51, "Green": 17, "Red": 34}
        giro = casillas_giro[self.color]
        if self.fichas[ficha] >= giro:
            return True
        return False

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
            cliente.nombre : {
                    "nombre": cliente.nombre,
                    "color": cliente.color,
                    "fichas": cliente.fichas,
                    "contadores_fichas": cliente.contadores_fichas,
                }
            }
        partida.update(informacion_cliente)
    return partida

# Funcion que valida si todos los usuarios (minimo 2) quieren iniciar la partida
def aprobacion_partida():
    # Se importan las variables globales
    global estado_partida
    global solicitud_esperada
    # Se valida si hay minimo 2 clientes conectados
    if len(hilos_clientes) >= 2:
        aprobaciones = 0
        # Se valida si todos los clientes quieren iniciar la partida
        for cliente in hilos_clientes:
            if cliente.iniciar_partida == True:
                aprobaciones += 1
        if aprobaciones == len(hilos_clientes):
            estado_partida = "turnos"
            solicitud_esperada = "lanzar_dados"
            return True
    return False

# Funcion que retorna el o los colores con el valor maximo de la suma de los dados
def mayor_suma(registro_dados):
    print(registro_dados)
    mayor_suma = 0
    colores = []
    for color, dados in registro_dados.items():
        suma = dados["D1"] + dados["D2"]
        if suma > mayor_suma:
            mayor_suma = suma
            colores = [color]
        elif suma == mayor_suma:
            colores.append(color)
    return colores

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
    primer_lugar = mayor_suma(registro_dados)
    # Si hay un jugador con el valor maximo, se asignan los turnos a su derecha
    if len(primer_lugar) == 1:
        ordenar_turnos(primer_lugar[0])
        estado_partida = "juego"
        broadcast({"tipo": "ganador", "color": primer_lugar[0]})
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

#conexion_bot()

# Funcion que actua como receptor de clientes (se ejecuta en un hilo)
def recibir_clientes():
    while True:
        # Espera a que un cliente se conecte
        connection, address = servidor.accept()
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