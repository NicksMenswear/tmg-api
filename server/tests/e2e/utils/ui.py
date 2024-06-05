from datetime import datetime, timedelta

from playwright.sync_api import Page

from server.tests.e2e import REQUIRE_STORE_PASSWORD, STORE_URL, STORE_PASSWORD


def access_store(page: Page):
    if REQUIRE_STORE_PASSWORD:
        page.goto(STORE_URL)
        page.get_by_label("Enter store password").fill(STORE_PASSWORD)
        page.get_by_role("button", name="Enter").click()


def login(page: Page, email: str, password: str):
    page.get_by_role("link", name="Login").click()
    page.get_by_role("textbox", name="Email address", exact=True).fill(email)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Login").click()


def create_new_event(page: Page, event_name: str, event_date: str = None):
    page.get_by_role("button", name="New Event ").first.click()
    page.locator("#eventName").fill(event_name)
    page.locator("#eventDate").fill(
        event_date if event_date else (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    )
    page.get_by_role("button", name="Create").click()
    event_item = page.locator(f'.tmg-item[data-event-name="{event_name}"]')
    event_item.wait_for(state="visible")
    event_item.scroll_into_view_if_needed()

    return event_item.get_attribute("data-event-id")


def open_event_accordion(page: Page, event_id: str):
    event_item = page.locator(f'.tmg-item[data-event-id="{event_id}"]')
    event_item.wait_for(state="visible")
    event_item.scroll_into_view_if_needed()
    event_item.click()


def add_attendee(page: Page, event_id: str, attendee_first_name: str, attendee_last_name: str, attendee_email: str):
    add_participant_button = page.locator(f'button.addAttendees[data-event-id="{event_id}"]')
    add_participant_button.wait_for(state="visible")
    add_participant_button.scroll_into_view_if_needed()
    add_participant_button.click()

    attendees_first_name_element = page.locator(".attendeesFirstName").first
    attendees_first_name_element.scroll_into_view_if_needed()
    attendees_first_name_element.fill(attendee_first_name)

    attendees_last_name_element = page.locator(".attendeesLastName").last
    attendees_last_name_element.scroll_into_view_if_needed()
    attendees_last_name_element.fill(attendee_last_name)

    attendees_email_element = page.locator(".attendeesEmail").first
    attendees_email_element.scroll_into_view_if_needed()
    attendees_email_element.fill(attendee_email)

    add_attendee_button = page.locator(f'//button[@class="tmg-btn" and contains(text(), "Add Attendee")]')
    add_attendee_button.wait_for(state="visible")
    add_attendee_button.scroll_into_view_if_needed()
    add_attendee_button.click()

    attendee_item = page.locator(
        f'//div[contains(@class, "tmg-attendees-item")]//div[@class="tmg-attendees-name" and contains(text(), "{attendee_first_name} {attendee_last_name}")]//ancestor::div[@class="tmg-attendees-item"]'
    ).first
    attendee_item.wait_for(state="visible")

    return attendee_item.get_attribute("data-attendee-id")


def delete_event(page: Page, event_id: str):
    remove_event_btn = page.locator(f'div[data-event-id="{event_id}"] button.removeEvent')
    remove_event_btn.scroll_into_view_if_needed()
    page.once("dialog", lambda dialog: dialog.accept())
    remove_event_btn.click()
    remove_event_btn.wait_for(state="hidden")


def delete_attendee(page: Page, attendee_id: str):
    delete_attendee_btn = page.locator(
        f'//div[@class="tmg-attendees-item" and @data-attendee-id="{attendee_id}"]//button[contains(@class, "tmg-btn") and contains(@class, "removeAttendee")]'
    )
    delete_attendee_btn.scroll_into_view_if_needed()
    page.once("dialog", lambda dialog: dialog.accept())
    delete_attendee_btn.click()

    attendee_item = page.locator(f'div.tmg-attendees-item[data-attendee-id="{attendee_id}"]')
    attendee_item.wait_for(state="hidden")
