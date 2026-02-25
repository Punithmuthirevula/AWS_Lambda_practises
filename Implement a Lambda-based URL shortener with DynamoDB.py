import json
import string
import random
import time
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("url-shortener")

SHORT_ID_LENGTH = 6
BASE_URL = "https://jzgtxkt4ii.execute-api.us-east-1.amazonaws.com/prod/"


def generate_short_id(length=SHORT_ID_LENGTH):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def create_short_url(long_url):
    short_id = generate_short_id()

    try:
        table.put_item(
            Item={
                "short_id": short_id,
                "long_url": long_url,
                "created_at": int(time.time()),
                "clicks": 0
            },
            ConditionExpression="attribute_not_exists(short_id)"
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return create_short_url(long_url)
        raise

    return short_id


def get_long_url(short_id):
    try:
        response = table.update_item(
            Key={"short_id": short_id},
            UpdateExpression="SET clicks = clicks + :inc",
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="ALL_NEW"
        )
        return response["Attributes"].get("long_url")
    except ClientError:
        return None


def get_url_stats(short_id):
    try:
        response = table.get_item(Key={"short_id": short_id})
        return response.get("Item")
    except ClientError:
        return None


def lambda_handler(event, context):
    http_method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", ""))
    path = event.get("path", event.get("rawPath", ""))
    query_params = event.get("queryStringParameters") or {}
    body = {}

    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except (json.JSONDecodeError, TypeError):
            body = {}

    # ----------------------------------------------------------
    # POST /shorten — Create a short URL
    # Body: {"url": "https://example.com/very-long-url"}
    # ----------------------------------------------------------
    if http_method == "POST" and path in ["/shorten", "/prod/shorten"]:
        long_url = body.get("url", "").strip()

        if not long_url:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'url' in request body"})
            }

        if not long_url.startswith(("http://", "https://")):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "URL must start with http:// or https://"})
            }

        short_id = create_short_url(long_url)
        short_url = BASE_URL + short_id

        logger.info("Created short URL: %s -> %s", short_url, long_url)

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "short_id": short_id,
                "short_url": short_url,
                "long_url": long_url
            })
        }

    # ----------------------------------------------------------
    # GET /stats?id=abc123 — Get click stats for a short URL
    # ----------------------------------------------------------
    if http_method == "GET" and path in ["/stats", "/prod/stats"]:
        short_id = query_params.get("id", "").strip()

        if not short_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'id' query parameter"})
            }

        stats = get_url_stats(short_id)

        if not stats:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Short URL not found"})
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "short_id": stats["short_id"],
                "long_url": stats["long_url"],
                "clicks": int(stats["clicks"]),
                "created_at": int(stats["created_at"])
            })
        }

    # ----------------------------------------------------------
    # GET /{short_id} — Redirect to the original long URL
    # ----------------------------------------------------------
    if http_method == "GET":
        short_id = path.strip("/").split("/")[-1]

        if not short_id or len(short_id) != SHORT_ID_LENGTH:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid short URL"})
            }

        long_url = get_long_url(short_id)

        if not long_url:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Short URL not found"})
            }

        logger.info("Redirecting %s -> %s", short_id, long_url)

        return {
            "statusCode": 301,
            "headers": {
                "Location": long_url,
                "Cache-Control": "no-cache"
            },
            "body": ""
        }

    # ----------------------------------------------------------
    # Unknown route
    # ----------------------------------------------------------
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Not found",
            "usage": {
                "shorten": "POST /shorten {\"url\": \"https://example.com\"}",
                "redirect": "GET /{short_id}",
                "stats": "GET /stats?id={short_id}"
            }
        })
    }