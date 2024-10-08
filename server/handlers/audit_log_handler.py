import json
import logging

from server.logs import init_logging, powerlogger
from server.models.audit_model import AuditLogMessage
from server.services.audit import AuditLogService

init_logging("tmg-audit-logs-processing", debug=False)


logger = logging.getLogger(__name__)


@powerlogger.inject_lambda_context()
def process_messages(event, context):
    audit_log_service = AuditLogService()

    for record in event["Records"]:
        message_body = record["body"]

        try:
            audit_log_message = AuditLogMessage.from_string(message_body)
            audit_log_service.save_audit_log(audit_log_message)

            # process audit log by calling shopify api
            if audit_log_message.type == "EVENT_UPDATED":
                logger.info(f"Processing event updated message: {audit_log_message}")
        except Exception as e:
            logger.exception(f"Error processing message: {message_body}", e)

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}
