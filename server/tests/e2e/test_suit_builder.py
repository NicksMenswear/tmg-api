import time

import pytest
from playwright.sync_api import Page

from server.tests import utils
from server.tests.e2e import (
    e2e_allowed_in,
    e2e_error_handling,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    STORE_URL,
)
from server.tests.e2e.utils import api, actions, verify


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_8
def test_suit_builder_save_default(page: Page):
    look_name = utils.generate_look_name()

    actions.access_store(page)

    api.delete_all_events(TEST_USER_EMAIL)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    page.goto(f"{STORE_URL}/pages/suit-builder")

    actions.verify_that_suit_builder_price_list_items_selected(page, {"suit"})

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_9
def test_suit_builder_just_a_suit(page: Page):
    look_name = utils.generate_look_name()

    actions.access_store(page)

    api.delete_all_events(TEST_USER_EMAIL)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    page.goto(f"{STORE_URL}/pages/suit-builder")

    actions.enable_suit_builder_items(page, set())
    actions.verify_that_suit_builder_price_list_items_selected(page, {"suit"})

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price > 195


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_10
def test_suit_builder_neck_tie_and_socks_enabled(page: Page):
    look_name = utils.generate_look_name()

    actions.access_store(page)

    api.delete_all_events(TEST_USER_EMAIL)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    page.goto(f"{STORE_URL}/pages/suit-builder")

    actions.enable_suit_builder_items(page, {"tie", "socks"})
    actions.verify_that_suit_builder_price_list_items_selected(page, {"suit", "tie", "socks"})

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price > 300


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_1
def test_suit_builder_shirt_belt_shoes_enabled(page: Page):
    look_name = utils.generate_look_name()

    actions.access_store(page)

    api.delete_all_events(TEST_USER_EMAIL)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    page.goto(f"{STORE_URL}/pages/suit-builder")

    actions.enable_suit_builder_items(page, {"shirt", "belt", "shoes"})
    actions.verify_that_suit_builder_price_list_items_selected(page, {"shirt", "belt", "shoes"})

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price > 300


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
def test_suit_builder_bow_tie(page: Page):
    look_name = utils.generate_look_name()

    actions.access_store(page)

    api.delete_all_events(TEST_USER_EMAIL)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    page.goto(f"{STORE_URL}/pages/suit-builder")

    actions.enable_suit_builder_items(page, {"tie"})
    actions.verify_that_suit_builder_price_list_items_selected(page, {"suit", "tie"})

    actions.select_bow_ties_tab(page)

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price > 200


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_3
def test_suit_builder_select_nth_from_all_sections(page: Page):
    look_name = utils.generate_look_name()

    actions.access_store(page)

    api.delete_all_events(TEST_USER_EMAIL)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    page.goto(f"{STORE_URL}/pages/suit-builder")

    actions.enable_suit_builder_items(page, {"shirt", "tie", "belt", "shoes", "socks"})

    actions.select_suit_builder_item_by_index(page, "shirt", 2)
    actions.select_suit_builder_item_by_index(page, "tie", 20)
    actions.select_suit_builder_item_by_index(page, "belt", 1)
    actions.select_suit_builder_item_by_index(page, "shoes", 1)
    actions.select_suit_builder_item_by_index(page, "socks", 4)

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price > 400


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_4
def test_suit_builder_select_and_remove(page: Page):
    actions.access_store(page)

    api.delete_all_events(TEST_USER_EMAIL)
    actions.login(page, TEST_USER_EMAIL, TEST_USER_PASSWORD)

    user_id = api.get_user_by_email(TEST_USER_EMAIL).get("id")
    api.delete_all_looks(user_id)

    page.goto(f"{STORE_URL}/pages/looks")
    time.sleep(3)

    verify.looks_page_is_empty(page)

    page.goto(f"{STORE_URL}/pages/suit-builder")

    actions.enable_suit_builder_items(page, {"shirt", "tie", "belt", "shoes", "socks"})
    actions.verify_that_suit_builder_price_list_items_selected(page, {"suit", "shirt", "tie", "belt", "shoes", "socks"})

    actions.suit_builder_remove_item_by_type(page, "shirt")
    actions.suit_builder_remove_item_by_type(page, "tie")
    actions.suit_builder_remove_item_by_type(page, "belt")
    actions.suit_builder_remove_item_by_type(page, "shoes")
    actions.suit_builder_remove_item_by_type(page, "socks")

    actions.verify_that_suit_builder_price_list_items_selected(page, {"suit"})
