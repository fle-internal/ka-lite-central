import json
import pathlib
import os
import re
import string
import subprocess
import sys
from random import choice
from urlparse import urlparse

from fle_utils.crypto import Key
from fle_utils.importing import resolve_model
import tempfile


def call_outside_command_with_output(command, *args, **kwargs):
    """
    Runs call_command for a KA Lite installation at the given location,
    and returns the output.
    """
    
    kalite_dir = None
    
    # some custom variables that have to be put inside kwargs
    # or else will mess up the way the command is called
    output_to_stdout = kwargs.pop('output_to_stdout', False)
    output_to_stderr = kwargs.pop('output_to_stderr', False)
    wait = kwargs.pop('wait', True)

    # build the command
    if kalite_dir:
        kalite_bin = os.path.join(kalite_dir, "bin", "kalite")
    else:
        kalite_bin = 'kalite'

    cmd = (kalite_bin, "manage", command) if os.name != "nt" else (sys.executable, kalite_bin, "manage", command)
    for arg in args:
        cmd += (arg,)

    kwargs_keys = kwargs.keys()
    
    # Ensure --settings occurs first, as otherwise docopt parsing barfs
    kwargs_keys = sorted(kwargs_keys, cmp=lambda x,y: -1 if x=="settings" else 0)
    
    for key in kwargs_keys:
        val = kwargs[key]
        key = key.replace(u"_",u"-")
        prefix = u"--" if command != "runcherrypyserver" else u""  # hack, but ... whatever!
        if isinstance(val, bool):
            cmd += (u"%s%s" % (prefix, key),)
        else:
            # TODO(jamalex): remove this replacement, after #4066 is fixed:
            # https://github.com/learningequality/ka-lite/issues/4066
            cleaned_val = unicode(val).replace(" ", "")
            cmd += (u"%s%s=%s" % (prefix, key, cleaned_val),)

    # we also need to change the environment to point to the the local
    # kalite settings. This is especially important for when the
    # central server calls this function, as if we don't change this,
    # kalitectl.py wil look for centralserver.settings instead of
    # kalite.settings.
    new_env = os.environ.copy()
    new_env["DJANGO_SETTINGS_MODULE"] = kwargs.get("settings") or "kalite.settings"

    extra_path = kwargs.pop("pythonpath", None)
    
    if extra_path:
        new_env["PYTHONPATH"] = extra_path

    p = subprocess.Popen(
        cmd,
        shell=False,
        # cwd=os.path.split(cmd[0])[0],
        stdout=None if output_to_stdout else subprocess.PIPE,
        stderr=None if output_to_stderr else subprocess.PIPE,
        env=new_env,
    )
    out = p.communicate() if wait else (None, None)

    # tuple output of stdout, stderr, exit code and process object
    return out + (1 if out[1] else 0, p)


class DistributedServer(object):

    def __init__(self, *args, **kwargs):
        # self.kalite_submodule_dir = pathlib.Path(settings.PROJECT_PATH).parent / 'ka-lite-submodule'
        # self.distributed_dir = (self.kalite_submodule_dir / 'kalite')
        # self.manage_py_path = self.distributed_dir / 'manage.py'

        self.path_temp = tempfile.mkdtemp()

        # Create an __init__ to make it a package
        # open(os.path.join(self.path_temp, "__init__.py"), "w").write("\n")

        uniq_name = 'settings_' + ''.join(choice(string.ascii_lowercase) for _ in range(10))

        self.key = kwargs.pop("key", None) or Key()

        # setup for custom settings for this distributed server
        self.settings_name = uniq_name
        self.settings_contents = self._generate_settings(**kwargs)
        self.settings_path = (pathlib.Path(self.path_temp) / self.settings_name).with_suffix(".py")

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
        new_settings = new_settings % os.path.join(self.path_temp, "db.sqlite3")

        # super hack to not run migrations on the distributed servers.
        # Basically, we replace south's syncdb (which adds migrations)
        # with the normal syncdb
        new_settings += '''
INSTALLED_APPS = filter(lambda app: 'south' not in app, INSTALLED_APPS)

INSTALLED_APPS.append("fle_utils.testing")  # Contains 'runcode' command
        '''

        # write some pregenerated pub/priv keys to the settings file,
        # to avoid having to generate some on the fly (which is slow)
        new_settings += '''
OWN_DEVICE_PUBLIC_KEY = %r
OWN_DEVICE_PRIVATE_KEY = %r
        ''' % (self.key.get_public_key_string(), self.key.get_private_key_string())

        # we have to remove the protocol (http or https) from the url
        # that the user gives to us
        if 'CENTRAL_SERVER_URL' in kwargs:
            parse_result = urlparse(kwargs['CENTRAL_SERVER_URL'])
            kwargs['CENTRAL_SERVER_HOST'] = parse_result.netloc
            kwargs['SECURESYNC_PROTOCOL'] = parse_result.scheme

        other_settings = ['%s = %r' % (k, v) for k, v in kwargs.iteritems()]
        new_settings = '\n'.join([new_settings] + other_settings)
        import kalite
        old_settings_path = os.path.join(os.path.dirname(kalite.__file__), 'project/settings/base.py')
        with open(old_settings_path, "r") as f:
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
        kwargs['pythonpath'] = self.path_temp

        _, _err, _ret, self.running_process = call_outside_command_with_output(
            commandname,
            output_to_stdout=output_to_stdout,
            output_to_stderr=output_to_stderr,
            settings=self.settings_name,
            # kalite_dir=str(self.kalite_submodule_dir),
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
            errmsgtemplate = "command returned non-zero errcode: stderr is %s" % stderr
            print(errmsgtemplate)
            raise subprocess.CalledProcessError(returncode,
                                                self.commandname,
                                                output=errmsgtemplate)

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
        with self.settings_path.open('w') as f:
            f.write(unicode(self.settings_contents))

        # prepare the DB
        self.call_command('syncdb', noinput=True, output_to_stdout=False)
        self.wait()

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if self.settings_path.exists():
            self.settings_path.unlink()
