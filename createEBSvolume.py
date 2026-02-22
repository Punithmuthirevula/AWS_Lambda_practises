import boto3

ec2 = boto3.client('ec2', region_name='us-east-1')

# Create EBS Volume
response = ec2.create_volume(
    AvailabilityZone='us-east-1a',
    Size=10,              # Size in GB
    VolumeType='gp3',     # General Purpose SSD
    TagSpecifications=[
        {
            'ResourceType': 'volume',
            'Tags': [
                {'Key': 'Name', 'Value': 'puneeth-ebs-volume'}
            ]
        }
    ]
)

volume_id = response['VolumeId']
print(f'EBS Volume created: {volume_id}')
print(f'Size: {response["Size"]} GB')
print(f'Type: {response["VolumeType"]}')
print(f'AZ:   {response["AvailabilityZone"]}')
print(f'State: {response["State"]}')
print(f'\nUse this Volume ID to delete: {volume_id}')
