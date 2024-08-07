from datetime import timedelta, datetime

from parameterized import parameterized

from server.database.models import Product, Address
from server.services.order_service import (
    ORDER_STATUS_READY,
    ORDER_STATUS_PENDING_MEASUREMENTS,
    ORDER_STATUS_PENDING_MISSING_SKU,
)
from server.services.sku_builder_service import ProductType, PRODUCT_TYPES_THAT_REQUIRES_MEASUREMENTS
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures, WEBHOOK_SHOPIFY_ENDPOINT

PAID_ORDER_REQUEST_HEADERS = {
    "X-Shopify-Topic": "orders/paid",
}


class TestWebhooksOrderPaidGeneral(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_order_without_items(self):
        # when
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, {}, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        self.assertTrue("Received paid order without items" in response.json["errors"])

    def test_order_with_event_id_in_cart(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=f"product-{utils.generate_unique_string()}")],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order_id = response.json["id"]
        order = self.order_service.get_order_by_id(order_id)
        # self.assertIsNotNone(order.ship_by_date)
        self.assertIsNone(order.ship_by_date)
        self.assertEqual(order.event_id, event_id)

        attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(attendee.pay)

    def test_order_ship_by_date_less_then_six_weeks(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        three_weeks = (datetime.now() + timedelta(weeks=3)).isoformat()
        event_id = self.event_service.create_event(
            fixtures.create_event_request(user_id=user.id, event_at=three_weeks), True
        ).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=f"product-{utils.generate_unique_string()}")],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order_id = response.json["id"]
        order = self.order_service.get_order_by_id(order_id)
        self.assertIsNone(order.ship_by_date)
        self.assertEqual(order.event_id, event_id)

        attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(attendee.pay)

    def test_order_status_for_general_product_without_sku(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        line_item = fixtures.webhook_shopify_line_item()
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(customer_email=user.email, line_items=[line_item]),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json["status"], ORDER_STATUS_PENDING_MISSING_SKU)
        self.assertEqual(response.json["order_items"][0]["shopify_sku"], "")

    def test_order_status_for_general_product_with_unknown_sku(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        line_item = fixtures.webhook_shopify_line_item(sku=f"z{utils.generate_unique_string()}")
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(customer_email=user.email, line_items=[line_item]),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json["status"], ORDER_STATUS_PENDING_MISSING_SKU)
        self.assertEqual(response.json["order_items"][0]["shopify_sku"], line_item["sku"])
        self.assertTrue(len(response.json["products"]) == 0)

    def test_order_general_details(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=user.email,
            line_items=[
                fixtures.webhook_shopify_line_item(sku=self.get_random_shopify_sku_by_product_type(ProductType.BOW_TIE))
            ],
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertEqual(order.user_id, user.id)
        self.assertEqual(order.discount_codes, [])
        self.assertEqual(order.shopify_order_id, str(webhook_request["id"]))
        self.assertEqual(order.shopify_order_number, str(webhook_request["order_number"]))
        self.assertEqual(order.shipping_address_line1, webhook_request["shipping_address"].get("address1"))
        self.assertEqual(order.shipping_address_line2, webhook_request["shipping_address"].get("address2"))
        self.assertEqual(order.shipping_city, webhook_request["shipping_address"]["city"])
        self.assertEqual(order.shipping_state, webhook_request["shipping_address"]["province"])
        self.assertEqual(order.shipping_zip_code, webhook_request["shipping_address"]["zip"])
        self.assertEqual(order.shipping_country, webhook_request["shipping_address"]["country"])
        self.assertEqual(order.order_date.isoformat(), webhook_request["created_at"])
        self.assertEqual(order.status, ORDER_STATUS_READY)
        self.assertEqual(len(order.products), 1)
        self.assertIsNone(order.event_id)
        response_order_item = response.json["order_items"][0]
        request_line_item = webhook_request["line_items"][0]
        self.assertEqual(response_order_item["shopify_sku"], request_line_item["sku"])

        address = Address.query.filter(Address.user_id == user.id).first()
        self.assertIsNotNone(address)
        self.assertEqual(address.user_id, order.user_id)
        self.assertEqual(address.address_line1, order.shipping_address_line1)
        self.assertEqual(address.address_line2, order.shipping_address_line2)
        self.assertEqual(address.city, order.shipping_city)
        self.assertEqual(address.state, order.shipping_state)
        self.assertEqual(address.zip_code, order.shipping_zip_code)
        self.assertEqual(address.country, order.shipping_country)

    def test_order_sku_and_status_for_one_non_measurable_product(self):
        for product_type in ProductType:
            # given
            user = self.user_service.create_user(fixtures.create_user_request())

            # skip suits, unknown and products that require measurements in this test
            if (
                product_type == ProductType.SUIT
                or product_type == ProductType.UNKNOWN
                or product_type in PRODUCT_TYPES_THAT_REQUIRES_MEASUREMENTS
            ):
                continue

            product_sku = self.get_random_shopify_sku_by_product_type(product_type)

            # when
            webhook_request = fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[fixtures.webhook_shopify_line_item(sku=product_sku)],
            )

            response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

            # then
            self.assert200(response)
            order = self.order_service.get_order_by_id(response.json["id"])
            self.assertIsNotNone(order)
            self.assertEqual(order.status, ORDER_STATUS_READY)
            response_order_item = response.json["order_items"][0]
            request_line_item = webhook_request["line_items"][0]
            self.assertEqual(response_order_item["shopify_sku"], request_line_item["sku"])
            self.assertTrue(response_order_item["shopify_sku"].startswith(product_sku))

    def test_order_sku_and_status_for_one_measurable_product(self):
        for product_type in ProductType:
            # given
            user = self.user_service.create_user(fixtures.create_user_request())

            if product_type not in PRODUCT_TYPES_THAT_REQUIRES_MEASUREMENTS or product_type == ProductType.SUIT:
                continue

            product_sku = self.get_random_shopify_sku_by_product_type(product_type)

            # when
            webhook_request = fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[fixtures.webhook_shopify_line_item(sku=product_sku)],
            )

            response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

            # then
            self.assert200(response)
            order = self.order_service.get_order_by_id(response.json["id"])
            self.assertIsNotNone(order)
            self.assertEqual(order.status, ORDER_STATUS_PENDING_MEASUREMENTS)
            response_order_item = response.json["order_items"][0]
            request_line_item = webhook_request["line_items"][0]
            self.assertEqual(response_order_item["shopify_sku"], request_line_item["sku"])
            self.assertTrue(response_order_item["shopify_sku"].startswith(product_sku))

    def test_order_status_for_mix_of_measurable_and_non_measurable_products(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        product_sku1 = self.get_random_shopify_sku_by_product_type(ProductType.JACKET)
        product_sku2 = self.get_random_shopify_sku_by_product_type(ProductType.SOCKS)

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=user.email,
            line_items=[
                fixtures.webhook_shopify_line_item(sku=product_sku1),
                fixtures.webhook_shopify_line_item(sku=product_sku2),
            ],
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertIsNotNone(order)
        self.assertEqual(order.status, ORDER_STATUS_PENDING_MEASUREMENTS)
        self.assertEqual(len(order.products), 1)
        self.assertEqual(len(order.order_items), 2)

    def test_order_status_with_measurements_but_unknown_sku(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        guest = self.user_service.create_user(fixtures.create_user_request())
        measurement = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))
        self.size_service.create_size(fixtures.store_size_request(user_id=guest.id, measurement_id=measurement.id))
        self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=guest.id))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=guest.id, event_id=event_id, email=guest.email)
        )

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=guest.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=f"invalid-{utils.generate_unique_string()}")],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertIsNotNone(order)
        self.assertEqual(order.order_items[0].shopify_sku, webhook_request["line_items"][0]["sku"])
        self.assertTrue(len(order.products) == 0)
        self.assertEqual(order.status, ORDER_STATUS_PENDING_MISSING_SKU)

    @parameterized.expand(
        [
            [["101A1BLK"], ["101A1BLK42RAF"]],  # jacket
            [["201A1BLK"], ["201A1BLK40R"]],  # pants
            [["301A2BLK"], ["301A2BLK00LRAF"]],  # vest
            [["403A2BLK"], ["403A2BLK1605"]],  # shirt
            [["503A400A"], ["503A400AOSR"]],  # bow tie
            [["603A400A"], ["603A400AOSR"]],  # tie
            [["703A4BLK"], ["703A4BLK460R"]],  # belt
            [["803A4BLK"], ["803A4BLK070D"]],  # shoes
            [["903A4BLK"], ["903A4BLKOSR"]],  # socks
            [
                ["101A1BLK", "201A1BLK", "703A4BLK", "903A4BLK"],
                ["101A1BLK42RAF", "201A1BLK40R", "703A4BLK460R", "903A4BLKOSR"],
            ],
        ]
    )
    def test_order_status_ready_shiphero_skus_correctness(self, shopify_skus, shiphero_skus):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())

        measurement = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(
                user_id=attendee_user.id,
                data=fixtures.test_measurements(),
            )
        )
        self.size_service.create_size(
            fixtures.store_size_request(
                user_id=attendee_user.id,
                measurement_id=measurement.id,
                data=fixtures.test_sizes(),
            )
        )

        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=shopify_sku) for shopify_sku in shopify_skus],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertIsNotNone(order)
        self.assertEqual(order.status, ORDER_STATUS_READY)

        response_shopify_skus = set([order_item.shopify_sku for order_item in order.order_items])
        response_shiphero_skus = set([product.sku for product in order.products])

        self.assertEqual(response_shopify_skus, set(shopify_skus))
        self.assertEqual(response_shiphero_skus, set(shiphero_skus))

    @parameterized.expand(
        [
            [
                ["101A2BLK", "201A2BLK", "301A2BLK", "903A4BLK"],
                ["001A2BLK42R", "101A2BLK42RAF", "201A2BLK40R", "301A2BLK00LRAF", "903A4BLKOSR"],
            ]
        ]
    )
    def test_order_with_suit_items_should_include_suit_as_well(self, shopify_skus, shiphero_skus):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        measurement = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(
                user_id=attendee_user.id,
                data=fixtures.test_measurements(),
            )
        )
        self.size_service.create_size(
            fixtures.store_size_request(
                user_id=attendee_user.id,
                measurement_id=measurement.id,
                data=fixtures.test_sizes(),
            )
        )

        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=shopify_sku) for shopify_sku in shopify_skus],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertIsNotNone(order)
        self.assertEqual(order.status, ORDER_STATUS_READY)

        response_shopify_skus = set([order_item.shopify_sku for order_item in order.order_items])
        response_shiphero_skus = set([product.sku for product in order.products])

        self.assertEqual(len(response_shopify_skus), len(shopify_skus) + 1)
        self.assertEqual(response_shiphero_skus, set(shiphero_skus))

    def test_order_process_from_file_without_measurements(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )
        webhook_order_payload = self._read_json_into_dict("assets/webhook_request_01.json")
        webhook_order_payload["customer"]["email"] = attendee_user.email
        webhook_order_payload["note_attributes"][1]["value"] = str(event_id)

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            webhook_order_payload,
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertIsNotNone(order)
        self.assertEqual(order.status, ORDER_STATUS_PENDING_MEASUREMENTS)

        response_shopify_skus = set([order_item.shopify_sku for order_item in order.order_items])
        response_shiphero_skus = set([product.sku for product in order.products])

        self.assertTrue(len(response_shopify_skus) == 8)
        self.assertTrue(len(response_shiphero_skus) == 2)  # only non-measurable products

        self.assertIsNone(order.meta.get("sizes_id"))
        self.assertIsNone(order.meta.get("measurements_id"))

    def test_order_process_from_file_with_measurements(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        measurement_model = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(
                user_id=attendee_user.id,
                data=fixtures.test_measurements(),
            )
        )
        size_model = self.size_service.create_size(
            fixtures.store_size_request(
                user_id=attendee_user.id,
                measurement_id=measurement_model.id,
                data=fixtures.test_sizes(),
            )
        )

        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )
        webhook_order_payload = self._read_json_into_dict("assets/webhook_request_01.json")
        webhook_order_payload["customer"]["email"] = attendee_user.email
        webhook_order_payload["note_attributes"][1]["value"] = str(event_id)

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            webhook_order_payload,
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertIsNotNone(order)
        self.assertEqual(order.status, ORDER_STATUS_READY)

        response_shopify_skus = set([order_item.shopify_sku for order_item in order.order_items])
        response_shiphero_skus = set([product.sku for product in order.products])

        self.assertTrue(len(response_shopify_skus) == 8)
        self.assertTrue(len(response_shiphero_skus) == 8)
        self.assertEqual(order.meta.get("sizes_id"), str(size_model.id))
        self.assertEqual(order.meta.get("measurements_id"), str(measurement_model.id))

    def test_order_process_not_found_in_db_but_found_in_shiphero(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )
        Product.query.delete()  # delete all products from the database
        shopify_sku = self.get_random_shopify_sku_by_product_type(ProductType.BOW_TIE)

        # when
        self.assertEqual(self.product_service.get_num_products(), 0)  # verify no products in products table

        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=shopify_sku)],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order_id = response.json["id"]
        order = self.order_service.get_order_by_id(order_id)
        self.assertEqual(order.status, ORDER_STATUS_READY)
        order_product_shiphero_sku = order.products[0].sku

        product = self.product_service.get_product_by_sku(order_product_shiphero_sku)
        self.assertIsNotNone(product)
        self.assertTrue(product.sku.startswith(shopify_sku))

    def test_order_process_not_found_in_db_and_not_found_in_shiphero(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )
        Product.query.delete()  # delete all products from the database
        shopify_sku = self.get_random_shopify_sku_by_product_type(ProductType.BOW_TIE) + "SHIPHERO_NOT_FOUND"

        # when
        self.assertEqual(self.product_service.get_num_products(), 0)  # verify no products in products table

        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=shopify_sku)],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order_id = response.json["id"]
        order = self.order_service.get_order_by_id(order_id)
        self.assertEqual(order.status, ORDER_STATUS_PENDING_MISSING_SKU)
        self.assertEqual(len(order.products), 0)
        self.assertIsNone(order.order_items[0].product_id)
        self.assertEqual(order.order_items[0].shopify_sku, shopify_sku)
