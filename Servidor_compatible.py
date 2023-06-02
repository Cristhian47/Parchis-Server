'''
SERVIDOR PARQUES PROYECTO FINAL SISTEMAS DISTRIBUIDOS

SOLICITUDES DE ENTRADA
{"tipo": "solicitud_color"}
{"tipo": "seleccion_color", "nombre": "Sarah", "color": "Red"}
{"tipo": "solicitud_iniciar_partida"}
{"tipo": "lanzar_dados", "dados": {"D1": 4, "D2": 1}}
{"tipo": "sacar_ficha", "ficha": "F1"}
{"tipo": "sacar_carcel", "ficha": "F1"}
{"tipo": "mover_ficha", "ficha": "F1"}

RESPUESTAS DE SALIDA
{"tipo": "denegado", "razon": "mensaje"}
{"tipo": "iniciar_partida"}
{"tipo": "sacar_ficha"}
{"tipo": "sacar_carcel"}
{"tipo": "mover_ficha"}

BROADCAST DE SALIDA
{"turno_actual": "red", "ultimos_dados": {"D1" : 5, "D2" : 2}, ...}
{"jugador": "Sarah", "color": "Red"}
{"tipo": "finalizar", "ganador": "Red"}
{"tipo": "desconexion", "cliente": (self.ip, self.puerto)}
{"tipo": "ganador_turno", "color": Blue}
{"tipo": "empate_turno", "colores": [Blue,Red,...]}
'''

