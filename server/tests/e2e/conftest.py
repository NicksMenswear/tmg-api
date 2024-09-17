import pytest
from playwright.sync_api import Page


# Viewports:
# 390 x 844 - mobile (iPhone 12)
# 1280 x 720 - desktop


def pytest_addoption(parser):
    parser.addoption(
        "--viewport", action="store", default="mobile", help="Viewport size. Default is either 'mobile' or 'desktop'"
    )


@pytest.fixture
def viewport_size(pytestconfig):
    viewport = pytestconfig.getoption("--viewport")

    if viewport == "desktop":
        return {"width": 1280, "height": 720}

    return {"width": 390, "height": 844}


@pytest.fixture
def page(browser, viewport_size) -> Page:
    context = browser.new_context(viewport=viewport_size)
    page = context.new_page()
    yield page
    page.close()
    context.close()
