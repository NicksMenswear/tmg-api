import unittest
import uuid

from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD
from server.tests.e2e.utils import api, actions, verify

EVENT_DATE = "2028-04-18"
EVENT_PRETTY_DATE = "Tuesday, April 18, 2028"


@unittest.skip("This test is incomplete due to bug in invites")
def test_invite_attendee(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    attendee_password = str(uuid.uuid4())

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    api.create_look("Test Look", user_id)

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name, EVENT_DATE)
    attendee_id = actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    verify.event_to_be_visible(page, event_name, EVENT_PRETTY_DATE)

    actions.open_event_accordion(page, event_id)

    role_id = actions.select_role_for_attendee(page, event_id, attendee_id, "Groomsman")
    look_id = actions.select_look_for_attendee(page, event_id, attendee_id, "Test Look")

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])

    actions.logout(page)

    # email_content = email.look_for_email("The Modern Groom: Account Created", EMAIL_FROM, attendee_email)
    # assert email_content is not None
    #
    # activation_link = email.link_from_email(email_content)
    #
    # assert activation_link is not None
    #
    # page.goto(activation_link)
    #
    # page.locator("#customer_password").fill(attendee_password)
    # page.locator("#customer_password_confirmation").fill(attendee_password)
    # page.get_by_role("button", name="Activate Account").click()
    #
    # confirmation_email_body = email.look_for_email("Customer account confirmation", None, attendee_email, 300)
    # assert "You've activated your customer account." in confirmation_email_body
    #
    # page.goto(f"{STORE_URL}/account")
    #
    # event_item = page.locator(f'.tmg-invite-event-name:has-text("{event_name}")')
    # event_item.scroll_into_view_if_needed()
    # event_item.wait_for(state="visible")
