from config.config import CONFIG
from deployment.targets.deployment_target import DeploymentTarget

import json
import re
import os
import platform
import subprocess

class Command(object):
    def run(self):
        pass

class BashCommand(Command):
    def __init__(self, command):
        self.command = command
        self.silent = silent

    def run(self):
        pass

class WriteFileCommand(Command):
    def __init__(self, path, content):
        self.path = path
        self.content = content
        self.silent = silent

    def run(self):
        pass

class DiskTarget(DeploymentTarget):
    def __init__(self, manager, identifier, communicator):
        super(DiskTarget, self).__init__(manager, identifier, communicator)

        print('DiskTarget initialized')
        self.command_queue = []

    def deploy_impl(self, params, progress):
        self.reset_commands()

        identifier = params['deployment_target']['identifier']

        self.unmount_disk(identifier, progress)
        self.setup_image(params['firmware'], identifier, progress)
        self.clone_repositories(params, progress)
        self.mount_disk(identifier, progress)
        self.copy_files(params, progress)

        for command in self.command_queue:
            command.run()


    def reset_commands(self):
        command_queue = []

    def queue_command(self, command):
        self.command_queue.append(command)

    def setup_image(self, firmware, identifier, progress):
        progress.record('Setting up image commands...')
        # if firware:
            # self.queue_command(BashCommand('dd if={} of=/{} bs=8M'.format(
                # params['firmware']['name'], params['deployment_target']['identifier'])))

    def clone_repositories(self, params, progress):
        progress.record('Cloning repositories...')

    def copy_files(self, paramsm, progress):
        progress.record('Copying files...')

    def unmount_image(self, params, progress):
        progress.record('Unmounting image...')

    def mount_disk(self, identifier, progress):
        progress.record('Mounting disk...')

    def unmount_disk(self, identifier, progress):
        progress.record('Unmounting disk...')

    @classmethod
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

        # only keep files that match disk* and are external drives
        r = re.compile(r'\Adisk\d+$')
        disks = []
        for disk in unfiltered:
            if r.match(disk) and cls.Darwin_disk_is_external(disk):
                disks.append(disk)

        return disks

    @staticmethod
    def Linux_get_disks_list(self):
        print('Disk listing not implemented for Linux')
        return []

    @staticmethod
    def Windows_get_disks_list(self):
        print('Disk listing not implemented for Windows')
        return []
