import json


def process_messages(event, context):
    for record in event["Records"]:
        message_body = record["body"]

        print(f"Processing message: {message_body}")

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}
