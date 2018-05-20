
from connection.communicator import Communicator
from deployment.firmwares import FirmwaresManager
from deployment.repositories import RepositoriesManager
from deployment.disks import DisksManager

class Core:
    def __init__(self):
        self.comm = Communicator(self.on_command)

        self.repositories = RepositoriesManager(self.comm)

        self.firmwares = FirmwaresManager(self.comm)
        self.firmwares.start()

        self.disks = DisksManager(self.comm)
        self.disks.start()

        self.comm.run()

    def on_command(self, message):
        print('Received command:', message)

        if 'repos' in message:
            self.repositories.update_repositories_list(message['repos'])
