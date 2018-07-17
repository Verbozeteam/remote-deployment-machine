from config.config import CONFIG
from deployment.targets.deployment_target import DeploymentTarget

import json
import re
import os
import platform
import subprocess

def join_path(p1, p2):
    return os.path.join(p1, p2.strip('/'))

class Command(object):
    def run(self, progress):
        pass


class BashCommand(Command):
    def __init__(self, command, caused_mount=False, caused_unmount=False):
        self.command = command
        self.caused_mount = caused_mount
        self.caused_unmount = caused_unmount
        self.successful = False

    def run(self, progress):
        progress.record('~~~~$ {}\n'.format(self.command))

        proc = subprocess.Popen(self.command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        ret = proc.returncode

        progress.record(out.decode() + '\n' + err.decode() + '\n')

        if ret != 0:
            raise Exception('{} ==> {}'.format(self.command, ret))

        if self.caused_mount or self.caused_unmount:
            self.successful = True


class WriteFileCommand(Command):
    def __init__(self, path, content):
        self.path = path
        self.content = content

    def run(self, progress):
        if self.content != None:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'wb') as f:
                f.write(self.content.encode('utf-8'))
        else:
            os.makedirs(self.path, exist_ok=True)


class MessageCommand(Command):
    def __init__(self, message):
        self.message = message

    def run(self, progress, count=0):
        progress.record('~==~ACTION {}: {}\n'.format(count, self.message))


class UpdateJsonCommand(Command):
    def __init__(self, file, content):
        self.file = file
        self.content = content

    def run(self, progress):
        existing_content = {}
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                existing_content = json.load(f)

        content = self.merge_dictionaries(existing_content, self.content)

        os.makedirs(os.path.dirname(self.file), exist_ok=True)

        with open(self.file, 'w') as f:
            json.dump(content, f, indent=4)

    @staticmethod
    def merge_dictionaries(original, new):
        content = {}
        for key in original:
            if key not in new:
                content[key] = original[key]
            else:
                if isinstance(original[key], dict):
                    content[key] = self.merge_dictionaries(original[key], new[key])
                else:
                    content[key] = new[key]

        for key in new:
            if key not in content:
                content[key] = new[key]

        return content


