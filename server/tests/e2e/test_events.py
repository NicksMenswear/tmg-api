from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD
from server.tests.e2e.utils import api, ui


def test_basic_create_event(page: Page):
    event_name = utils.generate_event_name()
    attendee_first_name = utils.generate_unique_name()
    attendee_last_name = utils.generate_unique_name()
    attendee_email = utils.generate_unique_email()

    api.delete_all_events(TEST_USER_EMAIL)
    ui.access_store(page)
    ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    expect(page.get_by_text("No Upcoming Events.").first).to_be_visible()

    ui.create_new_event(page, event_name, "2028-04-18")

    expect(page.get_by_text(event_name).first).to_be_visible()
    expect(page.get_by_text("TUESDAY 18, APR 2028").first).to_be_visible()
    expect(page.get_by_role("button", name="ADD PARTICIPANT")).to_be_visible()
    expect(page.get_by_role("button", name="SEND INVITE")).to_be_visible()
    expect(page.get_by_text("No Upcoming Events").first).not_to_be_visible()
    expect(page.get_by_role("heading", name=f"{attendee_first_name} {attendee_last_name}")).to_be_visible()


# def test_create_multiple_events(page: Page):
#     event_name_1 = f"test-event-{string.rnd_str()}"
#     attendee_first_name_1 = "f-" + string.rnd_str(4)
#     attendee_last_name_1 = "l-" + string.rnd_str(4)
#     attendee_email_1 = f"test-{string.rnd_str()}@example.com"
#     event_name_2 = f"test-event-{string.rnd_str()}"
#     attendee_first_name_2 = "f-" + string.rnd_str(4)
#     attendee_last_name_2 = "l-" + string.rnd_str(4)
#     attendee_email_2 = f"test-{string.rnd_str()}@example.com"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name_1, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
#     ui.create_new_event(page, event_name_2, "2028-04-18", attendee_first_name_2, attendee_last_name_2, attendee_email_2)
#
#     expect(page.get_by_text(event_name_1).first).to_be_visible()
#     expect(page.get_by_text(event_name_2).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
#
#
# def test_create_event_and_add_few_attendees(page: Page):
#     event_name = f"test-event-{string.rnd_str()}"
#     attendee_first_name_1 = "f-" + string.rnd_str(4)
#     attendee_last_name_1 = "l-" + string.rnd_str(4)
#     attendee_email_1 = f"test-{string.rnd_str()}@example.com"
#     attendee_first_name_2 = "f-" + string.rnd_str(4)
#     attendee_last_name_2 = "l-" + string.rnd_str(4)
#     attendee_email_2 = f"test-{string.rnd_str()}@example.com"
#     attendee_first_name_3 = "f-" + string.rnd_str(4)
#     attendee_last_name_3 = "l-" + string.rnd_str(4)
#     attendee_email_3 = f"test-{string.rnd_str()}@example.com"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
#     ui.add_participant(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
#     ui.add_participant(page, attendee_first_name_3, attendee_last_name_3, attendee_email_3)
#
#     expect(page.get_by_text(event_name).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_3} {attendee_last_name_3}")).to_be_visible()
#
#
# def test_create_event_add_and_remove_attendees(page: Page):
#     event_name = f"test-event-{string.rnd_str()}"
#     attendee_first_name_1 = "f-" + string.rnd_str(4)
#     attendee_last_name_1 = "l-" + string.rnd_str(4)
#     attendee_email_1 = f"test-{string.rnd_str()}@example.com"
#     attendee_first_name_2 = "f-" + string.rnd_str(4)
#     attendee_last_name_2 = "l-" + string.rnd_str(4)
#     attendee_email_2 = f"test-{string.rnd_str()}@example.com"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
#     ui.add_participant(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
#
#     expect(page.get_by_text(event_name).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
#
#     page.once("dialog", lambda dialog: dialog.accept())
#     page.locator("#attendeeDeletebutton path").nth(1).click()
#
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).not_to_be_visible()
#
#
# def test_delete_single_event(page: Page):
#     event_name_1 = f"test-event-{string.rnd_str()}"
#     attendee_first_name_1 = "f-" + string.rnd_str(4)
#     attendee_last_name_1 = "l-" + string.rnd_str(4)
#     attendee_email_1 = f"test-{string.rnd_str()}@example.com"
#     attendee_first_name_2 = "f-" + string.rnd_str(4)
#     attendee_last_name_2 = "l-" + string.rnd_str(4)
#     attendee_email_2 = f"test-{string.rnd_str()}@example.com"
#     event_name_2 = f"test-event-{string.rnd_str()}"
#     attendee_first_name_3 = "f-" + string.rnd_str(4)
#     attendee_last_name_3 = "l-" + string.rnd_str(4)
#     attendee_email_3 = f"test-{string.rnd_str()}@example.com"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name_1, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
#     ui.add_participant(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
#     ui.create_new_event(page, event_name_2, "2029-04-18", attendee_first_name_3, attendee_last_name_3, attendee_email_3)
#
#     expect(page.get_by_text(event_name_1).first).to_be_visible()
#     expect(page.get_by_text(event_name_2).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_3} {attendee_last_name_3}")).to_be_visible()
#
#     page.once("dialog", lambda dialog: dialog.accept())
#     page.locator(".customTrashBox").nth(1).click()
#
#     expect(page.get_by_text(event_name_1)).to_be_visible()
#     expect(page.get_by_text(event_name_2)).not_to_be_visible()
#
#
# def test_delete_all_events(page: Page):
#     event_name_1 = f"test-event-{string.rnd_str()}"
#     attendee_first_name_1 = "f-" + string.rnd_str(4)
#     attendee_last_name_1 = "l-" + string.rnd_str(4)
#     attendee_email_1 = f"test-{string.rnd_str()}@example.com"
#     event_name_2 = f"test-event-{string.rnd_str()}"
#     attendee_first_name_2 = "f-" + string.rnd_str(4)
#     attendee_last_name_2 = "l-" + string.rnd_str(4)
#     attendee_email_2 = f"test-{string.rnd_str()}@example.com"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name_1, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
#     ui.create_new_event(page, event_name_2, "2028-04-18", attendee_first_name_2, attendee_last_name_2, attendee_email_2)
#
#     expect(page.get_by_text("No Upcoming Events").first).not_to_be_visible()
#
#     expect(page.get_by_text(event_name_1).first).to_be_visible()
#     expect(page.get_by_text(event_name_2).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
#
#     page.once("dialog", lambda dialog: dialog.accept())
#     page.evaluate(f"() => document.querySelector('.customTrashBox').click()")
#
#     expect(page.get_by_text(event_name_1)).not_to_be_visible()
#     expect(page.get_by_text(event_name_2).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).not_to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
#
#     page.once("dialog", lambda dialog: dialog.accept())
#     page.evaluate(f"() => document.querySelector('.customTrashBox').click()")
#
#     expect(page.get_by_text(event_name_2).first).not_to_be_visible()
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#
# def test_send_invites_for_1_out_of_2_attendee(page: Page):
#     event_name = f"test-event-{string.rnd_str()}"
#     attendee_first_name_1 = "f-" + string.rnd_str(4)
#     attendee_last_name_1 = "l-" + string.rnd_str(4)
#     attendee_email_1 = f"e2etmg+{string.rnd_str(8)}@hotmail.com"
#     attendee_first_name_2 = "f-" + string.rnd_str(4)
#     attendee_last_name_2 = "l-" + string.rnd_str(4)
#     attendee_email_2 = f"e2etmg+{string.rnd_str(8)}@hotmail.com"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
#     ui.add_participant(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
#
#     expect(page.get_by_text(event_name).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
#
#     attendee_1_checkbox_id = page.locator(f'input[data-email="{attendee_email_1}"]').get_attribute("id")
#     label_1 = page.locator(f'label[for="{attendee_1_checkbox_id}"]')
#     label_1.wait_for(state="visible")
#     label_1.scroll_into_view_if_needed()
#     label_1.click()
#
#     page.get_by_role("button", name="Send Invite").click()
#
#     expect(page.locator("#inviteModal")).to_contain_text(f"{attendee_first_name_1} {attendee_last_name_1}")
#
#     page.get_by_role("button", name="Send Invites").click()
#
#     attendee_1_email_content = email.look_for_email("Wedding Invite", EMAIL_FROM, attendee_email_1)
#     assert attendee_1_email_content is not None
#
#
# def test_send_invites_for_all_attendees(page: Page):
#     event_name = f"test-event-{string.rnd_str()}"
#     attendee_first_name_1 = "f-" + string.rnd_str(4)
#     attendee_last_name_1 = "l-" + string.rnd_str(4)
#     attendee_email_1 = f"e2etmg+{string.rnd_str(8)}@hotmail.com"
#     attendee_first_name_2 = "f-" + string.rnd_str(4)
#     attendee_last_name_2 = "l-" + string.rnd_str(4)
#     attendee_email_2 = f"e2etmg+{string.rnd_str(8)}@hotmail.com"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name_1, attendee_last_name_1, attendee_email_1)
#     ui.add_participant(page, attendee_first_name_2, attendee_last_name_2, attendee_email_2)
#
#     expect(page.get_by_text(event_name).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_1} {attendee_last_name_1}")).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name_2} {attendee_last_name_2}")).to_be_visible()
#
#     check_all_checkbox_id = page.locator('input[type="checkbox"].checkAll[data-id][id^="checkAll_"]').get_attribute(
#         "id"
#     )
#     check_all_label = page.locator(f'label[for="{check_all_checkbox_id}"]')
#     check_all_label.wait_for(state="visible")
#     check_all_label.scroll_into_view_if_needed()
#     check_all_label.click()
#
#     page.get_by_role("button", name="Send Invite").click()
#
#     expect(page.locator("#inviteModal")).to_contain_text(f"{attendee_first_name_1} {attendee_last_name_1}")
#     expect(page.locator("#inviteModal")).to_contain_text(f"{attendee_first_name_2} {attendee_last_name_2}")
#
#     page.get_by_role("button", name="Send Invites").click()
#
#     attendee_1_email_content = email.look_for_email("Wedding Invite", EMAIL_FROM, attendee_email_1)
#     assert attendee_1_email_content is not None
#
#     attendee_2_email_content = email.look_for_email("Wedding Invite", EMAIL_FROM, attendee_email_2)
#     assert attendee_2_email_content is not None
#
#
# def test_send_invites_and_activate_new_account(page: Page):
#     event_name = f"test-event-{string.rnd_str()}"
#     attendee_first_name = "f-" + string.rnd_str(4)
#     attendee_last_name = "l-" + string.rnd_str(4)
#     attendee_email = f"e2etmg+{string.rnd_str(8)}@hotmail.com"
#     attendee_password = "123456"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name, attendee_last_name, attendee_email)
#
#     expect(page.get_by_text(event_name).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name} {attendee_last_name}")).to_be_visible()
#
#     checkbox_id = page.locator(f'input[data-email="{attendee_email}"]').get_attribute("id")
#     label = page.locator(f'label[for="{checkbox_id}"]')
#     label.wait_for(state="visible")
#     label.scroll_into_view_if_needed()
#     label.click()
#
#     page.get_by_role("button", name="Send Invite").click()
#
#     expect(page.locator("#inviteModal")).to_contain_text(f"{attendee_first_name} {attendee_last_name}")
#
#     page.get_by_role("button", name="Send Invites").click()
#
#     email_content = email.look_for_email("Wedding Invite", EMAIL_FROM, attendee_email)
#     assert email_content is not None
#
#     activation_link = string.link_from_email(email_content)
#
#     assert activation_link is not None
#
#     page.goto(activation_link)
#
#     page.locator("#customer_password").fill(attendee_password)
#     page.locator("#customer_password_confirmation").fill(attendee_password)
#     page.get_by_role("button", name="Activate Account").click()
#
#     confirmation_email_body = email.look_for_email("Customer account confirmation", None, attendee_email, 300)
#     assert "You've activated your customer account." in confirmation_email_body
#
#
# def test_send_invites_for_existing_account(page: Page):
#     event_name = f"test-event-{string.rnd_str()}"
#     attendee_first_name = "f-" + string.rnd_str(4)
#     attendee_last_name = "l-" + string.rnd_str(4)
#     attendee_email = f"e2etmg+{string.rnd_str(8)}@hotmail.com"
#
#     api.delete_all_events(TEST_USER_EMAIL)
#     api.create_user(attendee_first_name, attendee_last_name, attendee_email, True)
#     ui.access_store(page)
#     ui.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
#
#     expect(page.get_by_text("No Upcoming Events").first).to_be_visible()
#
#     ui.create_new_event(page, event_name, "2028-04-18", attendee_first_name, attendee_last_name, attendee_email)
#
#     expect(page.get_by_text(event_name).first).to_be_visible()
#     expect(page.get_by_role("heading", name=f"{attendee_first_name} {attendee_last_name}")).to_be_visible()
#
#     checkbox_id = page.locator(f'input[data-email="{attendee_email}"]').get_attribute("id")
#     label = page.locator(f'label[for="{checkbox_id}"]')
#     label.wait_for(state="visible")
#     label.scroll_into_view_if_needed()
#     label.click()
#
#     page.get_by_role("button", name="Send Invite").click()
#
#     expect(page.locator("#inviteModal")).to_contain_text(f"{attendee_first_name} {attendee_last_name}")
#
#     page.get_by_role("button", name="Send Invites").click()
#
#     email_content = email.look_for_email("Wedding Invite", EMAIL_FROM, attendee_email)
#     assert email_content is not None
#
#     login_link = string.link_from_email(email_content, "Click Here")
#
#     assert login_link is not None
#     # TODO: Uncomment once link in email is fixed
#     # assert login_link == f"{STORE_URL}/account/login"
