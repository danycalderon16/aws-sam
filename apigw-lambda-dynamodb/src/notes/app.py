import json
import logging
import os
import uuid
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo_client = boto3.client("dynamodb")
TABLE_NAME = os.environ["TABLE_NAME"]

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        http_method = event.get('httpMethod')
        logger.info(f"Processing {http_method} request")

        if http_method == "POST":
            body = json.loads(event.get('body', '{}'))
            note = body.get('note', '')
            
            if not note:
                return response(400, {"message": "note is required"})

            return create_note(note)
            
        if http_method == "GET":
            dynamo_response = dynamo_client.scan(
                TableName=TABLE_NAME
            )
            items = dynamo_response.get("Items", [])
            notes = [{"id": item.get("id").get("S"), "note": item.get("note").get("S")} for item in items]

            return response(200, {"data": notes})
        
        if http_method == "DELETE":
            path_params = event.get("pathParameters")
            if not path_params or not path_params.get("id"):
                return response(400, {"message": "Note ID is required"})
                
            note_id = path_params.get("id")
            
            try:
                get_response = dynamo_client.get_item(
                    TableName=TABLE_NAME,
                    Key={"id": {"S": note_id}}
                )
                if "Item" not in get_response:
                    return response(404, {"message": "Note not found"})
            except ClientError as e:
                logger.error(f"DynamoDB error: {e}")
                return response(500, {"message": "Error checking note"})
            
            dynamo_client.delete_item(
                TableName=TABLE_NAME,
                Key={"id": {"S": note_id}}
            )
            
            logger.info(f"Note deleted: {note_id}")
            return response(204, {})

        return response(405, {"message": "Method not allowed"})
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return response(400, {"message": "Invalid JSON"})
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return response(500, {"message": "Internal server error"})

def create_note(note: str) -> Dict[str, Any]:
    try:
        note_id = str(uuid.uuid4())

        dynamo_client.put_item(
            TableName=TABLE_NAME,
            Item={
                "id": {"S": note_id},
                "note": {"S": note}
            }
        )

        logger.info(f"Note created: {note_id}")
        return response(
            201,
            {
                "data": {
                    "id": note_id,
                    "note": note
                },
                "message": "Note created successfully"
            }
        )
    except ClientError as e:
        logger.error(f"Failed to create note: {e}")
        return response(500, {"message": "Failed to create note"})


def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*", 
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
            "Content-Type": "application/json"
        },
        "body": json.dumps(body) if body else ""
    }
