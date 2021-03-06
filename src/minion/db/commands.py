import json
import shlex

from sqlalchemy import Column, Integer, Float, String

from minion.db import Base
from minion import subprocess
from minion.logger import cmd_logger
from minion.subprocess.base_shell import BaseSubprocess


class Command(Base):
    __tablename__ = 'commands'

    uid = Column(String, primary_key=True)
    pid = Column(Integer, nullable=False)

    command = Column(String, nullable=False)
    progress = Column(Float, nullable=False, default=0.0)

    exit_code = Column(Integer)
    # TODO: add exit message to scheme?
    command_code = Column(Integer)

    start_ts = Column(Integer, nullable=False)
    finish_ts = Column(Integer)

    job_id = Column(String)
    task_id = Column(String)
    group_id = Column(String)
    node = Column(String)
    node_backend = Column(String)

    stdout = Column(String, default='')
    stderr = Column(String, default='')

    # "artifacts" field should be json dumped to string
    artifacts = Column(String, default='{}')

    def status(self):
        cmd = (shlex.split(self.command.encode('utf-8'))
               if isinstance(self.command, basestring) else
               self.command)
        Subprocess = subprocess.subprocess_factory(cmd)
        if issubclass(Subprocess, BaseSubprocess):
            Watcher = Subprocess.watcher_base
            exit_message = Watcher.exit_messages.get(self.exit_code, 'Unknown')
        else:
            exit_message = 'Success' if self.exit_code == 0 else ''

        artifacts = {}
        try:
            artifacts = json.loads(self.artifacts)
        except ValueError as e:
            cmd_logger.error(
                'Dumped command (uid {}) has mailformed "artifacts" field: {}'.format(
                    self.uid,
                    self.artifacts
                ),
                extra={'task_id': self.task_id, 'job_id': self.job_id},
            )
            pass

        return {
            'pid': self.pid,
            'command': self.command,
            'job_id': self.job_id,
            'task_id': self.task_id,
            'progress': self.progress,
            'exit_code': self.exit_code,
            'exit_message': exit_message,
            'command_code': self.command_code,
            'start_ts': self.start_ts,
            'finish_ts': self.finish_ts,
            'output': self.stdout,
            'error_output': self.stderr,
            'artifacts': artifacts,
        }
