import connexion
import six

from openapi_server.models.audit_log import AuditLog  # noqa: E501
from openapi_server import util


def list_audit_entries():  # noqa: E501
    """Lists all audit entries

     # noqa: E501


    :rtype: List[AuditLog]
    """
    return 'do some magic!'
