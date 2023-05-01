from django.http import HttpResponse
from django.http import JsonResponse
import json
from . import settings

def saludo(request):
    return HttpResponse("¡Hola, mundo!")

def get_json_data(request):
    with open(settings.DATA_FILE_PATH, 'r') as f:
        data = json.load(f)

    data_str = json.dumps(data)

    return HttpResponse(data_str)

def get_data_from_json_file():
    with open('data.json', 'r') as f:
        data = json.load(f)
    return data

def serve_json_file(request):
    data = get_data_from_json_file()
    return JsonResponse(data, json_dumps_params={'indent': 2})

import socket
import threading
import json

HOST = '127.0.0.1' # Dirección IP del servidor
PORT = 8000       # Puerto de escucha del servidor

# Datos que se devolverán como respuesta al cliente
data = {'message': '¡Hola, mundo!'}

# Función que se ejecutará en cada hilo
def handle_request(conn, addr):
    # Leemos la solicitud del cliente
    request = conn.recv(1024).decode('utf-8')
    print(f"Solicitud recibida desde {addr}: {request}")

    # Enviamos la respuesta al cliente
    response = json.dumps(data)
    conn.sendall(response.encode('utf-8'))

    # Cerramos la conexión con el cliente
    conn.close()

# Función principal del servidor
def run_server(request):
    # Creamos el socket del servidor

    s = socket.socket()
    #s.bind((HOST, PORT))
    #s.listen()
    #conn, addr = s.accept()
    return HttpResponse(f"Conexión aceptada desde")
   