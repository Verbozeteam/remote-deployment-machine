
from deployment.targets.deployment_target import DeploymentTarget

class WifiTarget(DeploymentTarget):
    def __init__(self, manager, identifier):
        super(WifiTarget, self).__init__(manager, identifier)

    @staticmethod
    def list_all_target_identifiers():
        return []
