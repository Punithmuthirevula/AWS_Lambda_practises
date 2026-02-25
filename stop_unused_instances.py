import json
import logging
from datetime import datetime, timezone, timedelta

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2_client = boto3.client("ec2")
cloudwatch_client = boto3.client("cloudwatch")

CPU_THRESHOLD = 5.0
EVALUATION_PERIOD_HOURS = 24
EXCLUDE_TAG_KEY = "AutoStop"
EXCLUDE_TAG_VALUE = "false"


def get_running_instances():
    instances = []
    try:
        paginator = ec2_client.get_paginator("describe_instances")
        for page in paginator.paginate(
            Filters=[
                {"Name": "instance-state-name", "Values": ["running"]}
            ]
        ):
            for reservation in page["Reservations"]:
                for instance in reservation["Instances"]:
                    tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}

                    if tags.get(EXCLUDE_TAG_KEY, "").lower() == EXCLUDE_TAG_VALUE:
                        continue

                    instances.append({
                        "instance_id": instance["InstanceId"],
                        "instance_type": instance["InstanceType"],
                        "launch_time": instance["LaunchTime"],
                        "name": tags.get("Name", "N/A"),
                        "tags": tags
                    })
    except ClientError as exc:
        logger.error("Error describing instances: %s", exc)

    return instances


def get_avg_cpu(instance_id, period_hours):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=period_hours)

    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[
                {"Name": "InstanceId", "Value": instance_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Average"]
        )

        datapoints = response.get("Datapoints", [])

        if not datapoints:
            return None

        avg_cpu = sum(d["Average"] for d in datapoints) / len(datapoints)
        return round(avg_cpu, 2)

    except ClientError as exc:
        logger.error("Error getting CPU for %s: %s", instance_id, exc)
        return None


def get_network_activity(instance_id, period_hours):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=period_hours)

    total_bytes = 0

    for metric_name in ["NetworkIn", "NetworkOut"]:
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName=metric_name,
                Dimensions=[
                    {"Name": "InstanceId", "Value": instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=["Sum"]
            )

            datapoints = response.get("Datapoints", [])
            total_bytes += sum(d["Sum"] for d in datapoints)

        except ClientError:
            pass

    return round(total_bytes / (1024 * 1024), 2)


def lambda_handler(event, context):
    cpu_threshold = float(event.get("cpu_threshold", CPU_THRESHOLD))
    period_hours = int(event.get("period_hours", EVALUATION_PERIOD_HOURS))
    dry_run = event.get("dry_run", False)

    running_instances = get_running_instances()

    if not running_instances:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No running instances found."})
        }

    unused_instances = []
    active_instances = []
    no_data_instances = []

    for instance in running_instances:
        instance_id = instance["instance_id"]

        avg_cpu = get_avg_cpu(instance_id, period_hours)
        network_mb = get_network_activity(instance_id, period_hours)

        if avg_cpu is None:
            no_data_instances.append({
                "instance_id": instance_id,
                "name": instance["name"],
                "reason": "No CPU data available"
            })
            continue

        if avg_cpu < cpu_threshold and network_mb < 50:
            unused_instances.append({
                "instance_id": instance_id,
                "name": instance["name"],
                "instance_type": instance["instance_type"],
                "avg_cpu": avg_cpu,
                "network_mb": network_mb
            })
        else:
            active_instances.append({
                "instance_id": instance_id,
                "name": instance["name"],
                "avg_cpu": avg_cpu,
                "network_mb": network_mb
            })

    stopped_instances = []
    stop_errors = []

    if unused_instances and not dry_run:
        ids_to_stop = [i["instance_id"] for i in unused_instances]

        try:
            ec2_client.stop_instances(InstanceIds=ids_to_stop)
            stopped_instances = ids_to_stop
            logger.info("Stopped unused instances: %s", ids_to_stop)
        except ClientError as exc:
            logger.error("Failed to stop instances: %s", exc)
            stop_errors.append(str(exc))

    summary = {
        "evaluation_period_hours": period_hours,
        "cpu_threshold_percent": cpu_threshold,
        "network_threshold_mb": 50,
        "dry_run": dry_run,
        "total_running": len(running_instances),
        "unused_detected": len(unused_instances),
        "unused_instances": unused_instances,
        "stopped_instances": stopped_instances,
        "active_instances": active_instances,
        "no_data_instances": no_data_instances,
        "errors": stop_errors
    }

    logger.info("Summary: %s", json.dumps(summary, default=str))

    return {
        "statusCode": 200,
        "body": json.dumps(summary, default=str)
    }