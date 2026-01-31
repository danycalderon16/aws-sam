import json
import os
import uuid
import boto3

dynamo_client = boto3.client("dynamodb")
TABLE_NAME = os.environ["TABLE_NAME"]

def lambda_handler(event, context):
    
    http_method = event.get('httpMethod')

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

        return response(200, {"notes": items})

    return response(405, {"message": "Method not allowed"})

def create_note(note: str):
    note_id = str(uuid.uuid4())

    dynamo_client.put_item(
        TableName=TABLE_NAME,
        Item={
            "id": {"S": note_id},
            "note": {"S": note}
        }
    )

    return response(
        201,
        {
            "id": note_id,
            "message": "Note created successfully"
        }
    )


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
