import time
from typing import List

from playwright.sync_api import Page, expect, Locator

from server.tests import utils
from server.tests.e2e import (
    REQUIRE_STORE_PASSWORD,
    STORE_URL,
    STORE_PASSWORD,
    HAS_ADDITIONAL_INITIAL_SCREEN_ON_STORE_ACCESS,
)
from server.tests.e2e.utils import api


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
    page.goto(f"{STORE_URL}/account")

    page.get_by_role("textbox", name="Email address", exact=True).fill(email)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Login").click()


def create_new_event(page: Page, event_name: str, event_date: str = "2028-04-18", event_type: str = "wedding"):
    page.get_by_role("button", name="New Event ").first.click()
    page.locator(f'label[data-event-type="{event_type}"]').first.click()
    page.locator("#eventName").fill(event_name)

    select_date_in_calendar(page)

    page.locator(f'input[value="{event_type}"]')
    page.get_by_role("button", name="Create").click()
    event_item = page.locator(f'.tmg-item[data-event-name="{event_name}"]')
    event_item.scroll_into_view_if_needed()
    event_item.wait_for(state="visible")

    event_id = event_item.get_attribute("data-event-id")

    assert event_id is not None

    return event_id


def select_date_in_calendar(page: Page):
    page.locator("#dropdown-date div .dp-year").select_option("2026")
    page.locator("#dropdown-date div .dp-month").select_option("March")
    page.locator("#dropdown-date div .dp-day").select_option("8")


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
        f'//div[contains(@class, "tmg-attendees-item") and .//div[@class="tmg-attendees-name" and contains(text(), "{attendee_first_name} {attendee_last_name}")]]'
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
        f'//div[contains(@class, "tmg-attendees-item") and .//div[@class="tmg-attendees-name" and contains(text(), "{attendee_first_name} {attendee_last_name}")]]'
    ).first
    attendee_item.scroll_into_view_if_needed()
    attendee_item.wait_for(state="visible")

    attendee_id = attendee_item.get_attribute("data-attendee-id")

    assert attendee_id is not None

    return attendee_id


def delete_event(page: Page, event_id: str, event_name: str):
    remove_event_btn = page.locator(f'div[data-event-id="{event_id}"] button.removeEvent')
    remove_event_btn.scroll_into_view_if_needed()
    remove_event_btn.click()

    confirm_btn = page.locator("#confirm-btn").first
    confirm_btn.scroll_into_view_if_needed()
    confirm_btn.wait_for(state="visible")
    confirm_btn.click()

    expect(page.get_by_role("heading", name=event_name).first).not_to_be_visible()


def delete_attendee(page: Page, event_id: str, attendee_id: str):
    event_locator = page.locator(f'div[data-event-id="{event_id}"]')

    delete_attendee_btn = event_locator.locator(
        f'//div[contains(@class, "tmg-attendees-item") and @data-attendee-id="{attendee_id}"]//button[contains(@class, "tmg-btn") and contains(@class, "removeAttendee")]'
    )
    delete_attendee_btn.scroll_into_view_if_needed()
    delete_attendee_btn.click()

    confirm_btn = page.locator("#confirm-btn").first
    confirm_btn.scroll_into_view_if_needed()
    confirm_btn.wait_for(state="visible")
    confirm_btn.click()

    attendee_item = event_locator.locator(f'div.tmg-attendees-item[data-attendee-id="{attendee_id}"]')
    attendee_item.wait_for(state="hidden")

    expect(attendee_item.first).not_to_be_visible()


def logout(page: Page):
    page.goto(f"{STORE_URL}/account/logout")


def sign_up(page: Page, first_name: str, last_name: str, email: str):
    page.goto(f"{STORE_URL}/account")

    page.get_by_role("link", name="Sign up").click()

    page.get_by_placeholder("First name").first.fill(first_name)
    page.get_by_placeholder("Last name").first.fill(last_name)
    page.get_by_placeholder("Email address*", exact=True).first.fill(email)
    page.get_by_role("button", name="Sign Up").click()


def fill_activation_form(page: Page, password: str, first_name: str = None, last_name: str = None):
    if first_name:
        page.locator("input#first_name").first.fill(first_name)
    if last_name:
        page.locator("input#last_name").first.fill(last_name)
    page.locator("#customer_phone").fill(utils.generate_phone_number())
    page.locator("#customer_password").fill(password)
    page.locator("#customer_password_confirmation").fill(password)

    activate_account_button = page.locator(f'//input[contains(@class, "tmg-btn") and @value="Activate Account"]').first
    activate_account_button.scroll_into_view_if_needed()
    activate_account_button.click()


