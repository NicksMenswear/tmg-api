import uuid

from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD, EMAIL_FROM
from server.tests.e2e.utils import actions, email, verify


def test_login(page: Page):
    verify.not_logged_in(page)

    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.logged_in(page)


def test_signup_form(page: Page):
    first_name = f"{utils.generate_unique_name(8, 12)}"
    last_name = f"{utils.generate_unique_name(8, 12)}"
    user_email = f"e2etmg+{utils.generate_unique_string()}@hotmail.com"
    password = str(uuid.uuid4())

    actions.access_store(page)

    actions.sing_up(page, first_name, last_name, user_email)

    email_content = email.look_for_email("The Modern Groom: Account Created", EMAIL_FROM, user_email)
    assert email_content is not None

    activation_link = email.link_from_email(email_content)
    assert activation_link is not None

    page.goto(activation_link)

    actions.activation_enter_password(page, password)

    confirmation_email_body = email.look_for_email("Customer account confirmation", None, user_email, 300)
    assert "You've activated your customer account." in confirmation_email_body

    verify.no_upcoming_events_visible(page)


def test_logout(page: Page):
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    verify.logged_in(page)

    page.get_by_role("link", name="Logout").click()

    verify.not_logged_in(page)
