import os
import re

from config.config import CONFIG

class RepositoriesManager:
    def __init__(self, communicator):

        self.repositories = []
        self.communicate = communicator

        self.directory = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            CONFIG.REPOS_DIR)
        os.makedirs(self.directory, exist_ok=True)

        print('RepositoriesManager initialized')

    def update_repositories_list(self, repos):
        print('Updating repositories list')
        self.repositories = repos
        self.fetch_repositores()

    @staticmethod
    def get_name_from_remote_path(repo):
        return re.search(r'\w+$', repo['remote_path'].replace('.git', '')).group(0)

    def fetch_repository(self, repo, name):
        fetch_all_branches = """for branch in `git branch -r | grep -v HEAD | grep -v master`; do git checkout "${branch#origin/}" && git pull; done; git checkout master; git pull"""
        if os.path.isdir(os.path.join(self.directory, name)):
            os.system('cd {} && cd {} && {}'.format(self.directory, name, fetch_all_branches))
        else:
            os.system('cd {} && git clone {} && cd {} && {}'.format(self.directory, repo['remote_path'], name, fetch_all_branches))

    def fetch_repositores(self):
        for repo in self.repositories:
            name = self.get_name_from_remote_path(repo)
            print('Fetching repository', name)
            self.fetch_repository(repo, name)
        print('Repositories list updated')
