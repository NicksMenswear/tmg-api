from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD
from server.tests.e2e.utils import api, actions, verify

DEFAULT_WEDDING_ROLES = {
    "Best Man",
    "Bride",
    "Father of the Bride",
    "Father of the Groom",
    "Groom",
    "Groomsman",
    "Officiant",
    "Usher",
}
DEFAULT_PROM_ROLES = {"Attendee", "Attendee Parent or Chaperone"}
DEFAULT_OTHER_ROLES = {"Attendee"}


def test_basic_create_event(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)

    actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)

    verify.event_to_be_visible(page, event_name)

    actions.open_event_accordion(page, event_id)

    verify.attendee_to_be_visible(page, attendee_first_name, attendee_last_name)


def test_create_multiple_events(page: Page):
    event_name_1 = utils.generate_event_name()
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = utils.generate_email()
    event_name_2 = utils.generate_event_name()
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    event_id_1 = actions.create_new_event(page, event_name_1)
    actions.add_first_attendee(page, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    verify.event_to_be_visible(page, event_name_1)

    event_id_2 = actions.create_new_event(page, event_name_2)
    actions.add_first_attendee(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    verify.event_to_be_visible(page, event_name_2)

    actions.open_event_accordion(page, event_id_1)
    verify.attendee_to_be_visible(page, attendee_first_name_1, attendee_last_name_1)

    actions.open_event_accordion(page, event_id_2)
    verify.attendee_to_be_visible(page, attendee_first_name_2, attendee_last_name_2)


def test_create_event_and_add_few_attendees(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = utils.generate_email()
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = utils.generate_email()
    attendee_first_name_3 = utils.generate_unique_name()
    attendee_last_name_3 = utils.generate_unique_name()
    attendee_email_3 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    actions.add_first_attendee(page, attendee_first_name_1, attendee_last_name_1, attendee_email_1)

    verify.event_to_be_visible(page, event_name)

    actions.open_event_accordion(page, event_id)

    actions.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    actions.add_attendee(page, event_id, attendee_first_name_3, attendee_last_name_3, attendee_email_3)

    verify.attendee_to_be_visible(page, attendee_first_name_1, attendee_last_name_1)
    verify.attendee_to_be_visible(page, attendee_first_name_2, attendee_last_name_2)
    verify.attendee_to_be_visible(page, attendee_first_name_3, attendee_last_name_3)


def test_create_event_and_add_few_attendees_using_save_and_add_next_button(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = utils.generate_email()
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = utils.generate_email()
    attendee_first_name_3 = utils.generate_unique_name()
    attendee_last_name_3 = utils.generate_unique_name()
    attendee_email_3 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    actions.add_first_attendee(page, attendee_first_name_1, attendee_last_name_1, attendee_email_1, "Save & Add Next")
    actions.add_first_attendee(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2, "Save & Add Next")
    actions.add_first_attendee(page, attendee_first_name_3, attendee_last_name_3, attendee_email_3, "Save")

    verify.event_to_be_visible(page, event_name)

    actions.open_event_accordion(page, event_id)

    verify.attendee_to_be_visible(page, attendee_first_name_1, attendee_last_name_1)
    verify.attendee_to_be_visible(page, attendee_first_name_2, attendee_last_name_2)
    verify.attendee_to_be_visible(page, attendee_first_name_3, attendee_last_name_3)


def test_create_event_add_and_remove_attendees(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = utils.generate_email()
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id_1 = actions.add_first_attendee(page, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    verify.event_to_be_visible(page, event_name)

    actions.open_event_accordion(page, event_id)

    actions.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)

    actions.delete_attendee(page, attendee_id_1)


def test_delete_event(page: Page):
    event_name_1 = utils.generate_event_name()
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = utils.generate_email()
    event_name_2 = utils.generate_event_name()
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    event_id_1 = actions.create_new_event(page, event_name_1)
    actions.add_first_attendee(page, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    verify.event_to_be_visible(page, event_name_1)

    actions.create_new_event(page, event_name_2)
    actions.add_first_attendee(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    verify.event_to_be_visible(page, event_name_2)

    actions.delete_event(page, event_id_1, event_name_1)


def test_delete_all_events(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    event_id_1 = actions.create_new_event(page, event_name)
    actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    verify.event_to_be_visible(page, event_name)

    actions.delete_event(page, event_id_1, event_name)


def test_delete_all_attendees(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = utils.generate_email()
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name)
    attendee_id_1 = actions.add_first_attendee(page, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    verify.event_to_be_visible(page, event_name)

    actions.open_event_accordion(page, event_id)

    attendee_id_2 = actions.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)

    actions.delete_attendee(page, attendee_id_1)
    actions.delete_attendee(page, attendee_id_2)

    verify.no_attendee_added_to_be_visible(page, event_id)


def test_create_all_types_of_events_and_check_roles(page: Page):
    event_name1 = utils.generate_event_name()
    attendee_first_name1 = utils.generate_unique_name()
    attendee_last_name1 = utils.generate_unique_name()
    attendee_email1 = utils.generate_email()

    event_name2 = utils.generate_event_name()
    attendee_first_name2 = utils.generate_unique_name()
    attendee_last_name2 = utils.generate_unique_name()
    attendee_email2 = utils.generate_email()

    event_name3 = utils.generate_event_name()
    attendee_first_name3 = utils.generate_unique_name()
    attendee_last_name3 = utils.generate_unique_name()
    attendee_email3 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    event_id1 = actions.create_new_event(page, event_name1, event_type="wedding")
    attendee_id1 = actions.add_first_attendee(page, attendee_first_name1, attendee_last_name1, attendee_email1)

    actions.open_event_accordion(page, event_id1)

    verify.roles_are_available_for_attendee(page, attendee_id1, DEFAULT_WEDDING_ROLES)

    verify.event_has_type(page, event_id1, "Wedding")

    event_id2 = actions.create_new_event(page, event_name2, event_type="prom")
    attendee_id2 = actions.add_first_attendee(page, attendee_first_name2, attendee_last_name2, attendee_email2)
    actions.open_event_accordion(page, event_id2)

    verify.roles_are_available_for_attendee(page, attendee_id2, DEFAULT_PROM_ROLES)
    verify.event_has_type(page, event_id2, "Prom")

    event_id3 = actions.create_new_event(page, event_name3, event_type="other")
    attendee_id3 = actions.add_first_attendee(page, attendee_first_name3, attendee_last_name3, attendee_email3)
    actions.open_event_accordion(page, event_id3)

    verify.roles_are_available_for_attendee(page, attendee_id3, DEFAULT_OTHER_ROLES)
    verify.event_has_type(page, event_id3, "Other")


def test_roles_persistence(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    event_id = actions.create_new_event(page, event_name, event_type="prom")
    attendee_id = actions.add_first_attendee(page, attendee_first_name, attendee_last_name, attendee_email)
    actions.open_event_accordion(page, event_id)

    role_name = "Attendee Parent or Chaperone"
    role_id = actions.select_role_for_attendee(page, event_id, attendee_id, role_name)

    page.reload()

    actions.open_event_accordion(page, event_id)

    verify.role_is_selected_for_attendee(page, event_id, attendee_id, role_id)
