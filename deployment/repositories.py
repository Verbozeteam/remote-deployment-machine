import os

from config.config import Config

class RepositoriesManager:
    def __init__(self, communicator):

        self.repositories = []
        self.communicate = communicator

        self.directory = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            Config.REPOS_DIR)
        os.makedirs(self.directory, exist_ok=True)

        print('RepositoriesManager initialized')

    def update_repositories_list(self, repos):
        print('Updating repositories list')
        self.repositories = repos
        self.fetch_repositores()

    def fetch_repositores(self):
        for R in self.repositories:
            print(R)
        pass
