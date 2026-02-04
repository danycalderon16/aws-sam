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
        notes = [{"id": item.get("id").get("S"), "note": item.get("note").get("S")} for item in items]

        return response(200, notes)
    
    if http_method == "DELETE":
        print(event.get("pathParameters").get("id"))
        return response(204, {"message": "Note deleted successfully"})

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
            "Access-Control-Allow-Origin": "*", 
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body)
    }
