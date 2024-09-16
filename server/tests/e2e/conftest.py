import pytest
from playwright.sync_api import Page


# Viewports:
# 390 x 844 - iPhone 12
# 1280 x 720 - Desktop


def pytest_addoption(parser):
    parser.addoption("--viewport", action="store", default="390x844", help="Viewport size. Default is '390x844'")


@pytest.fixture
def viewport_size(pytestconfig):
    viewport = pytestconfig.getoption("--viewport")

    if not viewport:
        return {"width": 390, "height": 844}

    sizes = viewport.lower().split("x")

    return {"width": int(sizes[0]), "height": int(sizes[1])}


@pytest.fixture
def page(browser, viewport_size) -> Page:
    context = browser.new_context(viewport=viewport_size)
    page = context.new_page()
    yield page
    page.close()
    context.close()
