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

#Diccionario para manejar los colores disponibles
colores_disponibles = {"Yellow": True , "Blue": True, "Green": True, "Red": True}

#lista de hilos para los clientes
clientes = []
hilos_clientes = []

#Clase para manejar a los clientes
class ManejarCliente(threading.Thread):
    def __init__(self, conn):
        super(ManejarCliente, self).__init__()
        self.conn = conn
        self.nombre = ""
        self.color = ""

    #Que es lo  que viene en el mensaje
    def procesar_informacion(self, msg):
        informacion = json.loads(msg)

        #el cliente solicita los colores disponibles
        if informacion["tipo"] == "solicitud_color":
            respuesta = colores_disponibles
            self.enviar_respuesta(respuesta)
        #el cliente selecciona un color
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

    #Funcion para enviar una respuesta al cliente
    def enviar_respuesta(self, informacion):
        respuesta = json.dumps(informacion)
        self.conn.sendall(respuesta.encode('utf-8'))

    #Funcion que se ejecuta cuando se inicia el hilo
    def run(self):
        while True:
            # Recibe los datos del cliente
            msg = self.conn.recv(1024).decode()
            if msg:
                self.procesar_informacion(msg)
        
    #Funcion para enviar un mensaje a todos los clientes
    def broadcast(self, msg):
            for client in hilos_clientes:
                client.send(msg.encode())
    
#Ciclo para aceptar clientes    
while True:
    if len(hilos_clientes) < 4:
        # Espera a que un cliente se conecte
        conn, addr = servidor.accept()
        print('Conexión establecida por', addr)
        mensaje = "Conexión establecida con el servidor."
        conn.sendall(mensaje.encode('utf-8'))
        # Crea un hilo para manejar al cliente
        thread = ManejarCliente(conn)
        clientes.append(conn)
        hilos_clientes.append(thread)
        thread.start()
    else:
        conn, addr = servidor.accept()
        mensaje = "No se pueden aceptar más clientes"
        conn.sendall(mensaje.encode('utf-8'))
        conn.close()