from config.config import CONFIG
from deployment.targets.deployment_target import DeploymentTarget

import json
import re
import os
import platform
import subprocess

class Command(object):
    def run(self, progress):
        pass

class BashCommand(Command):
    def __init__(self, command):
        self.command = command

    def run(self, progress):
        progress.record('~~~~$ {}\n'.format(self.command))

        proc = subprocess.Popen(self.command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        ret = proc.returncode

        progress.record(out.decode() + '\n' + err.decode() + '\n')

        if ret != 0:
            raise Exception('{} ==> {}'.format(self.command, ret))

class WriteFileCommand(Command):
    def __init__(self, path, content):
        self.path = path
        self.content = content

    def run(self, progress):
        pass

class MessageCommand(Command):
    def __init__(self, message):
        self.message = message

    def run(self, progress):
        progress.record('~==~ACTION: {}\n'.format(self.message))

class DiskTarget(DeploymentTarget):
    def __init__(self, manager, identifier, communicator):
        super(DiskTarget, self).__init__(manager, identifier, communicator)

        print('DiskTarget initialized')
        self.command_queue = []

    @classmethod
    def list_all_target_identifiers(cls):
        return eval('cls.' + CONFIG.OS + '_get_disks_list()')

    def get_json_dump(self):
        return super(DiskTarget, self).get_json_dump()

    def deploy_impl(self, params, progress):
        self.reset_commands()

        identifier = params['deployment_target']['identifier']
        self.unmount_disk(identifier)
        self.setup_image(params['firmware']['name'], identifier)
        self.clone_repositories(params)
        self.mount_disk(identifier)
        self.copy_files(params)

        for command in self.command_queue:
            command.run(progress)

        progress.record('~==~DEPLOYMENT COMPLETED SUCCESSFULLY')

    def reset_commands(self):
        command_queue = []

    def queue_command(self, command):
        self.command_queue.append(command)

    def setup_image(self, firmware, identifier):
        self.queue_command(MessageCommand('Setting up image...'))
        eval('self.' + CONFIG.OS + '_setup_image(firmware, identifier)')

    def Darwin_setup_image(self, firmware, identifier):
        if firmware:
            firmware_path = CONFIG.FIRMWARE_DIR + firmware
            self.queue_command(BashCommand('dd if={} of=/dev/r{} bs=8m'.format(
                firmware_path, identifier)))

    def Linux_setup_image(self, firmware, identifier):
        raise Exception('Linux_setup_image not implemented')

    def Windows_setup_image(self, firmware, identifier):
        raise Exception('Windows_setup_image not implemented')

    def clone_repositories(self, params):
        pass

    def copy_files(self, params):
        eval('self.' + CONFIG.OS + '_copy_files(params)')

    def Darwin_copy_files(self, params):
        pass
        # raise Exception('Darwin_copy_files not implemented')

    def Linux_copy_files(self, params):
        raise Exception('Linux_copy_files not implemented')

    def Windows_copy_files(self, params):
        raise Exception('Windows_copy_files not implemented')

    def unmount_image(self, params):
        pass

    def mount_disk(self, identifier):
        self.queue_command(MessageCommand(
            'Mounting disk {}...'.format(identifier)))
        eval('self.' + CONFIG.OS + '_mount_disk(identifier)')

    def Darwin_mount_disk(self, identifier):
        self.queue_command(BashCommand(
            'diskutil mountDisk /dev/{}'.format(identifier)))

    def Linux_mount_disk(self, identifier):
        raise Exception('Linux_mount_disk not implemented')

    def Windows_mount_disk(self, identifier):
        raise Exception('Windows_mount_disk not implemented')

    def unmount_disk(self, identifier):
        self.queue_command(MessageCommand(
            'Unmounting disk {}...'.format(identifier)))
        eval('self.' + CONFIG.OS + '_unmount_disk(identifier)')

    def Darwin_unmount_disk(self, identifier):
        self.queue_command(BashCommand(
            'diskutil unmountDisk /dev/{}'.format(identifier)))

    def Linux_unmount_disk(self, identifier):
        raise Exception('Linux_unmount_disk not implemented')

    def Windows_unmount_disk(self, identifier):
        raise Exception('Windows_unmount_disk not implemented')

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
