
import socket
import threading
import json

HOST = 'localhost'  # El host del servidor
PORT = 8001        # El puerto del servidor

# Conectarse al servidor
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

#Funcion para el hilo de cliente
def receive_messages():
    while True:
        data = cliente.recv(1024).decode('utf-8')
        if data:
            print("Mensaje recibido: " + data)

#Hilo para estar en constante funcionamiento
thread = threading.Thread(target=receive_messages)
thread.start()

#Enviar solicitud de colores disponibles
def solicitud_color():
    solicitud = {"tipo": "solicitud_color"}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))
    
#Enviar solicitud de eleccion de color
def seleccion_color():
    solicitud = {"tipo": "seleccion_color", "nombre": "Johan", "color": "Blue"}
    #solicitud = {"tipo": "seleccion_color", "nombre": "Sarah", "color": "Green"}
    #solicitud = {"tipo": "seleccion_color", "nombre": "Pepe", "color": "Red"}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

#Enviar solicitud de iniciar la partida
def solicitud_iniciar_partida():
    solicitud = {"tipo": "solicitud_iniciar_partida"}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

#Enviar solicitud de lanzar los dados
def solicitud_lanzar_dados():
    solicitud = {"tipo": "lanzar_dados", "dados": {"D1": 1, "D2": 2}}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

while True:
    print("1. solicitud_color")
    print("2. seleccion_color")
    print("3. solicitud_iniciar_partida")
    print("4. solicitud_lanzar_dados")
    solicitud = int(input("\nIngrese tipo de solicitud... "))
    if solicitud == 1:
        solicitud_color()
    elif solicitud == 2:
        seleccion_color()
    elif solicitud == 3:
        solicitud_iniciar_partida()
    elif solicitud == 4:
        solicitud_lanzar_dados()