# Librerias
import socket
import threading
import json

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

    # Que es lo que viene en el mensaje
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
        elif solicitud in solicitudes_juego and (estado_partida == "turnos" or estado_partida == "juego"):
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
        # Se extraen los argumentos
        nombre = informacion["nombre"]
        color = informacion["color"]
        
        # Se valida la congruencia de los argumentos
        respuesta = None
        if self.nombre != None and self.color != None:
            respuesta = {"tipo": "denegado", "razon": "ya seleccionaste un color"}
        elif nombre == None or color == None:
            respuesta = {"tipo": "denegado", "razon": "no seleccionaste un color"}   
        elif color not in ["Yellow", "Blue", "Green", "Red"]:
            respuesta = {"tipo": "denegado", "razon": "color no valido"}
        elif not colores_disponibles[color]:
            respuesta = {"tipo": "denegado", "razon": "color no disponible"}

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            self.enviar_respuesta(respuesta)
        else:
            colores_disponibles[color] = False
            self.nombre = nombre
            self.color = color
            # Se envia el mensaje de seleccion de color a todos los clientes
            mensaje = {"jugador": self.nombre, "color": self.color}
            broadcast(mensaje)

    # El cliente quiere iniciar la partida {"tipo": "solicitud_iniciar_partida"}
    def procesar_solicitud_iniciar_partida(self, informacion):     
        # Se valida que el cliente haya seleccionado un color
        respuesta = None
        if self.nombre == None or self.color == None:
            respuesta = {"tipo": "denegado", "razon": "no seleccionaste un color"}

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            self.enviar_respuesta(respuesta)
        else:
            # Se marca al cliente como listo para iniciar la partida
            self.iniciar_partida = True
            # Se comprueba si se puede iniciar la partida
            iniciar_partida()

    # El cliente lanza los dados {"tipo": "lanzar_dados", "dados": {"D1": 4, "D2": 1}}
    def procesar_lanzar_dados(self, informacion):
        # Variables globales
        global ultimos_dados, registro_dados, pares_seguidos, solicitud_esperada

        # Se extraen los argumentos
        D1 = informacion["dados"]["D1"]
        D2 = informacion["dados"]["D2"]
        
        # Se valida la congruencia de los argumentos
        respuesta = None
        if not isinstance(D1, int) or not isinstance(D2, int) or not (1 <= D1 <= 6) or not (1 <= D2 <= 6):
            respuesta = {"tipo": "denegado", "razon": "dados no validos"}
        
        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            self.enviar_respuesta(respuesta)
        else:
            # El estado de la partida es definir turnos
            if estado_partida == "turnos":
                # Se actualiza el registro de los ultimos dados
                ultimos_dados = informacion["dados"]
                # Se actualiza el registro de los dados de la ronda
                registro_dados[self.color] = informacion["dados"]
                # Se valida que todos los jugadores hayan lanzado los dados
                if len(registro_dados) == len(orden_turnos):
                    # Se envia la informacion de la partida actualizada a todos los clientes
                    mensaje = informacion_partida()
                    broadcast(mensaje)
                    # Se definen los turnos segun quien saco el mayor valor
                    definir_turnos()
                else:
                    # Se actualiza el turno
                    siguiente_turno()
                    # Se envia la informacion de la partida actualizada a todos los clientes
                    mensaje = informacion_partida()
                    broadcast(mensaje)

            # El estado de la partida es en juego
            elif estado_partida == "juego":
                # Se actualiza el registro de los ultimos dados
                ultimos_dados = informacion["dados"]

                # Se comprueba si saco pares
                if ultimos_dados["D1"] == ultimos_dados["D2"]:
                    # Si saca par tiene derecho a otro turno
                    self.turnos = 1
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
                        respuesta = {"tipo": "mover_ficha"}
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
                    else:
                        # Se actualiza la solicitud esperada
                        solicitud_esperada = "mover_ficha"
                        # Se envia la respuesta al cliente
                        respuesta = {"tipo": "mover_ficha"}
                        self.enviar_respuesta(respuesta)

                # Se envia la informacion de la partida actualizada a todos los clientes
                mensaje = informacion_partida()
                broadcast(mensaje)

    # El cliente saca una ficha del tablero {"tipo": "sacar_ficha", "ficha": "F1"}
    def procesar_sacar_ficha(self, informacion):
        # Variables globales
        global solicitud_esperada, estado_partida

        # Se extraen los argumentos
        ficha = informacion["ficha"]
        
        # Se valida la congruencia de los argumentos
        respuesta = None
        if ficha not in self.fichas:
            respuesta = {"tipo": "denegado", "razon": "ficha no valida"}
        
        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            self.enviar_respuesta(respuesta)
        else:
            # Se actualiza la posicion de la ficha
            self.fichas[ficha] = "Meta"
            # Se comprueba si todas las fichas estan en la meta
            if self.comprobar_meta():
                # Se actualiza el estado de la partida
                estado_partida = "finalizada"
                # Se envia el mensaje a todos los clientes
                mensaje = ({"tipo": "finalizar", "ganador": self.color})
                broadcast(mensaje)
                # Se imprime el mensaje en el servidor
                print("El jugador " + self.color + " ha ganado la partida")
            else:
                # Se actualiza los turnos
                self.turnos = 0
                # Se actualiza el turno
                siguiente_turno()
                # Se actualiza la solicitud esperada
                solicitud_esperada = "lanzar_dados"
                # Se envia la informacion de la partida actualizada a todos los clientes
                mensaje = informacion_partida()
                broadcast(mensaje)

    # El cliente saca una ficha de la carcel {"tipo": "sacar_carcel", "ficha": "F1"}
    def procesar_sacar_carcel(self, informacion):
        # Variables globales
        global solicitud_esperada

        # Se extraen los argumentos
        ficha = informacion["ficha"]
        
        # Se valida la congruencia de los argumentos
        respuesta = None
        if ficha not in self.fichas:
            respuesta = {"tipo": "denegado", "razon": "ficha no valida"}
        elif self.fichas[ficha] != "Carcel":
            respuesta = {"tipo": "denegado", "razon": "ficha no esta en la carcel"}

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            self.enviar_respuesta(respuesta)
        else:
            # Se actualiza la posicion de la ficha
            casillas_salida = {"Yellow": 56, "Blue": 5, "Green": 22, "Red": 39}
            self.fichas[ficha] = casillas_salida[self.color]
            # Se actualiza los turnos
            if self.turnos == 0:
                siguiente_turno()
            else:
                self.turnos -= 1
            # Se actualiza la solicitud esperada
            solicitud_esperada = "lanzar_dados"
            # Se envia la informacion de la partida actualizada a todos los clientes
            mensaje = informacion_partida()
            broadcast(mensaje)

    # El cliente mueve una ficha {"tipo": "mover_ficha", "ficha": "F1"}
    def procesar_mover_ficha(self, informacion):
        # Variables globales
        global estado_partida, hilos_clientes, solicitud_esperada

        # Se extraen los argumentos
        ficha = informacion["ficha"]
        
        # Se valida la congruencia de los argumentos
        respuesta = None
        if ficha not in self.fichas:
            respuesta = {"tipo": "denegado", "razon": "ficha no valida"}
        elif self.fichas[ficha] == "Carcel":
            respuesta = {"tipo": "denegado", "razon": "la ficha esta en la carcel"}

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            self.enviar_respuesta(respuesta)
        else:
            dados_suma = ultimos_dados["D1"] + ultimos_dados["D2"]
            nueva_posicion = self.fichas[ficha] + dados_suma
            nuevo_contador = self.contadores_fichas[ficha] + dados_suma

            # Llegó a la meta sin excederse
            if nuevo_contador == 71:
                # Llegó a la meta
                nueva_posicion = "Meta"

            # Está en la escalera
            elif  63 < nuevo_contador < 71:
                # Se calcula la nueva posicion
                nueva_posicion = 69 + (nuevo_contador - 63)

            # Está en el tablero
            elif nuevo_contador <= 63:      
                # Se comprueba si la ficha excede el limite del mapa
                if nueva_posicion > 68:
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
            # Se actualiza el contador de la ficha
            self.contadores_fichas[ficha] = nuevo_contador

            # Se comprueba si todas las fichas estan en la meta
            if self.comprobar_meta():
                # Se actualiza el estado de la partida
                estado_partida = "finalizada"
                # Se envia el mensaje a todos los clientes
                mensaje = ({"tipo": "finalizar", "ganador": self.color})
                broadcast(mensaje)
                # Se imprime el mensaje en el servidor
                print("El jugador " + self.color + " ha ganado la partida")
            else:
                # Se actualiza los turnos
                if self.turnos == 0:
                    siguiente_turno()
                else:
                    self.turnos -= 1
                # Se actualiza la solicitud esperada
                solicitud_esperada = "lanzar_dados"
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

    # Funcion para enviar una respuesta al cliente
    def enviar_respuesta(self, informacion):
        respuesta = json.dumps(informacion)
        self.connection.sendall(respuesta.encode('utf-8'))

    # Funcion para cerrar la conexion del cliente
    def cerrar_conexion(self):
        # Se imprime el mensaje en el servidor
        print("Desconexión causada por:", (self.ip, self.puerto))

        # Variables globales
        global hilos_clientes, estado_partida, orden_turnos, solicitud_esperada

        # Se termina la conexion
        self.connection.close()

        # Se elimina el cliente de la lista de hilos
        hilos_clientes.remove(self)

        # Se envia el mensaje a todos los clientes
        mensaje = ({"tipo": "desconexion", "cliente": (self.ip, self.puerto)})
        broadcast(mensaje)

        if estado_partida == "lobby":
            # El color del cliente se vuelve a poner disponible
            if self.color in ["Yellow", "Blue", "Green", "Red"]:
                colores_disponibles[self.color] = True
            # Se comprueba si se puede iniciar la partida
            iniciar_partida()
            
        elif estado_partida == "turnos":
            if len(hilos_clientes) < 2:
                # Se actualiza el estado de la partida
                estado_partida = "finalizada"
                # Se envia el mensaje a todos los clientes
                ganador = hilos_clientes[0].color
                mensaje = ({"tipo": "finalizar", "ganador": ganador})
                broadcast(mensaje)
                # Se imprime el mensaje en el servidor
                print("El jugador " + ganador + " ha ganado la partida")
            else:
                # Se comprueba si el cliente es el turno actual
                if self.color == turno_actual:
                    if len(registro_dados) == len(orden_turnos) - 1:
                        # Se elimina de la lista de turnos
                        orden_turnos.remove(self.color)
                        # Se envia la informacion de la partida actualizada a todos los clientes
                        mensaje = informacion_partida()
                        broadcast(mensaje)
                        # Se definen los turnos segun quien saco el mayor valor
                        definir_turnos()
                    else:
                        # Se actualiza el turno
                        siguiente_turno()
                        # Se elimina de la lista de turnos
                        orden_turnos.remove(self.color)
                        # Se envia la informacion de la partida actualizada a todos los clientes
                        mensaje = informacion_partida()
                        broadcast(mensaje)

        elif estado_partida == "juego":
            if len(hilos_clientes) < 2:
                # Se actualiza el estado de la partida
                estado_partida = "finalizada"
                # Se envia el mensaje a todos los clientes
                ganador = hilos_clientes[0].color
                mensaje = ({"tipo": "finalizar", "ganador": ganador})
                broadcast(mensaje)
                # Se imprime el mensaje en el servidor
                print("El jugador " + ganador + " ha ganado la partida")
            else:
                # Se comprueba si el cliente es el turno actual
                if self.color == turno_actual:
                    # Se actualiza el turno
                    siguiente_turno()
                    # Se actualiza la solicitud esperada
                    solicitud_esperada = "lanzar_dados"
                    # Se envia la informacion de la partida actualizada a todos los clientes
                    mensaje = informacion_partida()
                    broadcast(mensaje)
                # Se elimina de la lista de turnos
                orden_turnos.remove(self.color)

    # Funcion que se ejecuta cuando se inicia el hilo
    def run(self):
        while True:
            try:
                # Recibe los datos del cliente
                mensaje = self.connection.recv(1024).decode('utf-8')
                if mensaje:
                    self.procesar_informacion(mensaje)
                else:
                    # Se termina la conexion
                    self.cerrar_conexion()
                    # Se termina el hilo
                    break
            # La conexión cuando se cierra abruptamente
            except:
                # Se termina la conexion
                self.cerrar_conexion()
                # Se termina el hilo
                break

