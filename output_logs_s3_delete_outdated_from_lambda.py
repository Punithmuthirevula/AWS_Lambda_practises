# Lambda Execution Log and Response for S3 Outdated Bucket Deletion

# Status: Succeeded
# Test Event Name: delete_s3_event

response = {
    "statusCode": 200,
    "body": "{\"threshold_days\": 15, \"total_buckets_scanned\": 16, \"deleted_empty_buckets\": [\"dmeo-demo-demo\", \"uejvjwhvjwejbfkddbwke\"], \"deleted_outdated_buckets\": [], \"total_deleted\": 2, \"skipped_buckets\": [\"aws-cloudtrail-logs-267527029614-09da5221\", \"aws-cloudtrail-logs-267527029614-5c3f472d\", \"cloudfront-website-hosting-bucket-feb-12th-2026\", \"destination-bucket-feb-10th-2026\", \"destination-bucket-feb-11th20206-replication\", \"destination-bucket-lambda-compress-image-app-feb-18\", \"destination-puneeth-s3-bucket-lambda-feb-22-2026\", \"first-boto3-bucket-feb-20th-2026\", \"puneeth-bucket-demo-22-2026-feb\", \"s3-versioning-bucket-feb-10th-2026\", \"source-bucket-feb-11th20206-replication\", \"source-puneeth-s3-bucket-lambda-feb-22-2026\", \"storage-classes-bucket-feb-11th-2026\", \"vpc-flowlogs-bucket-feb-23rd-2026\"], \"errors\": []}"
}

# Function Logs:
# START RequestId: f234c7a6-8663-4ea5-b304-cdcabf634353 Version: $LATEST
# [INFO] 2026-02-24T11:15:28.913Z Deleted bucket: dmeo-demo-demo
# [INFO] 2026-02-24T11:15:32.121Z Deleted bucket: uejvjwhvjwejbfkddbwke
# [INFO] 2026-02-24T11:15:32.328Z Cleanup summary:
#   {"threshold_days": 15, "total_buckets_scanned": 16, "deleted_empty_buckets": ["dmeo-demo-demo", "uejvjwhvjwejbfkddbwke"], "deleted_outdated_buckets": [], "total_deleted": 2, "skipped_buckets": ["aws-cloudtrail-logs-267527029614-09da5221", "aws-cloudtrail-logs-267527029614-5c3f472d", "cloudfront-website-hosting-bucket-feb-12th-2026", "destination-bucket-feb-10th-2026", "destination-bucket-feb-11th20206-replication", "destination-bucket-lambda-compress-image-app-feb-18", "destination-puneeth-s3-bucket-lambda-feb-22-2026", "first-boto3-bucket-feb-20th-2026", "puneeth-bucket-demo-22-2026-feb", "s3-versioning-bucket-feb-10th-2026", "source-bucket-feb-11th20206-replication", "source-puneeth-s3-bucket-lambda-feb-22-2026", "storage-classes-bucket-feb-11th-2026", "vpc-flowlogs-bucket-feb-23rd-2026"], "errors": []}
# END RequestId: f234c7a6-8663-4ea5-b304-cdcabf634353
# REPORT RequestId: f234c7a6-8663-4ea5-b304-cdcabf634353 Duration: 7193.83 ms Billed Duration: 7194 ms Memory Size: 128 MB Max Memory Used: 97 MB
# Request ID: f234c7a6-8663-4ea5-b304-cdcabf634353
