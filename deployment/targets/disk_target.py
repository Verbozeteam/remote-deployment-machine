from config.config import CONFIG
from deployment.targets.deployment_target import DeploymentTarget

import json
import re
import os
import platform
import subprocess

class DiskTarget(DeploymentTarget):
    def __init__(self, manager, identifier):
        super(DiskTarget, self).__init__(manager, identifier)

    def deploy_impl(self, params):
        pass

    @staticmethod
    def list_all_target_identifiers(cls):
        return eval('cls.' + CONFIG.OS + '_get_disks_list()')

    def get_json_dump(self):
        return super(DiskTarget, self).get_json_dump()

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

    @classmethod
    def Darwin_get_disks_list(cls):
        unfiltered = os.listdir('/dev')

        r = re.compile(r'\Adisk\d+$')
        disks = []
        for disk in unfiltered:
            if r.match(disk) and cls.Darwin_disk_is_external(disk):
                disks.append(disk)

        print('Available disks', disks)
        return disks

    @staticmethod
    def Linux_get_disks_list(self):
        print('Disk listing not implemented for Linux')
        return []

    @staticmethod
    def Windows_get_disks_list(self):
        print('Disk listing not implemented for Windows')
        return []
