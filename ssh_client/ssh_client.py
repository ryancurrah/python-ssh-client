import paramiko
import socket
import time


class SshClient(object):
    _hostname = ''
    _username = ''
    _private_key_file = ''
    _connection_timeout = None
    _command_timeout = None
    _command_sleep = None

    def __init__(self,
                 hostname,
                 username,
                 password='',
                 private_key_file='',
                 connection_timeout=None,
                 command_timeout=None,
                 command_sleep=None):
        """
        :param hostname: Hostname or ip address string of the server
        :param username: Username of the user on the server
        :param password: Password of the user on the server can also be used for the private key pass phrase
        :param private_key_file: Full path and file name of the private key '/home/johndoe2/.ssh/my_key.priv'
        :param connection_timeout: timeout in seconds before giving up connecting to the server
        :param command_timeout: timeout in seconds for executing a command on the server
        :param command_sleep: sleep time in seconds to wait before returning after command execution
        :return: Nothing
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.private_key_file = private_key_file
        self.connection_timeout = connection_timeout
        self.command_timeout = command_timeout
        self.command_sleep = command_sleep

    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        if not value:
            raise ValueError(u"You must enter an Hostname!")
        self._hostname = value

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if not value:
            raise ValueError(u"You must enter an Username!")
        self._username = value

    @property
    def private_key_file(self):
        return self._private_key_file

    @private_key_file.setter
    def private_key_file(self, value):
        if not value and not self.password:
            raise ValueError(u"You must provide a password or private key file or both!")
        if value:
            value = value.rstrip('/')
        self._private_key_file = value

    @property
    def connection_timeout(self):
        return self._connection_timeout

    @connection_timeout.setter
    def connection_timeout(self, value):
        if value:
            if not isinstance(value, (int, long)):
                raise ValueError(u"Connection timeout parameter must be an integer!")
        self._connection_timeout = value

    @property
    def command_timeout(self):
        return self._command_timeout

    @command_timeout.setter
    def command_timeout(self, value):
        if value:
            if not isinstance(value, (int, long)):
                raise ValueError(u"Command execution timeout parameter must be an integer!")
        self._command_timeout = value

    @property
    def command_sleep(self):
        return self._command_sleep

    @command_sleep.setter
    def command_sleep(self, value):
        if value:
            if not isinstance(value, (int, long)):
                raise ValueError(u"Sleep after execute remote command parameter must be an integer!")
        self._command_sleep = value

    def execute_remote_command(self, commands):
        """
        :param commands: A list or Tuple of the commands to execute, must at least contain one command
        :return: Returns a dictionary with:
         1. The status of paramiko connecting and running command; NOT TO BE CONFUSED WITH THE COMMANDS EXIT CODE
         2. Message about the success or failure of the paramiko connection and command execution
         3. String of the standard out returned to the screen by the command
         4. String of the standard error returned to the screen byt the command
         5. Integer exit code status of the command
        """
        # Check commands variable is valid
        value_error_message = u"You must provide the commands argument as strings in a list or tuple."
        if not commands:
            return ValueError(value_error_message)
        if not isinstance(commands, (tuple, list)):
            return ValueError(value_error_message)
        for command in commands:
            if not isinstance(command, (unicode, basestring, str)):
                return ValueError(value_error_message)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.private_key_file and self.password:
                client.connect(hostname=self.hostname,
                               username=self.username,
                               password=self.password,
                               key_filename=self.private_key_file,
                               timeout=self.connection_timeout)
            elif self.private_key_file:
                client.connect(hostname=self.hostname,
                               username=self.username,
                               key_filename=self.private_key_file,
                               timeout=self.connection_timeout)
            else:
                client.connect(hostname=self.hostname,
                               username=self.username,
                               password=self.password,
                               timeout=self.connection_timeout)
        except paramiko.BadHostKeyException:
            return {'status': False,
                    'msg': u"The host key given by the SSH server did not match what we were expecting.",
                    'stdout': None,
                    'stderr': None,
                    'exit_code': None}
        except paramiko.AuthenticationException:
            return {'status': False,
                    'msg': u"Authentication failed for some reason. "
                           u"It may be possible to retry with different credentials.",
                    'stdout': None,
                    'stderr': None,
                    'exit_code': None}
        except paramiko.ChannelException:
            return {'status': False,
                    'msg': u"Exception raised when an attempt to open a new Channel failed.",
                    'stdout': None,
                    'stderr': None,
                    'exit_code': None}
        except paramiko.SSHException as e:
            return {'status': False,
                    'msg': u"There was an error connecting or establishing an SSH session. {0}.".format(e.message),
                    'stdout': None,
                    'stderr': None,
                    'exit_code': None}
        except socket.error:
            return {'status': False,
                    'msg': u"Socket error while connecting.",
                    'stdout': None,
                    'stderr': None,
                    'exit_code': None}
        try:
            channel = client.get_transport().open_session()
            if self.command_timeout:
                channel.settimeout(self.command_timeout)

            # If prompts are required to complete the command loop through
            # the prompt_data and enter into stdin
            # Else it will just run the single command
            for index, command in enumerate(commands):
                # On first command in list start channel execution command
                if index == 0:
                    channel.exec_command(command)
                else:
                    # The shell expects a return statement for each command
                    # place a "\n" in the data if it does not exist
                    # "\n" counts as one character that's why slice is -1
                    if not "\n" in command[-1:]:
                        command += "\n"
                    while True:
                        if channel.send_ready():
                            channel.send(command)
                            break

            channel.shutdown_write()

            stdout = channel.makefile().read()
            stderr = channel.makefile_stderr().read()
            exit_code = channel.recv_exit_status()

            channel.close()
            client.close()

            if self.command_sleep:
                time.sleep(self.command_sleep)
        except socket.timeout:
            return {'status': False,
                    'msg': u"Socket timeout while executing command. This server maybe unresponsive.",
                    'stdout': None,
                    'stderr': None,
                    'exit_code': None}
        except paramiko.SSHException as e:
            return {'status': False,
                    'msg': u"There was an error executing the command an "
                           u"SSH Exception occurred. {0}.".format(e.message),
                    'stdout': None,
                    'stderr': None,
                    'exit_code': None}
        return {'status': True,
                'msg': u"SSH connection executed successfully.",
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code}