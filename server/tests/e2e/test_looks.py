import time

import pytest
from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD, STORE_URL, e2e_error_handling, e2e_allowed_in
from server.tests.e2e.utils import api, actions, verify


@e2e_allowed_in({"dev", "stg"})
@e2e_error_handling
@pytest.mark.group_5
def test_create_delete_looks(page: Page):
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    actions.delete_look_by_look_id(page, data_look_id)

    verify.looks_page_is_empty(page)


@e2e_allowed_in({"dev", "stg"})
@e2e_error_handling
@pytest.mark.group_1
def test_add_look_to_cart_from_looks_page(page: Page):
    event_name = utils.generate_event_name()
    look_name = utils.generate_look_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    actions.add_look_to_cart(page, data_look_id)
    verify.shopify_checkout_has_item_with_name_and_price(page, f"Suit Bundle", str(price))


@e2e_allowed_in({"dev", "stg"})
@e2e_error_handling
@pytest.mark.group_2
def test_add_look_to_cart_from_looks_page_when_no_events_exist(page: Page):
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    actions.add_look_to_cart(page, data_look_id)

    actions.populate_what_is_special_occasion_dialog(page)
    time.sleep(1)

    page.goto(f"{STORE_URL}/pages/looks")

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)
    actions.add_look_to_cart(page, data_look_id)
    verify.shopify_checkout_has_item_with_name_and_price(page, f"Suit Bundle", str(price))
