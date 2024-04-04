from json import JSONEncoder
from server.database.base_model_ import Model
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class CustomJSONEncoder(JSONEncoder):
    include_nulls = False

    def default(self, o):
        if isinstance(o, Model):
            dikt = {}
            for attr, _ in o.openapi_types.items():
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
        elif isinstance(o, Decimal):
            return float(o)  # Round float to 6 decimal places for serialization
        else:
            return super(CustomJSONEncoder, self).default(o)
