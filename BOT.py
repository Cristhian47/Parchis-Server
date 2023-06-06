import socket
import threading
import json
import time
import random
import IP
from queue import Queue
import queue

#Bots iniciaados para funcionar
list_bots = []

#conexion para el bot
servidor_bot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor_bot.bind((IP.HOST_BOT, IP.PORT_BOT))
servidor_bot.listen(10)

class BOT(threading.Thread):
    def __init__(self):
        super(BOT, self).__init__()
        self.iniciar_partida = False
        self.seguras = [5,12,17,22,26,34,39,46,51,56,63,68]
        self.casillas = list(range(1, 69))
        self.bot = None
        self.contador_pares = 0
        self.nombre = None
        self.color = None
        self.d1 = None
        self.d2 = None
    #Activamos la conexion con el servidor principal
    def activar_conexion(self):
        self.bot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bot.connect((IP.HOST_SERVER, IP.PORT_SERVER))

    # Que es lo  que viene en el mensaje
    def procesar_informacion(self, informacion):
        if informacion == "Rechazado: La partida ya inició.":
            self.cerrar_conexion()

        elif 'tipo' in informacion.keys():
            if informacion['tipo'] == "conexion":
                print(informacion)
            elif informacion['tipo'] == "desconexion":
                print(informacion)
            elif informacion['tipo'] == "finalizar":
                print(f"{self.nombre} desconectado")
                self.cerrar_conexion()

        elif 'turno_actual' in informacion.keys():
            if informacion['estado_partida'] == "lobby":
                if self.iniciar_partida == False:
                    informacion = {"tipo": "solicitud_iniciar_partida"}
                    self.iniciar_partida = True
                    self.enviar_respuesta(informacion)
            elif informacion['estado_partida'] == "turnos":
                if informacion['turno_actual'] == self.color:
                    self.lanzar_dados()
                    print(f"({self.nombre}): Lanzando dados")
                    self.d1 = None
                    self.d2 = None
            elif informacion['estado_partida'] == "juego":
                if informacion['turno_actual'] == self.color:
                    dado_1 = informacion['ultimos_dados']['D1']
                    dado_2 = informacion['ultimos_dados']['D2']
                    if dado_1 != self.d1 and dado_2 != self.d2:
                        self.lanzar_dados()
                        print(f"({self.nombre}): Lanzando dados")
                        if self.d1 == self.d2:
                            self.contador_pares += 1
                    elif dado_1 == self.d1 and dado_2 == self.d2:   
                        self.determinar_movimiento(informacion)
                else:
                    self.d1 = None
                    self.d2 = None
                    self.contador_pares = 0
        
    #Funcion para lanzar los dados
    def lanzar_dados(self):
        self.d1 = random.randint(1, 6)
        self.d2 = random.randint(1, 6)
        solicitud = {"tipo": "lanzar_dados", "dados": {"D1": self.d1, "D2": self.d2}}
        self.enviar_respuesta(solicitud)
    
    #Funcion para determinar que hacer con los dados
    def determinar_movimiento(self, informacion_jugadores):
        contador_carcel = 0
        dados_usados = False
        #Determinar si todas las fichas estan en la carcel
        for mi_juego in informacion_jugadores['jugadores']:
            if mi_juego['nombre'] == self.nombre:
                for fichas_mias in mi_juego['fichas'].keys():
                    if mi_juego['fichas'][fichas_mias] == "Carcel":
                        contador_carcel += 1
        
        if contador_carcel != 4 or self.d1 == self.d2:
            print(f"({self.nombre}): Entrando a determinar movimiento")
            #Determinar cuantos pares llevo y si son 3 coronar una ficha
            menor_recorrido = 1000
            if self.contador_pares == 3:
                print(f"({self.nombre}): Estoy pensando en coronar")
                for mi_juego in informacion_jugadores['jugadores']:
                    if mi_juego['nombre'] == self.nombre:
                        for fichas_mias in mi_juego['contadores_fichas'].keys():
                            if mi_juego['fichas'][fichas_mias] != 'Carcel' and mi_juego['fichas'][fichas_mias] != 'Meta':
                                if mi_juego['contadores_fichas'][fichas_mias] < menor_recorrido:
                                    menor_recorrido = mi_juego['contadores_fichas'][fichas_mias]
                                    ficha_coronar = fichas_mias
                                    break
                self.sacar_ficha(ficha_coronar)          
            #Determinar si los dados son pares y sacar de la carcel
            elif self.d1 == self.d2:
                print(f"({self.nombre}): Estoy pensando en sacar de la carcel")
                for mi_juego in informacion_jugadores['jugadores']:
                    if mi_juego['nombre'] == self.nombre:
                        for fichas_mias in mi_juego['fichas'].keys():
                            if mi_juego['fichas'][fichas_mias] == "Carcel":
                                self.sacar_carcel(fichas_mias)
                                dados_usados = True
                                break
                                
            if self.d1 and self.d2 and dados_usados == False:
                print(f"({self.nombre}): Estoy pensando en mover")
                #Determinar que movimiento es mejor, comer, mover, coronar, quedar en seguro 
                suma_dados = self.d1 + self.d2
                if dados_usados == False:
                    Contador_fichas_coronadas = 0
                    #Determinar si puedo coronar una ficha
                    print(f"({self.nombre}): Estoy pensando en coronar moviendo ficha")
                    for mi_juego in informacion_jugadores['jugadores']:
                        if mi_juego['nombre'] == self.nombre:
                            for fichas_mias in mi_juego['contadores_fichas'].keys():
                                if mi_juego['fichas'][fichas_mias] == 'Meta':
                                    Contador_fichas_coronadas += 1
                                elif mi_juego['fichas'][fichas_mias] != 'Carcel' and mi_juego['fichas'][fichas_mias] != 'Meta':
                                    if mi_juego['contadores_fichas'][fichas_mias] + suma_dados >= 71:
                                        dados_usados = True
                                        self.mover_ficha(fichas_mias)
                                        break
                if dados_usados == False:
                    #Determinar si puedo comer una ficha
                    print(f"({self.nombre}): Estoy pensando en comer")
                    posicion_fichas_mias = []

                    for mi_juego in informacion_jugadores['jugadores']:
                        if mi_juego['nombre'] == self.nombre:
                            for fichas_mias in mi_juego['fichas'].keys():
                                if mi_juego['fichas'][fichas_mias] != 'Carcel' and mi_juego['fichas'][fichas_mias] != 'Meta':
                                    if mi_juego['contadores_fichas'][fichas_mias] + suma_dados < 63:
                                        posicion_fichas_mias.append((self.sumar_dados(self.casillas, mi_juego['fichas'][fichas_mias], suma_dados),
                                                                    mi_juego['contadores_fichas'][fichas_mias] + suma_dados , fichas_mias))

                    for rivales in  informacion_jugadores['jugadores']:
                        if rivales['nombre'] != self.nombre:
                            for fichas_rivales in rivales['fichas'].keys():
                                posicion_rival = rivales['fichas'][fichas_rivales]
                                if rivales['contadores_fichas'][fichas_rivales] < 63:
                                    if posicion_rival != 'Carcel' and posicion_rival != 'Meta'and posicion_rival not in self.seguras:
                                        for posicion_mia in posicion_fichas_mias:
                                            if posicion_mia[1] < 63:
                                                if posicion_mia[0] == posicion_rival:
                                                    dados_usados = True
                                                    self.mover_ficha(posicion_mia[2])
                                                    break
                if dados_usados == False:
                    posicion_fichas_mias = []
                    print(f"({self.nombre}): Estoy pensando en mover ficha a seguro")
                    #Determinar si al mover una ficha quedo en seguro contando la escalera
                    for mi_juego in informacion_jugadores['jugadores']:
                        if mi_juego['nombre'] == self.nombre:
                            for fichas_mias in mi_juego['fichas'].keys():
                                if mi_juego['contadores_fichas'][fichas_mias] < 63:
                                    if mi_juego['fichas'][fichas_mias] != 'Carcel' and mi_juego['fichas'][fichas_mias] != 'Meta':
                                        posicion_fichas_mias.append([self.sumar_dados(self.casillas, mi_juego['fichas'][fichas_mias], suma_dados),
                                                                    mi_juego['contadores_fichas'][fichas_mias] + suma_dados , fichas_mias])
                                else:
                                    if mi_juego['fichas'][fichas_mias] != 'Carcel' and mi_juego['fichas'][fichas_mias] != 'Meta':
                                        dados_usados = True
                                        self.mover_ficha(fichas_mias)
                                        break
                    if dados_usados == False:
                        for posicion_mia in posicion_fichas_mias:
                            if posicion_mia[1] >= 63:
                                dados_usados = True
                                self.mover_ficha(posicion_mia[2])
                                break
                            elif posicion_mia[0] in self.seguras:
                                dados_usados = True
                                self.mover_ficha(posicion_mia[2])
                                break
                if dados_usados == False:
                    fichas_posibles = []
                    print(f"({self.nombre}): No se que hacer, movere aleatoriamente")
                    #Si no se cumple ninguna de las anteriores, mover una ficha aleatoria
                    for mi_juego in informacion_jugadores['jugadores']:
                        if mi_juego['nombre'] == self.nombre:
                            for fichas_mias in mi_juego['fichas'].keys():
                                if mi_juego['fichas'][fichas_mias] != 'Carcel' and mi_juego['fichas'][fichas_mias] != 'Meta':
                                    fichas_posibles.append(fichas_mias)
                    print(len(fichas_posibles))
                    print(informacion_jugadores)
                    if len(fichas_posibles) > 0:
                        ficha_aleatoria = random.choice(fichas_posibles)
                        dados_usados = True
                        self.mover_ficha(ficha_aleatoria)
            #Reinicializar los dados
            self.d1 = None
            self.d2 = None
        else:
            self.lanzar_dados()
            print(f"({self.nombre}): lanzando dados")
            if self.d1 == self.d2:
                self.contador_pares += 1    
        
        
    #Funcion para sumar los dados a mi poscion
    def sumar_dados(self, lista, numero_inicial, posiciones):
        indice = lista.index(numero_inicial)  # Obtener el índice del número inicial
        for _ in range(posiciones):
            indice = (indice + 1) % len(lista)  # Actualizar el índice, volviendo al inicio cuando llega al final
        
        return lista[indice]  # Devolver el número en la nueva posición 


    #Funcion para mover la ficha
    def mover_ficha(self, ficha):
        solicitud = {"tipo": "mover_ficha", "ficha": ficha}
        self.enviar_respuesta(solicitud)

    #Funcion para coronar la ficha
    def sacar_ficha(self, ficha):
        solicitud = {"tipo": "sacar_ficha", "ficha": ficha}
        self.enviar_respuesta(solicitud)

    # Funcion para sacar una ficha de la carcel
    def sacar_carcel(self, ficha):
        solicitud = {"tipo": "sacar_carcel", "ficha": ficha}
        self.enviar_respuesta(solicitud)

    # Funcion para enviar una respuesta al cliente
    def enviar_respuesta(self, informacion):
        respuesta = json.dumps(informacion)
        self.bot.sendall(respuesta.encode('utf-8'))
    
    # Funcion para cerrar la conexion
    def cerrar_conexion(self):
        mensaje_cerrar_hilo(self)

    # Funcion que se ejecuta cuando se inicia el hilo
    def run(self):
        self.activar_conexion()
        while self.nombre == None:
            solicitud = {"tipo": "solicitud_color"}
            self.enviar_respuesta(solicitud)
            data = self.bot.recv(4096)
            try:
                data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                print("Error al decodificar JSON:", str(e))
            #Determinar que llegue la informacion correcta
            if 'Yellow' in data.keys():
                for index in data.keys():
                    if data[index] == True:
                        self.color = index
                        break
                self.nombre = "Bot_" + self.color
                solicitud = {"tipo": "seleccion_color", "nombre": self.nombre, "color": self.color}
                self.enviar_respuesta(solicitud)
                break

        #Cola de mensajes
        self.cola_mensajes = Queue()
        self.id_mensaje = 1

        # Crear hilo para manejar mensajes
        hilo_mensajes = threading.Thread(target=self.manejar_mensajes)
        hilo_mensajes.start()

        # Ciclo para recibir mensajes
        while True:
            try:
                data = self.bot.recv(4096).decode('utf-8')
                if data:
                    data = json.loads(data)
                    self.cola_mensajes.put(data)
            except:
                break

    # Funcion para procesar la informacion recibida
    def manejar_mensajes(self):
        while True:
            if not self.cola_mensajes.empty():
                # Procesar mensaje
                data = self.cola_mensajes.get()
                if "id_broadcast" in data:
                    if data['estado_partida'] != "lobby":
                        if data['id_broadcast'] == self.id_mensaje:
                            # Ejecuto la accion del mensaje
                            self.id_mensaje += 1
                            self.procesar_informacion(data)
                        else:
                            # Devuelvo el mensaje a la cola
                            self.cola_mensajes.put(data)
                    else:
                        self.procesar_informacion(data)
                else:
                    self.procesar_informacion(data)

