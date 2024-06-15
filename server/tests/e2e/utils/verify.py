from typing import Set

from playwright.sync_api import Page, expect


def no_upcoming_events_visible(page: Page):
    expect(page.locator(".tmg-section-events >> text=No Upcoming Events.")).to_be_visible()


def event_to_be_visible(page: Page, event_name: str, event_date: str):
    expect(page.get_by_role("heading", name=event_name).first).to_be_visible()
    expect(page.get_by_text(event_date).first).to_be_visible()


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


def logged_in(page: Page):
    expect(page.get_by_role("link", name="Account Login")).not_to_be_visible()
    expect(page.get_by_role("link", name="Account Account")).to_be_visible()
    expect(page.get_by_role("link", name="Logout")).to_be_visible()


def not_logged_in(page: Page):
    expect(page.locator("a", has_text="Logout")).not_to_be_visible()
    expect(page.locator("a", has_text="Account")).not_to_be_visible()
