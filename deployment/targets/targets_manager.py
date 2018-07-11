from config.config import CONFIG
from deployment.targets.disk_target import DiskTarget
from deployment.targets.wifi_target import WifiTarget

import threading
from time import sleep
import json

class TargetsManager(threading.Thread):
    def __init__(self, repositories_manager, communicator):
        threading.Thread.__init__(self)

        self.target_types = [
            DiskTarget,
            WifiTarget,
        ]
        self.discovered_targets = {}
        self.last_sent_dump = []
        self.communicator = communicator
        self.repositories_manager = repositories_manager
        self.running_deployments = []
        print('TargetsManager initialized')

    def deploy(self, params): # returns False if can't run
        print('TargetsManager deploy()')

        deployment_target = params['deployment_target']['identifier']

        if self.discovered_targets[deployment_target].deploy(params):
            self.running_deployments.append({
                id: params['deployment_lock']['deployment']['id'],
                deployment_target: deployment_target})
        else:
            print('Running deployment for target', deployment_target, 'failed...')

    def run(self):
        while True:
            current_all_targets = [] # list of (target_type, target_identifier)
            for target_type in self.target_types:
                current_all_targets += list(map(lambda tid: (target_type, tid),
                    target_type.list_all_target_identifiers()))
            current_all_targets_ids = list(map(lambda T: T[1], current_all_targets))

            # check if any targets don't exist anymore
            for target in list(self.discovered_targets):
            # list(self.discovered_targets) returns copy of list of keys,
            # prevents RuntimeError: dictionary changed size during iteration
                if target not in current_all_targets_ids:
                    # target has been removed
                    self.discovered_targets[target].on_removed()
                    del self.discovered_targets[target]

            # check if new targets are discovered
            for (target_type, tid) in current_all_targets:
                if tid not in self.discovered_targets:
                    # new target has been discovered
                    self.discovered_targets[tid] = target_type(self, tid, self.communicator) # instanciate a new target

            dump = list(map(lambda T: T.get_json_dump(), self.discovered_targets.values()))
            if json.dumps(self.last_sent_dump) != json.dumps(dump):
                print('Available deployment targets', dump)
                self.communicator.websocket_send({'deployment_targets': dump})
                self.last_sent_dump = dump

            sleep(CONFIG.DISKS_CHECK_INTERVAL)
