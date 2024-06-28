from typing import Set

from playwright.sync_api import Page, expect


def no_upcoming_events_visible(page: Page):
    events_locator = page.locator(".tmg-section-events")
    events_locator.scroll_into_view_if_needed()
    events_locator.wait_for(state="visible")

    tmg_event_content = page.locator(".tmg-event-content")
    tmg_event_content.locator(".preloader").wait_for(state="hidden")


def event_to_be_visible(page: Page, event_name: str, event_date: str = "Tuesday, April 18, 2028"):
    expect(page.get_by_role("heading", name=event_name).first).to_be_visible()
    # expect(page.get_by_text(event_date).first).to_be_visible()


def attendee_to_be_visible(page: Page, attendee_first_name: str, attendee_last_name: str):
    attendee_item = page.locator(
        f'//div[contains(@class, "tmg-attendees-item")]//div[@class="tmg-attendees-name" and contains(text(), "{attendee_first_name} {attendee_last_name}")]//ancestor::div[@class="tmg-attendees-item"]'
    ).first
    attendee_item.scroll_into_view_if_needed()
    attendee_item.wait_for(state="visible")
    expect(attendee_item.first).to_be_visible()


def no_attendee_added_to_be_visible(page: Page, event_id: str):
    expect(page.locator(f'div[data-event-id="{event_id}"] >> text=No attendees added.')).to_be_visible()


def roles_are_available_for_attendee(page: Page, attendee_id: str, roles_to_expect: Set[str]):
    roles = {
        role.inner_text().strip()
        for role in page.locator(
            f'div.tmg-attendees-item[data-attendee-id="{attendee_id}"] div.tmg-attendees-role li.tmg-select-item'
        ).all()
    }

    assert roles_to_expect == roles


def role_is_selected_for_attendee(page: Page, event_id: str, attendee_id: str, role_id: str):
    assert role_id == page.locator(
        f'div.tmg-item[data-event-id="{event_id}"] div.tmg-attendees-item[data-attendee-id="{attendee_id}"]'
    ).first.get_attribute("data-role-id")


def event_has_type(page: Page, event_id: str, event_type: str):
    assert (
        page.locator(f'div.tmg-item[data-event-id="{event_id}"] >> div.tmg-item-header-type').first.inner_text()
        == event_type
    )


def invite_is_of_type(page, expected_type):
    event_type = page.query_selector(".tmg-invite-event-type").inner_text()
    assert event_type == expected_type, f"Expected event type '{expected_type}', but got '{event_type}'"


def invite_has_name(page, expected_name):
    event_name = page.query_selector(".tmg-invite-event-name").inner_text()
    assert event_name == expected_name, f"Expected event name '{expected_name}', but got '{event_name}'"


def invite_event_date(page, expected_date):
    event_date = page.query_selector(".tmg-invite-event-date").inner_text()
    assert event_date == expected_date, f"Expected event date '{expected_date}', but got '{event_date}'"


def invite_role_is(page, expected_role):
    role_xpath = "//div[@class='tmg-invite-attendee-info'][span[text()='Role:']]"
    role = page.query_selector(role_xpath).inner_text().split("Role:")[1].strip()
    assert role == expected_role, f"Expected role '{expected_role}', but got '{role}'"


def invite_look_is(page, expected_look):
    look_xpath = "//div[@class='tmg-invite-attendee-info'][span[text()='Look:']]"
    look = page.query_selector(look_xpath).inner_text().split("Look:")[1].strip()
    assert look == expected_look, f"Expected look '{expected_look}', but got '{look}'"


def logged_in(page: Page):
    my_account_menu_item = page.locator('a.header__link:has-text("MY ACCOUNT")')
    parent_menu_item = my_account_menu_item.locator("..")
    parent_menu_item.hover()

    page.wait_for_selector(".navbar-dropdown .navbar-item#logoutButton", state="visible")
    logout_link = page.query_selector(".navbar-dropdown .navbar-item#logoutButton")

    assert logout_link.get_attribute("href") == "/account/logout" and logout_link.is_visible()


def not_logged_in(page: Page):
    my_account_menu_item = page.locator('a.header__link:has-text("MY ACCOUNT")')
    parent_menu_item = my_account_menu_item.locator("..")
    parent_menu_item.hover()

    page.wait_for_selector(".navbar-dropdown .navbar-item#loginButton", state="visible")
    login_link = page.query_selector(".navbar-dropdown .navbar-item#loginButton")

    assert login_link.get_attribute("href") == "/account" and login_link.is_visible()


def input_value_in_pay_dialog_for_attendee_by_name(page, first_name, last_name, value):
    attendee_1 = page.locator(
        f'li.tmg-pay-attendee-item:has(div.tmg-pay-attendee-item-title:text("{first_name} {last_name}"))'
    )
    input_1 = attendee_1.locator("input.tmg-pay-attendee-item-input")
    assert input_1.get_attribute("value") == str(value)


def warning_in_pay_dialog_for_attendee_by_name(page, first_name, last_name, warning):
    attendee_2 = page.locator(
        f'li.tmg-pay-attendee-item:has(div.tmg-pay-attendee-item-title:text("{first_name} {last_name}"))'
    )
    assert attendee_2.locator("p.tmg-pay-attendee-item-message").inner_text().strip() == warning


def shopify_checkout_has_item_with_name_and_price(page: Page, item_name: str, item_price: str):
    row_locator = page.locator(f'div[role="row"]:has-text("{item_name}")')
    row_locator.wait_for(state="visible")

    price_locator_in_row = row_locator.locator(f"text={item_price}")
    price_locator_in_row.wait_for(state="visible")

    assert price_locator_in_row.count() > 0


def looks_page_is_empty(page: Page):
    my_looks = page.locator(".tmg-section-looks .tmg-heading h1:has-text('My Looks')")
    my_looks.scroll_into_view_if_needed()
    my_looks.wait_for(state="visible")

    looks_message = page.locator(".tmg-empty-data p:has-text('Your looks will be displayed here.')")
    looks_message.scroll_into_view_if_needed()
    looks_message.wait_for(state="visible")
