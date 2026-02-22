import boto3

ec2 = boto3.client('ec2', region_name='us-east-1')

# Replace with the Volume ID from createEBSvolume.py output
VOLUME_ID = input('Enter the Volume ID to delete: ')

# Wait until volume is available before deleting
waiter = ec2.get_waiter('volume_available')
print(f'Waiting for volume {VOLUME_ID} to be available...')
waiter.wait(VolumeIds=[VOLUME_ID])

# Delete EBS Volume
response = ec2.delete_volume(VolumeId=VOLUME_ID)

if response['ResponseMetadata']['HTTPStatusCode'] == 200:
    print(f'EBS Volume {VOLUME_ID} deleted successfully!')
else:
    print(f'Failed to delete volume {VOLUME_ID}')
