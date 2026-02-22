import boto3

ec2 = boto3.resource('ec2', region_name='us-east-1')
client = boto3.client('ec2', region_name='us-east-1')

# 1. Create VPC
vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
vpc.wait_until_available()
vpc.create_tags(Tags=[{'Key': 'Name', 'Value': 'puneeth-vpc'}])
print(f'VPC created: {vpc.id}')

# 2. Enable DNS support and hostnames
client.modify_vpc_attribute(VpcId=vpc.id, EnableDnsSupport={'Value': True})
client.modify_vpc_attribute(VpcId=vpc.id, EnableDnsHostnames={'Value': True})

# 3. Create Public Subnet
public_subnet = ec2.create_subnet(
    VpcId=vpc.id,
    CidrBlock='10.0.1.0/24',
    AvailabilityZone='us-east-1a'
)
public_subnet.create_tags(Tags=[{'Key': 'Name', 'Value': 'puneeth-public-subnet'}])
print(f'Public Subnet created: {public_subnet.id}')

# 4. Create Private Subnet
private_subnet = ec2.create_subnet(
    VpcId=vpc.id,
    CidrBlock='10.0.2.0/24',
    AvailabilityZone='us-east-1b'
)
private_subnet.create_tags(Tags=[{'Key': 'Name', 'Value': 'puneeth-private-subnet'}])
print(f'Private Subnet created: {private_subnet.id}')

# 5. Create Internet Gateway and attach to VPC
igw = ec2.create_internet_gateway()
igw.create_tags(Tags=[{'Key': 'Name', 'Value': 'puneeth-igw'}])
vpc.attach_internet_gateway(InternetGatewayId=igw.id)
print(f'Internet Gateway created and attached: {igw.id}')

# 6. Create Route Table for Public Subnet
public_route_table = vpc.create_route_table()
public_route_table.create_tags(Tags=[{'Key': 'Name', 'Value': 'puneeth-public-rt'}])

# Add route to Internet Gateway (0.0.0.0/0 -> IGW)
public_route_table.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=igw.id
)

# Associate route table with public subnet
public_route_table.associate_with_subnet(SubnetId=public_subnet.id)
print(f'Public Route Table created and associated: {public_route_table.id}')

# 7. Enable auto-assign public IP for public subnet
client.modify_subnet_attribute(
    SubnetId=public_subnet.id,
    MapPublicIpOnLaunch={'Value': True}
)

print('\n--- Summary ---')
print(f'VPC:             {vpc.id}')
print(f'Public Subnet:   {public_subnet.id} (10.0.1.0/24, us-east-1a)')
print(f'Private Subnet:  {private_subnet.id} (10.0.2.0/24, us-east-1b)')
print(f'Internet Gateway: {igw.id}')
print(f'Public Route Table: {public_route_table.id}')
