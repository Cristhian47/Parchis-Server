'''
SERVIDOR PARA EL JUEGO PARQUES (PROYECTO FINAL SISTEMAS DISTRIBUIDOS)

ELABORADO POR:
Johan Fernando Acuña Pérez
Sarah Sofia Palacio Vanegas
Santiago Posada Florez
Cristian Andres Grajales Perez

Nota: Ver 'estructura.txt' para conocer la estructura de los mensajes
Nota 2: Ver 'tablero.png' para conocer la estructura del tablero
'''

# Librerias
import socket
import threading
import json
import time

# Variable para definir si se juega en local
local = True

# Cambio de IPs 
if local:
    # IP servidor privada
    IP_SERVER_PRIVADA = "localhost"
    # IP bot publica
    IP_BOT_PUBLICA = "localhost"
else:
    # IP servidor privada
    IP_SERVER_PRIVADA = "172.31.9.104"
    # IP bot publica
    IP_BOT_PUBLICA = "18.117.119.109"

# Puerto servidor
PORT_SERVER = 8001
# Puerto bot
PORT_BOT = 8002

# Clase para manejar a los clientes
class Cliente(threading.Thread):
    def __init__(self, connection, address):
        super(Cliente, self).__init__()
        # Atributos de la conexion
        self.connection = connection
        self.address = address
        # Atributos para la partida
        self.iniciar_partida = False
        self.turnos = 2
        # Atributos del jugador
        self.nombre = ""
        self.color = ""
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
        # Se imprime el mensaje recibido
        if self.color == "":
            print(f"[{self.address}]: {mensaje}")
        else: 
            print(f"[{self.address}, {self.color}]: {mensaje}")

        # Hay múltiples solicitudes en el mensaje
        if "}{" in mensaje:
            # Dividir el mensaje en solicitudes individuales
            solicitudes = mensaje.split("}")
            # Eliminar el último elemento de la lista, ya que no contiene un grupo completo
            solicitudes.pop()
            # Agregar las llaves de cierre a cada grupo, excepto al último
            for i in range(len(solicitudes)):
                solicitudes[i] += '}'
            # Procesar la primera solicitud
            solicitud = solicitudes[-1]
            # Se traduce el archivo json
            informacion = json.loads(solicitud)
            self.procesar_solicitud(informacion)

        # Solo hay una solicitud en el mensaje
        else:
            # Se traduce el archivo json
            informacion = json.loads(mensaje)
            self.procesar_solicitud(informacion)

    def procesar_solicitud(self, informacion):
        # Diccionario para manejar las solicitudes esperadas en lobby
        solicitudes_lobby = {
            "solicitud_color": self.procesar_solicitud_color,
            "seleccion_color": self.procesar_seleccion_color,
            "solicitud_iniciar_partida": self.procesar_solicitud_iniciar_partida,
            "solicitud_bot": self.procesar_solicitud_bot,
        }

        # Diccionario para manejar las solicitudes esperadas en juego
        solicitudes_juego = {
            "lanzar_dados": self.procesar_lanzar_dados,
            "sacar_ficha": self.procesar_sacar_ficha,
            "sacar_carcel": self.procesar_sacar_carcel,
            "mover_ficha": self.procesar_mover_ficha,
        }

        # Se obtiene el tipo de solicitud
        try:
            solicitud = informacion["tipo"]
        except:
            respuesta = {"tipo": "denegado", "razon": "no se especifico el tipo de solicitud"}
            self.enviar_respuesta(respuesta)
            return
        
        # Si el estado de la partida es lobby se ejecuta una accion
        if solicitud in solicitudes_lobby and estado_partida == "lobby":
            # Se imprime el inicio de ejecucion
            print(f"[{self.address}]: Ejecutando solicitud")
            # Se ejecuta la accion correspondiente
            solicitudes_lobby[solicitud](informacion)
            # Se imprime el fin de ejecucion
            print(f"[{self.address}]: Solicitud ejecutada")
        # Si el estado de la partida es juego o turnos se ejecuta una accion
        elif solicitud in solicitudes_juego and (estado_partida == "turnos" or estado_partida == "juego"):
            # Se verifica que sea el turno del jugador
            if self.color == turno_actual:
                # Se verifica que la solicitud sea la esperada
                if solicitud == solicitud_esperada:
                    # Se imprime el inicio de ejecucion
                    print(f"[{self.address}, {self.color}]: Ejecutando solicitud")
                    # Se ejecuta la accion correspondiente
                    solicitudes_juego[solicitud](informacion)
                    # Se imprime el fin de ejecucion
                    print(f"[{self.address}, {self.color}]: Solicitud ejecutada")
                else:
                    print(f"[DENEGADO]: Solicitud no esperada") 
                    respuesta = {"tipo": "denegado", "razon": "no es la solicitud esperada"}
                    self.enviar_respuesta(respuesta) 
            else:
                print(f"[DENEGADO]: No es tu turno")
                respuesta = {"tipo": "denegado", "razon": "no es tu turno"}
                self.enviar_respuesta(respuesta)
        else:
            print(f"[DENEGADO]: Solicitud no valida")
            respuesta = {"tipo": "denegado", "razon": "solicitud no valida"}
            self.enviar_respuesta(respuesta)

    # El cliente solicita los colores disponibles {"tipo": "solicitud_color"}
    def procesar_solicitud_color(self, informacion):
        # Se envia la respuesta al cliente
        respuesta = colores_disponibles
        self.enviar_respuesta(respuesta)

    # El cliente añade un bot {"tipo": "solicitud_bot"}
    def procesar_solicitud_bot(self, informacion):
        # Se valida la congruencia de los argumentos
        respuesta = None
        if len(hilos_clientes) == 4:
            respuesta = {"tipo": "denegado", "razon": "maximo de jugadores alcanzado"}

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            print(f"[DENEGADO]: {respuesta['razon']}")
            self.enviar_respuesta(respuesta)
        else:
            try:
                # Se crea la conexion con el bot
                servidor_bot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                servidor_bot.connect((IP_BOT_PUBLICA, PORT_BOT))
                # Se envia el mensaje al bot
                mensaje = {"tipo": "Activar_bot"}
                servidor_bot.sendall(json.dumps(mensaje).encode('utf-8'))
                time.sleep(0.1)
            except:
                print("[DENEGADO]: No se pudo conectar con el bot")
                respuesta = {"tipo": "denegado", "razon": "no se pudo conectar con el bot"}
                self.enviar_respuesta(respuesta)

    # El cliente se asigna un nombre y selecciona un color {"tipo": "seleccion_color", "nombre": "Johan", "color": "Blue"}
    def procesar_seleccion_color(self, informacion):
        # Se extraen los argumentos
        try:
            nombre = informacion["nombre"]
            color = informacion["color"]
        except:
            print("[DENEGADO]: No se especifico el nombre o el color")
            respuesta = {"tipo": "denegado", "razon": "no se especifico el nombre o el color"}
            self.enviar_respuesta(respuesta)
            return
        
        # Se valida la congruencia de los argumentos
        respuesta = None
        if self.nombre != "" and self.color != "":
            respuesta = {"tipo": "denegado", "razon": "ya seleccionaste un color"}
        elif nombre == "" or color == "" or nombre == None or color == None:
            respuesta = {"tipo": "denegado", "razon": "no seleccionaste un color"}   
        elif color not in ["Yellow", "Blue", "Green", "Red"]:
            respuesta = {"tipo": "denegado", "razon": "color no valido"}
        elif not colores_disponibles[color]:
            respuesta = {"tipo": "denegado", "razon": f"el color {color} no esta disponible"}

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            print(f"[DENEGADO]: {respuesta['razon']}")
            self.enviar_respuesta(respuesta)
        else:
            colores_disponibles[color] = False
            self.nombre = nombre
            self.color = color
            # Se envia la informacion de la partida actualizada a todos los clientes
            mensaje = informacion_partida()
            broadcast(mensaje)

    # El cliente quiere iniciar la partida {"tipo": "solicitud_iniciar_partida"}
    def procesar_solicitud_iniciar_partida(self, informacion):     
        # Se valida que el cliente haya seleccionado un color
        respuesta = None
        if self.nombre == "" or self.color == "":
            respuesta = {"tipo": "denegado", "razon": "no seleccionaste un color"}

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            print(f"[DENEGADO]: {respuesta['razon']}")
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
        try:
            D1 = informacion["dados"]["D1"]
            D2 = informacion["dados"]["D2"]
        except:
            print("[DENEGADO]: No se especifico los dados")
            respuesta = {"tipo": "denegado", "razon": "no se especifico los dados"}
            self.enviar_respuesta(respuesta)
            return
        
        # Se valida la congruencia de los argumentos
        respuesta = None
        if not isinstance(D1, int) or not isinstance(D2, int) or not (1 <= D1 <= 6) or not (1 <= D2 <= 6):
            respuesta = {"tipo": "denegado", "razon": "dados no validos"}
        
        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            print(f"[DENEGADO]: {respuesta['razon']}")
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
                if D1 == D2:
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
                        # Se envia la informacion de la partida actualizada a todos los clientes
                        mensaje = informacion_partida()
                        broadcast(mensaje)
                    elif self.fichas_carcel():
                        # Se actualiza la solicitud esperada
                        solicitud_esperada = "sacar_carcel"
                        # Se envia la informacion de la partida actualizada a todos los clientes
                        mensaje = informacion_partida()
                        broadcast(mensaje)
                    else:
                        # Se actualiza la solicitud esperada
                        solicitud_esperada = "mover_ficha"
                        # Se envia la informacion de la partida actualizada a todos los clientes
                        mensaje = informacion_partida()
                        broadcast(mensaje)

                # No saca par
                else:
                    # Se reinicia el contador de pares seguidos
                    pares_seguidos = 0
                    if self.comprobar_carcel():
                        # Se actualiza los turnos
                        if self.turnos == 0:
                            # Se actualiza la solicitud esperada
                            solicitud_esperada = "lanzar_dados"
                            # Se actualiza el turno
                            siguiente_turno()
                            # Se envia la informacion de la partida actualizada a todos los clientes
                            mensaje = informacion_partida()
                            broadcast(mensaje)
                        else:
                            self.turnos -= 1
                            # Se actualiza la solicitud esperada
                            solicitud_esperada = "lanzar_dados"
                            # Se envia la informacion de la partida actualizada a todos los clientes
                            mensaje = informacion_partida()
                            broadcast(mensaje)

                    else:
                        # Se actualiza la solicitud esperada
                        solicitud_esperada = "mover_ficha"
                        # Se envia la informacion de la partida actualizada a todos los clientes
                        mensaje = informacion_partida()
                        broadcast(mensaje)

    # El cliente saca una ficha del tablero {"tipo": "sacar_ficha", "ficha": "F1"}
    def procesar_sacar_ficha(self, informacion):
        # Variables globales
        global solicitud_esperada, estado_partida, turno_actual, hilos_clientes, ultima_ficha

        # Se extraen los argumentos
        try:
            ficha = informacion["ficha"]
        except:
            print("[DENEGADO]: No se especifico la ficha")
            respuesta = {"tipo": "denegado", "razon": "no se especifico la ficha"}
            self.enviar_respuesta(respuesta)
            return

        # Se valida la congruencia de los argumentos
        respuesta = None
        if ficha not in self.fichas:
            respuesta = {"tipo": "denegado", "razon": "ficha no valida"}
        elif self.fichas[ficha] == "Meta":
            respuesta = {"tipo": "denegado", "razon": "ficha en meta"}
        
        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            print(f"[DENEGADO]: {respuesta['razon']}")
            self.enviar_respuesta(respuesta)
        else:
            # Se actualiza el ultimo movimiento
            ultima_ficha = ficha
            # Se actualiza la posicion de la ficha
            self.fichas[ficha] = "Meta"
            # Se actualiza la posicion de la posicion
            self.contadores_fichas[ficha] = 71
            # Se comprueba si todas las fichas estan en la meta
            if self.comprobar_meta():
                # Se imprime el mensaje en el servidor
                print(f"[SERVIDOR: EL JUGADOR {self.color} HA GANADO LA PARTIDA]")
                # Se actualiza el estado de la partida
                estado_partida = "finalizada"
                # Se actualiza la solicitud esperada
                solicitud_esperada = ""
                # Se actualiza el turno actual
                turno_actual = ""
                # Se envia la informacion de la partida actualizada a todos los clientes
                mensaje = informacion_partida()
                broadcast(mensaje)
                # Se envia el mensaje a todos los clientes
                mensaje = {"tipo": "finalizar", "ganador": self.color}
                broadcast(mensaje)
                # Se elimina de la lista de hilos
                hilos_clientes.remove(self)
                # Se cierran las conexiones de los clientes
                for cliente in hilos_clientes:
                    cliente.connection.close()
                # Se añade el hilo a la lista de hilos
                hilos_clientes.append(self)
                # Se termina la conexion
                self.connection.close()
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
        global solicitud_esperada, ultima_ficha

        # Se extraen los argumentos
        try:
            ficha = informacion["ficha"]
        except:
            print("[DENEGADO]: No se especifico la ficha")
            respuesta = {"tipo": "denegado", "razon": "no se especifico la ficha"}
            self.enviar_respuesta(respuesta)
            return

        # Se valida la congruencia de los argumentos
        respuesta = None
        if ficha not in self.fichas:
            respuesta = {"tipo": "denegado", "razon": "ficha no valida"}
        elif self.fichas[ficha] != "Carcel":
            print("[SOLUCIONANDO ERROR]: Ficha no esta en la carcel")
            for ficha_carcel, posicion in reversed(list(self.fichas.items())):
                if posicion == "Carcel":
                    ficha = ficha_carcel
                    break
            print("[ERROR SOLUCIONADO]: Ficha " + ficha + " seleccionada")

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            print(f"[DENEGADO]: {respuesta['razon']}")
            self.enviar_respuesta(respuesta)
        else:
            # Se actualiza el ultimo movimiento
            ultima_ficha = ficha
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
        global estado_partida, hilos_clientes, solicitud_esperada, turno_actual, hilos_clientes, ultima_ficha

        # Se extraen los argumentos
        try:
            ficha = informacion["ficha"]
        except:
            print("[DENEGADO]: No se especifico la ficha")
            respuesta = {"tipo": "denegado", "razon": "no se especifico la ficha"}
            self.enviar_respuesta(respuesta)
            return
        
        # Se valida la congruencia de los argumentos
        respuesta = None
        if ficha not in self.fichas:
            respuesta = {"tipo": "denegado", "razon": "ficha no valida"}
        elif self.fichas[ficha] == "Carcel":
            respuesta = {"tipo": "denegado", "razon": "la ficha esta en la carcel"}
        elif self.fichas[ficha] == "Meta":
            respuesta = {"tipo": "denegado", "razon": "la ficha esta en la meta"}

        # Se rechaza o se ejecuta la solicitud
        if respuesta:
            print(f"[DENEGADO]: {respuesta['razon']}")
            self.enviar_respuesta(respuesta)
        else:
            # Se actualiza el ultimo movimiento
            ultima_ficha = ficha
            
            # Se calcula la nueva posicion
            dados_suma = ultimos_dados["D1"] + ultimos_dados["D2"]
            nueva_posicion = self.fichas[ficha] + dados_suma
            nuevo_contador = self.contadores_fichas[ficha] + dados_suma

            # Llegó a la meta (aunque se exceda)
            if nuevo_contador >= 71: # and nueva_posicion >= 77:
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
                if not self.comprobar_seguro(nueva_posicion):
                    for cliente in hilos_clientes:
                        if cliente.color != self.color:
                            for ficha_oponente, posicion_oponente in cliente.fichas.items():
                                if posicion_oponente == nueva_posicion:
                                    cliente.fichas[ficha_oponente] = "Carcel"
                                    cliente.contadores_fichas[ficha_oponente] = 0

            # Se actualiza la posicion de la ficha
            self.fichas[ficha] = nueva_posicion
            # Se actualiza el contador de la ficha
            self.contadores_fichas[ficha] = nuevo_contador

            # Se comprueba si todas las fichas estan en la meta
            if self.comprobar_meta():
                # Se imprime el mensaje en el servidor
                print(f"[SERVIDOR: EL JUGADOR {self.color} HA GANADO LA PARTIDA]")
                # Se actualiza el estado de la partida
                estado_partida = "finalizada"
                # Se actualiza la solicitud esperada
                solicitud_esperada = ""
                # Se actualiza el turno actual
                turno_actual = ""
                # Se envia la informacion de la partida actualizada a todos los clientes
                mensaje = informacion_partida()
                broadcast(mensaje)
                # Se envia el mensaje a todos los clientes
                mensaje = {"tipo": "finalizar", "ganador": self.color}
                broadcast(mensaje)
                # Se elimina de la lista de hilos
                hilos_clientes.remove(self)
                # Se cierran las conexiones de los clientes
                for cliente in hilos_clientes:
                    cliente.connection.close()
                # Se añade el hilo a la lista de hilos
                hilos_clientes.append(self)
                # Se termina la conexion
                self.connection.close()
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
            if posicion != "Carcel" and posicion != "Meta":
                return False
        return True

    # Funcion que comprueba si tiene alguna ficha en la carcel
    def fichas_carcel(self):
        for ficha in self.fichas:
            if self.fichas[ficha] == "Carcel":
                return True
        return False

    # Funcion que comprueba si la ficha esta en casilla de seguro
    def comprobar_seguro(self, nueva_posicion):
        if nueva_posicion in [5,12,17,22,26,34,39,46,51,56,63,68]:
            return True
        return False

    # Funcion para enviar una respuesta al cliente
    def enviar_respuesta(self, informacion):
        try:
            respuesta = json.dumps(informacion)
            self.connection.sendall(respuesta.encode('utf-8'))
        except:
            print(f"(ERROR): No se pudo enviar la respuesta al cliente {self.address} con el mensaje ({informacion})")

    # Funcion para cerrar la conexion del cliente
    def cerrar_conexion(self):
        # Variables globales
        global hilos_clientes, estado_partida, orden_turnos, solicitud_esperada, pares_seguidos, turno_actual

        # Se termina la conexion
        self.connection.close()

        # Se elimina el cliente de la lista de hilos
        hilos_clientes.remove(self)

        # Se envia el mensaje a todos los clientes
        mensaje = {"tipo": "desconexion", "cliente": self.address, "jugadores": len(hilos_clientes), "estado_partida" : estado_partida}
        broadcast(mensaje)

        if estado_partida == "lobby":
            # El color del cliente se vuelve a poner disponible
            if self.color in ["Yellow", "Blue", "Green", "Red"]:
                colores_disponibles[self.color] = True
            # Se envia la informacion de la partida actualizada a todos los clientes
            mensaje = informacion_partida()
            broadcast(mensaje)
            # Se comprueba si se puede iniciar la partida
            iniciar_partida()
            
        elif estado_partida == "turnos":
            if len(hilos_clientes) < 2:
                ganador = hilos_clientes[0]
                # Se imprime el mensaje en el servidor
                print(f"[SERVIDOR: EL JUGADOR {ganador.color} HA GANADO LA PARTIDA]")
                # Se actualiza el estado de la partida
                estado_partida = "finalizada"
                # Se actualiza la solicitud esperada
                solicitud_esperada = ""
                # Se actualiza el turno actual
                turno_actual = ""
                # Se envia la informacion de la partida actualizada a todos los clientes
                mensaje = informacion_partida()
                broadcast(mensaje)
                # Se envia el mensaje a todos los clientes
                mensaje = {"tipo": "finalizar", "ganador": ganador.color}
                broadcast(mensaje)
                # Se cierra la conexion del ultimo cliente
                ganador.connection.close()
                # Se añade el hilo a la lista de hilos
                hilos_clientes.append(self)
            else:
                # Se comprueba si el cliente es el turno actual
                if self.color == turno_actual:
                    if len(registro_dados) == len(orden_turnos) - 1:
                        # Se elimina de la lista de turnos
                        orden_turnos.remove(self.color)
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
                else: 
                    # Se elimina de la lista de turnos
                    orden_turnos.remove(self.color)
                    # Se elimina del diccinario de registro de dados
                    if self.color in registro_dados:
                        del registro_dados[self.color]
                    # Se envia la informacion de la partida actualizada a todos los clientes
                    mensaje = informacion_partida()
                    broadcast(mensaje)

        elif estado_partida == "juego":
            if len(hilos_clientes) < 2:
                ganador = hilos_clientes[0]
                # Se imprime el mensaje en el servidor
                print(f"[SERVIDOR: EL JUGADOR {ganador.color} HA GANADO LA PARTIDA]")
                # Se actualiza el estado de la partida
                estado_partida = "finalizada"
                # Se actualiza la solicitud esperada
                solicitud_esperada = ""
                # Se actualiza el turno actual
                turno_actual = ""
                # Se envia la informacion de la partida actualizada a todos los clientes
                mensaje = informacion_partida()
                broadcast(mensaje)
                # Se envia el mensaje a todos los clientes
                mensaje = {"tipo": "finalizar", "ganador": ganador.color}
                broadcast(mensaje)
                # Se cierra la conexion del ultimo cliente
                ganador.connection.close()
                # Se añade el hilo a la lista de hilos
                hilos_clientes.append(self)
            else:
                # Se comprueba si el cliente es el turno actual
                if self.color == turno_actual:
                    # Se reinicia el contador de pares seguidos
                    pares_seguidos = 0
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
                    # Se imprime el mensaje en el servidor
                    if self.color == "":
                        print(f"[{self.address}]: Desconexión tipo (1)")
                    else: 
                        print(f"[{self.address}, {self.color}]: Desconexión tipo (1)")
                    # Se termina la conexion
                    lock.acquire()
                    if estado_partida != "finalizada" and self in hilos_clientes:
                        self.cerrar_conexion()
                    if self in hilos_clientes:
                        hilos_clientes.remove(self)
                    lock.release()
                    # Se termina el hilo
                    print(f"[{self.address}]: Hilo terminado")
                    break
            except:
                # Se imprime el mensaje en el servidor
                if self.color == "":
                    print(f"[{self.address}]: Desconexión tipo (2)")
                else: 
                    print(f"[{self.address}, {self.color}]: Desconexión tipo (2)")
                # Se termina la conexion
                lock.acquire()
                if estado_partida != "finalizada" and self in hilos_clientes:
                    self.cerrar_conexion()
                if self in hilos_clientes:
                    hilos_clientes.remove(self)
                lock.release()
                # Se termina el hilo
                print(f"[{self.address}]: Hilo terminado")
                break

