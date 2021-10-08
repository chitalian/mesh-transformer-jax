from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import logging
import os
import uuid
import json
DEFAULT_HOSTNAME = '0.0.0.0'
DEFAULT_PORT = 8789
OUTPUT_DIR = 'tmp_output'
MAX_CHUNK_SIZE=1024
os.makedirs(OUTPUT_DIR, exist_ok=True)
from server_queue import Queue, QueueException, QueueWorker
from time import sleep
import threading
from server_worker import ServerWorker as Worker

QUEUE = Queue(Worker)

class ServerHandler(BaseHTTPRequestHandler):
    def _set_response(self, content_type='text/html'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def send_back_text(self, text: str):
        self._set_response()
        self.wfile.write(text.encode('utf-8'))

    def do_GET(self):
        '''
        supports
        <url>/base_key/status
        <url>/base_key/result
        '''
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        base_key = os.path.basename(os.path.dirname(self.path))
        if os.path.basename(self.path) == 'status':
            status: str = QUEUE.get_status(base_key)
            self.send_back_text(status)
        elif os.path.basename(self.path) == 'result':
            try:
                result: str = QUEUE.get_result(base_key)
                self.send_back_text(result)
            except QueueException as e:
                self.send_back_text(f"Got Error: {e}")
        else:
            self.send_back_text(f"Unsupported API: {os.path.basename(self.path)}")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        base_url = f"http://{self.headers.get('Host', '<url>')}"
        # print(str(post_data.decode('utf-8')))

        self._set_response()
        base_key = QUEUE.push(post_data)

        # res = f'Loaded new request. Here is your {base_key=}\n\n'
        # res += f'To check the status run\ncurl {base_url}/{base_key}/status\n\n'
        # res += f'To try to get the file run\ncurl {base_url}/{base_key}/result\n\n'
        res = f'{base_key}'

        self.wfile.write(res.encode('utf-8'))

class Server:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
    
    def start(self):
        logging.basicConfig(level=logging.INFO)
        logging.info(f'Starting server on {self.hostname}:{self.port}')
        with HTTPServer((self.hostname, self.port), ServerHandler) as server:
            self.server = server
            server.serve_forever()
        return self

    def stop(self):
        if self.server:
            self.server.server_close()

    def __enter__(self):
        QUEUE.start()
        return self.start()

    def __exit__(self, *args):
        QUEUE.stop()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='fetch and zip files web service')
    parser.add_argument('--port', metavar='p', type=int, default=DEFAULT_PORT,
                        help=f'Port for server to host on. {DEFAULT_PORT=}')
    parser.add_argument('--hostname', metavar='n', type=str, default=DEFAULT_HOSTNAME,
                        help=f'Hostname for the server to run on. {DEFAULT_HOSTNAME=}')

    args = parser.parse_args()
    try:
        from threading import Thread
        QUEUE.start()
        s = Server(args.hostname, args.port)
        s.start()
        # start = s.start
        # t = Thread(target=start, args=())
        # t.start()
    except KeyboardInterrupt:
        logging.info('Stopping server... Please wait threads to close\n')
        s.stop()
        QUEUE.stop()
        logging.info('Stopping server... Please wait threads to close\n')
        exit(1)
        
