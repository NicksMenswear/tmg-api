import time
import uuid

from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import (
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    EMAIL_FROM,
    EMAIL_SUBJECT_EVENT_INVITATION,
    EMAIL_SUBJECT_CUSTOMER_ACCOUNT_CONFIRMATION,
    STORE_URL,
    e2e_error_handling,
)
from server.tests.e2e.utils import api, actions, verify, email


@e2e_error_handling
def test_invite_attendee(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    attendee_password = str(uuid.uuid4())
    role_name = "Groomsman"
    look_name = "Test Look"

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
    verify.event_to_be_visible(page, event_name)

    actions.open_event_accordion(page, event_id)

    actions.select_role_for_attendee(page, event_id, attendee_id, role_name)
    time.sleep(1)
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)
    time.sleep(2)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])

    actions.logout(page)

    email_content = email.look_for_email(EMAIL_SUBJECT_EVENT_INVITATION, EMAIL_FROM, attendee_email)
    assert email_content is not None

    activation_link = email.get_activate_account_link_from_email(email_content)

    if activation_link is None:
        print("email_content: " + email_content)

    assert activation_link is not None

    page.goto(activation_link)

    try:
        actions.activation_enter_password(page, attendee_password)
    except Exception as e:
        print(activation_link)
        raise e

    confirmation_email_body = email.look_for_email(
        EMAIL_SUBJECT_CUSTOMER_ACCOUNT_CONFIRMATION, None, attendee_email, 300
    )
    assert "You've activated your customer account." in confirmation_email_body

    verify.no_upcoming_events_visible(page)
    verify.invite_is_of_type(page, "Wedding")
    verify.invite_has_name(page, event_name)
    verify.invite_role_is(page, role_name)
    verify.invite_look_is(page, look_name)


@e2e_error_handling
def test_invite_multiple_attendees(page: Page):
    event_name = utils.generate_event_name()

    # Attendee 1: Role and Look Selected
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    # Attendee 2: Only Role Selected
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    # Attendee 3: Only Look Selected
    attendee_first_name_3 = utils.generate_unique_name()
    attendee_last_name_3 = utils.generate_unique_name()
    attendee_email_3 = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    # Attendee 4: Role and Look Selected as well
    attendee_first_name_4 = utils.generate_unique_name()
    attendee_last_name_4 = utils.generate_unique_name()
    attendee_email_4 = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"

    role_name = "Groomsman"
    look_name = "Test Look"

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
    verify.event_to_be_visible(page, event_name)

    actions.open_event_accordion(page, event_id)

    attendee_id_2 = actions.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    attendee_id_3 = actions.add_attendee(page, event_id, attendee_first_name_3, attendee_last_name_3, attendee_email_3)
    attendee_id_4 = actions.add_attendee(page, event_id, attendee_first_name_4, attendee_last_name_4, attendee_email_4)

    # Attendee 1
    actions.select_role_for_attendee(page, event_id, attendee_id_1, role_name)
    actions.select_look_for_attendee(page, event_id, attendee_id_1, look_name)
    # Attendee 2
    actions.select_role_for_attendee(page, event_id, attendee_id_2, role_name)
    # Attendee 3
    actions.select_look_for_attendee(page, event_id, attendee_id_3, look_name)
    # Attendee 4
    actions.select_role_for_attendee(page, event_id, attendee_id_4, role_name)
    actions.select_look_for_attendee(page, event_id, attendee_id_4, look_name)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id_1, attendee_id_4])

    email_content = email.look_for_email(EMAIL_SUBJECT_EVENT_INVITATION, EMAIL_FROM, attendee_email_1)
    assert email_content is not None

    email_content = email.look_for_email(EMAIL_SUBJECT_EVENT_INVITATION, EMAIL_FROM, attendee_email_4)
    assert email_content is not None
