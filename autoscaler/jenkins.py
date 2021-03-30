import logging

import jenkins
import time

from spacelaunchnow.config import JENKINS_URL, JENKINS_USERNAME, JENKINS_PASSWORD
logger = logging.getLogger('autoscaler')


class DevOpsJenkins:
    def __init__(self):
        self.jenkins_server = jenkins.Jenkins(JENKINS_URL, username=JENKINS_USERNAME, password=JENKINS_PASSWORD)
        user = self.jenkins_server.get_whoami()
        version = self.jenkins_server.get_version()
        logger.info("Jenkins Version: {}".format(version))
        logger.info("Jenkins User: {}".format(user['id']))

    def build_job(self, name, parameters=None, token=None):
        next_build_number = self.jenkins_server.get_job_info(name)['nextBuildNumber']
        self.jenkins_server.build_job(name, parameters=parameters, token=token)
        time.sleep(20)
        build_info = self.jenkins_server.get_build_info(name, next_build_number)
        return build_info

    def scale_worker_count(self, worker_count):
        NAME_OF_JOB = "SpaceLaunchNow-Terraform/master"
        PARAMETERS = {'SLN_WORKERS': worker_count, 'AUTO_APPLY': True}
        output = self.build_job(NAME_OF_JOB, parameters=PARAMETERS)
        logger.info("Jenkins Build URL: {}".format(output['url']))
