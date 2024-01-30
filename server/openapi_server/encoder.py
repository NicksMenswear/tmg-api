from json import JSONEncoder
from openapi_server.models.base_model_ import Model
import six
from datetime import datetime
from uuid import UUID

class CustomJSONEncoder(JSONEncoder):
    include_nulls = False

    def default(self, o):
        if isinstance(o, Model):
            dikt = {}
            for attr, _ in six.iteritems(o.openapi_types):
                value = getattr(o, attr)
                if value is None and not self.include_nulls:
                    continue
                attr = o.attribute_map[attr]
                dikt[attr] = value
            return dikt
        elif isinstance(o, UUID):
            return str(o)  # Convert UUID to string for serialization
        elif isinstance(o, datetime):
            return o.isoformat()  # Convert datetime to ISO 8601 format
        return super(CustomJSONEncoder, self).default(o)
