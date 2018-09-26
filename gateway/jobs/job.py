import logging
from gateway.utils import camel_to_snake_case


class Job:
    PROTOCOL_VERSION = '1.4'

    def __init__(self, app):
        self.app = app
        self.job_name = camel_to_snake_case(self.__class__.__name__)
        self.job_settings = app.config.for_job(self.job_name)
        self.logger = self.init_logger()

    def init_logger(self):
        return logging.getLogger(f'jobs.{self.job_name}')

    @property
    def enabled(self):
        return self.job_settings.enabled

    async def set_protocol_version(self, session):
        await session.send_request('server.version', ['CPG', [self.PROTOCOL_VERSION, self.PROTOCOL_VERSION]])