#Cola para peticiones de cerrar hilo}
cola_cerrar_hilo = Queue()

#Funcion para agregar una terminacion de hilo a la cola
def mensaje_cerrar_hilo(bot):
    cola_cerrar_hilo.put(bot)

# Funcion que termina hilos
def cerrar_conexion(): 
    while True:
        bot = cola_cerrar_hilo.get()
        if bot != None:
            for index in list_bots:
                if index == bot:
                    list_bots.remove(index)
        cola_cerrar_hilo.task_done()

cerrar_conexion_hilo = threading.Thread(target=cerrar_conexion)
cerrar_conexion_hilo.start()

#Cola para recibir mensajes
message_queue = queue.Queue()

def handle_message():
    while True:
        informacion = message_queue.get()
        informacion = json.loads(informacion)
        if informacion["tipo"] == "Activar_bot":
            bot = BOT()
            bot.start()
            list_bots.append(bot)
            print(f"Bot activado")
            print("Cantidad de bots activos: ", len(list_bots))
        # Agrega aquí más lógica para manejar diferentes tipos de mensajes
        message_queue.task_done()

def message_handler():
    while True:
        connection, address = servidor_bot.accept()
        informacion = connection.recv(1024).decode('utf-8')
        message_queue.put(informacion)

# Crear un hilo para manejar los mensajes encolados de forma asíncrona
handler_thread = threading.Thread(target=handle_message)
handler_thread.start()

# Crear un conjunto de hilos para procesar los mensajes en la cola
NUM_THREADS = 4  # Puedes ajustar la cantidad de hilos según tus necesidades
for _ in range(NUM_THREADS):
    worker_thread = threading.Thread(target=message_handler)
    worker_thread.start()

