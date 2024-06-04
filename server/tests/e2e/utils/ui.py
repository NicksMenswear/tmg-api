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


def add_participant(page: Page, attendee_first_name: str, attendee_last_name: str, attendee_email: str):
    page.get_by_role("button", name="Add Participant").click()
    page.locator('input[name="attendees_first_name"]').fill(attendee_first_name)
    page.locator('input[name="attendees_last_name"]').fill(attendee_last_name)
    page.locator('input[name="attendees_email"]').fill(attendee_email)
    page.get_by_role("button", name="Save").click()
