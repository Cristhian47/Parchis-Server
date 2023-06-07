
import socket
import threading
import json
from queue import Queue

# Variable para definir si se juega en local
local = True

# Cambio de IPs 
if local:
    # IP servidor publica
    IP_SERVER_PUBLICA = "localhost"
else:
    # IP servidor publica
    IP_SERVER_PUBLICA = "3.17.187.70"

# Puerto servidor
PORT_SERVER = 8001

cola_mensajes = Queue()
id_mensaje = 1

# Conectarse al servidor
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((IP_SERVER_PUBLICA, PORT_SERVER))

#Funcion para el hilo de cliente
def receive_messages():
    while True:
        try:
            mensaje = cliente.recv(1024).decode('utf-8')
            if mensaje:
                mensaje = json.loads(mensaje)
                cola_mensajes.put(mensaje)
        except:
            print("Desconectado del servidor")
            break

def manejar_mensajes():
    global id_mensaje
    while True:
        if not cola_mensajes.empty():
            # Procesar mensaje
            mensaje = cola_mensajes.get()
            if "id_broadcast" in mensaje:
                if mensaje['estado_partida'] != "lobby":
                    if mensaje['id_broadcast'] == id_mensaje:
                        # Ejecuto la accion del mensaje
                        id_mensaje += 1
                        print("Mensaje recibido: ", mensaje, "\n")
                    else:
                        # Devuelvo el mensaje a la cola
                        cola_mensajes.put(mensaje)
                else:
                    print("Mensaje recibido: ", mensaje, "\n")
            else:
                print("Mensaje recibido: ", mensaje, "\n")

#Hilo para estar en constante funcionamiento
thread = threading.Thread(target=receive_messages)
thread2 = threading.Thread(target=manejar_mensajes)
thread.start()
thread2.start()

#Enviar solicitud de colores disponibles
def solicitud_color():
    solicitud = {"tipo": "solicitud_color"}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))
    
#Enviar solicitud de eleccion de color
def seleccion_color():
    nombre = input("Ingrese nombre: ")
    color = input("Ingrese color: ")
    solicitud = {"tipo": "seleccion_color", "nombre": nombre, "color": color}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

#Enviar solicitud de iniciar la partida
def solicitud_iniciar_partida():
    solicitud = {"tipo": "solicitud_iniciar_partida"}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

#Enviar solicitud de lanzar los dados
def solicitud_lanzar_dados():
    d1 = int(input("Ingrese valor del dado 1: "))
    d2 = int(input("Ingrese valor del dado 2: "))
    solicitud = {"tipo": "lanzar_dados", "dados": {"D1": d1, "D2": d2}}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

#Enviar solicitud de sacar ficha del tablero (ficha en estado de meta)
def solicitud_sacar_ficha():
    ficha = input("Ingrese ficha a sacar del tablero: ")
    solicitud = {"tipo": "sacar_ficha", "ficha": ficha}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

#Enviar solicitud de sacar ficha de la carcel
def solicitud_sacar_carcel():
    ficha = input("Ingrese ficha a sacar de la carcel: ")
    solicitud = {"tipo": "sacar_carcel", "ficha": ficha}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

#Enviar solicitud de mover ficha en el tablero
def solicitud_mover_ficha():
    ficha = input("Ingrese ficha a mover en el tablero: ")
    solicitud = {"tipo": "mover_ficha", "ficha": ficha}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

#Enviar solicitud de mover ficha en el tablero
def solicitud_bot():
    solicitud = {"tipo": "solicitud_bot"}
    cliente.sendall(json.dumps(solicitud).encode('utf-8'))

print("1. solicitud_color")
print("2. seleccion_color")
print("3. solicitud_iniciar_partida")
print("4. solicitud_lanzar_dados")
print("5. solicitud_sacar_ficha")
print("6. solicitud_sacar_carcel")
print("7. solicitud_mover_ficha")
print("8. solicitud_bot")
while True:
    solicitud = int(input("\nIngrese tipo de solicitud... "))
    if solicitud == 1:
        solicitud_color()
    elif solicitud == 2:
        seleccion_color()
    elif solicitud == 3:
        solicitud_iniciar_partida()
    elif solicitud == 4:
        solicitud_lanzar_dados()
    elif solicitud == 5:
        solicitud_sacar_ficha()
    elif solicitud == 6:
        solicitud_sacar_carcel()
    elif solicitud == 7:
        solicitud_mover_ficha()
    elif solicitud == 8:
        solicitud_bot()






