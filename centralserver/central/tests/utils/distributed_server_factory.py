import pathlib
import string
from multiprocessing import Process
from random import choice

from django.conf import settings
from fle_utils.django_utils import call_outside_command_with_output


class DistributedServer:

    def __init__(self, dbname=None, *args, **kwargs):
        self.distributed_dir = (pathlib.Path(settings.PROJECT_PATH).parent
                                / 'ka-lite' / 'kalite')
        self.manage_py_path = self.distributed_dir / 'manage.py'

        # setup for custom settings for this distributed server
        self.settings_contents = self._generate_settings(**kwargs)

        uniq_name = ''.join(choice(string.ascii_lowercase) for _ in range(10))
        self.settings_name = uniq_name
        self.settings_path = ((self.distributed_dir / self.settings_name)
                              .with_suffix('.py'))

        self.running_process = None

    def _generate_settings(self, **kwargs):
        new_settings = '''
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME"  : ":memory:",
        "OPTIONS": {
            "timeout": 60,
        },
    }
}
        '''
        old_settings_path = self.distributed_dir / 'settings.py'
        with open(old_settings_path.as_posix()) as f:
            old_settings = f.read()

        return old_settings + new_settings

    def call_command(self,
                     commandname,
                     output_to_stdout=True,
                     output_to_stderr=True,
                     **kwargs):
        '''
        Run a command in the context of this distributed server, customized to
        its own settings.

        commandname -- the management command to run
        output_to_stdout -- True to output the command's stdout to the console
                            instead of capturing to a variable
        output_to_stderr -- True to output the command's stderr to the console
                            instead of capturing to a variable
        '''
        if self.running_process:
            raise Exception('Command {} already started.'.format(commandname))

        _, _err, _ret, self.running_process = call_outside_command_with_output(
            commandname,
            output_to_stdout=output_to_stdout,
            output_to_stderr=output_to_stderr,
            settings=self.settings_name,
            manage_py_dir=self.distributed_dir.as_posix(),
            wait=False,
            **kwargs
        )

        return self

    def wait(self):
        '''
        Waits for the command run by `self.call_command` to finish. Returns
        the error code of the process. Returns the stdout and stderr
        of the command in the string, if output_to_stdout and
        output_to_stderr were given as False respectively.

        '''
        stdout, stderr = self.running_process.communicate()
        self.running_process = None  # so we can run other commands
        return (stdout, stderr)

    def sync(self):
        '''
        Convenience function for running `syncmodels` on the distributed
        server, waiting and then returning the stdout and stdin.
        '''
        self.call_command('syncmodels',
                          output_to_stdout=False,
                          output_to_stderr=False)
        return self.wait()

    def __enter__(self):
        # write our settings file
        with open(self.settings_path.as_posix(), 'w') as f:
            f.write(self.settings_contents)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # delete our settings file
        if self.settings_path.exists():
            self.settings_path.unlink()
