from playwright.sync_api import Page


def test_signup_form(page: Page):
    page.goto("https://themodern-groom.myshopify.com/password")
    page.get_by_label("Enter store password").click()
    page.get_by_label("Enter store password").fill("test")
    page.get_by_role("button", name="Enter").click()
    page.get_by_role("link", name="Account Login").click()
    page.get_by_role("link", name="Sign up").click()
    page.get_by_placeholder("First name").click()
    page.get_by_placeholder("First name").fill("test")
    page.get_by_placeholder("First name").press("Tab")
    page.get_by_placeholder("Last name").fill("test")
    page.get_by_placeholder("Email address*", exact=True).click()
    page.get_by_placeholder("Email address*", exact=True).fill("zinovii+02@themoderngroom.com")
    page.get_by_role("button", name="Sign Up").click()
