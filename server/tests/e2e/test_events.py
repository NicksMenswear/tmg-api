from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD
from server.tests.e2e.utils import api, ui

EVENT_DATE = "2028-04-18"
EVENT_PRETTY_DATE = "Tuesday, April 18, 2028"


def test_basic_create_event(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    event_id = ui.create_new_event(page, event_name, EVENT_DATE)

    expect(page.get_by_role("heading", name=event_name).first).to_be_visible()
    expect(page.get_by_text(EVENT_PRETTY_DATE).first).to_be_visible()

    ui.open_event_accordion(page, event_id)

    ui.add_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)


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
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    event_id_1 = ui.create_new_event(page, event_name_1, EVENT_DATE)
    event_id_2 = ui.create_new_event(page, event_name_2, EVENT_DATE)

    ui.open_event_accordion(page, event_id_1)
    attendee_id_1 = ui.add_attendee(page, event_id_1, attendee_first_name_1, attendee_last_name_1, attendee_email_1)

    assert attendee_id_1 is not None

    ui.open_event_accordion(page, event_id_2)
    attendee_id_2 = ui.add_attendee(page, event_id_2, attendee_first_name_2, attendee_last_name_2, attendee_email_2)

    assert attendee_id_2 is not None


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
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    event_id = ui.create_new_event(page, event_name, EVENT_DATE)

    expect(page.get_by_role("heading", name=event_name).first).to_be_visible()
    expect(page.get_by_text(EVENT_PRETTY_DATE).first).to_be_visible()

    ui.open_event_accordion(page, event_id)

    attendee_id_1 = ui.add_attendee(page, event_id, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    assert attendee_id_1 is not None

    attendee_id_2 = ui.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    assert attendee_id_2 is not None

    attendee_id_3 = ui.add_attendee(page, event_id, attendee_first_name_3, attendee_last_name_3, attendee_email_3)
    assert attendee_id_3 is not None


def test_create_event_add_and_remove_attendees(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name_1 = utils.generate_unique_name()
    attendee_last_name_1 = utils.generate_unique_name()
    attendee_email_1 = utils.generate_email()
    attendee_first_name_2 = utils.generate_unique_name()
    attendee_last_name_2 = utils.generate_unique_name()
    attendee_email_2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    event_id = ui.create_new_event(page, event_name, EVENT_DATE)

    expect(page.get_by_role("heading", name=event_name).first).to_be_visible()
    expect(page.get_by_text(EVENT_PRETTY_DATE).first).to_be_visible()

    ui.open_event_accordion(page, event_id)

    attendee_id_1 = ui.add_attendee(page, event_id, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    assert attendee_id_1 is not None

    attendee_id_2 = ui.add_attendee(page, event_id, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    assert attendee_id_2 is not None

    ui.delete_attendee(page, attendee_id_1)


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
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    event_id_1 = ui.create_new_event(page, event_name_1, EVENT_DATE)
    event_id_2 = ui.create_new_event(page, event_name_2, EVENT_DATE)

    ui.open_event_accordion(page, event_id_1)

    attendee_id_1 = ui.add_attendee(page, event_id_1, attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    assert attendee_id_1 is not None

    ui.open_event_accordion(page, event_id_2)

    attendee_id_2 = ui.add_attendee(page, event_id_2, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    assert attendee_id_2 is not None

    ui.delete_event(page, event_id_1)

    expect(page.get_by_role("heading", name=event_name_1).first).not_to_be_visible()
    expect(page.get_by_role("heading", name=event_name_2).first).to_be_visible()


def test_delete_all_events(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    event_id = ui.create_new_event(page, event_name, EVENT_DATE)

    ui.open_event_accordion(page, event_id)

    attendee_id = ui.add_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    assert attendee_id is not None

    ui.delete_event(page, event_id)

    expect(page.get_by_role("heading", name=event_name).first).not_to_be_visible()


def test_delete_all_attendees(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name1 = utils.generate_unique_name()
    attendee_last_name1 = utils.generate_unique_name()
    attendee_email1 = utils.generate_email()
    attendee_first_name2 = utils.generate_unique_name()
    attendee_last_name2 = utils.generate_unique_name()
    attendee_email2 = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    event_id = ui.create_new_event(page, event_name, EVENT_DATE)

    ui.open_event_accordion(page, event_id)

    attendee_id1 = ui.add_attendee(page, event_id, attendee_first_name1, attendee_last_name1, attendee_email1)
    assert attendee_id1 is not None

    attendee_id2 = ui.add_attendee(page, event_id, attendee_first_name2, attendee_last_name2, attendee_email2)
    assert attendee_id2 is not None

    ui.delete_attendee(page, attendee_id1)
    ui.delete_attendee(page, attendee_id2)

    expect(page.get_by_text("No attendees added.").first).to_be_visible()


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
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    event_id1 = ui.create_new_event(page, event_name1, EVENT_DATE, "wedding")
    ui.open_event_accordion(page, event_id1)
    attendee_id1 = ui.add_attendee(page, event_id1, attendee_first_name1, attendee_last_name1, attendee_email1)
    assert attendee_id1 is not None
    wedding_roles = {
        role.inner_text().strip()
        for role in page.locator(
            f'div.tmg-attendees-item[data-attendee-id="{attendee_id1}"] div.tmg-attendees-role li.tmg-select-item'
        ).all()
    }
    assert {
        "Best Man",
        "Bride",
        "Father of the Bride",
        "Father of the Groom",
        "Groom",
        "Groomsman",
        "Officiant",
        "Usher",
    } == wedding_roles
    assert (
        page.locator(f'div.tmg-item[data-event-id="{event_id1}"] >> div.tmg-item-header-type').first.inner_text()
        == "Wedding"
    )

    event_id2 = ui.create_new_event(page, event_name2, EVENT_DATE, "prom")
    ui.open_event_accordion(page, event_id2)
    attendee_id2 = ui.add_attendee(page, event_id2, attendee_first_name2, attendee_last_name2, attendee_email2)
    assert attendee_id2 is not None
    prom_roles = {
        role.inner_text().strip()
        for role in page.locator(
            f'div.tmg-attendees-item[data-attendee-id="{attendee_id2}"] div.tmg-attendees-role li.tmg-select-item'
        ).all()
    }
    assert {"Attendee", "Attendee Parent or Chaperone"} == prom_roles
    assert (
        page.locator(f'div.tmg-item[data-event-id="{event_id2}"] >> div.tmg-item-header-type').first.inner_text()
        == "Prom"
    )

    event_id3 = ui.create_new_event(page, event_name3, EVENT_DATE, "other")
    ui.open_event_accordion(page, event_id3)
    attendee_id3 = ui.add_attendee(page, event_id3, attendee_first_name3, attendee_last_name3, attendee_email3)
    assert attendee_id3 is not None
    assert (
        page.locator(f'div.tmg-item[data-event-id="{event_id3}"] >> div.tmg-item-header-type').first.inner_text()
        == "Other"
    )


def test_roles_persistence_test():
    pass
