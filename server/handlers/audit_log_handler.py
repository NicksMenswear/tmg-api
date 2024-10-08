import json
import logging

from server.database.database_manager import db
from server.database.models import AuditLog
from server.logs import init_logging, powerlogger
from server.models.audit_model import AuditLogMessage

init_logging("tmg-audit-logs-processing", debug=True)


logger = logging.getLogger(__name__)


@powerlogger.inject_lambda_context()
def process_messages(event, context):
    for record in event["Records"]:
        message_body = record["body"]

        try:
            print(f"Processing message: {message_body}")
            logger.info(f"Processing message: {message_body}")

            audit_log_message = AuditLogMessage.from_string(message_body)

            audit_log = AuditLog()
            audit_log.request = audit_log_message.request
            audit_log.type = audit_log_message.type
            audit_log.payload = audit_log_message.payload
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            print(f"Error processing message: {message_body}", str(e))
            logger.exception(f"Error processing message: {message_body}", e)

            return {"statusCode": 500, "body": json.dumps("Error processing messages")}

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}
