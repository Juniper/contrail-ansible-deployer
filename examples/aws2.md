## Introduction

This document contains instructions to deploy a Contrail cluster with OpenStack on AWS using CloudFormation.

## Requirements

To start working on AWS You will need AWS account with API key/secret access.
If You are using IAM AWS account, account should have this inline policy attached:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:*",
                "aws-marketplace:*",
                "sns:*",
                "s3:*",
                "ec2:*",
                "elasticloadbalancing:*",
                "cloudwatch:*",
                "autoscaling:*",
                "iam:*"
            ],
            "Resource": "*"
        }
    ]
}
```

Go to AWS console:

- Click services
- Find IAM service
- Click Users
- Find Yours user, and click on it
- Click "Add inline policy"
- Use JSON editor, and paste above policy
- Review policy
- Add policy name
- Click "Create policy"

## Deploying the Cluster

1. Select the AWS Region:

2. Execute the CloudFormation Template:
- In the AWS services search, look for CloudFormation and select it.
- Click on Create new stack.
- Click on Specify an Amazon S3 template URL, and specify this URL:

https://s3-eu-west-1.amazonaws.com/contrail-ansible-deployer/cloudformation_template.yaml

- Next.
- Give a name to the stack.
- Choose HTTP url for contrail-ansible-deployer config template.
- Optinal: change other values. Next. Next. Next. Create.
- Refresh the page until the stack is in CREATE_COMPLETE status.

When stack will be deployed, please see `output` tab in cloudformation. It will contain
ssh command to log to contrail-ansible-deployer `base` host. You should use password to log there.

From this node You can access all other nodes (user `centos`). IP addressess can be obtain from AWS console
(EC2 service).

If You set `InstallContrail: Yes`, logs from deployment can be found in `/var/log/messages`

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