# Funcion para enviar un mensaje a todos los clientes
def broadcast(mensaje):
    for client in hilos_clientes:
        client.enviar_respuesta(mensaje)

# Funcion que comprueba si se puede iniciar la partida
def iniciar_partida():
    # Se importan las variables globales
    global estado_partida
    global solicitud_esperada
    # Se valida si hay minimo 2 clientes conectados
    if len(hilos_clientes) >= 2:
        # Se valida si todos los clientes quieren iniciar la partida
        aprobaciones = 0
        for cliente in hilos_clientes:
            if cliente.iniciar_partida == True:
                aprobaciones += 1
        if aprobaciones == len(hilos_clientes):
            estado_partida = "turnos"
            solicitud_esperada = "lanzar_dados"
            # Se selecciona el primer turno
            primer_turno = hilos_clientes[0].color
            # Se ordenan los turnos segun el orden de los colores
            ordenar_turnos(primer_turno)
            # Se envia el mensaje de partida iniciada a todos los clientes
            mensaje = {"tipo": "iniciar_partida"}
            broadcast(mensaje)
            # Se imprime el mensaje en el servidor
            print("Partida iniciada")

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

# Funcion que retorna el o los colores con el valor maximo de la suma de los dados
def mayor_suma(registro_dados):
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
        broadcast({"tipo": "ganador_turno", "color": primer_lugar[0]})
        # Se imprime el mensaje en el servidor
        print("Turnos definidos")
    # Si hay un empate con el valor maximo, se debe hacer un desempate
    else:
        # Se reasignan los turnos para que solo lancen los jugadores del empate
        orden_turnos = [color for color in orden_turnos if color in primer_lugar]
        broadcast({"tipo": "empate_turno", "colores": orden_turnos})
        # Se imprime el mensaje en el servidor
        print("Empate de turnos")
        # Se limpia el registro de lanzamientos
        registro_dados.clear()
        # Se actualiza el turno
        siguiente_turno()

