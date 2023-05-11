import socket
import threading
import json

# Datos del servidor
HOST = 'localhost'  # El host del servidor
PORT = 8001        # El puerto del servidor

# Conectarse al servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORT))
servidor.listen(5)
print(f"Servidor esperando conexiones en {HOST}:{PORT}...")

# Diccionario para manejar los colores disponibles
colores_disponibles = {"Yellow": True , "Blue": True, "Green": True, "Red": True}

# Lista de hilos para los clientes
hilos_clientes = []

# Quien tiene el turno actual [IP]
turno_actual = None

# Parametro de parada para el hilo de recibir clientes
iniciar_partida = False

# Diccionario para el valor de los dados de la ultima jugada [1-6,1-6]
dados = {
    "d1" : None,
    "d2" : None
    }

# Clase para manejar a los clientes
class Cliente(threading.Thread):
    def __init__(self, connection, address, turno):
        super(Cliente, self).__init__()
        self.connection = connection
        self.ip, self.puerto = address
        self.nombre = ""
        self.color = ""
        self.turno = turno
        self.aprobacion = False
        self.f1 = 0
        self.f2 = 0
        self.f3 = 0
        self.f4 = 0
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

        # El cliente selecciona un color
        elif informacion["tipo"] == "seleccion_color":
            if colores_disponibles[informacion["color"]]:
                colores_disponibles[informacion["color"]] = False
                self.name = informacion["nombre"]
                self.color = informacion["color"]
                respuesta = {"color": informacion["color"], "disponible": True}
                self.enviar_respuesta(respuesta)
            else:
                respuesta = {"color": informacion["color"], "disponible": False}
                self.enviar_respuesta(respuesta)

        # El cliente quiere iniciar la partida
        elif informacion["tipo"] == "solicitud_iniciar_partida":
            self.aprobacion = True
            respuesta = {"jugador": self.ip, "aprobacion": True}
            self.enviar_respuesta(respuesta)

        # ¿El cliente solicita la informacion de la partida?
        elif informacion["tipo"] == "solicitud_informacion_partida":
            respuesta = informacion_partida()
            self.enviar_respuesta(respuesta)

        # ¿El cliente solicita lanzar los dados?
        elif informacion["tipo"] == "solicitud_turno":
            respuesta = True if self.turno == turno_actual else False
            self.enviar_respuesta(respuesta)

    # Funcion para enviar la informacion actual del cliente
    def informacion(self):
        respuesta = {
            self.ip : {
                    "nombre": self.nombre,
                    "color": self.color,
                    "turno": self.turno,
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
        "dados" : dados,
    }
    for cliente in hilos_clientes:
        partida.update(cliente.informacion())
    return partida

# Funcion que retorna la IP del cliente que tiene el turno
def buscar_turno(turno):
    for cliente in hilos_clientes:
        if cliente.turno == turno:
            return cliente

# Funcion que valida si todos los usuarios (minimo 2) quieren iniciar la partida
def aprobacion_partida():
    if len(hilos_clientes) >= 2:
        aprobaciones = 0
        for cliente in hilos_clientes:
            if cliente.aprobacion == True:
                aprobaciones += 1
        if aprobaciones == len(hilos_clientes):
            return True
    return False

# Funcion que actua como receptor de clientes (se ejecuta en un hilo)
def recibir_clientes():
    turno = 1
    while True:
        if len(hilos_clientes) < 4 and iniciar_partida == False:
                # Espera a que un cliente se conecte
                connection, address = servidor.accept()
                print('Conexión establecida por', address)
                mensaje = "Conexión establecida con el servidor."
                connection.sendall(mensaje.encode('utf-8'))

                # Crea un hilo para manejar al cliente
                thread = Cliente(connection, address, turno)
                hilos_clientes.append(thread)
                thread.start()
                turno += 1
        else:
            connection, address = servidor.accept()
            mensaje = "No se pueden aceptar más clientes"
            connection.sendall(mensaje.encode('utf-8'))
            connection.close()

# Hilo que actua como receptor de clientes
thread = threading.Thread(target=recibir_clientes)
thread.start()

# Ciclo principal de juego  
while True:
    # Si hay 2 o más clientes, se puede iniciar la partida
    while True: 
        iniciar_partida = aprobacion_partida()
        if iniciar_partida == True:
            mensaje = "Partida iniciada"
            broadcast(mensaje)
            break
            
    # Se definen los turnos lanzando el dado (se lanzan por orden de llegada)
    while True:
        break

    # Una vez definidos los turnos, se inicia el juego
    while True:
        break