def select_role_for_attendee(page: Page, event_id, attendee_id, role_name: str):
    event_locator = page.locator(f'div[data-event-id="{event_id}"]')
    attendee_locator = event_locator.locator(f'div[data-attendee-id="{attendee_id}"]')

    role_dropdown = attendee_locator.locator("div.tmg-attendees-role .tmg-select-title")
    role_dropdown.click()

    role_option = attendee_locator.locator(f'li[data-role-id] span.tmg-select-item-title:text("{role_name}")')
    role_option.click()

    return role_option.locator("..").get_attribute("data-role-id")


def select_look_for_attendee(page: Page, event_id, attendee_id, look_name: str):
    event_locator = page.locator(f'div[data-event-id="{event_id}"]')
    attendee_locator = event_locator.locator(f'div[data-attendee-id="{attendee_id}"]')

    look_dropdown = attendee_locator.locator("div.tmg-attendees-look .tmg-select-title")
    look_dropdown.click()

    look_option = attendee_locator.locator(f'li[data-look-id] span.tmg-select-item-title:text("{look_name}")')
    look_option.click()

    return look_option.locator("..").get_attribute("data-look-id")


def open_send_invites_dialog(page: Page, event_id):
    send_invites_button = page.locator(f'button[data-event-id="{event_id}"].inviteModal')
    send_invites_button.scroll_into_view_if_needed()
    send_invites_button.click()

    send_invites_dialog = page.locator(f"div#send-invite-modal.tmg-modal.showed")
    send_invites_dialog.wait_for(state="visible")

    return send_invites_dialog


def send_invites_to_attendees_by_id(page: Page, event_id, attendee_ids):
    send_invites_dialog = open_send_invites_dialog(page, event_id)

    for attendee_id in attendee_ids:
        invite_attendee_list_locator = page.locator("#inviteAttendeesList")
        attendee_locator = invite_attendee_list_locator.locator(
            f'li.tmg-invite-attendee-item[data-attendee-id="{attendee_id}"]'
        )
        checkbox_label_locator = attendee_locator.locator("label.tmg-checkbox")
        checkbox_label_locator.click()

    send_invites_button = send_invites_dialog.locator("button.tmg-btn.sendInvite")
    send_invites_button.click()


def open_pay_dialog(page: Page, event_id):
    pay_button = page.locator(f'button[data-event-id="{event_id}"].payModal')
    pay_button.scroll_into_view_if_needed()
    pay_button.click()

    pay_dialog = page.locator(f"div#pay-modal.tmg-modal.showed")
    pay_dialog.wait_for(state="visible")

    return pay_dialog


def pay_to_attendee_by_id(page: Page, event_id, attendee_id, amount):
    pay_dialog = open_pay_dialog(page, event_id)

    attendee_list_item = page.locator(f'li.tmg-pay-attendee-item[data-attendee-id="{attendee_id}"]')
    attendee_amount_input_element = attendee_list_item.locator("input.tmg-pay-attendee-item-input")

    attendee_amount_input_element.fill(str(amount))

    pay_button = pay_dialog.locator("button.tmg-btn.paySend")
    pay_button.click()


def create_default_look(page: Page, name):
    page.goto(f"{STORE_URL}/products/suit-builder", timeout=120000)

    look_name_input = page.locator(f'input[name="properties[_Name this Look]"]')
    look_name_input.fill(name)

    save_look_button = page.locator(f'input[type="button"][id="save_look_btn"]')
    save_look_button.click()


def get_look_by_name_on_looks_page(page: Page, look_name):
    page.wait_for_selector('div.tmg-heading h1:text("My Looks")', timeout=90000)

    look_card_locator = page.locator(f'div.tmg-look-card:has-text("{look_name}")')
    data_look_id = look_card_locator.get_attribute("data-look-id")
    data_look_variant_id = look_card_locator.get_attribute("data-look-variant-id")
    price_locator = look_card_locator.locator(".tmg-look-card-price")
    price = float(price_locator.inner_text().strip().replace("$", ""))

    assert price > 0

    return data_look_id, data_look_variant_id, price


