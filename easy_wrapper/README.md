1. Change inventory/group_vars/all.yml

2. Ensure you are able to do a passwordless ssh to the target hosts:
       Add the public key of the ansible host to the authorized_keys file of the target host 
       Configure sshd to accept root login.

Run ./provision_contrail.sh

