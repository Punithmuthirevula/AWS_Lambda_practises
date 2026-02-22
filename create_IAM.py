import boto3

iam = boto3.client('iam')

USERNAME = 'puneeth-user-demo-22-2026'

# 1. Create IAM User
response = iam.create_user(UserName=USERNAME)
print(f'IAM User created: {response["User"]["UserName"]}')
print(f'ARN: {response["User"]["Arn"]}')

# 2. Attach EC2 Full Access policy
ec2_policy_arn = 'arn:aws:iam::aws:policy/AmazonEC2FullAccess'
iam.attach_user_policy(UserName=USERNAME, PolicyArn=ec2_policy_arn)
print(f'Attached policy: AmazonEC2FullAccess')

# 3. Attach S3 Full Access policy
s3_policy_arn = 'arn:aws:iam::aws:policy/AmazonS3FullAccess'
iam.attach_user_policy(UserName=USERNAME, PolicyArn=s3_policy_arn)
print(f'Attached policy: AmazonS3FullAccess')

# 4. Create access keys for programmatic access
keys = iam.create_access_key(UserName=USERNAME)
access_key = keys['AccessKey']
print(f'\nAccess Key ID:     {access_key["AccessKeyId"]}')
print(f'Secret Access Key: {access_key["SecretAccessKey"]}')
print('\n Save the Secret Access Key now — you cannot retrieve it again!')

# 5. Verify attached policies
attached = iam.list_attached_user_policies(UserName=USERNAME)
print(f'\n--- Attached Policies for {USERNAME} ---')
for policy in attached['AttachedPolicies']:
    print(f'  - {policy["PolicyName"]} ({policy["PolicyArn"]})')