def delete_look_by_look_id(page: Page, look_id):
    look_card_locator = page.locator(f'div.tmg-look-card[data-look-id="{look_id}"]')
    remove_button = look_card_locator.locator("button.removeLook")
    remove_button.click()

    modal_locator = page.locator("div.confirm-modal-container")
    modal_locator.wait_for()

    modal_header = modal_locator.locator("div.confirm-modal-header")
    assert modal_header.inner_text().strip() == "Remove Look"

    confirm_button_locator = modal_locator.locator("button#confirm-btn")
    confirm_button_locator.click()


def pay_in_full_attendee_by_id(page: Page, event_id, attendee_id, expected_amount):
    pay_dialog = open_pay_dialog(page, event_id)

    attendee_list_item = page.locator(f'li.tmg-pay-attendee-item[data-attendee-id="{attendee_id}"]')
    attendee_amount_input_element = attendee_list_item.locator("input.tmg-pay-attendee-item-input")
    pay_in_full_button = attendee_list_item.locator("button.tmg-btn.btnPayFull")
    pay_in_full_button.click()

    assert float(attendee_amount_input_element.input_value()) == expected_amount

    pay_button = pay_dialog.locator("button.tmg-btn.paySend")
    pay_button.click()


def add_look_to_cart(page: Page, look_id):
    look_card_locator = page.locator(f'div.tmg-look-card[data-look-id="{look_id}"]')
    add_to_cart_button = look_card_locator.locator("button.tmg-btn.lookToCart")
    add_to_cart_button.click()


def attendee_add_suit_to_cart(page: Page, event_id: str):
    add_suit_to_cart_button = page.locator(
        f'button.tmg-btn.addLookToCart[data-event-id="{event_id}"]:has-text("Add suit to Cart")'
    )
    add_suit_to_cart_button.click()


def get_add_myself_button(page: Page, event_id: str):
    event_locator = get_event_block(page, event_id)

    add_myself_button = event_locator.locator(f'button[data-event-id="{event_id}"].tmg-btn.addMySelf')
    add_myself_button.scroll_into_view_if_needed()
    add_myself_button.wait_for(state="visible")

    return add_myself_button


def get_attendee_id_by_name(page: Page, event_id: str, attendee_firstname: str, attendee_lastname: str) -> str:
    event_locator = get_event_block(page, event_id)

    attendee_item = event_locator.locator(
        f'//div[contains(@class, "tmg-attendees-item") and .//div[@class="tmg-attendees-name" and contains(text(), "{attendee_firstname} {attendee_lastname}")]]'
    ).first
    attendee_item.scroll_into_view_if_needed()
    attendee_item.wait_for(state="visible")

    attendee_id = attendee_item.get_attribute("data-attendee-id")

    assert attendee_id is not None

    return attendee_id


def get_event_id_by_name(page: Page, event_name: str):
    event_item = page.locator(f'.tmg-item[data-event-name="{event_name}"]').first
    event_item.scroll_into_view_if_needed()
    return event_item.get_attribute("data-event-id")


def get_event_block(page: Page, event_id: str) -> Locator:
    event_locator = page.locator(f'div[data-event-id="{event_id}"]')
    event_locator.scroll_into_view_if_needed()
    event_locator.wait_for(state="visible")

    return page.locator(f'div[data-event-id="{event_id}"]')


def get_attendee_block(page: Page, event_id: str, attendee_id: str) -> Locator:
    event_locator = get_event_block(page, event_id)

    attendee_locator = event_locator.locator(
        f'//div[contains(@class, "tmg-attendees-item") and @data-attendee-id="{attendee_id}"]'
    )
    attendee_locator.scroll_into_view_if_needed()
    attendee_locator.wait_for(state="visible")

    return attendee_locator


def get_owner_fit_survey_button(page: Page, event_id: str, attendee_id: str) -> Locator:
    attendee_locator = get_attendee_block(page, event_id, attendee_id)

    fit_survey_button = attendee_locator.locator('button:has-text("Fit Quiz")').first
    fit_survey_button.scroll_into_view_if_needed()
    fit_survey_button.wait_for(state="visible")

    return fit_survey_button


def get_owner_add_suit_to_cart_button(page: Page, event_id: str, attendee_id: str) -> Locator:
    attendee_locator = get_attendee_block(page, event_id, attendee_id)

    add_suit_to_cart_button = attendee_locator.locator("button.addSuitToCart").first
    add_suit_to_cart_button.scroll_into_view_if_needed()
    add_suit_to_cart_button.wait_for(state="visible")

    return add_suit_to_cart_button


