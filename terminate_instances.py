import boto3

ec2 = boto3.client('ec2')
response = ec2.terminate_instances(InstanceIds=['i-092ed41856e6a7271'])
print('Terminated instance:', response)
