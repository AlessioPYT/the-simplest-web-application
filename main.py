import json
import os
import threading
import socket
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


STATIC_DIR = 'static'
STORAGE_DIR = 'storage'


HTTP_PORT = 3000
SOCKET_PORT = 5000


DATA_FILE_PATH = os.path.join(STORAGE_DIR, 'data.json')


if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)


if not os.path.isfile(DATA_FILE_PATH):
    with open(DATA_FILE_PATH, 'w') as f:
        json.dump({}, f)


class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/':
            self.path = 'index.html'
        elif parsed_path.path == '/message':
            self.path = 'message.html'
        elif parsed_path.startswith('/static/'):
            self.path = self.path[1:] 
        else:
            self.path = 'error.html'
        
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/submit-message':
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = parse_qs(post_data.decode('utf-8'))

            username = params.get('username', [''])[0]
            message = params.get('message', [''])[0]

            if username and message:
                
                send_to_socket_server({'username': username, 'message': message})

            
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_error(404, 'Not Found')

def run_http_server():
    server_address = ('', HTTP_PORT)
    httpd = HTTPServer(server_address, MyHTTPRequestHandler)
    print(f'HTTP Server running on port {HTTP_PORT}')
    httpd.serve_forever()


def socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', SOCKET_PORT))
    print(f'Socket Server running on port {SOCKET_PORT}')

    while True:
        data, _ = sock.recvfrom(4096)
        if data:
            message_dict = json.loads(data.decode('utf-8'))
            timestamp = str(datetime.now())
            with open(DATA_FILE_PATH, 'r') as f:
                existing_data = json.load(f)
            existing_data[timestamp] = message_dict
            with open(DATA_FILE_PATH, 'w') as f:
                json.dump(existing_data, f, indent=2)


def send_to_socket_server(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(data).encode('utf-8'), ('localhost', SOCKET_PORT))
    sock.close()


if __name__ == '__main__':
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()

    socket_thread = threading.Thread(target=socket_server)
    socket_thread.start()
