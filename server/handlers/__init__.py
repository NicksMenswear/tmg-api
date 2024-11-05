import os

import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger

from server.version import get_version


def init_sentry():
    if os.getenv("TMG_APP_TESTING", "false").lower() == "true":
        return

    sentry_sdk.init(
        dsn="https://8e6bac4bea5b3bf97a544417ca20e275@o4507018035724288.ingest.us.sentry.io/4507018177609728",
        environment=os.getenv("STAGE"),
        release=get_version(),
    )

    for logger in ["connexion.decorators.validation"]:
        ignore_logger(logger)
