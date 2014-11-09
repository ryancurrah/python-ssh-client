from ssh_client.ssh_client import SshClient

def mount_file_system(source_file_system, mount_directory, su_as='root'):
    """
    :param source_file_system: The mount source either a network location or local drive (String)
    :param mount_directory: The destination directory where the files system will be mounted to (String)
    :param su_as: The name of the user su as to run/execute the command (String)
    :return: sshclient result dict
    """
    if not isinstance(source_file_system, (str, basestring, unicode)):
	raise TypeError('source_file_system input variable is not a string or unicode type.')
    if not isinstance(mount_directory, (str, basestring, unicode)):
	raise TypeError('mount_directory input variable is not a string or unicode type.')

    # Set variables
    hostname = 'host01.acme.com'
    username=settings.DEV_CLOUD_USERNAME,
    private_key_file=settings.DEV_CLOUD_KEY)

    sshclient = SshClient(hostname=hostname, username=username, private_key_file=private_key_file)

    sudo_su = _sudo_su_command(su_as)
    command = ['{SUDO_SU}'.format(SUDO_SU=sudo_su),
		'mount {SOURCE_FS} {MOUNT_DIR}'.format(SOURCE_FS=source_file_system,
						       MOUNT_DIR=mount_directory)]

    result = sshclient.execute_remote_command(command)

    return result

    @staticmethod
    def _sudo_su_command(su_as):
        """
        :param su_as: The user name to su as (String)
        :return: The sudo su command with the requested user (String)
        """
        if not isinstance(su_as, (str, basestring, unicode)):
            raise TypeError('su_as input variable is not a string or unicode type.')
        su_as = su_as.lower()
        if re.match('^root$', su_as):
            return 'sudo su -'
        else:
            return 'sudo su - {SU_AS}'.format(SU_AS=su_as)

