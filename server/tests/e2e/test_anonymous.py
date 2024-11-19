import pytest
from playwright.sync_api import Page

from server.tests.e2e import e2e_allowed_in, e2e_error_handling
from server.tests.e2e.utils import actions


@e2e_allowed_in({"dev"})
@e2e_error_handling
@pytest.mark.group_9
def test_buy_sized_shoes_and_tie(page: Page):
    actions.access_store(page)
    # 1. go to /products/the-tan-suit
    # 2. click on `Fit quiz`
    # 3. populate fit quiz with random email
