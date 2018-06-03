import os
import platform
import threading
from time import sleep
import json

from config.config import CONFIG

class FirmwaresManager(threading.Thread):
    def __init__(self, communicator):
        threading.Thread.__init__(self)

        self.firmwares = []
        self.communicator = communicator

        self.directory = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            CONFIG.FIRMWARE_DIR)
        os.makedirs(self.directory, exist_ok=True)

        print('FirmwaresManager initialized')

    def run(self):
        while True:
            self.update_firmwares_list()
            sleep(CONFIG.FIRMWARES_CHECK_INTERVAL)

    def update_firmwares_list(self):
        firmwares = [f for f in os.listdir(self.directory) if not f.startswith('.')]
        firmwares = list(map(lambda f: {'name': f}, firmwares))

        if json.dumps(firmwares) != json.dumps(self.firmwares):
            self.communicator.websocket_send({'firmwares': firmwares})
            self.firmwares = firmwares
