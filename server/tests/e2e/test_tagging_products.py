import time

import pytest
from playwright.sync_api import Page, expect

from server.tests import utils
from server.tests.e2e import TEST_USER_EMAIL, TEST_USER_PASSWORD, STORE_URL, e2e_allowed_in, e2e_error_handling
from server.tests.e2e.utils import api, actions, verify, shopify


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_5
def test_suit_bundle_tagging_correctness_for_default_suit(page: Page):
    look_name = utils.generate_look_name()

    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    shopify_variant = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id}")

    tags = shopify_variant.get("product", {}).get("tags", [])

    assert {
        "has_belt",
        "has_neck_tie",
        "has_shirt",
        "has_shoes",
        "has_socks",
        "has_tie",
        "hidden",
        "not_linked_to_event",
        "suit_bundle",
    } == set(tags)


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_5
def test_suit_bundle_tagging_correctness_for_socks_and_belt_only(page: Page):
    look_name = utils.generate_look_name()

    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)
    page.goto(f"{STORE_URL}/pages/suit-builder")
    actions.enable_suit_builder_items(page, {"socks", "belt"})
    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    shopify_variant = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id}")

    tags = shopify_variant.get("product", {}).get("tags", [])

    assert {
        "has_belt",
        "has_socks",
        "hidden",
        "not_linked_to_event",
        "suit_bundle",
    } == set(tags)


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_5
def test_associate_look_to_attendee(page: Page):
    event_name = utils.generate_event_name()
    look_name = utils.generate_look_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    page.goto(f"{STORE_URL}/pages/looks")
    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name)
    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    shopify_variant = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id}")

    tags = set(shopify_variant.get("product", {}).get("tags", []))
    assert "not_linked_to_event" in tags
    assert "linked_to_event" not in tags

    page.goto(f"{STORE_URL}/account")

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)

    time.sleep(2)

    shopify_variant = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id}")

    tags = shopify_variant.get("product", {}).get("tags", [])

    assert "not_linked_to_event" not in tags
    assert "linked_to_event" in tags


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
def test_associate_look_to_attendee_then_remove_event(page: Page):
    event_name = utils.generate_event_name()
    look_name = utils.generate_look_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    page.goto(f"{STORE_URL}/pages/looks")
    verify.looks_page_is_empty(page)
    actions.create_default_look(page, look_name)
    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    shopify_variant = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id}")
    tags = set(shopify_variant.get("product", {}).get("tags", []))
    assert "not_linked_to_event" in tags
    assert "linked_to_event" not in tags

    page.goto(f"{STORE_URL}/account")
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name)

    time.sleep(2)

    shopify_variant = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id}")
    tags = shopify_variant.get("product", {}).get("tags", [])
    assert "not_linked_to_event" not in tags
    assert "linked_to_event" in tags

    actions.delete_event(page, event_id, event_name)

    time.sleep(2)

    shopify_variant = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id}")
    tags = set(shopify_variant.get("product", {}).get("tags", []))
    assert "not_linked_to_event" in tags
    assert "linked_to_event" not in tags


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
def test_associate_look1_and_then_look2(page: Page):
    event_name = utils.generate_event_name()
    look_name_1 = utils.generate_look_name()
    look_name_2 = utils.generate_look_name()
    attendee_first_name = f"E2E {utils.generate_unique_name()}"
    attendee_last_name = f"E2E {utils.generate_unique_name()}"
    attendee_email = utils.generate_email()

    api.delete_all_events(TEST_USER_EMAIL)
    actions.access_store(page)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)
    verify.no_upcoming_events_visible(page)

    time.sleep(1)

    event_id = actions.create_new_event(page, event_name)
    attendee_id = actions.add_first_attendee(page, event_id, attendee_first_name, attendee_last_name, attendee_email)
    event_block = actions.get_event_block(page, event_id)
    expect(event_block).to_be_visible()

    page.goto(f"{STORE_URL}/pages/looks")
    verify.looks_page_is_empty(page)

    actions.create_default_look(page, look_name_1)
    actions.create_default_look(page, look_name_2)

    _, data_look_variant_id_1, _ = actions.get_look_by_name_on_looks_page(page, look_name_1)
    _, data_look_variant_id_2, _ = actions.get_look_by_name_on_looks_page(page, look_name_2)

    shopify_variant_1 = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id_1}")
    tags_1 = set(shopify_variant_1.get("product", {}).get("tags", []))
    assert "not_linked_to_event" in tags_1
    assert "linked_to_event" not in tags_1

    shopify_variant_2 = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id_2}")
    tags_2 = set(shopify_variant_2.get("product", {}).get("tags", []))
    assert "not_linked_to_event" in tags_2
    assert "linked_to_event" not in tags_2

    page.goto(f"{STORE_URL}/account")
    actions.select_look_for_attendee(page, event_id, attendee_id, look_name_1)

    time.sleep(2)

    shopify_variant_1 = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id_1}")
    tags_1 = shopify_variant_1.get("product", {}).get("tags", [])
    assert "not_linked_to_event" not in tags_1
    assert "linked_to_event" in tags_1

    actions.select_look_for_attendee(page, event_id, attendee_id, look_name_2)
    shopify_variant_2 = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id_2}")
    tags_2 = shopify_variant_2.get("product", {}).get("tags", [])
    assert "not_linked_to_event" in tags_2
    assert "linked_to_event" not in tags_2

    actions.select_look_for_attendee(page, event_id, attendee_id, look_name_2)

    time.sleep(2)

    shopify_variant_1 = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id_1}")
    tags_1 = shopify_variant_1.get("product", {}).get("tags", [])
    assert "not_linked_to_event" in tags_1
    assert "linked_to_event" not in tags_1

    actions.select_look_for_attendee(page, event_id, attendee_id, look_name_2)
    shopify_variant_2 = shopify.get_variant_by_id(f"gid://shopify/ProductVariant/{data_look_variant_id_2}")
    tags_2 = shopify_variant_2.get("product", {}).get("tags", [])
    assert "not_linked_to_event" not in tags_2
    assert "linked_to_event" in tags_2
