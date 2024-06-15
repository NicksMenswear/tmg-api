from datetime import datetime, timedelta

from playwright.sync_api import Page, expect

from server.tests.e2e import (
    REQUIRE_STORE_PASSWORD,
    STORE_URL,
    STORE_PASSWORD,
    HAS_ADDITIONAL_INITIAL_SCREEN_ON_STORE_ACCESS,
)
from server.tests.e2e.utils import verify


def access_store(page: Page):
    page.goto(STORE_URL)

    if REQUIRE_STORE_PASSWORD:
        page.get_by_label("Enter store password").fill(STORE_PASSWORD)
        page.get_by_role("button", name="Enter").click()

    if HAS_ADDITIONAL_INITIAL_SCREEN_ON_STORE_ACCESS:
        page.get_by_role("link", name="Enter store using password").click()
        page.get_by_placeholder("Your password").fill(STORE_PASSWORD)
        page.get_by_role("button", name="Enter").click()


def login(page: Page, email: str, password: str):
    page.get_by_role("link", name="Login").click()
    page.get_by_role("textbox", name="Email address", exact=True).fill(email)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Login").click()


def create_new_event(page: Page, event_name: str, event_date: str = None, event_type: str = "wedding"):
    page.get_by_role("button", name="New Event ").first.click()
    page.locator(f'label[data-event-type="{event_type}"]').first.click()
    page.locator("#eventName").fill(event_name)
    page.locator("#eventDate").fill(
        event_date if event_date else (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    )
    page.locator(f'input[value="{event_type}"]')
    page.get_by_role("button", name="Create").click()
    event_item = page.locator(f'.tmg-item[data-event-name="{event_name}"]')
    event_item.scroll_into_view_if_needed()
    event_item.wait_for(state="visible")

    event_id = event_item.get_attribute("data-event-id")

    assert event_id is not None

    return event_id


def expect_no_upcoming_events_visible(page: Page):
    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()


def expect_event_to_be_visible(page: Page, event_name: str, event_date: str):
    expect(page.get_by_role("heading", name=event_name).first).to_be_visible()
    expect(page.get_by_text(event_date).first).to_be_visible()


def expect_attendee_to_be_visible(page: Page, attendee_first_name: str, attendee_last_name: str):
    attendee_item = page.locator(
        f'//div[contains(@class, "tmg-attendees-item")]//div[@class="tmg-attendees-name" and contains(text(), "{attendee_first_name} {attendee_last_name}")]//ancestor::div[@class="tmg-attendees-item"]'
    ).first
    attendee_item.scroll_into_view_if_needed()
    attendee_item.wait_for(state="visible")
    expect(attendee_item.first).to_be_visible()


def open_event_accordion(page: Page, event_id: str):
    event_item = page.locator(f'.tmg-item[data-event-id="{event_id}"]')
    event_item.scroll_into_view_if_needed()
    event_item.wait_for(state="visible")
    event_item.click()


def add_first_attendee(
    page: Page, attendee_first_name: str, attendee_last_name: str, attendee_email: str, button_text: str = "Save"
):
    attendees_first_name_element = page.locator(".attendeesFirstName").first
    attendees_first_name_element.scroll_into_view_if_needed()
    attendees_first_name_element.fill(attendee_first_name)

    attendees_last_name_element = page.locator(".attendeesLastName").last
    attendees_last_name_element.scroll_into_view_if_needed()
    attendees_last_name_element.fill(attendee_last_name)

    attendees_email_element = page.locator(".attendeesEmail").first
    attendees_email_element.scroll_into_view_if_needed()
    attendees_email_element.fill(attendee_email)

    add_attendee_button = page.locator(f'//button[@class="tmg-btn" and contains(text(), "{button_text}")]').first
    add_attendee_button.scroll_into_view_if_needed()
    add_attendee_button.wait_for(state="visible")
    add_attendee_button.click()

    attendee_item = page.locator(
        f'//div[contains(@class, "tmg-attendees-item")]//div[@class="tmg-attendees-name" and contains(text(), "{attendee_first_name} {attendee_last_name}")]//ancestor::div[@class="tmg-attendees-item"]'
    ).first

    attendee_id = attendee_item.get_attribute("data-attendee-id")

    assert attendee_id is not None

    return attendee_id


def add_attendee(
    page: Page,
    event_id: str,
    attendee_first_name: str,
    attendee_last_name: str,
    attendee_email: str,
    button_text: str = "Save",
):
    add_participant_button = page.locator(f'button.addAttendees[data-event-id="{event_id}"]')
    add_participant_button.scroll_into_view_if_needed()
    add_participant_button.wait_for(state="visible")
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

    add_attendee_button = page.locator(f'//button[@class="tmg-btn" and contains(text(), "{button_text}")]').first
    add_attendee_button.scroll_into_view_if_needed()
    add_attendee_button.wait_for(state="visible")
    add_attendee_button.click()

    attendee_item = page.locator(
        f'//div[contains(@class, "tmg-attendees-item")]//div[@class="tmg-attendees-name" and contains(text(), "{attendee_first_name} {attendee_last_name}")]//ancestor::div[@class="tmg-attendees-item"]'
    ).first
    attendee_item.scroll_into_view_if_needed()
    attendee_item.wait_for(state="visible")

    return attendee_item.get_attribute("data-attendee-id")


def delete_event(page: Page, event_id: str, event_name: str):
    remove_event_btn = page.locator(f'div[data-event-id="{event_id}"] button.removeEvent')
    remove_event_btn.scroll_into_view_if_needed()
    remove_event_btn.click()

    confirm_btn = page.locator("#confirm-btn").first
    confirm_btn.scroll_into_view_if_needed()
    confirm_btn.wait_for(state="visible")
    confirm_btn.click()

    expect(page.get_by_role("heading", name=event_name).first).not_to_be_visible()


def delete_attendee(page: Page, attendee_id: str):
    delete_attendee_btn = page.locator(
        f'//div[@class="tmg-attendees-item" and @data-attendee-id="{attendee_id}"]//button[contains(@class, "tmg-btn") and contains(@class, "removeAttendee")]'
    )
    delete_attendee_btn.scroll_into_view_if_needed()
    delete_attendee_btn.click()

    confirm_btn = page.locator("#confirm-btn").first
    confirm_btn.scroll_into_view_if_needed()
    confirm_btn.wait_for(state="visible")
    confirm_btn.click()

    attendee_item = page.locator(f'div.tmg-attendees-item[data-attendee-id="{attendee_id}"]')
    attendee_item.wait_for(state="hidden")

    expect(attendee_item.first).not_to_be_visible()


def logout(page: Page):
    page.get_by_role("link", name="Logout").click()


def sing_up(page: Page, first_name: str, last_name: str, email: str):
    page.get_by_role("link", name="Login").click()
    page.get_by_role("link", name="Sign up").click()

    page.get_by_placeholder("First name").fill(first_name)
    page.get_by_placeholder("Last name").fill(last_name)
    page.get_by_placeholder("Email address*", exact=True).fill(email)
    page.get_by_role("button", name="Sign Up").click()


def activation_enter_password(page: Page, password: str):
    page.locator("#customer_password").fill(password)
    page.locator("#customer_password_confirmation").fill(password)
    page.get_by_role("button", name="Activate Account").click()


def select_role_for_attendee(page: Page, event_id, attendee_id, role_name: str):
    page.locator(
        f'div.tmg-item[data-event-id="{event_id}"] div.tmg-attendees-item[data-attendee-id="{attendee_id}"] div.tmg-select'
    ).first.click()

    page.locator(
        f'div.tmg-item[data-event-id="{event_id}"] div.tmg-attendees-item[data-attendee-id="{attendee_id}"] ul.tmg-select-items li.tmg-select-item >> text="{role_name}"'
    ).first.click()

    return page.locator(
        f'div.tmg-item[data-event-id="{event_id}"] div.tmg-attendees-item[data-attendee-id="{attendee_id}"]'
    ).first.get_attribute("data-role-id")
