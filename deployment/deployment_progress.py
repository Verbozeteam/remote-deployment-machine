import traceback


class DeploymentProgress(object):
    def __init__(self, deployment_target):
        self.deployment_target = deployment_target

    def reset(self):
        pass

    def record_progress(self, progress):
        self.deployment_target.communicator.websocket_send({
            'identifier': self.deployment_target.identifier,
            'progress': progress
        })

    def record_exception(self, e):
        exception_string = ''.join(traceback.format_exception=(etype=type(e),
            value=e, tb=e.__traceback__))

        self.deployment_target.communicator.websocket_send({
            'identifier': self.deployment_target.identifier,
            'exception': exception_string
        })

    def get_json_dump(self):
        return {}