# Funcion que reinicia la partida (expulsa los jugadores y reinicia las variables)
def reiniciar_partida():
    # Se importan las variables globales
    global hilos_clientes, colores_disponibles, turno_actual, orden_turnos, estado_partida, solicitud_esperada, ultimos_dados, registro_dados, pares_seguidos

    print("Desconectando clientes: ", hilos_clientes)

    # Se cierran los sockets de los clientes
    for cliente in hilos_clientes:
        cliente.connection.close()

    # Esperar a que los hilos clientes finalicen
    for thread in hilos_clientes:
        thread.join()

    # Se inicializan las variables globales para el proximo juego
    hilos_clientes = [] # Hilos de los clientes
    colores_disponibles = {"Yellow": True , "Blue": True, "Green": True, "Red": True} # Disponibilidad de los colores
    turno_actual = None # Color del jugador con el turno actual
    orden_turnos = [] # Orden de los turnos en la partida
    ultimos_dados = {"D1" : None, "D2" : None} # Valor de los dados de la ultima jugada (1-6)
    registro_dados = {} # Registro de los dados lanzados en una ronda
    pares_seguidos = 0 # Contador de los pares seguidos por un jugador
    solicitud_esperada = None # Indica la solicitud esperada de la ronda (lanzar_dados, sacar_ficha, mover_ficha)
    estado_partida = "lobby" # Indica el estado actual del juego (lobby, turnos, juego)

    # Se imprime el mensaje en el servidor
    print("Partida reiniciada")

