#!/usr/bin/env python
import paramiko
import os
from argparse import ArgumentParser

def get_args():
    """
    Get CLI arguments.
    """
    parser = ArgumentParser(description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='ESXi host to connect to.')

    parser.add_argument('-u', '--username',
                        required=True,
                        action='store',
                        help='Username to use.')

    parser.add_argument('-p', '--password',
                        required=True,
                        action='store',
                        help='Password to use.')

    parser.add_argument('--mac',
                        required=False,
                        action='store',
                        default=None,
                        help='MAC of ContrailVM.')

    args = parser.parse_args()

    return args

def put_file(host, username, password, dirname, filename, mac):
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, password=password)
    sftp = ssh.open_sftp()
    f = sftp.open(dirname + '/' + filename, 'w')
    f.write('mac:' + mac + '\n')
    f.close()
    ssh.close()


def main():
    args = get_args()

    # Copy ContrailVM MAC to ESXi host
    put_file(args.host, args.username, args.password, '/var/tmp', 'mac', args.mac)


if __name__ == "__main__":
    exit(main())

