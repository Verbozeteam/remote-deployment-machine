from config.config import CONFIG
from deployment.targets.disk_target import DiskTarget
from deployment.targets.wifi_target import WifiTarget

import threading
from time import sleep

# TODO: Implement code to run on Windows and Linux as well - currently only Mac
class TargetsManager(threading.Thread):
    def __init__(self, communicator):
        super(TargetsManager, self).__init__(self)
        self.target_types = [
            DiskTarget,
            WifiTarget,
        ]
        self.discovered_targets = {}
        self.communicator = communicator
        print('TargetsManager initialized')

    def run(self):
        while True:
            is_changed = False

            current_all_targets = [] # list of (target_type, target_identifier)
            for target_type in self.target_types:
                current_all_targets += map(lambda tid: (target_type, tid), target_type.list_all_target_identifiers())
            current_all_targets_ids = map(lambda T, tid: tid, current_all_targets)

            # check if any targets don't exist anymore
            for target in self.discovered_targets.keys():
                if target not in current_all_targets_ids:
                    # target has been removed
                    del self.discovered_targets[target]
                    is_changed = True

            # check if new targets are discovered
            for (target_type, tid) in current_all_targets:
                if tid not in self.discovered_targets:
                    # new target has been discovered
                    self.discovered_targets[tid] = target_type(self, tid) # instanciate a new target
                    is_changed = True

            if is_changed:
                self.communicator.websocket_send({'deployment_targets': map(lambda T: T.get_json_dump(), self.discovered_targets.values())})

            sleep(CONFIG.DISKS_CHECK_INTERVAL)

