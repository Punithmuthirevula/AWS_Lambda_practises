import json
import uuid
import time
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("users")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body, default=str)
    }


def create_user(body):
    user_id = str(uuid.uuid4())
    name = body.get("name", "").strip()
    email = body.get("email", "").strip()
    age = body.get("age")
    role = body.get("role", "user").strip()

    if not name or not email:
        return response(400, {"error": "name and email are required"})

    item = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": role,
        "created_at": int(time.time()),
        "updated_at": int(time.time())
    }

    if age is not None:
        item["age"] = int(age)

    try:
        table.put_item(Item=item)
        logger.info("Created user: %s", user_id)
        return response(201, {"message": "User created", "user": item})
    except ClientError as exc:
        logger.error("Error creating user: %s", exc)
        return response(500, {"error": str(exc)})


def get_user(user_id):
    if not user_id:
        return response(400, {"error": "user_id is required"})

    try:
        result = table.get_item(Key={"user_id": user_id})
        item = result.get("Item")

        if not item:
            return response(404, {"error": "User not found"})

        return response(200, {"user": item})
    except ClientError as exc:
        logger.error("Error getting user: %s", exc)
        return response(500, {"error": str(exc)})


def get_all_users():
    try:
        result = table.scan()
        users = result.get("Items", [])

        while "LastEvaluatedKey" in result:
            result = table.scan(ExclusiveStartKey=result["LastEvaluatedKey"])
            users.extend(result.get("Items", []))

        return response(200, {"users": users, "count": len(users)})
    except ClientError as exc:
        logger.error("Error scanning users: %s", exc)
        return response(500, {"error": str(exc)})


def update_user(user_id, body):
    if not user_id:
        return response(400, {"error": "user_id is required"})

    try:
        existing = table.get_item(Key={"user_id": user_id})
        if "Item" not in existing:
            return response(404, {"error": "User not found"})
    except ClientError as exc:
        return response(500, {"error": str(exc)})

    update_parts = []
    expression_values = {}
    expression_names = {}

    allowed_fields = ["name", "email", "age", "role"]

    for field in allowed_fields:
        if field in body:
            update_parts.append(f"#{field} = :{field}")
            expression_names[f"#{field}"] = field
            expression_values[f":{field}"] = body[field]

    if not update_parts:
        return response(400, {"error": "No valid fields to update"})

    update_parts.append("#updated_at = :updated_at")
    expression_names["#updated_at"] = "updated_at"
    expression_values[":updated_at"] = int(time.time())

    update_expression = "SET " + ", ".join(update_parts)

    try:
        result = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        logger.info("Updated user: %s", user_id)
        return response(200, {"message": "User updated", "user": result["Attributes"]})
    except ClientError as exc:
        logger.error("Error updating user: %s", exc)
        return response(500, {"error": str(exc)})


def delete_user(user_id):
    if not user_id:
        return response(400, {"error": "user_id is required"})

    try:
        existing = table.get_item(Key={"user_id": user_id})
        if "Item" not in existing:
            return response(404, {"error": "User not found"})

        table.delete_item(Key={"user_id": user_id})
        logger.info("Deleted user: %s", user_id)
        return response(200, {"message": "User deleted", "user_id": user_id})
    except ClientError as exc:
        logger.error("Error deleting user: %s", exc)
        return response(500, {"error": str(exc)})


def lambda_handler(event, context):
    http_method = event.get("httpMethod", "")
    path = event.get("path", "")
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}
    body = {}

    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except (json.JSONDecodeError, TypeError):
            return response(400, {"error": "Invalid JSON body"})

    if http_method == "OPTIONS":
        return response(200, {"message": "CORS preflight"})

    user_id = path_params.get("user_id", "")

    # POST /users — Create a new user
    if http_method == "POST" and "/users" in path:
        return create_user(body)

    # GET /users — Get all users
    if http_method == "GET" and "/users" in path and not user_id:
        return get_all_users()

    # GET /users/{user_id} — Get a single user
    if http_method == "GET" and user_id:
        return get_user(user_id)

    # PUT /users/{user_id} — Update a user
    if http_method == "PUT" and user_id:
        return update_user(user_id, body)

    # DELETE /users/{user_id} — Delete a user
    if http_method == "DELETE" and user_id:
        return delete_user(user_id)

    return response(404, {
        "error": "Not found",
        "usage": {
            "create": "POST /users {name, email, age, role}",
            "get_all": "GET /users",
            "get_one": "GET /users/{user_id}",
            "update": "PUT /users/{user_id} {name, email, age, role}",
            "delete": "DELETE /users/{user_id}"
        }
    })

#############################################Below are the test events to follow###################

#Add user

# {
#     "httpMethod": "POST",
#     "path": "/users",
#     "pathParameters": null,
#     "body": "{\"name\": \"Puneeth\", \"email\": \"puneeth@example.com\", \"age\": 25, \"role\": \"admin\"}"
# }



#Get all user details

#     {
#     "httpMethod": "GET",
#     "path": "/users/bd66ce8e-07d2-4a7c-9fe7-3f23a28addeb",
#     "pathParameters": {"user_id": "bd66ce8e-07d2-4a7c-9fe7-3f23a28addeb"}
# }


#Update User

# {
#     "httpMethod": "PUT",
#     "path": "/users/bd66ce8e-07d2-4a7c-9fe7-3f23a28addeb",
#     "pathParameters": {"user_id": "bd66ce8e-07d2-4a7c-9fe7-3f23a28addeb"},
#     "body": "{\"name\": \"Puneeth Updated\", \"role\": \"superadmin\"}"
# }


#Delete user

# {
#     "httpMethod": "DELETE",
#     "path": "/users/bd66ce8e-07d2-4a7c-9fe7-3f23a28addeb",
#     "pathParameters": {"user_id": "bd66ce8e-07d2-4a7c-9fe7-3f23a28addeb"}
# }