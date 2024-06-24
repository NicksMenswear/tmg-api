import random
import time

from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import (
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    STORE_URL,
    EMAIL_SUBJECT_EVENT_INVITATION,
    EMAIL_FROM,
    EMAIL_SUBJECT_CUSTOMER_ACCOUNT_CONFIRMATION,
)
from server.tests.e2e.utils import api, actions, verify, email


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

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id_1 = actions.add_first_attendee(page, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    verify.event_to_be_visible(page, event_name)

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

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    verify.event_to_be_visible(page, event_name)

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

    verify.input_value_in_pay_dialog_for_attendee_by_name(page, attendee_first_name, attendee_last_name, amount)


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
    actions.create_default_look(page, look_name)
    _, _, price = actions.get_look_by_name_on_looks_page(page, look_name)
    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    verify.event_to_be_visible(page, event_name)

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

    verify.input_value_in_pay_dialog_for_attendee_by_name(page, attendee_first_name, attendee_last_name, price)


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
    actions.create_default_look(page, look_name)
    _, _, price = actions.get_look_by_name_on_looks_page(page, look_name)
    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    verify.event_to_be_visible(page, event_name)

    actions.open_event_accordion(page, event_id)

    actions.select_role_for_attendee(page, event_id, attendee_id, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)
    time.sleep(2)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])

    amount = round(random.uniform(0.01, 171.99), 2)

    actions.pay_to_attendee_by_id(page, event_id, attendee_id, amount)

    verify.shopify_checkout_has_item_with_name_and_price(page, f"{event_name} attendees discount", str(amount))

    continue_to_payment_button = page.locator('button:has-text("Continue to payment")').first
    continue_to_payment_button.click()

    iframe = page.frame_locator("iframe.card-fields-iframe").first
    input_cc_number = iframe.locator("input#number")
    input_cc_number.fill("1")
    input_name_number = iframe.locator("input#name")
    input_name_number.fill("Test Test")
    input_expiry_number = iframe.locator("input#expiry")
    input_expiry_number.fill("11/28")
    input_cvc_number = iframe.locator("input#verification_value")
    input_cvc_number.fill("123")

    pay_now_button = page.locator('button:has-text("Pay now")').first
    pay_now_button.click()

    actions.logout(page)

    email_content = email.look_for_email(EMAIL_SUBJECT_EVENT_INVITATION, EMAIL_FROM, attendee_email)
    assert email_content is not None

    activation_link = email.get_activate_account_link_from_email(email_content, "Activate Account &amp; Get Started")
    assert activation_link is not None

    page.goto(activation_link)

    actions.activation_enter_password(page, attendee_password)

    confirmation_email_body = email.look_for_email(
        EMAIL_SUBJECT_CUSTOMER_ACCOUNT_CONFIRMATION, None, attendee_email, 300
    )
    assert "You've activated your customer account." in confirmation_email_body

    add_suit_to_cart_button = page.locator(
        f'button.tmg-btn.addLookToCart[data-event-id="{event_id}"]:has-text("Add suit to Cart")'
    )
    add_suit_to_cart_button.click()

    verify.shopify_checkout_has_item_with_name_and_price(page, f"Look Suit Bundle", str(price))

    discount_code_prefix = f"GIFT-{int(amount)}-OFF-"
    span_locator = page.locator(f'span:has-text("{discount_code_prefix}")')
    assert span_locator.count() > 0
