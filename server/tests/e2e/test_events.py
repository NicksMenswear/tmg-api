import time
import uuid
from datetime import datetime

import pytest
from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import (
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    e2e_error_handling,
    STORE_URL,
    e2e_allowed_in,
    EMAIL_SUBJECT_EVENT_INVITATION,
    EMAIL_FROM,
    EMAIL_SUBJECT_CUSTOMER_ACCOUNT_CONFIRMATION,
)
from server.tests.e2e.utils import api, actions, verify, email

DEFAULT_WEDDING_ROLES = {
    "Best Man",
    "Bride",
    "Father of the Bride",
    "Father of the Groom",
    "Groom",
    "Groomsman",
    "Officiant",
    "Other",
    "Usher",
}
DEFAULT_PROM_ROLES = {"Attendee", "Attendee Parent or Chaperone", "Other"}
DEFAULT_OTHER_ROLES = {"Attendee", "Other"}


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_3
def test_basic_create_event(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)

    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)

    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    attendee_block = actions.get_attendee_block(page, event_id, attendee_id)
    expect(attendee_block).to_be_visible()


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_4
def test_create_multiple_events(page: Page):
    event_name_1 = utils.generate_event_name()
    attendee_first_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_email_1 = utils.generate_email()
    event_name_2 = utils.generate_event_name()
    attendee_first_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id_1 = actions.create_new_event(page, event_name_1)
    attendee_id_1 = actions.add_first_attendee(
        page, event_id_1, attendee_first_name_1, attendee_last_name_1, attendee_email_1
    )
    event_block = actions.get_event_block(page, event_id_1)
    expect(event_block).to_be_visible()

    event_id_2 = actions.create_new_event(page, event_name_2)
    attendee_id_2 = actions.add_first_attendee(
        page, event_id_2, attendee_first_name_2, attendee_last_name_2, attendee_email_2
    )
    event_block = actions.get_event_block(page, event_id_2)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id_1)

    attendee_block_1 = actions.get_attendee_block(page, event_id_1, attendee_id_1)
    expect(attendee_block_1).to_be_visible()

    actions.open_event_accordion(page, event_id_2)

    attendee_block_2 = actions.get_attendee_block(page, event_id_2, attendee_id_2)
    expect(attendee_block_2).to_be_visible()


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_5
def test_create_event_and_add_few_attendees(page: Page):
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

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
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

    attendee_block_1 = actions.get_attendee_block(page, event_id, attendee_id_1)
    expect(attendee_block_1).to_be_visible()

    attendee_block_2 = actions.get_attendee_block(page, event_id, attendee_id_2)
    expect(attendee_block_2).to_be_visible()

    attendee_block_3 = actions.get_attendee_block(page, event_id, attendee_id_3)
    expect(attendee_block_3).to_be_visible()


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_6
def test_create_event_and_add_few_attendees_using_save_and_add_next_button(page: Page):
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

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
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
        page, event_id, attendee_first_name_3, attendee_last_name_3, attendee_email_3, "Save"
    )

    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    attendee_block_1 = actions.get_attendee_block(page, event_id, attendee_id_1)
    expect(attendee_block_1).to_be_visible()

    attendee_block_2 = actions.get_attendee_block(page, event_id, attendee_id_2)
    expect(attendee_block_2).to_be_visible()

    attendee_block_3 = actions.get_attendee_block(page, event_id, attendee_id_3)
    expect(attendee_block_3).to_be_visible()


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_7
def test_create_event_add_and_remove_attendees(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_email_1 = utils.generate_email()
    attendee_first_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    attendee_id_1 = actions.add_first_attendee(
        page, event_id, attendee_first_name_1, attendee_last_name_1, attendee_email_1
    )
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.open_event_accordion(page, event_id)

    actions.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)

    actions.delete_attendee(page, event_id, attendee_id_1)


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_8
def test_delete_event(page: Page):
    event_name_1 = utils.generate_event_name()
    attendee_first_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_email_1 = utils.generate_email()
    event_name_2 = utils.generate_event_name()
    attendee_first_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id_1 = actions.create_new_event(page, event_name_1)
    actions.add_first_attendee(page, event_id_1, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    event_block = actions.get_event_block(page, event_id_1)
    expect(event_block).to_be_visible()

    event_id_2 = actions.create_new_event(page, event_name_2)
    actions.add_first_attendee(page, event_id_2, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    event_block = actions.get_event_block(page, event_id_2)
    expect(event_block).to_be_visible()

    actions.delete_event(page, event_id_1, event_name_1)


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_9
def test_delete_all_events(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.delete_event(page, event_id, event_name)


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_10
def test_delete_all_attendees(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_email_1 = utils.generate_email()
    attendee_first_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
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

    actions.delete_attendee(page, event_id, attendee_id_1)
    actions.delete_attendee(page, event_id, attendee_id_2)

    verify.no_attendee_added_to_be_visible(page, event_id)


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_1
def test_create_all_types_of_events_and_check_roles(page: Page):
    event_name1 = utils.generate_event_name()
    attendee_first_name1 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name1 = f"E2E {utils.generate_unique_name()}"
    attendee_email1 = utils.generate_email()

    event_name2 = utils.generate_event_name()
    attendee_first_name2 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name2 = f"E2E {utils.generate_unique_name()}"
    attendee_email2 = utils.generate_email()

    event_name3 = utils.generate_event_name()
    attendee_first_name3 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name3 = f"E2E {utils.generate_unique_name()}"
    attendee_email3 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id1 = actions.create_new_event(page, event_name1, event_type="wedding")
    attendee_id1 = actions.add_first_attendee(
        page, event_id1, attendee_first_name1, attendee_last_name1, attendee_email1
    )

    actions.open_event_accordion(page, event_id1)

    verify.roles_are_available_for_attendee(page, attendee_id1, DEFAULT_WEDDING_ROLES)

    verify.event_has_type(page, event_id1, "Wedding")

    event_id2 = actions.create_new_event(page, event_name2, event_type="prom")
    attendee_id2 = actions.add_first_attendee(
        page, event_id2, attendee_first_name2, attendee_last_name2, attendee_email2
    )
    actions.open_event_accordion(page, event_id2)

    verify.roles_are_available_for_attendee(page, attendee_id2, DEFAULT_PROM_ROLES)
    verify.event_has_type(page, event_id2, "Prom")

    event_id3 = actions.create_new_event(page, event_name3, event_type="other")
    attendee_id3 = actions.add_first_attendee(
        page, event_id3, attendee_first_name3, attendee_last_name3, attendee_email3
    )
    actions.open_event_accordion(page, event_id3)

    verify.roles_are_available_for_attendee(page, attendee_id3, DEFAULT_OTHER_ROLES)
    verify.event_has_type(page, event_id3, "Other")


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
def test_roles_persistence(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name, event_type="prom")
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    actions.open_event_accordion(page, event_id)

    role_name = "Attendee Parent or Chaperone"
    role_id = actions.select_role_for_attendee(page, event_id, attendee_id, role_name)

    page.reload()

    actions.open_event_accordion(page, event_id)

    verify.role_is_selected_for_attendee(page, event_id, attendee_id, role_id)


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_3
def test_add_myself_and_then_remove(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name, event_type="prom")
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    actions.open_event_accordion(page, event_id)

    add_myself_button = actions.get_add_myself_button(page, event_id)
    add_myself_button.click()
    expect(add_myself_button).to_be_disabled()

    owner_user = api.get_user_by_email(TEST_USER_EMAIL)
    owner_attendee_id = actions.get_attendee_id_by_name(
        page, event_id, owner_user.get("first_name"), owner_user.get("last_name")
    )

    fit_survey_button = actions.get_owner_fit_survey_button(page, event_id, owner_attendee_id)
    expect(fit_survey_button).to_be_visible()

    add_suit_to_cart_button = actions.get_owner_add_suit_to_cart_button(page, event_id, owner_attendee_id)
    expect(add_suit_to_cart_button).to_be_visible()

    owner_attendee_block = actions.get_attendee_block(page, event_id, owner_attendee_id)
    expect(owner_attendee_block).to_be_visible()

    attendee_block = actions.get_attendee_block(page, event_id, attendee_id)
    expect(attendee_block).to_be_visible()

    actions.delete_attendee(page, event_id, owner_attendee_id)
    expect(add_myself_button).to_be_enabled()


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_4
def test_add_myself_and_fill_fit_survey(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name, event_type="prom")
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    actions.open_event_accordion(page, event_id)

    add_myself_button = actions.get_add_myself_button(page, event_id)
    add_myself_button.click()

    owner_user = api.get_user_by_email(TEST_USER_EMAIL)
    owner_attendee_id = actions.get_attendee_id_by_name(
        page, event_id, owner_user.get("first_name"), owner_user.get("last_name")
    )

    fit_survey_button = actions.get_owner_fit_survey_button(page, event_id, owner_attendee_id)
    expect(fit_survey_button).to_be_visible()
    fit_survey_button.click()

    actions.populate_fit_survey(page, 50)

    time.sleep(3)  # wait for the survey to be saved

    page.reload()

    actions.open_event_accordion(page, event_id)

    assert not actions.is_assign_look_checkbox_selected(page, event_id, owner_attendee_id)
    assert actions.is_invite_checkbox_selected(page, event_id, owner_attendee_id)
    assert actions.is_fit_checkbox_selected(page, event_id, owner_attendee_id)
    assert not actions.is_pay_checkbox_selected(page, event_id, attendee_id)
    assert not actions.is_ship_checkbox_selected(page, event_id, attendee_id)


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_5
def test_style_and_invite_checkboxes(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()
    look_name = utils.generate_look_name()
    role_name = "Attendee Parent or Chaperone"

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    api.delete_all_events(TEST_USER_EMAIL)
    api.delete_all_looks(user_id)
    api.create_look(look_name, user_id)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name, event_type="prom")
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    actions.open_event_accordion(page, event_id)

    assert not actions.is_assign_look_checkbox_selected(page, event_id, attendee_id)
    assert not actions.is_invite_checkbox_selected(page, event_id, attendee_id)
    assert not actions.is_fit_checkbox_selected(page, event_id, attendee_id)
    assert not actions.is_pay_checkbox_selected(page, event_id, attendee_id)
    assert not actions.is_ship_checkbox_selected(page, event_id, attendee_id)

    actions.select_role_for_attendee(page, event_id, attendee_id, role_name)
    time.sleep(2)
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)
    time.sleep(2)

    assert actions.is_assign_look_checkbox_selected(page, event_id, attendee_id)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])
    assert actions.is_invite_checkbox_selected(page, event_id, attendee_id)


@e2e_allowed_in({"dev", "stg"})
@e2e_error_handling
@pytest.mark.group_6
def test_add_myself_and_pay_for_suit(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()
    look_name = utils.generate_look_name()
    role_name = "Attendee Parent or Chaperone"

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    api.delete_all_events(TEST_USER_EMAIL)
    api.delete_all_looks(user_id)
    api.create_look(look_name, user_id)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name, event_type="prom")
    actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    actions.open_event_accordion(page, event_id)

    add_myself_button = actions.get_add_myself_button(page, event_id)
    add_myself_button.click()

    owner_user = api.get_user_by_email(TEST_USER_EMAIL)
    owner_attendee_id = actions.get_attendee_id_by_name(
        page, event_id, owner_user.get("first_name"), owner_user.get("last_name")
    )

    fit_survey_button = actions.get_owner_fit_survey_button(page, event_id, owner_attendee_id)
    expect(fit_survey_button).to_be_visible()
    fit_survey_button.click()

    actions.populate_fit_survey(page, 50)

    time.sleep(5)

    actions.select_role_for_attendee(page, event_id, owner_attendee_id, role_name)
    time.sleep(2)
    actions.select_look_for_attendee(page, event_id, owner_attendee_id, look_name)
    time.sleep(2)

    add_suit_to_cart_button = actions.get_owner_add_suit_to_cart_button(page, event_id, owner_attendee_id)
    expect(add_suit_to_cart_button).to_be_visible()
    add_suit_to_cart_button.click()

    time.sleep(10)

    try:
        verify.shopify_open_order_summary_if_needed(page)
    except:
        page.reload()
        verify.shopify_open_order_summary_if_needed(page)

    actions.shopify_checkout_continue_to_shipping(page, owner_user.get("first_name"), owner_user.get("last_name"))
    actions.shopify_checkout_continue_to_payment(page)
    actions.shopify_checkout_pay_with_credit_card_for_order(
        page, owner_user.get("first_name"), owner_user.get("last_name")
    )
    verify.shopify_order_confirmed(page)

    time.sleep(20)  # wait for 20 sec so shopify webhook gets triggered and order is processed by our webhook backend

    page.goto(f"{STORE_URL}/account")

    actions.open_event_accordion(page, event_id)

    add_suit_to_cart_button = actions.get_owner_add_suit_to_cart_button(page, event_id, owner_attendee_id)
    expect(add_suit_to_cart_button).to_be_visible()
    expect(add_suit_to_cart_button).to_be_disabled()

    fit_survey_button = actions.get_owner_fit_survey_button(page, event_id, owner_attendee_id)
    expect(fit_survey_button).to_be_visible()
    expect(fit_survey_button).to_be_disabled()


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_7
def test_update_event_owner_name(page: Page):
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    top_section = page.locator("div.tmg-top-section")
    customer_section = top_section.locator("div.tmg-customer")

    current_customer_name = customer_section.locator("div.tmg-customer-name").inner_text()

    edit_customer_button = customer_section.locator("button.editCustomer")
    edit_customer_button.scroll_into_view_if_needed()
    edit_customer_button.wait_for(state="visible")
    edit_customer_button.click()

    edit_customer_dialog = page.locator("div#edit-customer")
    edit_customer_dialog.scroll_into_view_if_needed()
    edit_customer_dialog.wait_for(state="visible")

    time.sleep(2)

    first_name_input = edit_customer_dialog.locator("input#newCustomerFirstName")
    first_name_input.fill("Test")
    new_last_name = f"Group2 {datetime.now().strftime('%H%M%S')}"
    last_name_input = edit_customer_dialog.locator("input#newCustomerLastName")
    last_name_input.fill(new_last_name)

    update_button = edit_customer_dialog.locator("button.tmg-btn")
    update_button.scroll_into_view_if_needed()
    update_button.wait_for(state="visible")
    update_button.click()

    time.sleep(5)

    new_customer_name = customer_section.locator("div.tmg-customer-name").inner_text()

    assert current_customer_name != new_customer_name
    assert new_customer_name == f"Test {new_last_name}"


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_8
def test_update_attendee_uber_test(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_1 = f"E2E {utils.generate_unique_name()}"
    attendee_first_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_2 = f"E2E {utils.generate_unique_name()}"
    attendee_email_2 = utils.generate_email()
    attendee_password_2 = str(uuid.uuid4())
    attendee_first_name_3 = f"E2E {utils.generate_unique_name()}"
    attendee_last_name_3 = f"E2E {utils.generate_unique_name()}"
    attendee_email_3 = utils.generate_email()
    look_name = utils.generate_look_name()
    role_name = "Groomsman"

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")

    api.delete_all_events(TEST_USER_EMAIL)
    api.delete_all_looks(user_id)
    api.create_look(look_name, user_id)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name_1, attendee_last_name_1, None)
    actions.open_event_accordion(page, event_id)

    attendee_block = actions.get_attendee_block(page, event_id, attendee_id)
    first_name = attendee_block.locator("div.tmg-attendees-name span.afn").inner_text()
    last_name = attendee_block.locator("div.tmg-attendees-name span.aln").inner_text()

    assert first_name == attendee_first_name_1
    assert last_name == attendee_last_name_1

    actions.select_role_for_attendee(page, event_id, attendee_id, role_name)
    time.sleep(2)
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)
    time.sleep(2)

    edit_attendee_button = attendee_block.locator("button.editAttendee")
    edit_attendee_button.click()

    edit_attendee_dialog = page.locator("div#edit-attendee-modal")
    edit_attendee_dialog.scroll_into_view_if_needed()
    edit_attendee_dialog.wait_for(state="visible")

    input_first_name = edit_attendee_dialog.locator("input.attendeesFirstName")
    input_first_name.fill(attendee_first_name_2)
    input_last_name = edit_attendee_dialog.locator("input.attendeesLastName")
    input_last_name.fill(attendee_last_name_2)
    input_email = edit_attendee_dialog.locator("input.attendeesEmail")
    input_email.fill(attendee_email_2)
    update_button = edit_attendee_dialog.locator("button#editAttendeeBtn")
    update_button.click()

    time.sleep(2)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])

    actions.logout(page)

    email_content = email.look_for_email(EMAIL_SUBJECT_EVENT_INVITATION, EMAIL_FROM, attendee_email_2)
    assert email_content is not None

    activation_link = email.get_activate_account_link_from_email(email_content)
    assert activation_link is not None

    page.goto(activation_link)

    actions.fill_activation_form(page, attendee_password_2, attendee_first_name_2, attendee_last_name_2)

    confirmation_email_body = email.look_for_email(
        EMAIL_SUBJECT_CUSTOMER_ACCOUNT_CONFIRMATION, None, attendee_email_2, 300
    )
    assert "You've activated your customer account." in confirmation_email_body

    verify.no_upcoming_events_visible(page)
    verify.invite_is_of_type(page, "Wedding")
    verify.invite_has_name(page, event_name)
    verify.invite_role_is(page, role_name)
    verify.invite_look_is(page, look_name)

    top_section = page.locator("div.tmg-top-section")
    customer_section = top_section.locator("div.tmg-customer")

    current_customer_name = customer_section.locator("div.tmg-customer-name").inner_text()
    assert current_customer_name == f"{attendee_first_name_2} {attendee_last_name_2}"

    actions.logout(page)

    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    attendee_block = actions.get_attendee_block(page, event_id, attendee_id)

    edit_attendee_button = attendee_block.locator("button.editAttendee")
    edit_attendee_button.click()

    edit_attendee_dialog = page.locator("div#edit-attendee-modal")
    edit_attendee_dialog.scroll_into_view_if_needed()
    edit_attendee_dialog.wait_for(state="visible")

    input_first_name = edit_attendee_dialog.locator("input.attendeesFirstName")
    input_first_name.fill(attendee_first_name_3)
    input_last_name = edit_attendee_dialog.locator("input.attendeesLastName")
    input_last_name.fill(attendee_last_name_3)
    input_email = edit_attendee_dialog.locator("input.attendeesEmail")
    input_email.fill(attendee_email_3)
    update_button = edit_attendee_dialog.locator("button#editAttendeeBtn")
    update_button.click()

    time.sleep(2)

    actions.send_invites_to_attendees_by_id(page, event_id, [attendee_id])

    actions.logout(page)

    email_content = email.look_for_email(EMAIL_SUBJECT_EVENT_INVITATION, EMAIL_FROM, attendee_email_2)
    assert email_content is not None

    actions.login(page, attendee_email_2, attendee_password_2)

    time.sleep(2)

    verify.no_upcoming_events_visible(page)
