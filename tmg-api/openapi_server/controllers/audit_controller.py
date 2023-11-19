import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.audit_log import AuditLog  # noqa: E501
from openapi_server import util


def list_audit_entries():  # noqa: E501
    """Lists all audit entries

     # noqa: E501


    :rtype: Union[List[AuditLog], Tuple[List[AuditLog], int], Tuple[List[AuditLog], int, Dict[str, str]]
    """
    return 'do some magic!'
