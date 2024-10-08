import signal

import awsgi
from aws_lambda_powertools.logging import correlation_paths

from server.app import init_app, init_sentry, init_db, lambda_teardown
from server.logs import powerlogger, init_logging

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
@powerlogger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def lambda_handler(event, context):
    return awsgi.response(app, event, context)


# Handle lambda termination gracefully
signal.signal(signal.SIGTERM, lambda_teardown)
