import boto3

client = boto3.client('s3')
response = client.create_bucket(
    ACL='private',
    Bucket='puneeth-bucket-demo-22-2026-feb'
)
print('Created bucket:', response)