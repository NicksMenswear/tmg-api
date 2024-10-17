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

SUIT_PRICE = 260.0
SHIRT_PRICE = 50.0
NECK_TIE_PRICE = 40.0
BOW_TIE_PRICE = 40.0
PREMIUM_POCKET_SQUARE_PRICE = 10.0
BELT_PRICE = 30.0
SHOES_PRICE = 115.0
SOCKS_PRICE = 5.0


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
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

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
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
    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price == SUIT_PRICE


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
def test_suit_builder_neck_tie_socks_and_premium_pocket_square_enabled(page: Page):
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

    actions.enable_suit_builder_items(page, {"tie", "socks", "premium_pocket_square"})
    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price == SUIT_PRICE + NECK_TIE_PRICE + SOCKS_PRICE + PREMIUM_POCKET_SQUARE_PRICE


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
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
    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price == SUIT_PRICE + SHIRT_PRICE + BELT_PRICE + SHOES_PRICE


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
    actions.select_bow_ties_tab(page)

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert price == SUIT_PRICE + BOW_TIE_PRICE


@e2e_allowed_in({"dev", "stg", "prd"})
@e2e_error_handling
@pytest.mark.group_2
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

    actions.enable_suit_builder_items(page, {"shirt", "tie", "premium_pocket_square", "belt", "shoes", "socks"})

    actions.select_suit_builder_item_by_index(page, "shirt", 2)
    actions.select_suit_builder_item_by_index(page, "tie", 20)
    actions.select_suit_builder_item_by_index(page, "premium_pocket_square", 2)
    actions.select_suit_builder_item_by_index(page, "belt", 1)
    actions.select_suit_builder_item_by_index(page, "shoes", 1)
    actions.select_suit_builder_item_by_index(page, "socks", 4)

    actions.save_look_with_name(page, look_name)

    data_look_id, data_look_variant_id, price = actions.get_look_by_name_on_looks_page(page, look_name)

    assert data_look_id is not None
    assert (
        price
        == SUIT_PRICE
        + SHIRT_PRICE
        + NECK_TIE_PRICE
        + PREMIUM_POCKET_SQUARE_PRICE
        + BELT_PRICE
        + SHOES_PRICE
        + SOCKS_PRICE
    )
