
from connection.communicator import Communicator
from deployment.firmwares import FirmwaresManager
from deployment.repositories import RepositoriesManager
from deployment.targets.targets_manager import TargetsManager

class Core:
    def __init__(self):
        self.comm = Communicator(self.on_command)

        self.repositories = RepositoriesManager(self.comm)

        self.firmwares = FirmwaresManager(self.comm)
        self.firmwares.start()

        self.targets = TargetsManager(self.repositories, self.comm)
        self.targets.start()

        self.comm.run()
        print('Core initialized...')

    def on_command(self, message):
        print('Received command:', message)

        if 'repos' in message:
            self.repositories.update_repositories_list(message['repos'])

        if 'deploy' in message:
            self.targets.deploy(message['deploy'])
