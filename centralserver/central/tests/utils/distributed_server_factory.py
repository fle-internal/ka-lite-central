import json
import pathlib
import re
import string
import subprocess
from random import choice
from urlparse import urlparse

from django.conf import settings
from fle_utils.crypto import Key
from fle_utils.django_utils import call_outside_command_with_output
from fle_utils.importing import resolve_model


class DistributedServer(object):

    def __init__(self, *args, **kwargs):
        self.kalite_submodule_dir = pathlib.Path(settings.PROJECT_PATH).parent / 'ka-lite-submodule'
        self.distributed_dir = (self.kalite_submodule_dir / 'kalite')
        self.manage_py_path = self.distributed_dir / 'manage.py'

        uniq_name = 'settings_' + ''.join(choice(string.ascii_lowercase) for _ in range(10))
        self.db_path = ((self.distributed_dir / 'database' / uniq_name)
                        .with_suffix('.sqlite'))

        self.key = kwargs.pop("key", None) or Key()

        # setup for custom settings for this distributed server
        self.settings_name = uniq_name
        self.settings_contents = self._generate_settings(**kwargs)
        self.settings_path = ((self.distributed_dir / self.settings_name)
                              .with_suffix('.py'))

        self.running_process = None

    def _generate_settings(self, **kwargs):

        new_settings = '''
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME"  : "%s",
        "OPTIONS": {
            "timeout": 60,
        },
    }
}
        '''
        new_settings = new_settings % self.db_path

        # super hack to not run migrations on the distributed servers.
        # Basically, we replace south's syncdb (which adds migrations)
        # with the normal syncdb
        new_settings += '''
INSTALLED_APPS = filter(lambda app: 'south' not in app, INSTALLED_APPS)
        '''

        # write some pregenerated pub/priv keys to the settings file,
        # to avoid having to generate some on the fly (which is slow)
        new_settings += '''
OWN_DEVICE_PUBLIC_KEY = %r
OWN_DEVICE_PRIVATE_KEY = %r
        ''' % (self.key.get_public_key_string(), self.key.get_private_key_string())

        # we have to remove the protocol (http or https) from the url
        # that the user gives to us
        if 'CENTRAL_SERVER_HOST' in kwargs:
            parse_result = urlparse(kwargs['CENTRAL_SERVER_HOST'])
            kwargs['CENTRAL_SERVER_HOST'] = parse_result.netloc

        other_settings = ['%s = %r' % (k, v) for k, v in kwargs.iteritems()]
        new_settings = '\n'.join([new_settings] + other_settings)
        old_settings_path = self.distributed_dir / 'settings.py'
        with open(old_settings_path.as_posix()) as f:
            old_settings = f.read()

        return old_settings + new_settings

    def call_command(self,
                     commandname,
                     *args,
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

        output_to_stdout = kwargs.pop('output_to_stdout', True)
        output_to_stderr = kwargs.pop('output_to_stderr', True)
        self.commandname = commandname

        if self.running_process:
            raise Exception('Command {} already started.'.format(commandname))

        kwargs['traceback'] = True

        _, _err, _ret, self.running_process = call_outside_command_with_output(
            commandname,
            output_to_stdout=output_to_stdout,
            output_to_stderr=output_to_stderr,
            settings=self.settings_name,
            kalite_dir=self.kalite_submodule_dir.as_posix(),
            wait=False,
            *args,
            **kwargs
        )

        return self

    def wait(self, noerr=False):
        '''
        Waits for the command run by `self.call_command` to finish. Returns
        a tuple (stdin, stderr, returncode). Returns the stdout and stderr
        of the command in the string, if output_to_stdout and
        output_to_stderr were given as False respectively. `returncode` is the
        return code of the process. Raises CalledProcessError if the command
        returns a non-zero return code.

        If `noerr` is True, then it won't raise an error, and simply
        returns the return code as well.

        '''
        stdout, stderr = self.running_process.communicate()
        returncode = self.running_process.returncode
        self.running_process = None  # so we can run other commands

        if not noerr and returncode != 0:
            errmsgtemplate = "command returned non-zero errcode: stderr is %s"
            raise subprocess.CalledProcessError(returncode,
                                                self.commandname,
                                                output=errmsgtemplate % stderr)

        return (stdout, stderr, returncode)

    def sync(self, verbose=False):
        '''
        Convenience function for running `syncmodels` on the distributed
        server, waiting and then returning the stdout, stderr and returncode.
        '''
        self.call_command('syncmodels',
                          verbose=verbose,
                          output_to_stdout=False,
                          output_to_stderr=False)

        results, _, retcode = self.wait()

        return {
            "uploaded": int(re.search("Total uploaded: (\d+)", results).group(1)),
            "downloaded": int(re.search("Total downloaded: (\d+)", results).group(1)),
            "errors": int(re.search("Total errors: (\d+)", results).group(1)),
            "results": results,
            "retcode": retcode,
        }

    def addmodel(self, modelname, count=1, **attrs):
        '''
        Create the model given by modelname in the distributed server,
        with attributes given by attrs. Returns the id of the new
        model.

        '''
        self.call_command('createmodel',
                          modelname,
                          data=json.dumps(attrs),
                          count=count,
                          output_to_stdout=False,
                          output_to_stderr=False)
        model_id, err, ret = self.wait()

        # Strip newlines before returning the model ID.
        model_id = model_id.strip()

        # Split the IDs into a list if > 1
        if "," in model_id:
            model_id = model_id.split(",")

        return model_id

    def modifymodel(self, modelname, id, **attrs):
        '''
        Modify the model given by modelname and id with the keyword
        arguments provided. Raises an error if modifying the model
        fails.
        '''

        self.call_command('modifymodel',
                          modelname,
                          id,
                          data=json.dumps(attrs),
                          output_to_stdout=True,
                          output_to_stderr=True)
        self.wait()

    def countmodels(self, modelpath):
        '''
        Return the number of instances of a particular model that exist on
        this distributed server.
        '''

        model = resolve_model(modelpath)

        code = '''
        from %(module_path)s import %(model_name)s
        count = %(model_name)s.objects.count()
        ''' % {"model_name": model.__name__, "module_path": model.__module__}

        return self.runcode(code)["count"]

    def register(self, username, password, zone_id, noerr=False):
        '''
        Registers the distributed server to the zone id, which the user
        given by the username and password is a part of. Returns the
        stdout, stderr and returncode.
        '''
        result = self.call_command(
            'register',
            username=username,
            password=password,
            zone=zone_id,
            output_to_stdout=False,
            output_to_stderr=False,
        ).wait(noerr)

        return result

    def readmodel(self, modelname, id):
        '''
        Reads the model with the modelname with the attributes given by
        **attrs.  Returns a list of dictionaries corresponding to the
        models matching the given attributes.
        '''

        stdout, _stderr, _ret = self.call_command(
            'readmodel',
            modelname,
            id=id,
            output_to_stdout=False,
            output_to_stderr=False,
        ).wait()

        return json.loads(stdout)

    def runcode(self, code, noerr=False):
        '''
        Runs a block of code and returns a dictionary with the serializable
        portions of the resulting local namespace.
        '''

        # put it all into one line; note: may blow up anything with if statements, etc
        code = re.sub("\s*\n\s*", "; ", code.strip())

        stdout, _stderr, _ret = self.call_command(
            'runcode',
            code,
            output_to_stdout=False,
            output_to_stderr=False,
        ).wait(noerr)

        # json.loads will return an error when given an empty string, so send it an empty JSON object string
        if not stdout:
            stdout = "{}"
        return json.loads(stdout)

    def validate(self):
        return self.call_command('validate', output_to_stdout=False)

    def __enter__(self):
        # write our settings file
        with open(self.settings_path.as_posix(), 'w') as f:
            f.write(self.settings_contents)

        # prepare the DB
        self.call_command('syncdb', noinput=True, output_to_stdout=False)
        self.wait()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # delete our settings file
        if self.settings_path.exists():
            self.settings_path.unlink()

        # delete the db file
        if self.db_path.exists():
            self.db_path.unlink()
