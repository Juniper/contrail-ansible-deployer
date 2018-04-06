## Introduction

This document contains instructions to deploy a Contrail cluster with OpenStack on AWS using CloudFormation.

## Requirements

To start working on AWS You will need AWS account with API key/secret access.

## Deploying the Cluster

1. Select the AWS Region:

2. Execute the CloudFormation Template:
- In the AWS services search, look for CloudFormation and select it.
- Click on Create new stack.
- Click on Specify an Amazon S3 template URL, and specify this URL:

https://s3-eu-west-1.amazonaws.com/contrail-ansible-deployer/cloudformation_template.yaml

- Next. Give a name to the stack.
- Give it an InstancePassword.
- Choose HTTP url for contrail-ansible-deployer config template.
- Optinal: change other values. Next. Next. Next. Create.
- Refresh the page until the stack is in CREATE_COMPLETE status.

## Contrail-ansible-deployer templates

By default contrail ansible deployer will deploy env from:

https://raw.githubusercontent.com/Juniper/contrail-ansible-deployer/master/examples/aws/contrail_with_k8s.yaml

Other templates are available in

https://github.com/Juniper/contrail-ansible-deployer/tree/master/examples/aws/

You can always prepare own template and serve it to cloudformation from any http url (gist, nopaste, s3, own http server, ...)

## Cleanup

When You finish, You should cleanup yours AWS resources.

1) Remove all EC2 instances created by contrail-ansible-deployer
2) Remove ssh key-pair created by contrail-ansible-deployer
3) Remove Cloudformation stack