def get_fit_survey_dialog(page: Page) -> Locator:
    fit_survey_dialog = page.locator("div#size-selection.tmg-modal.showed")
    fit_survey_dialog.scroll_into_view_if_needed()
    fit_survey_dialog.wait_for(state="visible")

    return fit_survey_dialog


def populate_fit_survey(
    page: Page,
    age: int = 40,
    gender: str = "Male",  # Male | Female
    weight: int = 180,
    height_feet: int = 5,
    height_inch: int = 10,
    shoe_size: str = "10.5 Wide",  # 7 | 7.5 | 8 | 8.5 | 9 | 9 Wide | 9.5 | 9.5 Wide | 10 | 10 Wide | 10.5 | 10.5 Wide | 11 | 11 Wide | 11.5 | 11.5 Wide | 12 | 12 Wide | 13 | 13 Wide | 14 | 14 Wide | 15 | 16 |
    chest_shape: str = "Moderate",  # Low | Moderate | High
    stomach_shape: str = "Average",  # Flat | Average | Belly
    hip_shape: str = "Moderate",  # Low | Moderate | High
):
    fit_survey_dialog = get_fit_survey_dialog(page)

    # age
    age_input = fit_survey_dialog.locator("#measurement_age")
    age_input.fill(str(age))

    # gender
    gender_radio_button = page.locator(
        f'//label[.//span[text()="{gender}"] and .//input[@name="measurement_gender" and @value="{gender}"]]'
    )
    gender_radio_button.click()

    # weight
    weight_input = fit_survey_dialog.locator("#measurement_weight")
    weight_input.scroll_into_view_if_needed()
    weight_input.wait_for(state="visible")
    weight_input.fill(str(weight))

    # height
    height_feet_input = fit_survey_dialog.locator("#measurement_height")
    height_feet_input.scroll_into_view_if_needed()
    height_feet_input.wait_for(state="visible")
    height_feet_input.fill(str(height_feet))
    height_feet_inch_input = fit_survey_dialog.locator("#measurement_height_inch")
    height_feet_inch_input.fill(str(height_inch))

    # shoes size
    measurement_shoe_size_select = fit_survey_dialog.locator("#measurement_shoe_size")
    measurement_shoe_size_select.scroll_into_view_if_needed()
    measurement_shoe_size_select.wait_for(state="visible")
    measurement_shoe_size_select.select_option(shoe_size)

    # chest shape
    measurement_chest_shape_radio_button = page.locator(
        f'//input[@name="measurement_chest_shape" and @value="{chest_shape}"]/parent::label'
    )
    measurement_chest_shape_radio_button.scroll_into_view_if_needed()
    measurement_chest_shape_radio_button.wait_for(state="visible")
    measurement_chest_shape_radio_button.click()

    # stomach shape
    measurement_stomach_shape_radio_button = page.locator(
        f'//input[@name="measurement_stomach_shape" and @value="{stomach_shape}"]/parent::label'
    )
    measurement_stomach_shape_radio_button.scroll_into_view_if_needed()
    measurement_stomach_shape_radio_button.wait_for(state="visible")
    measurement_stomach_shape_radio_button.click()

    # hip shape
    measurement_hip_shape_radio_button = page.locator(
        f'//input[@name="measurement_hip_shape" and @value="{hip_shape}"]/parent::label'
    )
    measurement_hip_shape_radio_button.scroll_into_view_if_needed()
    measurement_hip_shape_radio_button.wait_for(state="visible")
    measurement_hip_shape_radio_button.click()

    # submit
    submit_button = fit_survey_dialog.locator("button.tmg-btn.setMeasurementBtn")
    submit_button.scroll_into_view_if_needed()
    submit_button.wait_for(state="visible")
    submit_button.click()


def attendee_checkbox_selected(page, event_id: str, attendee_id: str, type: str) -> bool:
    attendee_item = get_attendee_block(page, event_id, attendee_id)

    check_element = attendee_item.locator(f'//li[.//span[text()="{type}"]]')

    return check_element.evaluate("element => element.classList.contains('active')")


def is_assign_look_checkbox_selected(page, event_id: str, attendee_id: str):
    return attendee_checkbox_selected(page, event_id, attendee_id, "Assign Look")


def is_invite_checkbox_selected(page, event_id: str, attendee_id: str):
    return attendee_checkbox_selected(page, event_id, attendee_id, "Invite")


