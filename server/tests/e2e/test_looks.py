from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD, STORE_URL
from server.tests.e2e.utils import api, actions, verify


def test_create_delete_looks(page: Page):
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")

    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    actions.delete_look_by_look_id(page, data_look_id)

    verify.looks_page_is_empty(page)


def test_add_look_to_cart_from_looks_page(page: Page):
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")
    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    actions.add_look_to_cart(page, data_look_id)
    verify.shopify_checkout_has_item_with_name_and_price(page, f"Look Suit Bundle", str(price))
