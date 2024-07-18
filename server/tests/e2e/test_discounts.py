import logging
import random
import time

import pytest
from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import (
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    STORE_URL,
    e2e_error_handling,
)
from server.tests.e2e.utils import api, actions, verify

logger = logging.getLogger(__name__)


@e2e_error_handling
@pytest.mark.group_4
def test_pay_dialog_correctness(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    attendee_first_name_3 = utils.generate_unique_name()
    attendee_last_name_3 = utils.generate_unique_name()
    attendee_email_3 = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"

    role_name = "Groomsman"
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    api.delete_all_looks(user_id)
    api.create_look(look_name, user_id)
    page.goto(f"{STORE_URL}/pages/looks")
    actions.get_look_by_name_on_looks_page(page, look_name)
    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id_1 = actions.add_first_attendee(page, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    actions.select_role_for_attendee(page, event_id, attendee_id_1, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id_1, look_name)
    time.sleep(2)

    attendee_id_2 = actions.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    actions.select_role_for_attendee(page, event_id, attendee_id_2, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id_2, look_name)
    time.sleep(2)

    actions.add_attendee(page, event_id, attendee_first_name_3, attendee_last_name_3, attendee_email_3)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id_1])

    actions.open_pay_dialog(page, event_id)

    verify.input_value_in_pay_dialog_for_attendee_by_name(page, attendee_first_name_1, attendee_last_name_1, 0)

    verify.warning_in_pay_dialog_for_attendee_by_name(
        page, attendee_first_name_2, attendee_last_name_2, "No invite accepted"
    )

    verify.warning_in_pay_dialog_for_attendee_by_name(
        page, attendee_first_name_3, attendee_last_name_3, "No look and/or role selected"
    )


@e2e_error_handling
@pytest.mark.group_3
def test_discount_intent_saved(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"

    role_name = "Groomsman"
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    api.delete_all_looks(user_id)
    api.create_look(look_name, user_id)
    page.goto(f"{STORE_URL}/pages/looks")
    actions.get_look_by_name_on_looks_page(page, look_name)
    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    actions.select_role_for_attendee(page, event_id, attendee_id, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)
    time.sleep(2)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])

    amount = round(random.uniform(0.01, 171.99), 2)

    actions.pay_to_attendee_by_id(page, event_id, attendee_id, amount)

    verify.shopify_checkout_has_item_with_name_and_price(page, f"{event_name} attendees discount", str(amount))

    page.goto(f"{STORE_URL}/account")

    actions.open_event_accordion(page, event_id)
    actions.open_pay_dialog(page, event_id)

    verify.input_value_in_pay_dialog_for_attendee_by_id(page, attendee_id, amount)


@e2e_error_handling
@pytest.mark.group_2
def test_pay_in_full_click(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"

    role_name = "Groomsman"
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    api.delete_all_looks(user_id)
    api.create_look(look_name, user_id)
    page.goto(f"{STORE_URL}/pages/looks")
    _, _, price = actions.get_look_by_name_on_looks_page(page, look_name)
    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    actions.select_role_for_attendee(page, event_id, attendee_id, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)
    time.sleep(2)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])

    actions.pay_in_full_attendee_by_id(page, event_id, attendee_id, price)

    verify.shopify_checkout_has_item_with_name_and_price(page, f"{event_name} attendees discount", str(price))

    page.goto(f"{STORE_URL}/account")

    actions.open_event_accordion(page, event_id)
    actions.open_pay_dialog(page, event_id)

    verify.input_value_in_pay_dialog_for_attendee_by_id(page, attendee_id, price)


@e2e_error_handling
@pytest.mark.group_5
def test_grooms_gift(page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    attendee_password = utils.generate_unique_string()

    role_name = "Groomsman"
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    api.delete_all_looks(user_id)
    api.create_look(look_name, user_id)
    page.goto(f"{STORE_URL}/pages/looks")
    _, _, price = actions.get_look_by_name_on_looks_page(page, look_name)
    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    actions.select_role_for_attendee(page, event_id, attendee_id, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)
    time.sleep(2)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])
    attendee_user_id = api.get_user_by_email(attendee_email).get("id")

    amount = round(random.uniform(0.01, 171.99), 2)

    actions.pay_to_attendee_by_id(page, event_id, attendee_id, amount)

    verify.shopify_checkout_has_item_with_name_and_price(page, f"{event_name} attendees discount", str(amount))

    actions.shopify_checkout_enter_billing_address(page, attendee_first_name, attendee_last_name)
    actions.shopify_checkout_continue_to_payment(page)
    actions.shopify_checkout_pay_with_credit_card_for_order(page, attendee_first_name, attendee_last_name)

    actions.logout(page)

    activation_link = api.get_user_activation_url(attendee_user_id)
    assert activation_link is not None
    page.goto(activation_link)
    actions.activation_enter_password(page, attendee_password)

    actions.attendee_add_suit_to_cart(page, event_id)

    verify.shopify_checkout_has_item_with_name_and_price(page, f"Suit Bundle", str(price))
    verify.shopify_checkout_has_discount_with_name(page, f"GIFT-{int(amount)}-OFF-")