# Funcion para enviar un mensaje a todos los clientes
def broadcast(mensaje):
    global id_broadcast
    # Se agrega el ID al broadcast
    if "id_broadcast" in mensaje:
        if mensaje["estado_partida"] != "lobby":
            id_broadcast += 1
            mensaje["id_broadcast"] = id_broadcast
    for client in hilos_clientes:
        client.enviar_respuesta(mensaje)
    # Esperar 0.1 segundos para evitar que se junten los mensajes
    time.sleep(0.1)    

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
            # Se imprime el mensaje en el servidor
            print("[PARTIDA INICIADA]")
            # Se actualiza el estado de la partida
            estado_partida = "turnos"
            solicitud_esperada = "lanzar_dados"
            # Se selecciona el primer turno
            primer_turno = hilos_clientes[0].color
            # Se ordenan los turnos segun el orden de los colores
            ordenar_turnos(primer_turno)
            # Se envia la informacion de la partida actualizada a todos los clientes
            mensaje = informacion_partida()
            broadcast(mensaje)

# Funcion que retorna la informacion de la partida
def informacion_partida():
    # Se crea el diccionario con la informacion de la partida
    partida = {
        "id_broadcast" : id_broadcast,
        "turno_actual" : turno_actual,
        "solicitud_esperada" : solicitud_esperada,
        "estado_partida" : estado_partida,
        "ultimos_dados" : ultimos_dados,
        "ultima_ficha" : ultima_ficha,
        "ultimo_turno" : ultimo_turno,
    }
    # Se agrega la informacion de cada cliente
    jugadores = []
    for cliente in hilos_clientes:
        informacion_cliente = {
                "nombre": cliente.nombre,
                "color": cliente.color,
                "fichas": cliente.fichas,
                "contadores_fichas": cliente.contadores_fichas,
            }
        jugadores.append(informacion_cliente)
    partida["jugadores"] = jugadores
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
    global turno_actual, ultimo_turno, orden_turnos
    # Se actualiza el ultimo turno
    ultimo_turno = turno_actual

    # Se valida si el turno actual es el ultimo
    if turno_actual in orden_turnos:
        # Se obtiene el indice del turno actual
        indice_actual = orden_turnos.index(turno_actual)
        # Se obtiene el indice del siguiente turno
        indice_siguiente = (indice_actual + 1) % len(orden_turnos)
        # Se actualiza el turno actual
        turno_actual = orden_turnos[indice_siguiente]
    else:
        # Se actualiza el turno actual
        turno_actual = orden_turnos[0]

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
    global orden_turnos, registro_dados, estado_partida
    # Se busca el jugador con el valor maximo
    primer_lugar = mayor_suma(registro_dados)
    # Si hay un jugador con el valor maximo, se asignan los turnos a su derecha
    if len(primer_lugar) == 1:
        # Se imprime el mensaje en el servidor
        print(f"[TURNOS DEFINIDOS ({primer_lugar[0]})]")
        # Se ordenan los turnos a partir del jugador con el valor maximo
        ordenar_turnos(primer_lugar[0])
        estado_partida = "juego"
        # Se envia la informacion de la partida actualizada a todos los clientes
        mensaje = informacion_partida()
        broadcast(mensaje)
    # Si hay un empate con el valor maximo, se debe hacer un desempate
    else:
        # Se reasignan los turnos para que solo lancen los jugadores del empate
        orden_turnos = [color for color in orden_turnos if color in primer_lugar]
        # Se imprime el mensaje en el servidor
        print(f"[EMPATE DE TURNOS ({orden_turnos})]")
        # Se limpia el registro de lanzamientos
        registro_dados.clear()
        # Se actualiza el turn
        siguiente_turno()
        # Se envia la informacion de la partida actualizada a todos los clientes
        mensaje = informacion_partida()
        broadcast(mensaje)

