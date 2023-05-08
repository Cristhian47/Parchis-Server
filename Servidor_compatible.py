import socket
import json

HOST = 'localhost'  # El host del servidor
PORT = 8888        # El puerto del servidor

# Crea un socket y lo vincula al host y al puerto especificados
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Servidor esperando conexiones en {HOST}:{PORT}...")

    # Espera a que un cliente se conecte
    conn, addr = s.accept()
    with conn:
        print('Conexión establecida por', addr)

        # Recibe los datos del cliente
        data = conn.recv(1024)
        # Decodifica el mensaje JSON
        msg = json.loads(data.decode('utf-8'))
        print(f"Mensaje recibido: {msg}")

        # Procesa los datos
        respuesta = {"resultado": msg["valor1"] + msg["valor2"]}

        # Codifica la respuesta en formato JSON
        respuesta_json = json.dumps(respuesta)
        print(f"Respuesta enviada: {respuesta_json}")

        # Envía la respuesta al cliente
        conn.sendall(respuesta_json.encode('utf-8'))
