import time

import pytest
from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD, e2e_allowed_in, e2e_error_handling, STORE_URL
from server.tests.e2e.utils import api, actions, verify, shopify


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_5
def test_new_customer_for_attendee_has_no_tags(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()
    attendee_password = utils.generate_unique_string()

    role_name = "Groomsman"
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    api.delete_all_looks(user_id)
    actions.create_default_look(page, look_name)
    actions.get_look_by_name_on_looks_page(page, look_name)

    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    actions.select_role_for_attendee(page, event_id, attendee_id, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)
    time.sleep(2)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])
    attendee_user = api.get_user_by_email(attendee_email)
    attendee_user_id = attendee_user.get("id")

    actions.logout(page)

    activation_link = api.get_user_activation_url(
        attendee_user_id,
        attendee_first_name,
        attendee_last_name,
        attendee_email,
    )
    assert activation_link is not None
    page.goto(activation_link)
    actions.fill_activation_form(page, attendee_password, attendee_first_name, attendee_last_name)

    attendee_user = api.get_user_by_email(attendee_email)

    time.sleep(10)  # sometimes it takes a while for the tags to be updatedÏ

    shopify_customer = shopify.get_customer_by_id(f"gid://shopify/Customer/{attendee_user.get('shopify_id')}")

    tags = shopify_customer.get("tags", [])

    assert len(tags) == 0


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_6
def test_owner_and_attendee_tagged_for_event_4_plus(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_email_1 = utils.generate_email()
    attendee_password_1 = utils.generate_unique_string()
    attendee_first_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_email_2 = utils.generate_email()
    attendee_first_name_3 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_3 = f"E2E {utils.generate_unique_name()}"
    attendee_email_3 = utils.generate_email()
    attendee_first_name_4 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_4 = f"E2E {utils.generate_unique_name()}"
    attendee_email_4 = utils.generate_email()

    role_name = "Groomsman"
    look_name = utils.generate_look_name()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    owner = api.get_user_by_email(TEST_USER_EMAIL)
    owner_id = owner.get("id")

    api.delete_all_looks(owner_id)
    actions.create_default_look(page, look_name)
    actions.get_look_by_name_on_looks_page(page, look_name)

    shopify_owner_customer = shopify.get_customer_by_id(f"gid://shopify/Customer/{owner.get('shopify_id')}")
    tags = shopify_owner_customer.get("tags", [])
    assert len(tags) == 0

    page.goto(f"{STORE_URL}/account")

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    attendee_id_1 = actions.add_first_attendee(
        page, event_id, attendee_first_name_1, attendee_last_name_1, attendee_email_1, "Save & Add Next"
    )
    attendee_id_2 = actions.add_first_attendee(
        page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2, "Save & Add Next"
    )
    attendee_id_3 = actions.add_first_attendee(
        page, event_id, attendee_first_name_3, attendee_last_name_3, attendee_email_3, "Save & Add Next"
    )
    attendee_id_4 = actions.add_first_attendee(
        page, event_id, attendee_first_name_4, attendee_last_name_4, attendee_email_4, "Save"
    )

    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

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

    actions.send_invites_to_attendees_by_id(
        page, event_id, [attendee_id_1, attendee_id_2, attendee_id_3, attendee_id_4]
    )
    attendee_user_1 = api.get_user_by_email(attendee_email_1)
    attendee_user_1_id = attendee_user_1.get("id")

    actions.logout(page)

    activation_link = api.get_user_activation_url(
        attendee_user_1_id,
        attendee_first_name_1,
        attendee_last_name_1,
        attendee_email_1,
    )
    assert activation_link is not None
    page.goto(activation_link)
    actions.fill_activation_form(page, attendee_password_1, attendee_first_name_1, attendee_last_name_1)

    attendee_user = api.get_user_by_email(attendee_email_1)

    time.sleep(10)  # sometimes it takes a while for the tags to be updated

    shopify_attendee_customer = shopify.get_customer_by_id(f"gid://shopify/Customer/{attendee_user.get('shopify_id')}")
    tags = shopify_attendee_customer.get("tags", [])
    assert set(tags) == {"member_of_4_plus_event"}

    shopify_owner_customer = shopify.get_customer_by_id(f"gid://shopify/Customer/{owner.get('shopify_id')}")
    tags = shopify_owner_customer.get("tags", [])
    assert set(tags) == {"event_owner_4_plus"}