# Funcion que reinicia la partida (expulsa los jugadores y reinicia las variables)
def reiniciar_partida():
    # Se importan las variables globales
    global id_broadcast, ultima_ficha, ultimo_turno, hilos_clientes, colores_disponibles, turno_actual, orden_turnos, estado_partida, solicitud_esperada, ultimos_dados, registro_dados, pares_seguidos

    while True:
        if estado_partida == "finalizada":
            # Se cierran los hilos de los clientes
            for cliente in hilos_clientes:
                cliente.join()

            # Se imprime el mensaje en el servidor
            print("[PARTIDA FINALIZADA]")

            # Se inicializan las variables globales para el proximo juego
            id_broadcast = 0 # Identificador de los mensajes broadcast
            hilos_clientes = [] # Hilos de los clientes
            colores_disponibles = {"Yellow": True , "Blue": True, "Green": True, "Red": True} # Disponibilidad de los colores
            turno_actual = "" # Color del jugador con el turno actual
            orden_turnos = [] # Orden de los turnos en la partida
            ultima_ficha = "" # Ultima ficha movida
            ultimo_turno = "" # Color del jugador del ultimo turno
            ultimos_dados = {"D1" : 0, "D2" : 0} # Valor de los dados de la ultima jugada (1-6)
            registro_dados = {} # Registro de los dados lanzados en una ronda
            pares_seguidos = 0 # Contador de los pares seguidos por un jugador
            solicitud_esperada = "" # Indica la solicitud esperada de la ronda (lanzar_dados, sacar_ficha, mover_ficha)
            estado_partida = "lobby" # Indica el estado actual del juego (lobby, turnos, juego)

            # Se imprime el mensaje en el servidor
            print("[PARTIDA REINICIADA]")

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
            print(f"({address}): Conexión rechazada por ({respuesta})")
            connection.sendall(respuesta.encode('utf-8'))
            connection.close()
        else:
            # Se imprime el mensaje en el servidor
            print(f"[{address}]: Conexión establecida")
            # Se envia el mensaje a todos los clientes
            mensaje = {"tipo": "conexion", "cliente": address, "jugadores": len(hilos_clientes), "estado_partida" : estado_partida}
            broadcast(mensaje)
            # Crea un hilo para manejar al cliente
            thread = Cliente(connection, address)
            # Agrega el hilo a la lista de hilos
            hilos_clientes.append(thread)
            # Inicia el hilo
            thread.start()

