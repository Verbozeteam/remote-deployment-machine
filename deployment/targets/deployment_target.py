
class DeploymentTarget(object):
    def __init__(self, manager, identifier):
        self.manager = manager
        self.identifier = identifier

    def deploy(self):
        pass

    def get_json_dump(self):
        return {
            "identifier": self.identifier,
        }

    @staticmethod
    def list_all_target_identifiers():
        return []