class DiskTarget(DeploymentTarget):
    def __init__(self, manager, identifier, communicator):
        super(DiskTarget, self).__init__(manager, identifier, communicator)

        os.makedirs(CONFIG.MOUNTING_DIR, exist_ok=True)

        self.identifier = identifier
        self.command_queue = []
        self.mounting_point = join_path(CONFIG.MOUNTING_DIR, identifier)
        self.image_mounted = os.path.exists(self.mounting_point)
        self.message_counter = 1

        print('DiskTarget initialized')

    def get_json_dump(self):
        return super(DiskTarget, self).get_json_dump()

    @classmethod
    def disk_is_external(cls, disk):
        # TODO: Implement this
        # Should return false for Ubuntu disk and true for other disks
        return True

    @classmethod
    def list_all_target_identifiers(cls):
        unfiltered = os.listdir('/dev')

        # only keep files that match sd[a-z]$
        r = re.compile(r'\Asd[a-z]$')
        disks = []
        for disk in unfiltered:
            if r.match(disk) and cls.disk_is_external(disk):
                disks.append(disk)

        return disks

    def deploy_impl(self, params, progress):
        self.reset_commands()

        self.check_image_unmounted()
        self.setup_image(params['firmware']['name'])
        self.mount_image()
        self.copy_repositories(params, progress)
        self.run_build_options(params)
        self.copy_files(params)
        self.unmount_image()

        for command in self.command_queue:
            if isinstance(command, MessageCommand):
                command.run(progress, count=self.message_counter)
                self.message_counter += 1
            else:
                command.run(progress)

            if isinstance(command, BashCommand):
                if command.caused_mount and command.successful:
                    self.image_mounted = True
                elif command.caused_unmount and command.successful:
                    self.image_mounted = False

        progress.record('~==~DEPLOYMENT COMPLETED SUCCESSFULLY', 'Completed')

    def reset_commands(self):
        self.command_queue = []
        self.message_counter = 1

    def queue_command(self, command):
        self.command_queue.append(command)

    def setup_image(self, firmware):
        if firmware:
            self.queue_command(MessageCommand('Setting up image...'))

            dd_command = 'dd if={} of=/dev/{} bs=10M'.format(
                join_path(CONFIG.FIRMWARE_DIR, firmware),
                self.identifier)
            self.queue_command(BashCommand(dd_command))

    def mount_image(self):
        self.queue_command(MessageCommand('Mounting image...'))
        self.queue_command(BashCommand('rm -rf {}'.format(self.mounting_point)))
        self.queue_command(BashCommand('mkdir {}'.format(self.mounting_point)))
        self.queue_command(BashCommand('mount /dev/{}2 {}'.format(
            self.identifier, self.mounting_point), caused_mount=True))

    def copy_repositories(self, params, progress):
        repositories_manager = self.manager.repositories_manager

        for repo in params['repositories']:
            if repo['repo']['id'] in params['disabled_repo_ids']:
                continue

            name = repositories_manager.get_name_from_remote_path(repo['repo'])
            MessageCommand('Updating repository {}...'.format(name)).run(progress, self.message_counter)
            self.message_counter += 1
            repositories_manager.fetch_repository(repo['repo'], name)

            repository_path = join_path(CONFIG.REPOS_DIR, name)
            repository_files_expr = join_path(repository_path, '*')
            git_checkout_command = 'cd {} && git checkout {}'.format(
                repository_path, repo['commit'])
            local_path = join_path(self.mounting_point, repo['repo']['local_path'])
            copy_command = 'cp -r {} {}'.format(repository_files_expr, local_path)

            self.queue_command(MessageCommand('Copying repository {}...'.format(name)))
            self.queue_command(BashCommand(git_checkout_command))
            self.queue_command(WriteFileCommand(local_path, None))
            self.queue_command(BashCommand(copy_command))

    def get_repository_from_id(self, params, repo_id):
        for repo in params['repositories']:
            if repo['repo']['id'] == repo_id:
                return repo['repo']
        return {}

    def run_build_options(self, params):
        # make a dictionary of repo_id -> list of options for that repo
        options = {}
        for option in params['options']:
            if option['repo'] in options: options[option['repo']].append(option)
            else:                         options[option['repo']] = [option]
        for repo_id in options.keys():
            repo_options = sorted(options[repo_id], key=lambda o: o['option_priority'])
            repo_local_mounted_path = join_path(self.mounting_point, self.get_repository_from_id(params, repo_id)['local_path'])
            for option in repo_options:
                self.queue_command(MessageCommand('Running build option {}: {}'.format(option['option_name'], option['option_command'])))
                self.queue_command(BashCommand("cd {} && {}".format(repo_local_mounted_path, option['option_command'])))

    def copy_files(self, params):
        arguments = {}
        for param in params['params']:
            arguments[param['parameter_name']] = param['parameter_value']

        for f in params['files']:
            target_filename = f['target_filename']
            self.queue_command(MessageCommand('Copying file {}'.format(target_filename)))

            if len(target_filename) > 0 and target_filename[0] == '/':
                target_filename = target_filename[1:]
            local_path = join_path(self.mounting_point, target_filename)

            content = f['file_contents']
            for kw in re.findall('\{\{(.+)\}\}', content):
                content = content.replace('{{' + kw + '}}', str(arguments[kw]))
            content = content.replace('\r\n', '\n')

            self.queue_command(WriteFileCommand(local_path, content))
            if f['is_executable']:
                self.queue_command(BashCommand('chmod +x {}'.format(local_path)))

        # write deployment info file
        self.queue_command(MessageCommand('Writing deployment info file...'))
        deployment_file = join_path(self.mounting_point, 'deployment_info.json')
        self.queue_command(UpdateJsonCommand(deployment_file, self.get_deployment_info(params)))

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

    def check_image_unmounted(self):
        if self.image_mounted or os.path.exists(self.mounting_point):
            self.unmount_image()

    def unmount_image(self):
        self.queue_command(MessageCommand('Unmounting image...'))
        self.queue_command(BashCommand('sync'))
        self.queue_command(BashCommand('umount -l {}'.format(
            self.mounting_point), caused_unmount=True))
        self.queue_command(BashCommand('rm -rf {}'.format(self.mounting_point)))