# Crear un objeto de bloqueo
lock = threading.Lock()

# Se crea el socket para recibir clientes
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((IP_SERVER_PRIVADA, PORT_SERVER))
servidor.listen(10)

# Se imprime el mensaje en el servidor
print(f"[SERVIDOR INICIADO ({IP_SERVER_PRIVADA}:{PORT_SERVER})]")

# Se inicializan las variables globales
id_broadcast = 0 # Identificador de los mensajes broadcast
hilos_clientes = [] # Hilos de los clientes
colores_disponibles = {"Yellow": True , "Blue": True, "Green": True, "Red": True} # Disponibilidad de los colores
turno_actual = "" # Color del jugador con el turno actual
orden_turnos = [] # Orden de los turnos en la partida
ultima_ficha = "" # Ultima ficha movida
ultimo_turno = "" # Color del jugador del ultimo turno
ultimos_dados = {"D1" : 0, "D2" : 0} # Valor de los dados de la ultima jugada (1-6)
registro_dados = {} # Registro de los dados lanzados en una ronda
pares_seguidos = 0 # Contador de los pares seguidos por un jugador
solicitud_esperada = "" # Indica la solicitud esperada de la ronda (lanzar_dados, sacar_ficha, mover_ficha)
estado_partida = "lobby" # Indica el estado actual del juego (lobby, turnos, juego)

# Hilo que actua como receptor de clientes
thread = threading.Thread(target=recibir_clientes)

# Hilo que reinicia la partida
thread2 = threading.Thread(target=reiniciar_partida)

# Iniciar el hilo receptor de clientes
thread.start()

# Iniciar el hilo receptor de clientes
thread2.start()

# Esperar a que el hilo receptor de clientes finalice
thread.join()

# Esperar a que el hilo de reinicio de la partida finalice
thread2.join()

# Se cierra el socket del servidor
servidor.close()

# Se imprime el mensaje en el servidor
print("[SERVIDOR FINALIZADO]")

