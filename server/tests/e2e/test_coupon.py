import time

import pytest
from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import (
    e2e_allowed_in,
    e2e_error_handling,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    STORE_URL,
    TEST_COUPON_DISCOUNT_CODE,
)
from server.tests.e2e.utils import actions, api, verify


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_4
def test_create_coupon(page: Page):
    event_name = utils.generate_event_name()

    attendee_first_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_email_1 = utils.generate_email()
    attendee_first_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_email_2 = utils.generate_email()
    attendee_first_name_3 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_3 = f"E2E {utils.generate_unique_name()}"
    attendee_email_3 = utils.generate_email()
    attendee_first_name_4 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_4 = f"E2E {utils.generate_unique_name()}"
    attendee_email_4 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    role_name = "Groomsman"
    look_name = utils.generate_look_name()

    api.delete_all_looks(user_id)
    actions.create_default_look(page, look_name)
    actions.get_look_by_name_on_looks_page(page, look_name)
    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    attendee_id_1 = actions.add_first_attendee(
        page, event_id, attendee_first_name_1, attendee_last_name_1, attendee_email_1
    )
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    attendee_id_2 = actions.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    attendee_id_3 = actions.add_attendee(page, event_id, attendee_first_name_3, attendee_last_name_3, attendee_email_3)
    attendee_id_4 = actions.add_attendee(page, event_id, attendee_first_name_4, attendee_last_name_4, attendee_email_4)

    actions.select_role_for_attendee(page, event_id, attendee_id_1, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id_1, look_name)
    time.sleep(1)
    actions.select_role_for_attendee(page, event_id, attendee_id_2, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id_2, look_name)
    time.sleep(1)
    actions.select_role_for_attendee(page, event_id, attendee_id_3, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id_3, look_name)
    time.sleep(1)
    actions.select_role_for_attendee(page, event_id, attendee_id_4, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id_4, look_name)
    time.sleep(1)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id_1, attendee_id_2, attendee_id_3])
    time.sleep(2)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)
    actions.add_look_to_cart(page, data_look_id)
    verify.shopify_checkout_has_item_with_name_and_price(page, look_name, f"${str(price)}")

    actions.shopify_checkout_apply_discount_code(page, TEST_COUPON_DISCOUNT_CODE)
    actions.shopify_checkout_verify_discount_code_is_not_applicable(page, TEST_COUPON_DISCOUNT_CODE)

    page.goto(f"{STORE_URL}/account")
    time.sleep(2)
    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id_4])

    time.sleep(1)

    actions.open_cart_drawer(page)
    actions.click_on_cart_checkout_button(page)
    verify.shopify_checkout_has_item_with_name_and_price(page, look_name, f"${str(price)}")
    actions.shopify_checkout_apply_discount_code(page, TEST_COUPON_DISCOUNT_CODE)
    verify.shopify_checkout_has_discount_with_name(page, TEST_COUPON_DISCOUNT_CODE)

    page.goto(f"{STORE_URL}/account")
    time.sleep(2)

    actions.delete_attendee(page, event_id, attendee_id_2)
    time.sleep(5)
    actions.open_cart_drawer(page)
    actions.click_on_cart_checkout_button(page)
    verify.shopify_checkout_has_item_with_name_and_price(page, look_name, f"${str(price)}")
    actions.shopify_checkout_apply_discount_code(page, TEST_COUPON_DISCOUNT_CODE)
    actions.shopify_checkout_verify_discount_code_is_not_applicable(page, TEST_COUPON_DISCOUNT_CODE)
