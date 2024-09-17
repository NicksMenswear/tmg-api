from playwright.sync_api import Page


def is_mobile_view(page: Page):
    return page.viewport_size["width"] < 768
