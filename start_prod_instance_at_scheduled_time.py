import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2_client = boto3.client("ec2")


def get_instances_by_tag(env_value, desired_state):
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {"Name": "tag:Environment", "Values": [env_value]},
                {"Name": "instance-state-name", "Values": [desired_state]}
            ]
        )
        instance_ids = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance_ids.append(instance["InstanceId"])
        return instance_ids
    except ClientError as exc:
        logger.error("Error describing instances: %s", exc)
        return []


def lambda_handler(event, context):
    instance_ids = get_instances_by_tag("prod", "stopped")

    if not instance_ids:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No stopped prod instances found.", "started_instances": []})
        }

    try:
        ec2_client.start_instances(InstanceIds=instance_ids)
        logger.info("Started prod instances: %s", instance_ids)
    except ClientError as exc:
        logger.error("Failed to start instances: %s", exc)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(exc)})
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "action": "START",
            "environment": "prod",
            "started_instances": instance_ids,
            "count": len(instance_ids)
        })
    }