from config.config import CONFIG
from deployment.targets.disk_target import DiskTarget
from deployment.targets.wifi_target import WifiTarget

import threading
from time import sleep
import json

# TODO: Implement code to run on Windows and Linux as well - currently only Mac
class TargetsManager(threading.Thread):
    def __init__(self, communicator):
        threading.Thread.__init__(self)

        self.target_types = [
            DiskTarget,
            WifiTarget,
        ]
        self.discovered_targets = {}
        self.last_sent_dump = []
        self.communicator = communicator
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


            # FIXME: RuntimeError: dictionary changed size during iteration
            # FIXME: This happens when SD card is removed

            # check if any targets don't exist anymore
            for target in self.discovered_targets.keys():
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
