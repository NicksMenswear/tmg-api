import signal

import awsgi

from server.app import init_app, init_logging, init_sentry, init_db, lambda_teardown

if __name__ == "__main__":
    print("Running a local dev server...")
    init_logging(debug=True)
    app = init_app()
    init_db()
    app.run(host="0.0.0.0", port=8080)
else:
    print("Running in AWS Lambda...")
    init_logging(debug=True)
    init_sentry()
    app = init_app()
    init_db()


# This is the entry point for the AWS Lambda function
def lambda_handler(event, context):
    return awsgi.response(app, event, context)


def lambda_job_sync_users_from_legacy_db(event, context):
    from server.jobs.sync_users_from_legacy_db import sync_users_from_legacy_db

    init_logging(debug=True)
    init_sentry()
    sync_users_from_legacy_db()


# Handle lambda termination gracefully
signal.signal(signal.SIGTERM, lambda_teardown)
