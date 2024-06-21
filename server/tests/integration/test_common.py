from unittest import TestCase

from server.models.user_model import CreateUserModel


class TestCommon(TestCase):
    def test_model_strip_whitespaces(self):
        data = {
            "first_name": "  John  ",
            "last_name": "  Doe  ",
            "email": "  john@example.com  ",
            "shopify_id": "  123  ",
        }

        create_user_request = CreateUserModel(**data)

        assert create_user_request.first_name == "John"
        assert create_user_request.email == "john@example.com"
        assert create_user_request.shopify_id == "123"
