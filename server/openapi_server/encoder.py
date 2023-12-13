import six
from json.encoder import JSONEncoder
from openapi_server.models.base_model_ import Model


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
        return super(CustomJSONEncoder, self).default(o)

