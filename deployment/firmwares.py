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

        print(self.directory)

        print('FirmwaresManager initialized')

    def run(self):
        self.update_firmwares_list()

    def update_firmwares_list(self):
        firmwares = eval('self.' + platform.system() + '_update_firmwares_list()')

        if json.dumps(firmwares) != json.dumps(self.firmwares):
            self.communicator.websocket_send({'firmwares': firmwares})
            self.firmwares = firmwares

        sleep(CONFIG.FIRMWARES_CHECK_INTERVAL)
        self.update_firmwares_list()

    def Darwin_update_firmwares_list(self):

        return []

    def Linux_update_firmwares_list(self):
        print('Firmwares listing not implemented for Linux')
        return []

    def Windows_update_firmwares_list(self):
        print('Firmwares listing not implemented for Windows')
        return []
