import socket
import threading
import json
from queue import Queue
import random

# Variable para definir si se juega en local
local = True

# Cambio de IPs 
if local:
    # IP servidor publica
    IP_SERVER_PUBLICA = "localhost"
else:
    # IP servidor publica
    IP_SERVER_PUBLICA = "3.15.208.30"

# Puerto servidor
PORT_SERVER = 8001

# Conectarse al servidor
try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((IP_SERVER_PUBLICA, PORT_SERVER))
except:
    print("Error: No se pudo conectar con el servidor.")
    exit()

cola_mensajes = Queue()
id_mensaje = 1

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
                        procesar_mensaje(mensaje)
                    else:
                        # Devuelvo el mensaje a la cola
                        cola_mensajes.put(mensaje)
                else:
                    procesar_mensaje(mensaje)
            else:
                procesar_mensaje(mensaje)

def procesar_mensaje(mensaje):
    nuevo_mensaje = ""

    if "tipo" in mensaje:
        tipo = mensaje["tipo"]
        if tipo == "conexion":
            cliente = mensaje["cliente"]
            informacion = f"Se ha conectado el cliente {cliente}.\n"
            print("\nMensaje recibido:\n" + informacion)
        elif tipo == "desconexion":
            cliente = mensaje["cliente"]
            jugadores = mensaje["jugadores"]
            informacion = f"Se ha desconectado el cliente {cliente}.\nQuedan {jugadores} jugadores en la partida.\n"
            print("\nMensaje recibido:\n" + informacion)
        elif tipo == "finalizar":
            ganador = mensaje["ganador"]
            informacion = f"La partida ha finalizado.\nEl ganador es {ganador}.\n"
            print("\nMensaje recibido:\n" + informacion)
        elif tipo == "denegado":
            razon = mensaje["razon"]
            informacion = f"La solicitud ha sido denegada.\nRazón: {razon}.\n"
            print("\nMensaje recibido:\n" + informacion)
        else:
            informacion = "Mensaje desconocido\n"
            print("\nMensaje recibido:\n" + informacion)
    else:
        if "turno_actual" in mensaje:
            turno_actual = mensaje["turno_actual"]
            solicitud_esperada = mensaje["solicitud_esperada"]
            estado_partida = mensaje["estado_partida"]
            ultimos_dados = mensaje["ultimos_dados"]
            jugadores = mensaje["jugadores"]
            # Crear mensaje
            nuevo_mensaje = f"El estado de la partida es {estado_partida}.\n"
            if turno_actual != "":
                nuevo_mensaje += f"Es el turno de {turno_actual}.\n"
            if solicitud_esperada != "":
                nuevo_mensaje += f"Se espera la solicitud {solicitud_esperada}.\n"
            if ultimos_dados['D1'] != 0 and ultimos_dados['D2'] != 0:
                nuevo_mensaje += f"\nÚltimos dados lanzados: D1={ultimos_dados['D1']}, D2={ultimos_dados['D2']}.\n"
            # Mostrar jugadores
            for jugador in jugadores:
                nombre = jugador["nombre"]
                color = jugador["color"]
                fichas = jugador["fichas"]
                contadores_fichas = jugador["contadores_fichas"]
                
                nuevo_mensaje += f"\nJugador: {nombre}\n"
                nuevo_mensaje += f"Color: {color}\n"
                nuevo_mensaje += "Fichas:\n"
                for ficha, estado in fichas.items():
                    nuevo_mensaje += f"  {ficha}: {estado}\n"
                nuevo_mensaje += "Contadores de fichas:\n"
                for ficha, contador in contadores_fichas.items():
                    nuevo_mensaje += f"  {ficha}: {contador}\n"
            # Mostrar mensaje
            print("\nMensaje recibido:\n" + nuevo_mensaje)
        elif "Blue" in mensaje:
            blue = mensaje["Blue"]
            yellow = mensaje["Yellow"]
            green = mensaje["Green"]
            red = mensaje["Red"]
            informacion = f"Colores disponibles:\nBlue: {blue}\nYellow: {yellow}\nGreen: {green}\nRed: {red}\n"
            print("\nMensaje recibido:\n" + informacion)
        else:
            informacion = "Mensaje desconocido"
            print("\nMensaje recibido:\n" + informacion)

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
    d1 = random.randint(1,6)
    d2 = random.randint(1,6)
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

def mostrar_menu():
    print("1. solicitud_color")
    print("2. seleccion_color")
    print("3. solicitud_iniciar_partida")
    print("4. solicitud_lanzar_dados")
    print("5. solicitud_sacar_ficha")
    print("6. solicitud_sacar_carcel")
    print("7. solicitud_mover_ficha")
    print("8. solicitud_bot")
    print("\nIngrese una opción... ")

opciones = {
    1: solicitud_color,
    2: seleccion_color,
    3: solicitud_iniciar_partida,
    4: solicitud_lanzar_dados,
    5: solicitud_sacar_ficha,
    6: solicitud_sacar_carcel,
    7: solicitud_mover_ficha,
    8: solicitud_bot
}

mostrar_menu()
while True:
    try:
        solicitud = int(input())
        if solicitud in opciones:
            opciones[solicitud]()
        else:
            print("Error: Opción no válida.")
    except ValueError:
        print("Error: Debes ingresar un número válido.")