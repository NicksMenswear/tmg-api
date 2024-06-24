import time

from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD
from server.tests.e2e.utils import api, actions, verify


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
    look_name = "Test Look"

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
