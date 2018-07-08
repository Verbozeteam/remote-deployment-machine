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
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'wb') as f:
            f.write(self.content.encode('utf-8'))

class MessageCommand(Command):
    def __init__(self, message):
        self.message = message

    def run(self, progress):
        progress.record('~==~ACTION: {}\n'.format(self.message))

class UpdateJson(Command):
    def __init__(self, file, dump):
        self.file = file
        self.dump = dump

    def run(self, progress):
        existing_dump = {}
        if os.path.exists(self.file):
            with open(self.file) as f:
                existing_dump = json.load(f)

        dump = self.merge_dictionaries(existing_dump, self.dump)

        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        with open(self.file, 'wb') as f:
            f.write(json.dumps(dump, indent=4))

    @staticmethod
    def merge_dictionaries(original, new):
        modified = {}
        for key in original:
            if key not in new:
                modified[key] = original[key]
            else:
                if isinstance(original[key], dict):
                    modified[key] = self.merge_dictionary(original[key], new[key])
                else:
                    modified[key] = new[key]

        for key in new:
            if key not in modified:
                modified[key] = new[key]

        return modified

class DiskTarget(DeploymentTarget):
    def __init__(self, manager, identifier, communicator):
        super(DiskTarget, self).__init__(manager, identifier, communicator)

        os.makedirs(CONFIG.MOUNTING_DIR, exist_ok=True)

        print('DiskTarget initialized')
        self.command_queue = []
        self.image_mounted = False

    @classmethod
    def list_all_target_identifiers(cls):
        return eval('cls.' + CONFIG.OS + '_get_disks_list()')

    def get_json_dump(self):
        return super(DiskTarget, self).get_json_dump()

    def deploy_impl(self, params, progress):
        self.reset_commands()
        identifier = params['deployment_target']['identifier']
        # self.unmount_disk(identifier)
        self.setup_image(params['firmware']['name'], identifier)
        self.mount_image(identifier)
        if 'repositories' in params:
            self.copy_repositories(params, identifier, progress)
        self.copy_files(params, identifier)
        self.unmount_image(identifier)

        for command in self.command_queue:
            command.run(progress)
            if isinstance(command, BashCommand) and 'mount ' in command.command:
                self.image_mounted = True
            elif isinstance(command, BashCommand) and 'unmout ' in command.command:
                self.image_mounted = False

        progress.record('~==~DEPLOYMENT COMPLETED SUCCESSFULLY', 'COMPLETED')

    def reset_commands(self):
        self.command_queue = []

    def queue_command(self, command):
        self.command_queue.append(command)

    def setup_image(self, firmware, identifier):
        if firmware:
            self.queue_command(MessageCommand('Setting up image...'))
            eval('self.' + CONFIG.OS + '_setup_image(firmware, identifier)')

    def Darwin_setup_image(self, firmware, identifier):
        self.queue_command(BashCommand('dd if={} of=/dev/r{} bs=8m'.format(
            CONFIG.FIRMWARE_DIR + firmware, identifier)))

    def Linux_setup_image(self, firmware, identifier):
        self.queue_command(BashCommand('dd if={} of=/dev/{} bs=8M'.format(
            CONFIG.FIRMWARE_DIR + firmware, identifier)))

    def Windows_setup_image(self, firmware, identifier):
        raise Exception('Windows_setup_image not implemented')

    def copy_repositories(self, params, identifier, progress):
        self.queue_command(MessageCommand('Copying repositories...'))
        eval('self.' + CONFIG.OS + '_copy_repositories(params, identifier, progress)')

    def Linux_copy_repositories(self, params, identifier, progress):
        repositories_manager = self.manager.repositories_manager

        for repo in params['repositories']:
            if repo['repo']['id'] in params['disabled_repo_ids']:
                continue

            name = repositories_manager.get_name_from_remote_path(repo['repo'])
            MessageCommand('Updating repository {}'.format(name)).run(progress)
            repositories_manager.fetch_repository(repo['repo'], name)

            self.queue_command(BashCommand('cd {} && git checkout {}'.format(
                os.path.join(CONFIG.REPOS_DIR, name), repo['commit'])))

            local_path = os.path.join(os.path.join(
                os.path.join(CONFIG.MOUNTING_DIR, identifier),
                repo['repo']['local_path']), name)
            self.queue_command(BashCommand('pwd'))
            self.queue_command(BashCommand('cp -r {} {}'.format(
                os.path.join(CONFIG.REPOS_DIR, name), local_path)))

    def copy_files(self, params, identifier):
        self.queue_command(MessageCommand('Copying files...'))
        eval('self.' + CONFIG.OS + '_copy_files(params, identifier)')

    def Linux_copy_files(self, params, identifier):
        arguments = {}
        for param in params['params']:
            arguments[param['parameter_name']] = param['parameter_value']

        for file in params['files']:
            target_filename = file['target_filename']
            self.queue_command(MessageCommand('Copying file {}'.format(target_filename)))
            if len(target_filename) > 0 and target_filename[0] == '/':
                target_filename = target_filename[1:]
            local_path = os.path.join(
                os.path.join(CONFIG.MOUNTING_DIR, identifier), target_filename)

            content = file['file_contents']
            for kw in re.findall('\{\{(.+)\}\}', content):
                content = content.replace('{{' + kw + '}}', str(arguments[kw]))
            content = content.replace('\r\n', '\n')
            self.queue_command(WriteFileCommand(local_path, content))
            if file['is_executable']:
                self.queue_command(BashCommand('chmod +x {}'.format(local_path)))

        # write deployment info file
        self.queue_command(MessageCommand('Writing deployment info file'))
        self.queue_command(UpdateJson(
            os.path.join(os.path.join(CONFIG.MOUNTING_DIR, identifier),
                'deployment_info.json'), self.get_deployment_info(params)))

    def Darwin_copy_files(self, params):
        raise Exception('Darwin_copy_files not implemented')

    def Windows_copy_files(self, params):
        raise Exception('Windows_copy_files not implemented')

    @staticmethod
    def get_deployment_info(params):
        return {
            'firmawre': params['firmware']['name'],
            'repositories': params['repositories'],
            'files': params['files'],
            'config': params['dep']['config'],
            'target': params['dep']['target'],
            'date': params['dep']['date'],
            'deployment': params['dep']['id'],
            'comment': params['dep']['comment']
        }

    def mount_image(self, params):
        self.queue_command(MessageCommand('Mounting image...'))
        eval('self.' + CONFIG.OS + '_mount_image(params)')

    def Darwin_mount_image(self, identifier):
        mounting_path = os.path.join(CONFIG.MOUNTING_DIR, identifier)
        self.queue_command(BashCommand('rm -rf {}'.format(mounting_path)))
        self.queue_command(BashCommand('mkdir {}'.format(mounting_path)))
        self.queue_command(BashCommand('mount /dev/{}s2 {}'.format(identifier,
            mounting_path)))

    def Linux_mount_image(self, identifier):
        mounting_path = os.path.join(CONFIG.MOUNTING_DIR, identifier)
        self.queue_command(BashCommand('rm -rf {}'.format(mounting_path)))
        self.queue_command(BashCommand('mkdir {}'.format(mounting_path)))
        self.queue_command(BashCommand('mount /dev/{}2 {}'.format(identifier,
            mounting_path)))

    def Windows_mount_image(self, identifier):
        raise Exception('Windows_mount_image not implemented')

    def unmount_image(self, identifier):
        self.queue_command(MessageCommand('Unmounting image...'))
        eval('self.' + CONFIG.OS + '_unmount_image(identifier)')

    def Darwin_unmount_image(self, identifier):
        self.queue_command(BashCommand(''))

    def Linux_unmount_image(self, identifier):
        mounting_path = os.path.join(CONFIG.MOUNTING_DIR, identifier)
        self.queue_command(BashCommand('sync'))
        self.queue_command(BashCommand('umount {}'.format(mounting_path)))
        self.queue_command(BashCommand('rm -rf {}'.format(mounting_path)))

    def Windows_unmount_image(self, identifier):
        raise Exception('Windows_unmount_image not implemented')

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
        self.queue_command(BashCommand(
            'umount /dev/{}'.format(identifier)))

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
    def Linux_disk_is_external(disk):
        return True

    @classmethod
    def Linux_get_disks_list(cls):
        unfiltered = os.listdir('/dev')

        # only keep files that match sd[a-z]$
        r = re.compile(r'\Asd[a-z]$')
        disks = []
        for disk in unfiltered:
            if r.match(disk) and cls.Linux_disk_is_external(disk):
                disks.append(disk)

        return disks

    @classmethod
    def Windows_get_disks_list(cls):
        print('Disk listing not implemented for Windows')
        return []
