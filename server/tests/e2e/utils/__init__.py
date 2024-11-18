import inspect
from datetime import datetime

from playwright.sync_api import Page


def is_mobile_view(page: Page):
    return page.viewport_size["width"] < 768


def take_screenshot(page: Page, name: str):
    caller_frame = inspect.stack()[1]
    test_name = caller_frame.function
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    page.screenshot(path=f"../../../screenshots/{test_name}.{name}.{timestamp}.png", full_page=True)


def take_error_screenshot(page: Page):
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    page.screenshot(path=f"../../../screenshots/error.{timestamp}.png", full_page=True)