def is_fit_checkbox_selected(page, event_id: str, attendee_id: str):
    return attendee_checkbox_selected(page, event_id, attendee_id, "Fit")


def is_pay_checkbox_selected(page, event_id: str, attendee_id: str):
    return attendee_checkbox_selected(page, event_id, attendee_id, "Pay")


def is_ship_checkbox_selected(page, event_id: str, attendee_id: str):
    return attendee_checkbox_selected(page, event_id, attendee_id, "Ship")


def shopify_checkout_pay_with_credit_card_for_order(page: Page, firstname: str, lastname: str):
    iframe = page.frame_locator("iframe.card-fields-iframe").first

    input_cc_number = iframe.locator("input#number")
    input_cc_number.fill("1")

    time.sleep(1)

    input_name_number = iframe.locator("input#name")
    input_name_number.fill(f"{firstname} {lastname}")

    time.sleep(1)

    input_expiry_number = iframe.locator("input#expiry")
    input_expiry_number.fill("11/32")

    time.sleep(1)

    input_cvc_number = iframe.locator("input#verification_value")
    input_cvc_number.fill("123")

    time.sleep(1)

    pay_now_button = page.locator('button:has-text("Pay now")').first
    pay_now_button.click()

    time.sleep(5)

    order_confirmed_element = page.locator('h2:has-text("Your order is confirmed")')
    expect(order_confirmed_element.first).to_be_visible()


def shopify_checkout_enter_billing_address(
    page: Page,
    firstname: str,
    lastname: str,
    address1: str = "709 Redwood Drive",
    city: str = "Cedar Falls",
    state: str = "IA",
    zip: str = "50613",
):
    input_firstname = page.locator('input[name="firstName"]').first
    input_firstname.fill(firstname)

    input_lastname = page.locator('input[name="lastName"]').first
    input_lastname.fill(lastname)

    input_address1 = page.locator("#billing-address1").first
    input_address1.fill(address1)

    input_city = page.locator('input[name="city"]').first
    input_city.fill(city)

    select_state_element = page.locator('select[name="zone"]').first
    select_state_element.select_option(state)

    input_zip = page.locator('input[name="postalCode"]').first
    input_zip.fill(zip)


def shopify_checkout_continue_to_shipping(page: Page):
    try:
        continue_to_shipping_button = page.locator('button:has-text("Continue to shipping")').first
        continue_to_shipping_button.click()
    except:
        pass


def shopify_checkout_continue_to_payment(page: Page):
    continue_to_payment_button = page.locator('button:has-text("Continue to payment")').first
    continue_to_payment_button.click()


def get_processed_discount_codes_for_event(event_id: str) -> List[str]:
    iteration = 0

    while iteration <= 24:  # 2 minutes
        discounts = api.get_discounts_for_event(event_id)

        assert len(discounts) == 1

        if len(discounts[0].get("gift_codes")) == 0:
            time.sleep(5)
            iteration += 1
            break

        return [discount.get("code") for discount in discounts[0].get("gift_codes")]

    return []


def get_get_started_dialog_locator(page: Page) -> Locator:
    get_started_dialog = page.locator("div.tmg-get-started-modal")
    get_started_dialog.scroll_into_view_if_needed()
    get_started_dialog.wait_for(state="visible")

    return get_started_dialog


def get_started_select_event_type(get_started_dialog_locator: Locator, event_type: str = "wedding") -> None:
    event_label = get_started_dialog_locator.locator(f"label.radio-image-item[data-event-type='{event_type}']")
    event_label.click()


def get_started_click_next_button(get_started_dialog_locator: Locator) -> None:
    next_button = get_started_dialog_locator.locator("button#next")
    next_button.click()


def get_started_select_event_role(get_started_dialog_locator: Locator, event_role: str = "bride") -> None:
    role_label = get_started_dialog_locator.locator(f"label.radio-image-item[data-event-role='{event_role}']")
    role_label.click()


def populate_what_is_special_occasion_dialog(page: Page, event_type: str = "wedding"):
    get_started_dialog_locator = get_get_started_dialog_locator(page)

    get_started_select_event_type(get_started_dialog_locator, event_type)
    get_started_click_next_button(get_started_dialog_locator)

    get_started_select_event_role(get_started_dialog_locator, "bride")
    get_started_click_next_button(get_started_dialog_locator)

    select_date_in_calendar(page)
    get_started_click_next_button(get_started_dialog_locator)
