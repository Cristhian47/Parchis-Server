import socket
import threading
import json

HOST = '127.0.0.1' # Dirección IP del servidor
PORT = 8080       # Puerto de escucha del servidor

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
def run_server():
    # Creamos el socket del servidor
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Asociamos el socket a una dirección y puerto de escucha
        s.bind((HOST, PORT))
        s.listen()

        # Ciclo principal del servidor
        while True:
            # Esperamos a que llegue una solicitud de un cliente
            conn, addr = s.accept()
            print(f"Conexión aceptada desde {addr}")

            # Creamos un nuevo hilo para manejar la solicitud
            t = threading.Thread(target=handle_request, args=(conn, addr))
            t.start()

if __name__ == '__main__':
    run_server()