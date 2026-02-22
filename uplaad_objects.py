import boto3
s3 = boto3.client('s3')
with open('stop_instances.py', 'rb') as file:
    s3.upload_fileobj(file, 'puneeth-bucket-demo-22-2026-feb', 'stop_instances.py')
    
    print('Uploaded stop_instances.py to S3 bucket')