import signal
import awsgi

from server.logs import logger, correlation_paths, init_logging
from server.app import init_app, init_sentry, init_db, lambda_teardown


if __name__ == "__main__":
    print("Running a local dev server...")
    init_logging("tmg-api", debug=True)
    app = init_app()
    init_db()
    app.run(host="0.0.0.0", port=8080)
else:
    print("Running in AWS Lambda...")
    init_logging("tmg-api", debug=True)
    init_sentry()
    app = init_app()
    init_db()


# Entry point for the API lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def lambda_handler(event, context):
    return awsgi.response(app, event, context)


# Entry point for the sync users cronjob lambda
def lambda_job_sync_users_from_legacy_db(event, context):
    from server.jobs.sync_users_from_legacy_db import sync_users_from_legacy_db

    init_logging("job_sync_users_from_legacy_db", debug=True)
    init_sentry()
    sync_users_from_legacy_db()


# Entry point for the expedited shipping cronjob lambda
def lambda_job_add_expedited_shipping_for_suit_bundles(event, context):
    from server.jobs.add_expedited_shipping_for_suit_bundles import add_expedited_shipping_for_suit_bundles

    init_logging("job_add_expedited_shipping_for_suit_bundles", debug=True)
    init_sentry()
    add_expedited_shipping_for_suit_bundles()


# Handle lambda termination gracefully
signal.signal(signal.SIGTERM, lambda_teardown)
