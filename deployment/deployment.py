import threading, os, re
import json
from os import listdir

from config.config import CONFIG

class DeploymentThread(threading.Thread):
    def __init__(self, deployment_lock, disk_path, firmware, config, dep,
        params, options, disabled_repo_ids):

        threading.Thread.__init__(self)
        self.firmware = firmware
        self.deployment_lock = deployment_lock
        self.config = config
        self.deployment = dep
        self.parameters = params
        self.build_optiosn = options
        # self.repositories =
        # self.files =
        self.disabled_repo_ids = disabled_repo_ids

        self.command_queue = []

        self.mounting_point = '/home/pi/mnt/'
        self.deployment_info_filename = '/home/pi/.deployment'
