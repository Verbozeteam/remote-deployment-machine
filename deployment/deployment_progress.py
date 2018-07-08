import traceback
import json


class DeploymentProgress(object):
    def __init__(self, deployment_target):
        self.deployment_target = deployment_target

    def reset(self):
        pass

    def record(self, progress, status='Running'):
        print('DeploymentProgress record(): ', progress)
        self.deployment_target.communicator.websocket_send({
            'deployment_update': {
                'deployment': self.deployment_target.deployment_id,
                'message': progress,
                'status': status
            }
        })

    def exception(self, e):
        print('DeploymentProgress record_exception')
        exception_string = ''.join(traceback.format_exception(etype=type(e),
            value=e, tb=e.__traceback__))
        self.record(exception_string, 'Error')

    def get_json_dump(self):
        return {}
