import time

import pytest
from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import e2e_allowed_in, e2e_error_handling, STORE_URL
from server.tests.e2e.utils import actions, verify


@e2e_allowed_in({"dev"})
@e2e_error_handling
@pytest.mark.group_9
def test_anon(page: Page):
    email = utils.generate_email()
    first_name = utils.generate_unique_name()
    last_name = utils.generate_unique_name()

    actions.access_store(page)

    page.goto(f"{STORE_URL}/products/the-tan-suit")

    actions.click_fit_quiz_button(page)

    time.sleep(2)

    actions.populate_fit_survey(page, email=email)

    time.sleep(5)

    page.goto(f"{STORE_URL}/pages/suit-builder")

    actions.click_buy_now_button(page)

    verify.shopify_checkout_has_item_with_name_and_price(page, "Black Suit", "260", True)
    actions.shopify_checkout_enter_email_for_anonymous_checkout(page, email)
    actions.shopify_checkout_continue_to_shipping(page, "ASDf", "ASDF")
    actions.shopify_checkout_continue_to_payment(page)
    actions.shopify_checkout_pay_with_credit_card_for_order(page, first_name, last_name)

    actions.logout(page)
