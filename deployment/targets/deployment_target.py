from deployment.deployment_progress import DeploymentProgress
import threading

class DeploymentTargetStatus:
    READY = 0
    RUNNING = 1
    DESTROYED = 2

class DeploymentTarget(object):
    def __init__(self, manager, identifier):
        self.manager = manager
        self.identifier = identifier
        self.status = DeploymentTargetStatus.READY
        self.progress = DeploymentProgress()
        self.thread = None

    def on_removed(self):
        self.status = DeploymentTargetStatus.DESTROYED

    def deploy(self, params):
        if self.status != DeploymentTargetStatus.READY:
            return False

        self.status = DeploymentTargetStatus.RUNNING
        self.progress.reset()
        self.thread = DeploymentThread(self, params)
        self.thread.run()
        return True

    def deploy_impl(self, params):
        raise Exception("This needs to be implemented by a child class")

    def get_json_dump(self):
        return {
            "identifier": self.identifier,
            "status": self.status,
            "progress": self.progress.get_json_dump(),
        }

    @staticmethod
    def list_all_target_identifiers():
        return []

class DeploymentThread(threading.Thread):
    def __init__(self, target, params):
        self.target = target
        self.params = params

    def run(self):
        try:
            self.target.deploy_impl(self.params)
        except Exception as e:
            self.target.progress.record_exception(e)
        self.target.status = DeploymentTargetStatus.READY
