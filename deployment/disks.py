import os
import platform
import subprocess
import threading
from time import sleep
import json
import re

from config.config import Config

# TODO: Implement code to run on Windows and Linux as well - currently only Mac
class DisksManager(threading.Thread):
    def __init__(self, communicator):
        threading.Thread.__init__(self)

        self.disks = []
        self.communicator = communicator
        print('DisksManager initialized')

    def run(self):
        self.update_disks_list()

    def update_disks_list(self):
        disks = eval('self.' + platform.system() + '_update_disks_list()')

        if json.dumps(disks) != json.dumps(self.disks):
            self.communicator.websocket_send({'disks': disks})
            self.disks = disks

        sleep(Config.DISKS_CHECK_INTERVAL)
        self.update_disks_list()

    @staticmethod
    def Darwin_disk_is_external(disk):
        proc = subprocess.Popen('diskutil info /dev/' + disk + \
            ' | grep "Removable Media:          Removable"',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = proc.communicate()

        return len(out.decode()) > 0

    @staticmethod
    def Darwin_get_disk_name(disk):
        proc = subprocess.Popen('diskutil info /dev/' + disk + \
            ' | grep "Device / Media Name:      "',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = proc.communicate()

        return out.decode().replace('Device / Media Name:      ', '').strip()

    def Darwin_update_disks_list(self):
        unfiltered = os.listdir('/dev')

        r = re.compile(r'\Adisk\d+$')
        disks = []
        for disk in unfiltered:
            if r.match(disk) and self.Darwin_disk_is_external(disk):
                disks.append({'identifier': disk,
                    'name': self.Darwin_get_disk_name(disk)})

        return disks

    def Linux_update_disks_list(self):
        print('Disk listing not implemented for Linux')
        return []

    def Windows_update_disks_list(self):
        print('Disk listing not implemented for Windows')
        return []