# Funcion que actua como receptor de clientes (se ejecuta en un hilo)
def recibir_clientes():
    while True:
        # Espera a que un cliente se conecte
        connection, address = servidor.accept()
        # Se valida la solicitud
        respuesta = None
        if estado_partida != "lobby":
            respuesta = "Rechazado: La partida ya inició."
        elif not (len(hilos_clientes) < 4):
            respuesta = "Rechazado: Ya se superó el número máximo de jugadores."

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            # Se imprime el mensaje en el servidor
            print(f"Conexión rechazada por: {address}, razón: {respuesta}")
            connection.sendall(respuesta.encode('utf-8'))
            connection.close()
        else:
            # Se imprime el mensaje en el servidor
            print("Conexión establecida por:", address)
            # Crea un hilo para manejar al cliente
            thread = Cliente(connection, address)
            # Agrega el hilo a la lista de hilos
            hilos_clientes.append(thread)
            # Inicia el hilo
            thread.start()

# Datos del servidor
HOST = "localhost"  # El host del servidor
PORT = 8001         # El puerto del servidor

# Conectarse al servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORT))
servidor.listen(10)

# Se imprime el mensaje en el servidor
print(f"Servidor esperando conexiones en {HOST}:{PORT}...")

# Se inicializan las variables globales
hilos_clientes = [] # Hilos de los clientes
colores_disponibles = {"Yellow": True , "Blue": True, "Green": True, "Red": True} # Disponibilidad de los colores
turno_actual = None # Color del jugador con el turno actual
orden_turnos = [] # Orden de los turnos en la partida
ultimos_dados = {"D1" : None, "D2" : None} # Valor de los dados de la ultima jugada (1-6)
registro_dados = {} # Registro de los dados lanzados en una ronda
pares_seguidos = 0 # Contador de los pares seguidos por un jugador
solicitud_esperada = None # Indica la solicitud esperada de la ronda (lanzar_dados, sacar_ficha, mover_ficha)
estado_partida = "lobby" # Indica el estado actual del juego (lobby, turnos, juego)

# Hilo que actua como receptor de clientes
thread = threading.Thread(target=recibir_clientes)

# Iniciar el hilo receptor de clientes
thread.start()

'''
# Funcion para conectarse al BotAI
def conexion_bot():
    # Se crea el socket para conectarse al BotAI
    servidor_bot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_bot.connect(("localhost", 8002))
    # Se envia el mensaje al BotAI
    mensaje = {"tipo": "Activar_bot"}
    servidor_bot.sendall(json.dumps(mensaje).encode('utf-8'))

conexion_bot()
'''

# Esperar a que el hilo receptor de clientes finalice
thread.join()

# Se cierra el socket del servidor
servidor.close()

# Se imprime el mensaje en el servidor
print("Servidor finalizado")

