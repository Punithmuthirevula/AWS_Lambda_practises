import json
import logging
from datetime import datetime, timezone, timedelta

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

OUTDATED_THRESHOLD_DAYS = 90


def _is_bucket_empty(bucket_name):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        return response.get("KeyCount", 0) == 0
    except ClientError as exc:
        logger.warning("Could not list objects in %s: %s", bucket_name, exc)
        return False


def _is_bucket_outdated(creation_date, threshold_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=threshold_days)
    return creation_date < cutoff


def _delete_all_objects(bucket_name):
    deleted = 0
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name):
            objects = page.get("Contents", [])
            if objects:
                delete_keys = [{"Key": obj["Key"]} for obj in objects]
                s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={"Objects": delete_keys, "Quiet": True},
                )
                deleted += len(delete_keys)
        try:
            ver_paginator = s3_client.get_paginator("list_object_versions")
            for page in ver_paginator.paginate(Bucket=bucket_name):
                versions = page.get("Versions", []) + page.get("DeleteMarkers", [])
                if versions:
                    delete_keys = [
                        {"Key": v["Key"], "VersionId": v["VersionId"]}
                        for v in versions
                    ]
                    s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={"Objects": delete_keys, "Quiet": True},
                    )
                    deleted += len(delete_keys)
        except ClientError:
            pass
    except ClientError as exc:
        logger.error("Error deleting objects from %s: %s", bucket_name, exc)
    return deleted


def _delete_bucket(bucket_name):
    _delete_all_objects(bucket_name)
    s3_client.delete_bucket(Bucket=bucket_name)
    logger.info("Deleted bucket: %s", bucket_name)


def lambda_handler(event, context):
    threshold_days = int(event.get("threshold_days", OUTDATED_THRESHOLD_DAYS))

    try:
        buckets = s3_client.list_buckets().get("Buckets", [])
    except ClientError as exc:
        logger.error("Failed to list buckets: %s", exc)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(exc)})
        }

    deleted_empty = []
    deleted_outdated = []
    skipped = []
    errors = []

    for bucket in buckets:
        name = bucket["Name"]
        creation_date = bucket["CreationDate"]
        empty = _is_bucket_empty(name)
        outdated = _is_bucket_outdated(creation_date, threshold_days)

        if not empty and not outdated:
            skipped.append(name)
            continue

        reason = []
        if empty:
            reason.append("empty")
        if outdated:
            reason.append("outdated")

        try:
            _delete_bucket(name)
            if "empty" in reason:
                deleted_empty.append(name)
            if "outdated" in reason:
                deleted_outdated.append(name)
        except ClientError as exc:
            logger.error("Failed to delete bucket %s: %s", name, exc)
            errors.append({"bucket": name, "error": str(exc)})

    summary = {
        "threshold_days": threshold_days,
        "total_buckets_scanned": len(buckets),
        "deleted_empty_buckets": deleted_empty,
        "deleted_outdated_buckets": deleted_outdated,
        "total_deleted": len(set(deleted_empty + deleted_outdated)),
        "skipped_buckets": skipped,
        "errors": errors
    }

    logger.info("Cleanup summary: %s", json.dumps(summary))

    return {
        "statusCode": 200,
        "body": json.dumps(summary, default=str)
    }