from deployment.deployment_progress import DeploymentProgress
import threading
import json

class DeploymentTargetStatus:
    READY = 'Ready'
    RUNNING = 'Running'
    DESTROYED = 'Destroyed'

class DeploymentTarget(object):
    def __init__(self, manager, identifier, communicator):
        self.manager = manager
        self.identifier = identifier
        self.communicator = communicator
        self.deployment_id = 0

        self.status = DeploymentTargetStatus.READY
        self.progress = DeploymentProgress(self)
        self.thread = None

    def on_removed(self):
        self.status = DeploymentTargetStatus.DESTROYED

    def deploy(self, params):
        print('DeloymentTarget deploy()')
        if self.status != DeploymentTargetStatus.READY:
            return False

        self.deployment_id = params['deployment_lock']['deployment']['id']
        self.status = DeploymentTargetStatus.RUNNING

        self.thread = DeploymentThread(self, params)
        self.thread.start()
        return True

    def clean_after_deploy(self):
        self.deployment_id = 0
        self.thread = None
        self.progress.reset()
        self.status = DeploymentTargetStatus.READY


    def deploy_impl(self, parameters):
        raise Exception("This needs to be implemented by a child class")

    # def update_status(self, status):
    #     self.status = status
    #     self.communicator.websocket_send(json.dumps({
    #         'deployment_target_status': {
    #             'identifier': self.identifier,
    #             'status': self.status
    #         }
    #     }))

    @classmethod
    def list_all_target_identifiers(cls):
        return []

    def get_json_dump(self):
        return {
            "identifier": self.identifier,
            "status": self.status
            # "progress": self.progress.get_json_dump(),
        }

class DeploymentThread(threading.Thread):
    def __init__(self, target, params):
        threading.Thread.__init__(self)

        self.target = target
        self.params = params

    def run(self):
        print('DeploymentThread running')
        try:
            self.target.deploy_impl(self.params, self.target.progress)
        except Exception as e:
            self.target.progress.exception(e)
        finally:
            print('DeploymentThread completed')
            self.target.clean_after_deploy()
