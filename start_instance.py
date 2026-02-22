import boto3

ec2 = boto3.client('ec2')
response = ec2.start_instances(InstanceIds=['i-092ed41856e6a7271'])
print('Started instance:', response)


