from __future__ import absolute_import

import uuid

from server.database.models import Order
from server.test import BaseTestCase


class TestOrders(BaseTestCase):
    def assert_equal_response_order_with_db_order(self, order: Order, response_order: dict):
        self.assertEqual(response_order["id"], str(order.id))
        self.assertEqual(response_order["user_id"], str(order.user_id))
        # TODO fix this, it should just return None and not 'None'
        self.assertEqual(response_order["event_id"], str(order.event_id) if order.event_id else "None")
        self.assertEqual(response_order["shipped_date"], order.shipped_date.isoformat() if order.shipped_date else None)
        self.assertEqual(response_order["order_date"], order.order_date.isoformat() if order.order_date else None)
        self.assertEqual(
            response_order["received_date"], order.received_date.isoformat() if order.received_date else None
        )

    def test_get_non_existing_order_by_id(self):
        # when
        response = self.client.open(
            "/orders/{order_id}".format(order_id=str(uuid.uuid4())),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    # def test_get_existing_order_by_id(self):
    #     # given
    #     order_id = str(uuid.uuid4())
    #     user_service = UserService(self.session_factory)
    #
    #     user_data = create_user_request_payload()
    #     user = user_service.create_user(**user_data)
    #
    #     order = create_db_order(id=order_id, user_id=user.id)
    #     self.db.add(order)
    #     self.db.commit()
    #
    #     # when
    #     response = self.client.open(
    #         "/orders/{order_id}".format(order_id=order_id), query_string=self.hmac_query_params, method="GET"
    #     )
    #
    #     # then
    #     self.assert200(response)
    #     self.assert_equal_response_order_with_db_order(order, response.json)
