from playwright.sync_api import Page

BASE_STORE_URL = "https://quickstart-a91e1214.myshopify.com"
CONFIG_REQUIRE_STORE_PASSWORD = True
CONFIG_STORE_PASSWORD = "test123"


def access_store(page: Page):
    if CONFIG_REQUIRE_STORE_PASSWORD:
        page.goto(BASE_STORE_URL)
        page.get_by_label("Enter store password").fill(CONFIG_STORE_PASSWORD)
        page.get_by_role("button", name="Enter").click()


def login(page: Page, email: str, password: str):
    page.get_by_role("link", name="Login").click()
    page.get_by_role("textbox", name="Email address", exact=True).fill(email)
    page.get_by_placeholder("Password").fill(password)
    page.get_by_role("button", name="Login").click()


def create_new_event(
    page: Page, event_name: str, event_date: str, attendee_first_name: str, attendee_last_name: str, attendee_email: str
):
    page.get_by_role("link", name="NEW EVENTS").click()
    page.get_by_label("Event Name:").fill(event_name)
    page.get_by_label("Event Date:").fill(event_date)
    page.get_by_role("button", name="Save").click()
    page.locator('input[name="attendees_first_name"]').fill(attendee_first_name)
    page.locator('input[name="attendees_last_name"]').fill(attendee_last_name)
    page.locator('input[name="attendees_email"]').fill(attendee_email)
    page.get_by_role("button", name="Save").click()


def add_participant(page: Page, attendee_first_name: str, attendee_last_name: str, attendee_email: str):
    page.get_by_role("button", name="Add Participant").click()
    page.locator('input[name="attendees_first_name"]').fill(attendee_first_name)
    page.locator('input[name="attendees_last_name"]').fill(attendee_last_name)
    page.locator('input[name="attendees_email"]').fill(attendee_email)
    page.get_by_role("button", name="Save").click()
