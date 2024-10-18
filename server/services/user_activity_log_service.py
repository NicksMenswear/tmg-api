from server.models.audit_model import AuditLogMessage


class UserActivityLogService:
    def __init__(self):
        pass

    def user_created(self, audit_log_message: AuditLogMessage):
        print(audit_log_message)
