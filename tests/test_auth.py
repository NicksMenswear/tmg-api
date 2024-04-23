import email

from playwright.sync_api import Page, expect

from utils import string, ui, email, TEST_USER_EMAIL, TEST_USER_PASSWORD, EMAIL_FROM


def test_login(page: Page):
    expect(page.locator("a", has_text="Logout")).not_to_be_visible()
    expect(page.locator("a", has_text="Account")).not_to_be_visible()

    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_role("link", name="Account Login")).not_to_be_visible()
    expect(page.get_by_role("link", name="Account Account")).to_be_visible()
    expect(page.get_by_role("link", name="Logout")).to_be_visible()


def test_signup_form(page: Page):
    first_name = f"f-{string.rnd_str(12)}"
    last_name = f"l-{string.rnd_str(12)}"
    user_email = f"e2etmg+{string.rnd_str(12)}@hotmail.com"
    password = string.rnd_str(12)

    ui.access_store(page)

    page.get_by_role("link", name="Login").click()
    page.get_by_role("link", name="Sign up").click()

    page.get_by_placeholder("First name").fill(first_name)
    page.get_by_placeholder("Last name").fill(last_name)
    page.get_by_placeholder("Email address*", exact=True).fill(user_email)
    page.get_by_role("button", name="Sign Up").click()

    found_email = email.look_for_email("Registration email", EMAIL_FROM, user_email, timeout_seconds=120)
    assert found_email is not None

    activation_link = string.link_from_email(found_email)
    assert activation_link is not None

    page.goto(activation_link)

    page.locator("#customer_password").fill(password)
    page.locator("#customer_password_confirmation").fill(password)
    page.get_by_role("button", name="Activate Account").click()

    confirmation_email_body = email.look_for_email("Customer account confirmation", None, user_email)
    assert "You've activated your customer account." in confirmation_email_body

    expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
