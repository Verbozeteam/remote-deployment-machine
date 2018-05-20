import os
import threading
import sys
import getpass
import websocket
import requests
import json

from config.config import CONFIG
from config.auth import AUTH_CONFIG

class Communicator:
    def __init__(self, on_command):
        self.ws = None
        self.connected = False
        self.token = None
        self.messages_queue = []
        self.on_command = on_command

        self.authenticate()

    def get_machine_info(self):
        return os.uname().nodename

    def authenticate(self):
        auth_info = {
            'username': AUTH_CONFIG.USERNAME,
            'password': AUTH_CONFIG.PASSWORD,
            'machine': self.get_machine_info()
        }
        if auth_info['username'] == '':
            auth_info['username'] = input('Username: ')
        if auth_info['password'] == '':
            auth_info['password'] = getpass.getpass('Password: ')

        print('Authenticating...')

        if CONFIG.NOT_SECURE:
            url = 'http://'
        else:
            url = 'https://'
        url += CONFIG.BASE_URL + '/api/token-auth/'

        r = requests.post(url, auth_info)

        if r.status_code != 200:
            print('Authentication error - try again')
            self.authenticate()

        elif not 'rdm_ws_token' in r.json():
            print('You do not have the right permissions to use this tool')
            sys.exit(0)

        else:
            self.token = r.json()['rdm_ws_token']

    def run(self):
        self.thread = threading.Thread(target=self.initialize_websocket)
        self.thread.start()

    def initialize_websocket(self):
        if CONFIG.NOT_SECURE:
            url = 'ws://'
        else:
            url = 'wss://'
        url += CONFIG.BASE_URL + '/deployment-comm/' + self.token + '/'

        self.ws = websocket.WebSocketApp(url,
            on_message=self.websocket_message,
            on_error=self.websocket_error,
            on_close=self.websocket_close)
        self.ws.on_open = self.websocket_open

        print('Websocket initialized')
        self.ws.run_forever()

    def websocket_open(self, ws):
        print('Connected to server')
        print('Ready to receive commands')

        self.connected = True

        print('Flushing queue', self.messages_queue)
        for message in self.messages_queue:
            self.websocket_send(message)
        self.messages_queue = []

    def websocket_message(self, ws, message):
        print('Websocket message')
        self.on_command(json.loads(message))

    def websocket_send(self, message):
        if self.ws and self.connected:
            print('Sending message', message)
            self.ws.send(json.dumps(message))
        else:
            print('Queueing message', message)
            self.messages_queue.append(message)

    def websocket_error(self, ws, error):
        self.connected = False

    def websocket_close(self, ws):
        print('Disconnected from server')
        self.connected = False
