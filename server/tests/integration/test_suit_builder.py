from server.tests.integration import BaseTestCase, fixtures


class TestSuitBuilder(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.populate_shopify_variants()

    # def test_get_items(self):
    #     # given
    #     suit_item_1 = fixtures.add_suit_builder_item_request(type="suit", index=10)
    #     suit_item_2 = fixtures.add_suit_builder_item_request(type="suit", index=100)
    #     shirt_item = fixtures.add_suit_builder_item_request(type="shirt")
    #     self.suit_builder_service.add_item(suit_item_1)
    #     self.suit_builder_service.add_item(suit_item_2)
    #     self.suit_builder_service.add_item(shirt_item)
    #
    #     # when
    #     response = self.client.open(
    #         "/suit-builder/items",
    #         method="GET",
    #         headers=self.request_headers,
    #         content_type=self.content_type,
    #     )
    #
    #     # then
    #     self.assertStatus(response, 200)
    #     self.assertEqual(len(response.json.get("suit")), 2)
    #     self.assertEqual(len(response.json.get("shirt")), 1)
    #     response_item1 = response.json.get(suit_item_1.type)[0]
    #     response_item2 = response.json.get(suit_item_2.type)[1]
    #     response_item3 = response.json.get(shirt_item.type)[0]
    #
    #     self.assertEqual(suit_item_2.sku, response_item1.get("sku"))
    #     self.assertEqual(suit_item_1.sku, response_item2.get("sku"))
    #     self.assertEqual(shirt_item.sku, response_item3.get("sku"))
