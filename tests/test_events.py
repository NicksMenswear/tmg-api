from playwright.sync_api import Page, expect

import utils
from utils import api, string, ui


def test_basic_create_event(page: Page):
    event_name = f"test-event-{string.rnd_str()}"
    attendee_first_name = "f-" + string.rnd_str(4)
    attendee_last_name = "l-" + string.rnd_str(4)
    attendee_email = f"test-{string.rnd_str()}@example.com"

    api.delete_all_events(utils.TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, utils.TEST_USER_EMAIL, utils.TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events").first).to_be_visible()

    ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name, attendee_last_name, attendee_email)

    expect(page.get_by_text(event_name).first).to_be_visible()
    expect(page.get_by_text("TUESDAY 18, APR 2028").first).to_be_visible()
    expect(page.get_by_role("button", name="ADD PARTICIPANT")).to_be_visible()
    expect(page.get_by_role("button", name="SEND INVITE")).to_be_visible()
    expect(page.get_by_text("No Upcoming Events").first).not_to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name} {attendee_last_name}")).to_be_visible()


def test_create_multiple_events(page: Page):
    event_name_1 = f"test-event-{string.rnd_str()}"
    attendee_first_name_1 = "f-" + string.rnd_str(4)
    attendee_last_name_1 = "l-" + string.rnd_str(4)
    attendee_email_1 = f"test-{string.rnd_str()}@example.com"
    event_name_2 = f"test-event-{string.rnd_str()}"
    attendee_first_name_2 = "f-" + string.rnd_str(4)
    attendee_last_name_2 = "l-" + string.rnd_str(4)
    attendee_email_2 = f"test-{string.rnd_str()}@example.com"

    api.delete_all_events(utils.TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, utils.TEST_USER_EMAIL, utils.TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events").first).to_be_visible()

    ui.create_new_event(page, event_name_1, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    ui.create_new_event(page, event_name_2, "2028-04-18", attendee_first_name_2, attendee_last_name_2, attendee_email_2)

    expect(page.get_by_text(event_name_1).first).to_be_visible()
    expect(page.get_by_text(event_name_2).first).to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()


def test_create_event_and_add_few_attendees(page: Page):
    event_name = f"test-event-{string.rnd_str()}"
    attendee_first_name_1 = "f-" + string.rnd_str(4)
    attendee_last_name_1 = "l-" + string.rnd_str(4)
    attendee_email_1 = f"test-{string.rnd_str()}@example.com"
    attendee_first_name_2 = "f-" + string.rnd_str(4)
    attendee_last_name_2 = "l-" + string.rnd_str(4)
    attendee_email_2 = f"test-{string.rnd_str()}@example.com"
    attendee_first_name_3 = "f-" + string.rnd_str(4)
    attendee_last_name_3 = "l-" + string.rnd_str(4)
    attendee_email_3 = f"test-{string.rnd_str()}@example.com"

    api.delete_all_events(utils.TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, utils.TEST_USER_EMAIL, utils.TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events").first).to_be_visible()

    ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    ui.add_participant(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    ui.add_participant(page, attendee_first_name_3, attendee_last_name_3, attendee_email_3)

    expect(page.get_by_text(event_name).first).to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name_3} {attendee_last_name_3}")).to_be_visible()


def test_create_event_add_and_remove_attendees(page: Page):
    event_name = f"test-event-{string.rnd_str()}"
    attendee_first_name_1 = "f-" + string.rnd_str(4)
    attendee_last_name_1 = "l-" + string.rnd_str(4)
    attendee_email_1 = f"test-{string.rnd_str()}@example.com"
    attendee_first_name_2 = "f-" + string.rnd_str(4)
    attendee_last_name_2 = "l-" + string.rnd_str(4)
    attendee_email_2 = f"test-{string.rnd_str()}@example.com"

    api.delete_all_events(utils.TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, utils.TEST_USER_EMAIL, utils.TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events").first).to_be_visible()

    ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    ui.add_participant(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)

    expect(page.get_by_text(event_name).first).to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()

    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#attendeeDeletebutton path").nth(1).click()

    expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).not_to_be_visible()


def test_delete_single_event(page: Page):
    event_name_1 = f"test-event-{string.rnd_str()}"
    attendee_first_name_1 = "f-" + string.rnd_str(4)
    attendee_last_name_1 = "l-" + string.rnd_str(4)
    attendee_email_1 = f"test-{string.rnd_str()}@example.com"
    attendee_first_name_2 = "f-" + string.rnd_str(4)
    attendee_last_name_2 = "l-" + string.rnd_str(4)
    attendee_email_2 = f"test-{string.rnd_str()}@example.com"
    event_name_2 = f"test-event-{string.rnd_str()}"
    attendee_first_name_3 = "f-" + string.rnd_str(4)
    attendee_last_name_3 = "l-" + string.rnd_str(4)
    attendee_email_3 = f"test-{string.rnd_str()}@example.com"

    api.delete_all_events(utils.TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, utils.TEST_USER_EMAIL, utils.TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events").first).to_be_visible()

    ui.create_new_event(page, event_name_1, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
    ui.add_participant(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
    ui.create_new_event(page, event_name_2, "2029-04-18", attendee_first_name_3, attendee_last_name_3, attendee_email_3)

    expect(page.get_by_text(event_name_1).first).to_be_visible()
    expect(page.get_by_text(event_name_2).first).to_be_visible()

    page.once("dialog", lambda dialog: dialog.accept())
    page.locator(".customTrashBox").nth(1).click()

    expect(page.get_by_text(event_name_1)).to_be_visible()
    expect(page.get_by_text(event_name_2)).not_to_be_visible()


def test_delete_all_events(page: Page):
    event_name_1 = f"test-event-{string.rnd_str()}"
    attendee_first_name_1 = "f-" + string.rnd_str(4)
    attendee_last_name_1 = "l-" + string.rnd_str(4)
    attendee_email_1 = f"test-{string.rnd_str()}@example.com"

    api.delete_all_events(utils.TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, utils.TEST_USER_EMAIL, utils.TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events").first).to_be_visible()

    ui.create_new_event(page, event_name_1, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)

    expect(page.get_by_text("No Upcoming Events").first).not_to_be_visible()

    expect(page.get_by_text(event_name_1).first).to_be_visible()

    page.once("dialog", lambda dialog: dialog.accept())
    # page.locator(".customTrashBox").nth(0).click()
    page.evaluate(f"() => document.querySelector('.customTrashBox').click()")

    expect(page.get_by_text(event_name_1)).not_to_be_visible()

    expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
